from flask import Flask, render_template_string

app = Flask(__name__)

#
with app.app_context():  # 手动进入应用上下文
    result = render_template_string("<p>{{ 2 * 2 }}</p>")
    print(result)  # 输出: <p>4</p>

if __name__ == "__main__":
    app.run()