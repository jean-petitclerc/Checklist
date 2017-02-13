from flask import Flask, request
from flask_script import Manager

app = Flask(__name__)
manager = Manager(app)

@app.route('/')
def index():
    return '<H1>Hello World!</H1>'

@app.route('/user/<name>')
def user(name):
    user_agent = request.headers.get('User-Agent')
    return '<H1>Hello, %s!</H1><p>Your browser is %s.</p>' % (name, user_agent)

if __name__ == '__main__':
    manager.run()