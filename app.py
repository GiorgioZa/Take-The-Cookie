from flask import Flask, render_template, url_for
from tinydb import TinyDB, Query
biscotti = TinyDB("biscotti.json")
group = TinyDB("group.json")
app = Flask(__name__)
def myFunc(e):
  return e['quantity']

@app.route('/')
@app.route('/index')
def index():
  biscott = biscotti.all()
  gruppo = group.all()
  biscott.sort(reverse=True, key=myFunc)
  if len(biscott) == 0:
    return render_template('error.html')
  if len(biscott) >= 1:
    return render_template('index.html',number=len(biscott), user = biscott, gruppi = gruppo)

@app.errorhandler(404)
def page_not_found(error):
  return render_template('error.html'), 404

app.run(host='0.0.0.0', port=80)
