from  pyrogram import Client, filters, errors
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import db, random, os,bet, commands,group, cookies, sys
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
is_taken = True    #flag che verifica se esiste la condizione per inviare un nuovo biscotto
is_first = True     #flag che verifica se chi prende il biscotto è il primo a farlo


def log_message(message):
    app.send_message(LOG_GROUP, message)


def select_group():
    global group_id
    last_group = group_id
    query = db.query_db_no_value("SELECT `id_group` FROM `groups`")
    selected = []
    if len(query) >= 2:
        random.seed()
        srand = random.randrange(101)
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
            if srand < 30:  # 0 a 29   (30%)
                if temp_info >= 500:  # 500
                    selected.append(groups[0])
                    continue
            elif srand < 30 + 10:  # 30 a 39     (10%)
                if temp_info < 10:  # 0 a 9
                    selected.append(groups[0])
                    continue
            elif srand < 30 + 10 + 25:  # 45 a 64    (25%)
                if temp_info >= 10 and temp_info < 50:  # 10 a 49
                    selected.append(groups[0])
                    continue
            elif srand <= 30 + 10 + 25 + 35:  # 65 a 100     (35%)
                if temp_info >= 50 and temp_info < 500:  # da 50 a 499
                    selected.append(groups[0])
                    continue
        if len(selected) >= 2:
            group_id = selected[random.randrange(len(selected))]
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
    if group_id == last_group:
        log_message("Gruppo scelto uguale al precedente!")
        select_group()
    else:
        group_name = app.get_chat(group_id)
        log_message(
            f"Il prossimo gruppo in cui verrà inviato il biscotto è: {group_name.title}")



def start_scheduler():
    if group_id == "0":
        scheduler.add_job(restart, 'interval',  seconds=10,
                          id='main', replace_existing=True)
    else:
        scheduler.add_job(cookies.biscotto, 'interval',  seconds=10, args=(group_id,), id='biscotto', replace_existing=True)
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
    today = datetime.now()
    if today.hour <= 23 and today.hour >= 0 and today.minute <= 59:
        rimuovi = datetime(today.year, today.month,
                           today.day, 23, 00, 00)
        temp = str(create_date(find_seconds(rimuovi, today)))
        temp = temp.replace('(', "")
        temp = temp.replace(')', "")
        temp = temp.replace(' ', "")
        a = temp.split(',')
        try:
            scheduler.add_job(
                time_check, 'interval', days=int(a[0]), hours=int(a[1]), minutes=int(a[2]), seconds=int(a[3]), id='timecheck')
        except:
            pass
    else:
        time_check()


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
    if remove_scheduler('timecheck') == False:
        log_message("Non sono riuscito a togliere lo scheduler che scansiona le vincite")

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
        db.modify_db("UPDATE `users` SET `propic` = %s WHERE `id_user` = %s",(1, user.from_user.id))  # true
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
    group.add_group(message)


@app.on_message(filters.command('remove'))
def removec(client, message):
    group.remove_group(message)


@app.on_message((filters.group) & filters.command("bet"))
def betc(client, message):
    bet.bet_fun(message)


@app.on_message(filters.command("list"))
def listc(client, message):
    cookies.print_list(message)


@app.on_message((filters.group) & filters.command("group_info"))
def group_info(client, message):
    group.group_info(message)


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
