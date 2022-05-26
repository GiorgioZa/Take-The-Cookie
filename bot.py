import random
import time
import os.path
import sys
from datetime import datetime, timedelta
from pytz import timezone

from apscheduler.schedulers.background import BackgroundScheduler
from pyrogram import Client, filters, errors

from pyrogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                            ReplyKeyboardMarkup)
from tinydb import Query, TinyDB, queries

scheduler = BackgroundScheduler()

group_id = "0"
sys.setrecursionlimit(1500)
temp = open("super_user.txt", "r").read().split(", ")
SUPER_USER = [eval(x) for x in temp]
LOG_GROUP = int(open("log_group.txt", "r").read())

takenb = True
cookie = TinyDB("cookie.json")
session = TinyDB("session.json")
group = TinyDB("group.json")
bet = TinyDB("bet.json")
admin = []
unicity = False
unicityex = False
result = []
date = []

app = Client(
    "<NAME OF BOT HERE>",
    bot_token="<BOT TOKEN HERE>",
    sleep_threshold=50
)


def get_result(e):
    return e['result']


def get_quantity(e):
    return -e['quantity']


def get_name(e):
    return e['user']


def find_seconds(dt2, dt1):
    timedelta = dt2 - dt1
    return timedelta.days * 24 * 3600 + timedelta.seconds


def create_date(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return (abs(days), hours, minutes, seconds)


def start_scheduler():
    if group_id == "0":
        scheduler.add_job(main, 'interval',  seconds=10,
                          id='main', replace_existing=True)
    else:
        scheduler.add_job(biscotto, 'interval',  seconds=10, args=(
            group_id,), id='biscotto', replace_existing=True)
    try:
        scheduler.start()
    except:
        pass


def welcome(message):
    app.send_message(message.chat.id, "Questo bot ti permette di intrattenere il tuo gruppo con un gioco molto divertente.\nPer usare questo bot, devi aggiungerlo ad un gruppo in cui tu sei admin!")
    return


def how_work(message):
    app.send_message(message.chat.id, "Per avviare la raccolta dei biscotti, utilizza il comando /add@TakeTheCookieBot, in questo modo dirai al bot che il tuo gruppo è pronto a ricevere dei gustosi biscotti! Inoltre, se vorrai rendere la sfida molto più esaltante, potrai attivare la ricezione dei premi automatici dal comando /groupinfo@TakeTheCookieBot !")
    return


def found_admin(id):
    ad = app.get_chat_members(id, filter="administrators")
    for a in ad:
        admin.append(a.user.id)
    return


def dev(message):
    app.send_message(
        message.chat.id, "Versione biscotti: 2.0.3.3\n\nSviluppato da @GiorgioZa con l'aiuto e supporto dei suoi amiketti che lo sostengono in ogni sua minchiata ❤️\n\nUltime info sul bot -> <a href='https://t.me/TakeTheCookie'>canale ufficiale</a>")
    return


@app.on_callback_query(filters.regex("update_cookie"))
def update(client, callback_query):
    try:
        app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id, create_list(), reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(
                    "Aggiorna", callback_data="update_cookie")],
            ]))
    except:
        callback_query.answer("Informazioni già aggiornate!", show_alert=True)
    return


def print_list(message):
    app.send_message(message.chat.id, create_list(), reply_markup=InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(
                "Aggiorna", callback_data="update_cookie")],
        ]))
    return


def create_list():
    totale = cookie.all()
    if len(totale) < 1:
        return "Nessuno ha riscattato biscotti per ora :("
    totale.sort(key=lambda x: (get_quantity(x), get_name(x)))
    text = "Podio goloso:"
    for x in range(0, 3):
        try:
            user = app.get_users(totale[x]['id_user'])
            text += f"\n{'🥇' if x==0 else '🥈' if x==1 else '🥉' if x==2 else ''} {user.mention()}: {totale[x]['quantity']}"
        except:
            text += f"\n{'🥇' if x==0 else '🥈' if x==1 else '🥉' if x==2 else ''} {totale[x]['username'] if totale[x]['username'] else totale[x]['user']}: {totale[x]['quantity']}"
            pass
    text += "\n\nPer vedere la classifica completa, visita il <a href='biscotti.uk.to'>sito</a>"
    return text


def expired(bisquit):
    global takenb
    takenb = True
    app.edit_message_reply_markup(bisquit.chat.id, bisquit.message_id, InlineKeyboardMarkup([[
        InlineKeyboardButton("Mangia il biscotto!🤔🍪", callback_data="expired")]]))
    app.send_message(
        LOG_GROUP, f"{bisquit.chat.title} ha aspettato troppo tempo. il biscotto è andato a male!")
    try:
        scheduler.remove_job(f'expired{bisquit.chat.id}')
    except:
        log_message(
            "non sono riuscito a modificare lo scheduler del biscotto marcio!")
    select_group()
    if group_id != "0":
        biscotto(group_id)
    return


