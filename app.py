from flask import Flask, render_template, url_for
from flask_mysqldb import MySQL
 
file = open("config_file.txt", "r").readlines()
line = file[1].split(", ")
db_auth = [x for x in line]
app = Flask(__name__)

app.config['MYSQL_HOST'] = db_auth[0]
app.config['MYSQL_USER'] = db_auth[1]
app.config['MYSQL_PASSWORD'] = db_auth[2]
app.config['MYSQL_DB'] = db_auth[3]
 
mysql = MySQL(app)

@app.route('/')
@app.route('/index')
def index():
    cursor = mysql.connection.cursor()
    number = cursor.execute("SELECT u.id_user, `name_user`, `username`, `quantity`, `session`, `propic`, `id_group` FROM `users` u JOIN `sessions` s ON u.id_user = s.id_user ORDER BY `quantity` DESC")
    cookies = cursor.fetchall()
    cursor.execute("SELECT `id_group`, `name`, `privacy` FROM `groups`")
    groups = cursor.fetchall()
    if number >=1:
        return render_template('index.html', number=number, user=cookies, gruppi=groups)
    else:
        return render_template('error.html')


@app.route('/global')       
def global_stats(): 
    cursor = mysql.connection.cursor()
    number = cursor.execute("SELECT * FROM `users` ORDER BY `global_quantity` DESC")
    cookies = cursor.fetchall()
    if number >=1:
        return render_template('global.html', number=number, user=cookies)
    else:
        return render_template('error.html')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html'), 404


app.run(host='0.0.0.0', port=80)