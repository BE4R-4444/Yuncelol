import json
import os
from flask import Flask, render_template, request, redirect, url_for, current_app, render_template_string
import sys
import io
import random
from werkzeug.middleware.proxy_fix import ProxyFix

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

app = Flask(__name__, template_folder='templates')
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

app.config.update(
    JSON_AS_ASCII=False,
    TEMPLATES_AUTO_RELOAD=True,
    PREFERRED_URL_SCHEME='https'
)
app.jinja_env.auto_reload = True
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

# Vercel适配的文件路径处理
def get_data_path(filename):
    if 'VERCEL' in os.environ:
        return f'/tmp/{filename}'
    return filename

def init_data():
    """初始化数据文件"""
    for filename in ['teams.json', 'yunwan.json']:
        src_path = os.path.join(os.path.dirname(__file__), filename)
        dest_path = get_data_path(filename)
        if not os.path.exists(dest_path) and os.path.exists(src_path):
            with open(src_path, 'rb') as src, open(dest_path, 'wb') as dst:
                dst.write(src.read())

def load_data():
    """加载数据文件"""
    init_data()
    try:
        with open(get_data_path('teams.json'), 'r', encoding='utf-8') as f:
            teams = json.load(f)
        with open(get_data_path('yunwan.json'), 'r', encoding='utf-8') as f:
            questions = json.load(f)
            random.shuffle(questions['questions'])
        return teams, questions
    except Exception as e:
        print(f"加载数据出错: {e}")
        return {'teams': [{'id': 1, 'name': '默认队伍', 'points': 0}]}, {'questions': []}

def save_teams(teams):
    """保存队伍数据"""
    try:
        with open(get_data_path('teams.json'), 'w', encoding='utf-8') as f:
            json.dump(teams, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存失败: {e}")
        return False

# 初始化数据
teams_data, questions_data = load_data()

@app.after_request
def add_header(response):
    """禁用缓存并设置安全头"""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.route('/')
def yunwanlol():
    return render_template('yunwanlol.html')

@app.route('/yunwan')
def yunwan():
    global teams_data
    teams_data, _ = load_data()
    return render_template('yunwan.html', teams=teams_data['teams'])

@app.route('/ranking')
def ranking():
    teams = sorted(teams_data['teams'], key=lambda x: -x['points'])
    return render_template('Ranking.html', teams=teams)

@app.route('/start', methods=['POST'])
def start():
    try:
        team_id = int(request.form['team'])
        random.shuffle(questions_data['questions'])
        return redirect(url_for('questions', team_id=team_id, q_index=0))
    except Exception as e:
        print(f"开始答题错误: {e}")
        return redirect(url_for('yunwan'))

@app.route('/questions/<int:team_id>/<int:q_index>', methods=['GET', 'POST'])
def questions(team_id, q_index):
    team = next((t for t in teams_data['teams'] if t['id'] == team_id), None)
    if not team:
        return redirect(url_for('yunwan'))

    if q_index >= len(questions_data['questions']):
        return redirect(url_for('result', team_id=team_id))

    current_question = questions_data['questions'][q_index]

    if request.method == 'POST':
        try:
            selected = int(request.form.get('answer', -1))
            is_correct = selected == current_question['answer']
            
            if is_correct:
                team['points'] += 1
                save_teams(teams_data)
                
            return redirect(url_for('result',
                                  team_id=team_id,
                                  q_index=q_index,
                                  is_correct=str(is_correct).lower(),
                                  selected=selected,
                                  correct=current_question['answer']))
        except Exception as e:
            print(f"处理答案错误: {e}")
            return redirect(url_for('questions', team_id=team_id, q_index=q_index))

    return render_template('questions.html',
                         team=team,
                         q_index=q_index,
                         question=current_question)

@app.route('/result/<int:team_id>/<int:q_index>/<is_correct>')
def result(team_id, q_index, is_correct):
    team = next((t for t in teams_data['teams'] if t['id'] == team_id), None)
    if not team:
        return redirect(url_for('yunwan'))

    return render_template('result.html',
                         team=team,
                         q_index=q_index,
                         is_correct=is_correct.lower() == 'true',
                         selected_option=request.args.get('selected', type=int),
                         correct_answer=request.args.get('correct', type=int),
                         total=len(questions_data['questions']))

@app.route('/test')
def test():
    return render_template_string("<h1>测试页面: {{ 2+2 }}</h1>")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