def verify_win(info):
    bisquit = cookie.search(Query()['id_user'] == info.from_user.id)
    sessionva = session.search(Query()['id_user'] == info.from_user.id)
    quantity = bisquit[0]['quantity']
    sessionqa = sessionva[0]['session']
    quantity = bisquit[0]['quantity']
    if quantity == 10:
        app.send_message(info.message.chat.id,
                         f"{'@'+info.from_user.username if info.from_user.username else info.from_user.first_name} ha raggiunto i 10 biscotti!🎊")
    elif quantity == 20:
        app.send_message(info.message.chat.id,
                         f"{'@'+info.from_user.username if info.from_user.username else info.from_user.first_name} ha raggiunto i 20 biscotti!🎊")
    elif quantity == 30:
        query = group.search(Query()['id'] == info.message.chat.id)
        if query[0]['myfilms'] == True:
            app.send_message(info.message.chat.id, f"Complementi {'@'+info.from_user.username if info.from_user.username else info.from_user.first_name}, sei arrivato ai 30 biscotti🎉🎊.\nHai vinto il premio messo in palio dal progetto MyFilms che collabora con noi. Per ritirare il tuo mese gratuito contatta @Mario_Myfilms, ti guiderà lui.\n\nPer tutti gli altri utenti incuriositi del progetto che vorrebbero avere ulteriori info, potete contattare @Mario_Myfilms! (anche perchè ai non vincitori spetta comunque una promo 🌚)\n\nIn bocca al lupo al prossimo vincitore 😁\n\n❕*Ovviamente il vincitore attuale è escluso dalle vincite per i prossimi mesi.*\n** *Il vincitore può anche rifiutare il premio scegliendo se passarlo al secondo classificato o ad un utente a caso;* **")
        else:
            app.send_message(info.message.chat.id,
                             f"Complementi {'@'+info.from_user.username if info.from_user.username else info.from_user.first_name}, sei arrivato ai 30 biscotti perciò hai vinto questa sessione!🎉🎊")
        app.send_message(
            LOG_GROUP, f"{'@'+info.from_user.username if info.from_user.username else info.from_user.first_name} è arrivato a 30 biscotti! Database resettato.")
        win(info)
        session.update({'session': sessionqa+1}, Query()
                       ['id_user'] == info.from_user.id)
        cookie.update({'session': sessionqa+1}, Query()
                      ['id_user'] == info.from_user.id)
        cookie.truncate()


