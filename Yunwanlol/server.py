import json
import os
from flask import Flask, render_template, request, redirect, url_for, current_app, render_template_string
import sys
import io
import random  # 新增随机模块

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
app = Flask(__name__, template_folder='templates')
app.config.update(
    JSON_AS_ASCII=False,
    TEMPLATES_AUTO_RELOAD=True,
)
app.jinja_env.auto_reload = True
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

# 强制禁用缓存（开发模式）
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


@app.after_request
def add_header(response):
    """禁用所有缓存"""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


def load_data():
    """加载数据文件"""
    try:
        # 加载队伍数据
        with open('teams.json', 'r', encoding='utf-8') as f:
            teams = json.load(f)

        # 加载问题数据
        with open('yunwan.json', 'r', encoding='utf-8') as f:
            questions = json.load(f)

            # 随机打乱题目顺序
            random.shuffle(questions['questions'])
            print("已随机打乱题目顺序")

        print("数据加载成功！")
        return teams, questions
    except Exception as e:
        print(f"加载数据出错: {e}")
        # 返回默认数据
        return {'teams': [{'id': 0, 'name': '默认队伍', 'points': 0}]}, {'questions': []}


# 初始化数据
teams_data, questions_data = load_data()


@app.route('/')
def yunwanlol():
    """新的大主页，比yunwan更前面"""
    return render_template('yunwanlol.html')


@app.route('/yunwan')
def yunwan():
    """首页路由"""
    return render_template('yunwan.html', teams=teams_data['teams'])


@app.route('/ranking')
def ranking():
    """排行榜页面"""
    teams = sorted(teams_data['teams'], key=lambda x: -x['points'])
    return render_template('Ranking.html', teams=teams)


@app.route('/start', methods=['POST'])
def start():
    """开始答题路由"""
    try:
        team_id = int(request.form['team'])
        # 重置题目顺序
        random.shuffle(questions_data['questions'])
        return redirect(url_for('questions', team_id=team_id, q_index=0))
    except:
        return redirect(url_for('yunwan'))


@app.route('/questions/<int:team_id>/<int:q_index>', methods=['GET', 'POST'])
def questions(team_id, q_index):
    """答题页路由"""
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
                # 保存更新后的数据
                with open('teams.json', 'w', encoding='utf-8') as f:
                    json.dump(teams_data, f, ensure_ascii=False, indent=4)

            return redirect(url_for('result',
                                    team_id=team_id,
                                    q_index=q_index,
                                    is_correct=is_correct))
        except Exception as e:
            print(f"处理答案时出错: {e}")
            return redirect(url_for('questions', team_id=team_id, q_index=q_index))

    return render_template('questions.html',
                           team=team,
                           q_index=q_index,
                           question=current_question)


@app.route('/result/<int:team_id>/<int:q_index>/<string:is_correct>')
def result(team_id, q_index, is_correct):
    # 1. 获取队伍信息
    team = next((t for t in teams_data['teams'] if t['id'] == team_id), None)
    if not team:
        return redirect(url_for('yunwan'))

    # 2. 转换参数类型（关键修复）
    try:
        is_correct_bool = is_correct.lower() == 'true'
    except AttributeError:
        is_correct_bool = False  # 默认值

    # 3. 获取其他参数
    selected_option = request.args.get('selected', type=int)
    correct_answer = request.args.get('correct', type=int)

    # 4. 渲染模板（确保传递布尔值）
    return render_template(
        'result.html',
        team=team,
        q_index=q_index,
        is_correct=is_correct_bool,  # 使用转换后的布尔值
        selected_option=selected_option,
        correct_answer=correct_answer,
        total=len(questions_data['questions'])
    )


@app.route('/test')
def test():
    return render_template_string("<h1>这是一个测试网页: {{ 2+2 }}</h1>")


@app.route('/debug')
def debug():
    """调试路由"""
    test_data = {
        'teams': [{'name': '测试队伍', 'points': 100}],
        'question': {'question': '测试问题', 'options': ['A', 'B', 'C', 'D']}
    }
    rendered = render_template('questions.html',
                               team=test_data['teams'][0],
                               q_index=0,
                               question=test_data['question'])
    print("调试渲染结果:", rendered)
    return rendered


@app.after_request
def add_charset(response):
    """确保所有文本响应强制使用 UTF-8 编码"""
    if "text/html" in response.content_type:
        response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response


if __name__ == '__main__':
    # 检查模板文件是否存在
    print("检查模板文件是否存在:")
    print("yunwan.html:", os.path.exists(os.path.join(app.template_folder, 'yunwan.html')))
    print("questions.html:", os.path.exists(os.path.join(app.template_folder, 'questions.html')))
    print("result.html:", os.path.exists(os.path.join(app.template_folder, 'result.html')))

    # 运行应用，允许局域网访问
    app.run(host='0.0.0.0', port=5000, debug=True)