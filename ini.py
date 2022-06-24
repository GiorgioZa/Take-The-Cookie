from pyrogram import Client, filters, errors
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import db
import random
import os
import bet
import commands
import group
import cookies
import sys
sys.setrecursionlimit(1500)
file = open("config_file.txt", "r").readlines()
line = file[3].split(", ")
dev_stuff = [x for x in line]
app = Client(
    dev_stuff[0],
    bot_token=dev_stuff[1],
    sleep_threshold=50
)

scheduler = BackgroundScheduler()
group_id = "0"
LOG_GROUP = int(dev_stuff[2])
SUPER_USER = int(dev_stuff[3])
is_taken = True  # flag che verifica se esiste la condizione per inviare un nuovo biscotto
is_first = True  # flag che verifica se chi prende il biscotto è il primo a farlo


def log_message(message):
    app.send_message(LOG_GROUP, message)


def ramdom_gen(limit):
    random.seed()
    return random.randrange(limit)

def select_group():
    global group_id
    query = db.query_db_no_value("SELECT `id_group` FROM `groups`")
    selected = []
    flag = False  # gruppo piccolo
    if len(query) >= 2:
        srand = ramdom_gen(101)
        for groups in query:
            try:
                temp_info = app.get_chat_members_count(groups[0])
            except errors.ChannelInvalid:
                group.remove_error(groups[0])
                continue
            except errors.ChannelPrivate:
                group.remove_error(groups[0])
                continue
            except errors.PeerIdInvalid:
                group.remove_error(groups[0])
                continue
            if srand < 10:  # 0 a 9   (10%)
                flag = True
                if temp_info >= 500:  # 500
                    selected.append(groups[0])
                    continue
            elif srand < 10 + 15:  # 10 a 24     (15%)
                flag = False
                if temp_info < 10:  # 0 a 9
                    selected.append(groups[0])
                    continue
            elif srand < 10 + 15 + 20:  # 25 a 44    (20%)
                flag = False
                if temp_info >= 10 and temp_info < 50:  # 10 a 49
                    selected.append(groups[0])
                    continue
            elif srand < 10 + 15 + 20 + 25:  # 45 a 69    (25%)
                flag = True
                if temp_info >= 50 and temp_info < 100:  # 50 a 99
                    selected.append(groups[0])
                    continue
            elif srand <= 10 + 15 + 20 + 25 + 30:  # 70 a 100     (30%)
                flag = True
                if temp_info >= 100 and temp_info < 500:  # da 50 a 499
                    selected.append(groups[0])
                    continue
        if len(selected) >= 2:
            group_id = selected[ramdom_gen(len(selected))]
        elif len(selected) == 1:
            group_id = selected[0]
        else:
            group_id = "0"
            select_group()
            return
    elif len(query) == 1:
        group_id = query[0][0]
    elif len(query) == 0:
        group_id = "0"
        log_message("Nessun gruppo selezionato per ricevere il biscotto")
        return
    verify_group(flag)


def verify_group(flag):
    f = open("last_groups.txt", "r")
    groups = f.read().split(",")
    for element in groups:
        if element == "":
            groups.pop()
    definitive = groups.copy()
    max = 0
    if flag == True:  # gruppo grande
        max = 4
    else:   #gruppo piccolo
        max = 1
    while len(groups) > max:
        groups.pop(0)
    if str(group_id) in groups:
        log_message("Gruppo scelto uguale al precedente!")
        select_group()
        return
    while len(definitive) > 9:
        definitive.pop(0)
    definitive.append(group_id)
    f.close()
    f1 = open("last_groups.txt", "w")
    for x in definitive:
        f1.write(str(x)+",")
    group_name = app.get_chat(group_id)
    log_message(
        f"Il prossimo gruppo in cui verrà inviato il biscotto è: {group_name.title}")
    f1.close()


def start_scheduler():
    if group_id == "0":
        scheduler.add_job(restart, 'interval',  seconds=10,
                          id='main', replace_existing=True)
    else:
        scheduler.add_job(cookies.biscotto, 'interval',  seconds=10, args=(
            group_id,), id='biscotto', replace_existing=True)
    bets = db.query_db_no_value("SELECT `id_group`, `closed` FROM `bets`")
    if bets != []:
        for element in bets:
            if element[1] == 0:
                try:
                    scheduler.add_job(bet.remove, 'interval', minutes=10,
                                      args=(element[0], False), id=f'remove{element[0]}')
                except:
                    pass
    time_scheduler()


def find_seconds(dt2, dt1):
    timedelta = dt2 - dt1
    return timedelta.days * 24 * 3600 + timedelta.seconds