@app.on_callback_query(filters.regex("expired"))
def expired_query(client, callback_query):
    global unicityex
    if unicityex == True:
        return
    unicityex = True
    if random.choice([True, False]) == True:
        try:
            scheduler.remove_job(f'expired{callback_query.message.chat.id}')
        except:
            pass
        app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id,
                              f"Avendo mangiato un biscotto avariato🤢, {'@'+callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.mention()} ha avuto problemi di stomaco e quindi ha perso un biscotto dalla classifica generale!\n\nPress F to pay respect!")
        callback_query.answer(
            "Mi dispiace, questo biscotto ha atteso per troppo tempo che qualcuno lo mangiasse e quindi è avariato🥺🤢... Sei stato avvelenato, hai vomitato e hai perso dei biscotti!", show_alert=True)
        bisquit = cookie.search(
            Query()['id_user'] == callback_query.from_user.id)
        sessionva = session.search(
            Query()['id_user'] == callback_query.from_user.id)
        if bisquit == []:
            app.send_message(callback_query.message.chat.id,
                             f"Che sfortuna, il primo biscotto in assoluto di {'@'+callback_query.from_user.username if callback_query.from_user.username!=None else callback_query.from_user.mention()} era avariato *biscotto triste*. Mostrategli un pò di compassione.")
        else:
            quantity = bisquit[0]['quantity']
            sessionv = sessionva[0]['session']
            quantity -= 1
            total = sessionva[0]['total_quantity']
            cookie.update({'user': callback_query.from_user.first_name, 'quantity': quantity, 'session': sessionv, 'username': f"{'@'+callback_query.from_user.username if callback_query.from_user.username!=None else None}",
                           'group': f"{'@'+callback_query.message.chat.username if callback_query.message.chat.username!=None else callback_query.message.chat.title}", 'group_id': callback_query.message.chat.id}, Query()['id_user'] == callback_query.from_user.id)
            session.update({'total_quantity': total-1}, Query()
                           ['id_user'] == callback_query.from_user.id)
    else:
        app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id,
                              f"Il 🍪 avariato è stato mangiato da {'@'+callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.mention()} senza conseguenze🎉!")
        callback_query.answer(
            f"WOW😳, caro {callback_query.from_user.first_name} che fortuna! Hai divorato il biscotto avariato senza conseguenze!", show_alert=True)
        log_message(
            f"Biscotto del gruppo: {callback_query.message.chat.title} riscattato da: {callback_query.from_user.username if callback_query.from_user.username!=None else callback_query.from_user.first_name}")
        total = 0
        sessionqa = 0
        bisquit = cookie.search(
            Query()['id_user'] == callback_query.from_user.id)
        sessionva = session.search(
            Query()['id_user'] == callback_query.from_user.id)
        if bisquit == []:
            cookie.insert({'id_user': callback_query.from_user.id, 'user': callback_query.from_user.first_name, 'quantity': 1, 'session': 0, 'username': f"{'@'+callback_query.from_user.username if callback_query.from_user.username else None}",
                           'group': f"{'@'+callback_query.message.chat.username if callback_query.message.chat.username!=None else callback_query.message.chat.title}", 'group_id': callback_query.message.chat.id})
            if sessionva == []:
                session.insert({'id_user': callback_query.from_user.id, 'user': callback_query.from_user.first_name,
                                'username': f"{'@'+callback_query.from_user.username if callback_query.from_user.username else None}", 'total_quantity': 1, 'session': 0})
            else:
                total = sessionva[0]['total_quantity']
                sessionqa = sessionva[0]['session']
                session.update({'total_quantity': total+1}, Query()
                               ['id_user'] == callback_query.from_user.id)
                cookie.update({'session': sessionqa}, Query()[
                    'id_user'] == callback_query.from_user.id)
        else:
            quantity = bisquit[0]['quantity']
            sessionqa = sessionva[0]['session']
            quantity += 1
            total = sessionva[0]['total_quantity']
            cookie.update({'user': callback_query.from_user.first_name, 'quantity': quantity, 'session': sessionqa, 'username': f"{'@'+callback_query.from_user.username if callback_query.from_user.username else None}",
                           'group': f"{'@'+callback_query.message.chat.username if callback_query.message.chat.username!=None else callback_query.message.chat.title}", 'group_id': callback_query.message.chat.id}, Query()['id_user'] == callback_query.from_user.id)
            session.update({'total_quantity': total+1}, Query()
                           ['id_user'] == callback_query.from_user.id)

            verify_win(callback_query)
            group.update({'name': callback_query.message.chat.title},
                         Query()['id'] == callback_query.message.chat.id)
    try:
        app.download_media(callback_query.from_user.photo.big_file_id,
                           f"static/img/{callback_query.from_user.id}.png")
    except:
        if not (os.path.exists(f"static/{callback_query.from_user.id}.png")):
            cookie.update({'propic': "false"}, Query()[
                'id_user'] == callback_query.from_user.id)
        else:
            cookie.update({'propic': "true"}, Query()[
                'id_user'] == callback_query.from_user.id)
    unicityex = False
    return


def win(winner):
    all_group = group.all()
    for element in all_group:
        if element['id'] != winner.message.chat.id:
            app.send_message(
                element['id'], f"EVVIVA! Questa sessione è stata vinta da {winner.from_user.mention}!🥳")


def biscotto(chat_group):
    global takenb, unicity
    try:
        scheduler.remove_job('biscotto')
    except:
        pass
    if takenb == True:
        a = group.search(Query()['id'] == group_id)
        gruppo = app.get_chat(chat_group)
        if a == []:
            log_message(
                f"a quanto pare {gruppo.title} non esiste più nel database, provo a cambiare gruppo")
            main()
            return
        try:
            bisquit = app.send_message(chat_group, "Oh, ma cosa c'è qui... Un biscotto?! Corri a mangiarlo prima che qualche altro utente te lo rubi👀!!",
                                       reply_markup=InlineKeyboardMarkup(
                                           [
                                               [InlineKeyboardButton(
                                                   "Mangia il biscotto!😋🍪", callback_data="taken")],
                                           ]))
            takenb = False
            unicity = False
            log_message(f"ho inviato biscotto nel gruppo: '{gruppo.title}'")
        except:
            group.remove(Query()['id'] == chat_group)
            log_message(
                f"non ho inviato il biscotto nel gruppo {gruppo.title} perchè ho avuto un problema")
            main()
            return
        try:
            scheduler.add_job(expired, 'interval',  hours=1,
                              args=(bisquit,), id=f"expired{chat_group}")
        except:
            log_message(
                "non sono riuscito a creare lo scheduler per i biscotti scaduti :(")
        try:
            nbiscotti = a[0]['biscotti']
        except:
            nbiscotti = 0
        data = create_data()
        group.update({'date': data, 'biscotti': nbiscotti+1},
                     Query()['id'] == group_id)
        temp_bet = bet.search(Query()['id_group'] == group_id)
        if temp_bet != []:
            bet.update({'result': 'SI'}, Query()['id_group'] == chat_group)
            remove_before(chat_group)
    else:
        main()


