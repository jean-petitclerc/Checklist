from flask import Flask, request, render_template
from flask_script import Manager
from flask_bootstrap import Bootstrap

app = Flask(__name__)
manager = Manager(app)
bootstrap = Bootstrap(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user/<name>')
def user(name):
    user_agent = request.headers.get('User-Agent')
    return render_template ('user.html', name=name, browser=user_agent)

if __name__ == '__main__':
    manager.run()