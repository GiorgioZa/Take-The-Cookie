from flask import Flask, render_template, url_for
from tinydb import TinyDB, Query
cookie = TinyDB("cookie.json")
group = TinyDB("group.json")
app = Flask(__name__)


def sort_QTA(e):
    return -e['quantity']


def sort_name(e):
    return e['user']


@app.route('/')
@app.route('/index')
def index():
    cookies = cookie.all()
    groups = group.all()
    cookies.sort(key=lambda x: (sort_QTA(x), sort_name(x)))
    if len(cookies) == 0:
        return render_template('error.html')
    if len(cookies) >= 1:
        return render_template('index.html', number=len(cookies), user=cookies, gruppi=groups)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html'), 404


app.run(host='0.0.0.0', port=80)