def create_data():
    data = []
    presentime = datetime.now()
    hour = {
        'hour': presentime.hour,
        'minutes': presentime.minute,
        'seconds': presentime.second
    }
    data.append(hour)
    return data


def add_group(message):
    global admin
    if group.search(Query()['id'] == message.chat.id) == []:
        found_admin(message.chat.id)
        if message.from_user.id in admin:
            date = create_data()
            chat = app.get_chat(message.chat.id)
            if chat.members_count >= 10:
                group.insert({'id': message.chat.id, 'name': chat.title, 'date': date,
                             'biscotti': 0, 'hidden': False, 'myfilms': False})
                app.send_message(
                    message.chat.id, "Gruppo aggiunto! Da adesso può ricevere biscotti in qualsiasi momento... Tenete gli occhi aperti👀")
                log_message(
                    f"Ho aggiunto un nuovo gruppo: {chat.title} da parte di: {message.from_user.username if message.from_user.username!=None else message.from_user.firstname}")
            else:
                app.send_message(
                    message.chat.id, "Questo gruppo è troppo piccolo per questo bot! Contatta @GiorgioZa per ulteriori informazioni.")
        else:
            app.send_message(
                message.chat.id, "Per usare questo bot, devi aggiungerlo ad un **GRUPPO** in cui tu sei admin!")
    else:
        app.send_message(
            message.chat.id, "A quanto pare, hai già iscritto questo gruppo ai partecipanti!")
    admin = []


def scheduler_new_date():
    a = random.randrange(3)  # da 0 a 2 ore
    b = random.randrange(10, 60)  # da 10 a 59 minuti
    c = random.randrange(60)  # da 0 a 59 secondi
    try:
        scheduler.remove_job('biscotto')
    except:
        pass
    try:
        scheduler.add_job(biscotto, 'interval', hours=a, minutes=b,
                          seconds=c, args=(group_id,), id='biscotto')
        log_message(f"Prossimo biscotto tra: {a}h:{b}m:{c}s")
    except:
        main()


def log_message(message):
    app.send_message(LOG_GROUP, message)


def remove_error(gruppo):
    group.remove(Query()['id'] == gruppo['id'])
    log_message(f"Ho rimosso il gruppo {gruppo['name']} dal database!")


def select_group():
    global group_id
    last_group = group_id
    query = group.all()
    selected = []
    if len(query) >= 2:
        random.seed()
        srand = random.randrange(101)
        for gruppi in query:
            try:
                temp_info = app.get_chat_members_count(gruppi['id'])
            except errors.ChannelInvalid:
                remove_error(gruppi)
                continue
            except errors.ChannelPrivate:
                remove_error(gruppi)
                continue
            if srand < 40:  # 0 a 39   (40%)
                if temp_info > 500:  # +500
                    selected.append(gruppi['id'])
                    continue
            elif srand < 40 + 5:  # 40 a 44     (5%)
                if temp_info < 10:  # 0 a 9
                    selected.append(gruppi['id'])
                    continue
            elif srand < 40 + 5 + 22:  # 45 a 67    (22%)
                if temp_info > 10 and temp_info < 50:  # 10 a 49
                    selected.append(gruppi['id'])
                    continue
            elif srand <= 40 + 5 + 22 + 33:  # 67 a 100     (33%)
                if temp_info > 50 and temp_info < 500:  # da 50 a 499
                    selected.append(gruppi['id'])
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
        group_id = query[0]['id']
    elif len(query) <= 0:
        group_id = "0"
        log_message("Nessun gruppo selezionato per ricevere il biscotto")
        return
    if group_id == last_group:
        log_message("Gruppo scelto uguale al precedente!")
        select_group()
    else:
        temp = app.get_chat(group_id)
        log_message(
            f"Il prossimo gruppo in cui verrà inviato il biscotto è: {temp.title}")


