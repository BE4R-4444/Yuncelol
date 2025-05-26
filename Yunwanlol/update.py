import json
import re
from datetime import datetime
import os


def debug_print(*args):
    """调试时使用的打印函数"""
    print("[DEBUG]", *args)


def load_teams_data():
    """加载JSON队伍数据并排序"""
    try:
        debug_print("当前工作目录:", os.getcwd())
        debug_print("尝试读取teams.json...")

        with open('teams.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        debug_print("成功读取JSON数据，共找到", len(data['teams']), "支队伍")

        # 按积分降序排序，积分相同则按队伍名称升序
        teams = sorted(data['teams'], key=lambda x: (-x['points'], x['name']))

        debug_print("排名前3的队伍:")
        for i, team in enumerate(teams[:3]):
            debug_print(f"第{i + 1}名: {team['name']} - {team['points']}分")

        return teams

    except Exception as e:
        debug_print("加载JSON数据时出错:", str(e))
        raise


def update_html_ranking(teams):
    """更新HTML文件中的排名"""
    try:
        debug_print("尝试读取Ranking.html...")

        with open('templates/Ranking.html', 'r', encoding='utf-8') as f:
            html = f.read()

        debug_print("成功读取HTML文件")

        # 生成新的队伍列表HTML
        new_teams_html = []
        for i, team in enumerate(teams):
            # 前三名有特殊样式
            if i == 0:
                row_class = "team-row top-1"
            elif i == 1:
                row_class = "team-row top-2"
            elif i == 2:
                row_class = "team-row top-3"
            else:
                row_class = "team-row"

            new_teams_html.append(f"""
            <div class="{row_class}">
                <div class="rank">{i + 1}</div>
                <div class="team-info">
                    <img src="{team.get('logo', '')}" alt="{team.get('name', '')}" class="team-logo">
                    <span>{team.get('name', '未知队伍')}</span>
                </div>
                <div class="points">{team.get('points', 0)}</div>
            </div>""")

        debug_print("生成的队伍HTML块:")
        debug_print("\n".join(new_teams_html[:3]) + "\n...")  # 只打印前3个作为示例

        # 用正则表达式替换队伍列表部分
        pattern = r'(<!-- 表头 -->\s*<div class="leaderboard-header">.*?</div>\s*)(<!-- 队伍列表 -->\s*).*?(\s*</div>\s*</div>\s*</div>)'

        if not re.search(pattern, html, flags=re.DOTALL):
            debug_print("错误: 在HTML中找不到匹配的标记")
            debug_print("请确保HTML中包含正确的表头和结束标记")
            return False

        updated_html = re.sub(
            pattern,
            r'\1\2' + '\n'.join(new_teams_html) + r'\3',
            html,
            flags=re.DOTALL
        )

        # 保存更新后的HTML
        with open('templates/Ranking.html', 'w', encoding='utf-8') as f:
            f.write(updated_html)

        debug_print("成功更新HTML文件")
        return True

    except Exception as e:
        debug_print("更新HTML时出错:", str(e))
        return False


if __name__ == '__main__':
    print("=" * 50)
    print("开始更新队伍排名...")

    try:
        teams = load_teams_data()
        success = update_html_ranking(teams)

        if success:
            print("排名更新成功！")
        else:
            print("排名更新失败，请查看上面的调试信息")

    except Exception as e:
        print("发生严重错误:", str(e))

    print("=" * 50)