import mysql.connector
from posixpath import split

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

mycursor.execute("CREATE TABLE `Groups`("
                 "`id_group` VARCHAR(255) NOT NULL,"
                 "`name` VARCHAR(255) NOT NULL,"
                 "`tot_cookie` int NOT NULL,"
                 "`privacy` int NOT NULL,"
                 "`gift` int NOT NULL,"
                 "PRIMARY KEY (`id_group`)"
                 ")")

mycursor.execute("CREATE TABLE `Users`("
                 "`id_user` VARCHAR(255) NOT NULL,"
                 "`name_user` VARCHAR(255) NOT NULL,"
                 "`username` VARCHAR(255) NOT NULL,"
                 "`global_quantity` int DEFAULT 0 CHECK(`global_quantity`>=0),"
                 "`session` int DEFAULT 0 CHECK(`session`>=0),"
                 "`propic` int NOT NULL,"
                 "PRIMARY KEY (`id_user`))")

mycursor.execute("CREATE TABLE `Sessions`("
                 "`id_user` VARCHAR(255) NOT NULL,"
                 "`id_group` VARCHAR(255),"
                 "`quantity` int DEFAULT 0 CHECK(`quantity`>=0 AND `quantity`<=30),"
                 "PRIMARY KEY(`id_user`),"
                 "FOREIGN KEY (`id_user`) REFERENCES `Users`(`id_user`) ON DELETE CASCADE ON UPDATE CASCADE,"
                 "FOREIGN KEY (`id_group`) REFERENCES `Groups`(`id_group`) ON DELETE CASCADE ON UPDATE CASCADE)")

mycursor.execute("CREATE TABLE `Bets`("
                 "`id_group` VARCHAR(255) NOT NULL,"
                 "`id_poll` int NOT NULL,"
                 "`result` VARCHAR(255),"
                 "`announce` int NOT NULL,"
                 "`closed` int DEFAULT 0,"
                 "PRIMARY KEY (`id_group`, `id_poll`),"
                 "FOREIGN KEY (`id_group`) REFERENCES `Groups`(`id_group`) ON DELETE CASCADE ON UPDATE CASCADE)")

mycursor.execute("CREATE TABLE `Yes_bets`("
                 "`id_group` VARCHAR(255) NOT NULL,"
                 "`id_poll` int NOT NULL,"
                 "`id_user` VARCHAR(255) NOT NULL,"
                 "`quantity` int NOT NULL,"
                 "PRIMARY KEY (`id_group`, `id_poll`, `id_user`),"
                 "FOREIGN KEY (`id_group`) REFERENCES `Groups`(`id_group`) ON DELETE CASCADE ON UPDATE CASCADE,"
                 "FOREIGN KEY (`id_user`) REFERENCES `Users`(`id_user`) ON DELETE CASCADE ON UPDATE CASCADE)")

mycursor.execute("CREATE TABLE `No_bets`("
                 "`id_group` VARCHAR(255) NOT NULL,"
                 "`id_poll` int NOT NULL,"
                 "`id_user` VARCHAR(255) NOT NULL,"
                 "`quantity` int NOT NULL,"
                 "PRIMARY KEY (`id_group`, `id_poll`, `id_user`),"
                 "FOREIGN KEY (`id_user`) REFERENCES `Users`(`id_user`) ON DELETE CASCADE ON UPDATE CASCADE,"
                 "FOREIGN KEY (`id_group`) REFERENCES `Groups`(`id_group`) ON DELETE CASCADE ON UPDATE CASCADE)")
