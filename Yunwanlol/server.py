import json
import random
from flask import Flask, render_template, request, redirect, url_for
from flask_wtf.csrf import CSRFProtect  # 新增CSRF保护

app = Flask(__name__, template_folder='templates')
app.config.update(
    JSON_AS_ASCII=False,
    TEMPLATES_AUTO_RELOAD=True,
    SECRET_KEY='your-secret-key-here'  # 必须设置用于生产环境
)
csrf = CSRFProtect(app)  # 启用CSRF保护

class QuizData:
    """封装数据加载逻辑"""
    def __init__(self):
        self.teams = []
        self.questions = []
        self.load_data()

    def load_data(self):
        """安全加载JSON数据"""
        try:
            with open('teams.json', 'r', encoding='utf-8') as f:
                self.teams = json.load(f).get('teams', [])

            with open('yunwan.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.questions = data.get('questions', [])
                random.shuffle(self.questions)
                
        except Exception as e:
            print(f"数据加载失败: {e}")
            # 提供默认数据保证服务可用性
            self.teams = [{'id': 0, 'name': '默认队伍', 'points': 0}]
            self.questions = []

# 初始化数据
quiz_data = QuizData()

@app.route('/')
def yunwanlol():
    return render_template('yunwanlol.html')

@app.route('/yunwan')
def yunwan():
    return render_template('yunwan.html', teams=quiz_data.teams)

@app.route('/ranking')
def ranking():
    teams = sorted(quiz_data.teams, key=lambda x: -x['points'])
    return render_template('Ranking.html', teams=teams)

@app.route('/start', methods=['POST'])
def start():
    try:
        team_id = int(request.form['team'])
        random.shuffle(quiz_data.questions)  # 重新打乱题目
        return redirect(url_for('questions', team_id=team_id, q_index=0))
    except (ValueError, KeyError):
        return redirect(url_for('yunwan'))

@app.route('/questions/<int:team_id>/<int:q_index>', methods=['GET', 'POST'])
def questions(team_id, q_index):
    team = next((t for t in quiz_data.teams if t['id'] == team_id), None)
    if not team or q_index >= len(quiz_data.questions):
        return redirect(url_for('yunwan'))

    if request.method == 'POST':
        try:
            selected = int(request.form['answer'])
            is_correct = selected == quiz_data.questions[q_index]['answer']
            
            if is_correct:
                team['points'] += 1
                # Vercel环境建议改用数据库，此处保留但添加警告
                print("警告：文件写入在Vercel无服务器环境中可能失效")

            return redirect(url_for(
                'result',
                team_id=team_id,
                q_index=q_index,
                is_correct=str(is_correct).lower()  # 确保布尔值转为字符串
            ))
        except (ValueError, KeyError):
            return redirect(url_for('questions', team_id=team_id, q_index=q_index))

    return render_template(
        'questions.html',
        team=team,
        q_index=q_index,
        question=quiz_data.questions[q_index]
    )

# 其他路由保持不变...

# Vercel必需配置
def create_app():
    return app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