def create_date(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return (abs(days), hours, minutes, seconds)


def time_scheduler():
    remove_scheduler("scheduler")
    scheduler.add_job(time_check, 'cron', hour=23)
    #today = datetime.now()
    # if today.hour <= 23 and today.hour >= 0 and today.minute <= 59:
    #    rimuovi = datetime(today.year, today.month,
    #                       today.day, 23, 00, 00)
    #    temp = str(create_date(find_seconds(rimuovi, today)))
    #    temp = temp.replace('(', "")
    #    temp = temp.replace(')', "")
    #    temp = temp.replace(' ', "")
    #    a = temp.split(',')
    #    try:
    #        scheduler.add_job(
    #            time_check, 'interval', days=int(a[0]), hours=int(a[1]), minutes=int(a[2]), seconds=int(a[3]), id='timecheck')
    #    except:
    #        pass
    # else:
    #    time_check()


def scheduler_new_date():
    a = random.randrange(3)  # da 0 a 2 ore
    b = random.randrange(10, 60)  # da 10 a 59 minuti
    c = random.randrange(60)  # da 0 a 59 secondi
    remove_scheduler('biscotto')
    try:
        scheduler.add_job(cookies.biscotto, 'interval', hours=a, minutes=b,
                          seconds=c, args=(group_id,), id='biscotto')
        log_message(f"Prossimo biscotto tra: {a}h:{b}m:{c}s")
    except:
        restart()


def time_check():
    temp = db.query_db_no_value("SELECT `id_group` FROM `bets`")
    for gruppi in temp:
        bet.find_result(gruppi[0])
    db.modify_db_no_value("DELETE FROM `bets`")
    db.modify_db_no_value("DELETE FROM `yes_bets`")
    db.modify_db_no_value("DELETE FROM `no_bets`")


def remove_scheduler(id):
    try:
        scheduler.remove_job(id)
    except:
        return False
    return True


def restart():
    remove_scheduler("main")
    select_group()
    start_scheduler()


@app.on_callback_query(filters.regex("taken"))
def taken(client, callback_query):
    cookies.taken(client, callback_query)


@app.on_callback_query(filters.regex("update_cookie"))
def update(client, callback_query):
    cookies.update_list(callback_query)


@app.on_callback_query(filters.regex("expired"))
def expired_query(client, callback_query):
    cookies.taken_query(callback_query)


def download_propic(user):
    try:
        app.download_media(user.from_user.photo.big_file_id,
                           f"static/img/{user.from_user.id}.png")
    except:
        pass
    if os.path.exists(f"static/img/{user.from_user.id}.png"):
        db.modify_db("UPDATE `users` SET `propic` = %s WHERE `id_user` = %s",
                     (1, user.from_user.id))  # true
    else:
        db.modify_db("UPDATE `users` SET `propic` = %s WHERE `id_user` = %s",
                     (0, user.from_user.id))  # false
    return


@app.on_callback_query(filters.regex("end"))
def end_poll(client, callback_query):
    bet.stop_bet(callback_query)


@app.on_callback_query(filters.regex("yes"))
def yes_choice(client, callback_query):
    bet.choice(callback_query)


@app.on_callback_query(filters.regex("nope"))
def no_choice(client, callback_query):
    bet.choice(callback_query)


@app.on_message((filters.private) & filters.command("start"))
def start(client, message):
    commands.welcome(message)


@app.on_message((filters.group) & filters.command('start'))
def start_group(client, message):
    commands.welcome(message)
    commands.how_work(message)


@app.on_message(filters.command("dev"))
def devc(client, message):
    commands.dev(message)


@app.on_message((filters.private) & filters.command("add"))
def addp(client, message):
    commands.welcome(message)


@app.on_message((filters.group) & filters.command("add"))
def add(client, message):
    group.add_group(message, False)


@app.on_message(filters.command('remove'))
def removec(client, message):
    group.remove_group(message)


@app.on_message((filters.group) & filters.command("bet"))
def betc(client, message):
    bet.bet_fun(message)


@app.on_message(filters.command("list"))
def listc(client, message):
    cookies.print_list(message)


@app.on_message(filters.command("give"))
def give(client, message):
    commands.give(message)


@app.on_message((filters.group) & filters.command("group_info"))
def group_info(client, message):
    group.group_info(message)


@app.on_message((filters.group) & filters.command("reboot"))
def group_info(client, message):
    messager = app.send_message(message.chat.id, "💤Riavvio in corso...💤")
    commands.reboot(message, messager)


@app.on_callback_query(filters.regex('set_privacy'))
def set_privacy(client, callback_query):
    group.set_privacy(callback_query)


@app.on_callback_query(filters.regex("set_gift"))
def set_gift(client, callback_query):
    group.set_gift(callback_query)


@app.on_message(filters.chat(SUPER_USER) & filters.command("info"))
def info(client, message):
    commands.info(message)


@app.on_message(filters.chat(SUPER_USER) & filters.command("force_cookie"))
def force_cookie(client, message):
    commands.instant_cookie()


@app.on_message(filters.chat(SUPER_USER) & filters.command("force_close"))
def force_result(client, message):
    commands.manual_close_bet()


@app.on_message(filters.chat(SUPER_USER) & filters.command("close_id"))
def force_result(client, message):
    commands.close_bet_by_id(message)


@app.on_message(filters.chat(SUPER_USER) & filters.command("force_group"))
def force_group(client, message):
    commands.manual_choice_new_group()


@app.on_message(filters.chat(SUPER_USER) & filters.command("manual_group"))
def force_send_cookie(client, message):
    commands.manual_choice_group_by_id(message)


@app.on_message(filters.chat(SUPER_USER) & filters.command("announce"))
def announce(client, message):
    commands.create_and_send_announce(message)


@app.on_message(filters.chat(SUPER_USER) & filters.command("modify_user"))
def modify_user(client, message):
    commands.modify_manually_users(message)


@app.on_message(filters.chat(SUPER_USER) & filters.command("show_jobs"))
def modify_user(client, message):
    commands.show_jobs(message)


@app.on_message((filters.group) & filters.command("stats"))
def stats(client, message):
    commands.send_stats(message)


@app.on_message((filters.group) & filters.command("quantity"))
def p_quantity(client, message):
    commands.send_personal_cookies_qta(message)


@app.on_callback_query(filters.regex("update_stats"))
def edit(client, callback_query):
    commands.update_stats(callback_query)


@app.on_callback_query(filters.regex("update_qta"))
def edit(client, callback_query):
    commands.update_qta(callback_query)


def start_bot():
    try:
        scheduler.start()
    except:
        pass
    start_scheduler()