def find_result(chat_group):
    query = bet.search(Query()['id_group'] == chat_group)
    gruppo = app.get_chat(chat_group)
    if query[0]['choice'] != None:
        if query[0]['result'] == query[0]['choice']:
            if query[0]['announce'] == False:
                app.send_message(
                    chat_group, "Complimenti! Questo gruppo ha vinto la scommessa della giornata!!")
                bet.update({'announce': True}, Query()
                           ['id_group'] == chat_group)
                log_message(f"Scommessa vinta in : {gruppo.title}")
                global takenb
                takenb = True
                biscotto(chat_group)
        else:
            if query[0]['announce'] == False:
                app.send_message(
                    chat_group, "Oh no! Hai perso la scommessa di giornata *sad cookie intensifies*")
                bet.update({'announce': True}, Query()
                           ['id_group'] == chat_group)
                log_message(f"Scommessa persa in : {gruppo.title}")


def time_check():
    try:
        scheduler.remove_job('timecheck')
    except:
        log_message(
            "Non sono riuscito a togliere lo scheduler che scansiona le vincite")
    temp = bet.all()
    for gruppi in temp:
        find_result(gruppi['id_group'])
    bet.truncate()


def bet_fun(message):
    id = message.chat.id
    gruppo = app.get_chat(id)
    if bet.search(Query()['id_group'] == id) == []:
        try:
            id_poll = app.send_poll(
                id, "Il gruppo riceverà almeno un biscotto da questo momento fino alla mezzanotte?\n(In caso di vittoria, il gruppo riceverà un biscotto aggiuntivo)", ['SI', 'NO'], False)
            log_message(
                f"Questo gruppo ha avviato un nuovo sondaggio: {gruppo.title}")
            bet.insert({'id_group': id, 'id_poll': id_poll['message_id'],
                        'choice': None, 'result': 'NO', 'announce': False})
        except errors.ChatSendPollForbidden:
            app.send_message(
                id, "Mi dispiace, non posso inviare sondaggi in questo gruppo. Controlla i permessi del gruppo. Nel caso l'opzione 'Inviare sondaggi' sia disattivata contatta @GiorgioZa .")
            log_message(
                f"In questo gruppo l'opione sondaggi è disattivata: {gruppo.title}")
            return
    else:
        app.send_message(id,
                         "questo gruppo ha già fatto la scommessa di giornata")

    try:
        scheduler.add_job(remove, 'interval', hours=1,
                          args=(id,), id='remove'+str(id))
    except:
        pass
    return


def remove_before(chatgroup):
    global result
    tp = app.get_chat(chatgroup)
    gruppo = bet.search(Query()['id_group'] == chatgroup)
    if gruppo[0]['announce'] == False:
        if gruppo[0]['choice'] == None:
            try:
                poll_result = app.stop_poll(
                    gruppo[0]['id_group'], gruppo[0]['id_poll'])
            except:
                log_message(
                    f"Non posso chiudere questo sondaggio anticipatamente: {tp.title}, {gruppo[0]['id_poll']}")
                return
            temp = []
            for results in poll_result['options']:
                temp = {
                    'value': results.text,
                    'result': results.voter_count
                }
                result.append(temp)
            result.sort(reverse=True, key=get_result)
            if result[0]['result'] == result[1]['result']:
                app.send_message(
                    gruppo[0]['id_group'], "Wow, avete raggiunto una parità sul voto che implica l'annullamento di questa scommessa :(")
                log_message(
                    f"Parità raggiunta anticipatamente in questo gruppo: {tp.title}")
            else:
                app.send_message(
                    gruppo[0]['id_group'], f"Risultato del sondaggio:\n-{result[0]['value']}: {result[0]['result']}\n-{result[1]['value']}: {result[1]['result']}\n\nHa vinto il {result[0]['value']}!")
                bet.update({'choice': result[0]['value']}, Query()[
                    'id_group'] == gruppo[0]['id_group'])
                log_message(
                    f"In questo gruppo, il sondaggio si è chiuso positivamente anticipatamente: {tp.title}")
        result = []
        find_result(chatgroup)


