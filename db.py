import mysql.connector

DELETE_QUERY_GROUPS = ("DELETE FROM `groups` WHERE `id_group` = %s")

file = open("config_file.txt", "r").readlines()
line = file[1].split(", ")
db_auth = [x for x in line]
mydb = mysql.connector.connect(
    host=db_auth[0],
    user=db_auth[1],
    password=db_auth[2],
    database=db_auth[3]
)


mycursor = mydb.cursor()


def modify_db(query, value):
    mycursor.execute(query, value)
    mydb.commit()


def modify_db_no_value(query):
    mycursor.execute(query)
    mydb.commit()


def query_db(query, value):
    mycursor.execute(query, value)
    return mycursor.fetchall()


def query_db_no_value(query):
    mycursor.execute(query)
    return mycursor.fetchall()
