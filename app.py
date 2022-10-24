from flask import Flask, render_template, url_for
import Db
app = Flask(__name__)

@app.route('/')
@app.route('/index')
async def index():
    x = 0
    users =[]
    temp = Db.session.aggregate([
        {"$sort": {"qta": -1}},
        {"$lookup":{
            "from": "users",
            "localField": "_id",
            "foreignField": "_id",
            "as": "users_session"
        }},
        {"$lookup":{
            "from": "groups",
            "localField": "group_id",
            "foreignField": "_id",
            "as": "group"
        }}])
    for element in temp:
        x+=1
        users.append(element)
    if x >=1:
        return render_template('index.html', number=x, users = users)
    else:
        return render_template('error.html')


@app.route('/global')       
def global_stats(): 
    x = 0
    users = []
    temp = Db.users.find({}).sort("tot_qta", -1)
    for element in temp:
        x+=1
        users.append(element)
    if x >=1:
        return render_template('global.html', number=x, users=users)
    else:
        return render_template('error.html')


@app.route('/group')       
def group_stats(): 
    x = 0
    groups = []
    temp = Db.groups.find({"privacy": {"$ne": 0}}).sort("n_cookie", -1)
    for element in temp:
        x+=1
        groups.append(element)
    if x >=1:
        return render_template('group.html', number=x, groups=groups)
    else:
        return render_template('error.html')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html'), 404


app.run(host='0.0.0.0', port=80, debug=False)