def remove(id_group):
    try:
        scheduler.remove_job('remove'+str(id_group))
    except:
        log_message(
            f"Non sono riuscito a rimuovere lo scheduler della chiusura scommesse")
        pass
    global result
    gruppo = bet.search(Query()['id_group'] == id_group)
    if gruppo == []:
        return
    if gruppo[0]['announce'] == False:
        group = app.get_chat(gruppo[0]['id_group'])
        try:
            poll_result = app.stop_poll(
                gruppo[0]['id_group'], gruppo[0]['id_poll'])
        except:
            log_message(
                f"Non posso chiudere questo sondaggio: {group.title}, {gruppo[0]['id_poll']}")
            return
        temp = []
        for results in poll_result['options']:
            temp = {
                'value': results.text,
                'result': results.voter_count
            }
            result.append(temp)
        result.sort(reverse=True, key=get_result)
        if result[0]['result'] == result[1]['result']:
            app.send_message(
                gruppo[0]['id_group'], "Wow, avete raggiunto una parità sul voto che implica l'annullamento di questa scommessa :(")
            log_message(f"Parità raggiunta in questo gruppo: {group.title}")
        else:
            app.send_message(
                gruppo[0]['id_group'], f"Risultato del sondaggio:\n-{result[0]['value']}: {result[0]['result']}\n-{result[1]['value']}: {result[1]['result']}\n\nHa vinto il {result[0]['value']}!")
            bet.update({'choice': result[0]['value']}, Query()[
                'id_group'] == gruppo[0]['id_group'])
            log_message(
                f"In questo gruppo, il sondaggio si è chiuso positivamente: {group.title}")
        result = []
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


@app.on_callback_query(filters.regex("taken"))
def taken(client, callback_query):
    global takenb, unicity
    if unicity == True:
        return
    unicity = True
    app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id,
                          f"Il 🍪 è stato mangiato da {'@'+callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.mention()}🎉!")
    callback_query.answer(
        f"Complimenti🥳 {callback_query.from_user.first_name}! Hai divorato il biscotto!", show_alert=True)
    try:
        scheduler.remove_job('biscotto')
    except:
        pass
    try:
        scheduler.remove_job('expired')
    except:
        pass
    try:
        scheduler.remove_job(f'expired{callback_query.message.chat.id}')
    except:
        pass
    log_message(
        f"Biscotto del gruppo: {callback_query.message.chat.title} riscattato da: {callback_query.from_user.username if callback_query.from_user.username!=None else callback_query.from_user.first_name}")
    takenb = True
    total = 0
    sessionqa = 0
    bisquit = cookie.search(
        Query()['id_user'] == callback_query.from_user.id)
    sessionv = session.search(
        Query()['id_user'] == callback_query.from_user.id)
    if bisquit == []:
        cookie.insert({'id_user': callback_query.from_user.id, 'user': callback_query.from_user.first_name, 'quantity': 1, 'session': 0, 'username': f"{'@'+callback_query.from_user.username if callback_query.from_user.username else None}",
                       'group': f"{'@'+callback_query.message.chat.username if callback_query.message.chat.username!=None else callback_query.message.chat.title}", 'group_id': callback_query.message.chat.id})
        if sessionv == []:
            session.insert({'id_user': callback_query.from_user.id, 'user': callback_query.from_user.first_name,
                            'username': f"{'@'+callback_query.from_user.username if callback_query.from_user.username else None}", 'total_quantity': 1, 'session': 0})
        else:
            total = sessionv[0]['total_quantity']
            sessionqa = sessionv[0]['session']
            session.update({'total_quantity': total+1}, Query()
                           ['id_user'] == callback_query.from_user.id)
            cookie.update({'session': sessionqa}, Query()[
                'id_user'] == callback_query.from_user.id)
        try:
            app.download_media(callback_query.from_user.photo.big_file_id,
                               f"static/img/{callback_query.from_user.id}.png")
        except:
            if not (os.path.exists(f"static/{callback_query.from_user.id}.png")):
                cookie.update({'propic': "false"}, Query()[
                    'id_user'] == callback_query.from_user.id)
            else:
                cookie.update({'propic': "true"}, Query()[
                    'id_user'] == callback_query.from_user.id)
    else:
        quantity = bisquit[0]['quantity']
        quantity += 1
        sessionqa = sessionv[0]['session']
        total = sessionv[0]['total_quantity']
        cookie.update({'user': callback_query.from_user.first_name, 'quantity': quantity, 'session': sessionqa, 'username': f"{'@'+callback_query.from_user.username if callback_query.from_user.username else None}",
                       'group': f"{'@'+callback_query.message.chat.username if callback_query.message.chat.username!=None else callback_query.message.chat.title}", 'group_id': callback_query.message.chat.id}, Query()['id_user'] == callback_query.from_user.id)
        session.update({'total_quantity': total+1}, Query()
                       ['id_user'] == callback_query.from_user.id)
        try:
            app.download_media(callback_query.from_user.photo.big_file_id,
                               f"static/img/{callback_query.from_user.id}.png")
            cookie.update({'propic': "true"}, Query()[
                'id_user'] == callback_query.from_user.id)
        except:
            cookie.update({'propic': "false"}, Query()[
                'id_user'] == callback_query.from_user.id)
        verify_win(callback_query)
    group.update({'name': callback_query.message.chat.title},
                 Query()['id'] == callback_query.message.chat.id)
    select_group()
    scheduler_new_date()
    unicity = False


@app.on_message((filters.private) & filters.command("start"))
def start(client, message):
    welcome(message)


@app.on_message((filters.group) & filters.command('start'))
def start_group(client, message):
    welcome(message)
    how_work(message)


@app.on_message(filters.command("dev"))
def devc(client, message):
    dev(message)


@app.on_message((filters.private) & filters.command("add"))
def addp(client, message):
    welcome(message)


@app.on_message((filters.group) & filters.command("add"))
def add(client, message):
    add_group(message)


@app.on_message(filters.command('remove'))
def removec(client, message):
    global admin
    if group.search(Query()['id'] == message.chat.id) != []:
        found_admin(message.chat.id)
        if message.from_user.id in admin:
            group.remove(Query()['id'] == message.chat.id)
            app.send_message(
                message.chat.id, "Ho rimosso questo gruppo dalla lista dei partecipanti! Se hai riscontrato problemi o non sei stato a tuo agio, contatta il creatore -> @GiorgioZa")
            log_message(f"Ho rimosso un nuovo gruppo: {message.chat.title}")
        else:
            app.send_message(
                message.chat.id, "Per usare questo bot, devi aggiungerlo ad un gruppo in cui tu sei admin!")
    else:
        app.send_message(
            message.chat.id, "Questo gruppo non risulta nella lista dei partecipanti... L'informazione è errata? Perchè non contatti @GiorgioZa?")
    admin = []


@app.on_message((filters.group) & filters.command("bet"))
def betc(client, message):
    bet_fun(message)


@app.on_message(filters.command("list"))
def listc(client, message):
    print_list(message)


@app.on_message((filters.group) & filters.command("group_info"))
def group_info(client, message):
    gruppi = group.search(Query()['id'] == message.chat.id)
    if gruppi == []:
        app.send_message(
            message.chat.id, "Gruppo non trovato *biscotto triste*")
        return
    gruppo = app.get_chat(message.chat.id)
    text = f"Nome: **{gruppo.title}**\nID: <code>{gruppo.id}</code>\nMembri: **{gruppo.members_count}**\nTotale biscotti: {0 if gruppi[0]['biscotti']==0 else gruppi[0]['biscotti']}\nPremio: {'**Disattivato**' if gruppi[0]['myfilms']==False else '**Attivato**'}\nVisibilità: {'**Visibile**' if gruppi[0]['hidden']==False else '**Nascosta**'}"
    app.send_message(message.chat.id, text, reply_markup=InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Visibilità", callback_data="set_privacy"), InlineKeyboardButton(
                "Premio", callback_data="set_gift")],
            [InlineKeyboardButton(
                "Tutorial", url="https://t.me/TakeTheCookie/6")]
        ]))


@app.on_callback_query(filters.regex('set_privacy'))
def set_privacy(client, callback_query):
    global admin
    found_admin(callback_query.message.chat.id)
    if callback_query.from_user.id in admin:
        gruppi = group.search(Query()['id'] == callback_query.message.chat.id)
        if gruppi[0]['hidden'] == True:
            group.update({'hidden': False}, Query()[
                         'id'] == callback_query.message.chat.id)
        else:
            group.update({'hidden': True}, Query()[
                         'id'] == callback_query.message.chat.id)
        gruppi = group.search(Query()['id'] == callback_query.message.chat.id)
        gruppo = app.get_chat(callback_query.message.chat.id)
        try:
            app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id, f"Nome: **{gruppo.title}**\nID: <code>{gruppo.id}</code>\nMembri: **{gruppo.members_count}**\nTotale biscotti: {0 if gruppi[0]['biscotti']==0 else gruppi[0]['biscotti']}\nPremio: {'**Disattivato**' if gruppi[0]['myfilms']==False else '**Attivato**'}\nVisibilità: {'**Visibile**' if gruppi[0]['hidden']==False else '**Nascosta**'}", reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Visibilità", callback_data="set_privacy"), InlineKeyboardButton(
                        "Premio", callback_data="set_gift")],
                    [InlineKeyboardButton(
                        "Tutorial", url="https://t.me/TakeTheCookie/6")]
                ]))
        except:
            pass
    else:
        callback_query.answer(
            "Non se un admin di questo gruppo!", show_alert=True)
    admin = []


@app.on_callback_query(filters.regex("set_gift"))
def set_gift(client, callback_query):
    global admin
    found_admin(callback_query.message.chat.id)
    if callback_query.from_user.id in admin:
        query = group.search(Query()['id'] == callback_query.message.chat.id)
        if query[0]['myfilms'] == True:
            group.update({'myfilms': False}, Query()[
                         'id'] == callback_query.message.chat.id)
        else:
            group.update({'myfilms': True}, Query()[
                         'id'] == callback_query.message.chat.id)
        query = group.search(Query()['id'] == callback_query.message.chat.id)
        gruppo = app.get_chat(callback_query.message.chat.id)
        try:
            app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id, f"Nome: **{gruppo.title}**\nID: <code>{gruppo.id}</code>\nMembri: **{gruppo.members_count}**\nTotale biscotti: {0 if query[0]['biscotti']==0 else query[0]['biscotti']}\nPremio: {'**Disattivato**' if query[0]['myfilms']==False else '**Attivato**'}\nVisibilità: {'**Visibile**' if query[0]['hidden']==False else '**Nascosta**'}", reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Visibilità", callback_data="set_privacy"), InlineKeyboardButton(
                        "Premio", callback_data="set_gift")],
                    [InlineKeyboardButton(
                        "Tutorial", url="https://t.me/TakeTheCookie/6")]
                ]))
        except:
            pass
    else:
        callback_query.answer(
            "Non se un admin di questo gruppo!", show_alert=True)
    admin = []
    return


@app.on_message(filters.chat(SUPER_USER) & filters.command("info"))
def info(client, message):
    gruppi = group.all()
    text = f"Tutti i gruppi presenti:\n\n"
    for element in gruppi:
        temp = app.get_chat(element['id'])
        text += f"- __{temp.id}__, **{temp.title}**, n°utenti: {temp.members_count}\n"
    app.send_message(message.chat.id, text)


@app.on_message(filters.chat(SUPER_USER) & filters.command("force_cookie"))
def force_cookie(client, message):
    log_message("Ho avviato la scelta manuale del biscotto")
    select_group()
    biscotto(group_id)
    return


@app.on_message(filters.chat(SUPER_USER) & filters.command("force_close"))
def force_result(client, message):
    log_message("Ho avviato la chiusura delle scommesse manuali")
    time_check()
    return


@app.on_message(filters.chat(SUPER_USER) & filters.command("force_group"))
def force_group(client, message):
    log_message("Ho avviato la scelta di prendere un nuovo gruppo")
    select_group()
    scheduler_new_date()
    return


@app.on_message(filters.chat(SUPER_USER) & filters.command("manual_group"))
def force_send_cookie(client, message):
    info = message.text
    if info == "/manual_group":
        return
    info = info.replace("/manual_group ", "")
    query = group.search(Query()['id'] == int(info))
    if query == []:
        log_message("gruppo non trovato")
    else:
        global group_id
        group_id = int(info)
        log_message(f"{query[0]['name']} è stato selezionato!")
        scheduler_new_date()


@app.on_message(filters.chat(SUPER_USER) & filters.command("announce"))
def announce(client, message):
    info = message.text
    if info == "/announce":
        return
    info = info.replace("/announce ", "")
    query = group.all()
    for gruppi in query:
        app.send_message(gruppi['id'], info)


@app.on_message((filters.group) & filters.command("stats"))
def stats(client, message):
    query = session.search(Query()['id_user'] == message.from_user.id)
    if query == []:
        app.send_message(message.chat.id, "Utente non trovato!")
        return
    app.send_message(
        message.chat.id, f"Statisiche di {message.from_user.mention}:\n\nTotale biscotti: **{query[0]['total_quantity']}**\nTotale sessioni vinte: **{query[0]['session']}**", reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(
                    "Aggiorna", callback_data="update_stats")],
            ]))


@app.on_callback_query(filters.regex("update_stats"))
def edit(client, callback_query):
    query = session.search(Query()['id_user'] == callback_query.from_user.id)
    if query == []:
        try:
            app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id, "Utente non trovato!", reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(
                        "Aggiorna", callback_data="update_stats")],
                ]))
        except:
            pass
    else:
        try:
            app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id, f"Statisiche di {callback_query.from_user.mention}:\n\nTotale biscotti: **{query[0]['total_quantity']}**\nTotale sessioni vinte: **{query[0]['session']}**", reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(
                        "Aggiorna", callback_data="update_stats")],
                ]))
        except:
            callback_query.answer(
                "Informazioni già aggiornate!", show_alert=True)


def main():
    try:
        scheduler.remove_job("main")
    except:
        pass
    select_group()
    start_scheduler()


def ini():
    start_scheduler()


ini()
app.run()