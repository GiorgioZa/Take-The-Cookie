import random
import time
from datetime import datetime
from pytz import timezone
import os.path

from apscheduler.schedulers.background import BackgroundScheduler
from pyrogram import Client, filters
from pyrogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                            ReplyKeyboardMarkup)
from tinydb import Query, TinyDB

scheduler = BackgroundScheduler()

group_id = "0"


def readFile():
    try:
        f = open("last_group.txt", "r")
        last_group_id = f.read().split("\n")
        f.close()
        return last_group_id
    except FileNotFoundError:
        return None


takenb = True
biscotti = TinyDB("biscotti.json")
sessioni = TinyDB("sessioni.json")
group = TinyDB("group.json")
scommesse = TinyDB("bet.json")
admin = []
unicity = False
unicityex = False
risultato = []
date = []

app = Client(
    "my_bot",
    bot_token="<YOUR TOKEN BOT HERE>",
    sleep_threshold=50
)


def myFunc(e):
    return e['result']


def sort(e):
    return e['quantity']


def findSeconds(dt2, dt1):
    timedelta = dt2 - dt1
    return timedelta.days * 24 * 3600 + timedelta.seconds


def createDate(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return (abs(days), hours, minutes, seconds)


def start_scheduler():
    if group_id == "0":
        try:
            scheduler.add_job(main, 'interval',  seconds=5, id='main')
        except:
            pass
    else:
        try:
            scheduler.add_job(biscotto, 'interval',  seconds=10,
                              args=(group_id,), id='biscotto')
        except:
            pass
    try:
        scheduler.start()
    except:
        pass


def welcome(message):
    app.send_message(message.chat.id, "Questo bot ti permette di intrattenere il tuo gruppo con un gioco molto divertente.\nPer usare questo bot, devi aggiungerlo ad un gruppo in cui tu sei admin!")
    return


def howWork(message):
    app.send_message(message.chat.id, "Per avviare la raccolta dei biscotti, utilizza il comando /add@TakeTheCookieBot, in questo modo dirai al bot che il tuo gruppo è pronto a ricevere dei gustosi biscotti! Inoltre, se vorrai rendere la sfida molto più esaltante, potrai attivare la ricezione dei premi automatici dal comando /groupinfo@TakeTheCookieBot !")
    return


def foundAdmin(id):
    ad = app.get_chat_members(id, filter="administrators")
    for a in ad:
        admin.append(a.user.id)
    return


def dev(message):
    app.send_message(
        message.chat.id, "Versione biscotti: 2.0.3\n\nSviluppato da @GiorgioZa con l'aiuto e supporto dei suoi amiketti che lo sostengono in ogni sua minchiata ❤️\n\nUltime info sul bot -> <a href='https://t.me/TakeTheCookie'>canale ufficiale</a>")
    return


@app.on_callback_query(filters.regex("updateCookie"))
def update(client, callback_query):
    try:
        app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id, createlist(), reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(
                    "Aggiorna", callback_data="updateCookie")],
            ]))
    except:
        callback_query.answer("Informazioni già aggiornate!", show_alert=True)
    return


def printlist(message):
    app.send_message(message.chat.id, createlist(), reply_markup=InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(
                "Aggiorna", callback_data="updateCookie")],
        ]))
    return


def createlist():
    totale = biscotti.all()
    if len(totale) < 1:
        return "Nessuno ha riscattato biscotti per ora :("
    totale.sort(reverse=True, key=sort)
    text = "Podio goloso:"
    for x in range(0, 3):
        try:
            user = app.get_users(totale[x]['id_user'])
            text += f"\n{'🥇' if x==0 else '🥈' if x==1 else '🥉' if x==2 else ''} {user.mention()}: {totale[x]['quantity']}"
        except:
            pass
    text += "\n\nPer vedere la classifica completa, visita il <a href='biscotti.uk.to'>sito</a>"
    return text


def expired(bisquit):
    global takenb
    takenb = True
    app.edit_message_reply_markup(bisquit.chat.id, bisquit.message_id, InlineKeyboardMarkup([[
        InlineKeyboardButton("Mangia il biscotto!🤔🍪", callback_data="expired")]]))
    try:
        scheduler.remove_job('expired')
    except:
        app.send_message("<YOUR LOG GROUP ID>",
                         "non sono riuscito a modificare la tastiera del biscotto marcio!")
    selectGroup()
    biscotto(group_id)
    return


@app.on_callback_query(filters.regex("expired"))
def expired_query(client, callback_query):
    global unicityex
    if unicityex == True:
        return
    unicityex == True
    random.seed()
    if random.choice([True, False]) == True:
        try:
            scheduler.remove_job('expired')
        except:
            pass
        app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id,
                              f"Avendo mangiato un biscotto avariato🤢, {'@'+callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.mention()} ha avuto problemi di stomaco e quindi ha perso un biscotto dalla classifica generale!\n\nPress F to pay respect!")
        unicityex == False
        callback_query.answer(
            "Mi dispiace, questo biscotto ha atteso per troppo tempo che qualcuno lo mangiasse e quindi è avariato🥺🤢... Sei stato avvelenato, hai vomitato e hai perso dei biscotti!", show_alert=True)
        bisquit = biscotti.search(
            Query()['id_user'] == callback_query.from_user.id)
        session = sessioni.search(
            Query()['id_user'] == callback_query.from_user.id)
        if bisquit == []:
            app.send_message(callback_query.message.chat.id,
                             f"Che sfortuna, il primo biscotto in assoluto di {'@'+callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.mention()} era avariato *biscotto triste*. Mostrategli un pò di compassione.")
        else:
            quantity = bisquit[0]['quantity']
            quantity -= 1
            total = session[0]['total_quantity']
            biscotti.update({'user': callback_query.from_user.first_name, 'quantity': quantity, 'username': f"{'@'+callback_query.from_user.username if callback_query.from_user.username else None}",
                            'group': f"{'@'+callback_query.message.chat.username if callback_query.message.chat.username else callback_query.message.chat.title}", 'group_id': callback_query.message.chat.id}, Query()['id_user'] == callback_query.from_user.id)
            sessioni.update({'total_quantity': total-1}, Query()
                            ['id_user'] == callback_query.from_user.id)
    else:
        app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id,
                              f"Il 🍪 avariato è stato mangiato da {'@'+callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.mention()} senza conseguenze🎉!")
        unicityex == False
        callback_query.answer(
            f"WOW😳, caro {callback_query.from_user.first_name} che fortuna! Hai divorato il biscotto avariato senza conseguenze!", show_alert=True)
        app.send_message("<YOUR LOG GROUP ID>",
                         f"Biscotto del gruppo: {callback_query.message.chat.title} riscattato da: {callback_query.from_user.username if callback_query.from_user.username!=None else callback_query.from_user.first_name}")
        total = 0
        sessionqa = 0
        bisquit = biscotti.search(
            Query()['id_user'] == callback_query.from_user.id)
        session = sessioni.search(
            Query()['id_user'] == callback_query.from_user.id)
        if bisquit == []:
            biscotti.insert({'id_user': callback_query.from_user.id, 'user': callback_query.from_user.first_name, 'quantity': 1, 'session': 0, 'username': f"{'@'+callback_query.from_user.username if callback_query.from_user.username else None}",
                            'group': f"{'@'+callback_query.message.chat.username if callback_query.message.chat.username else callback_query.message.chat.title}", 'group_id': callback_query.message.chat.id})
            if session == []:
                sessioni.insert({'id_user': callback_query.from_user.id, 'user': callback_query.from_user.first_name,
                                'username': f"{'@'+callback_query.from_user.username if callback_query.from_user.username else None}", 'total_quantity': 1, 'session': 0})
            else:
                total = session[0]['total_quantity']
                sessionqa = session[0]['session']
                sessioni.update({'total_quantity': total+1}, Query()
                                ['id_user'] == callback_query.from_user.id)
                biscotti.update({'session': sessionqa}, Query()[
                                'id_user'] == callback_query.from_user.id)
        else:
            quantity = bisquit[0]['quantity']
            quantity += 1
            total = session[0]['total_quantity']
            biscotti.update({'user': callback_query.from_user.first_name, 'quantity': quantity, 'username': f"{'@'+callback_query.from_user.username if callback_query.from_user.username else None}",
                            'group': f"{'@'+callback_query.message.chat.username if callback_query.message.chat.username else callback_query.message.chat.title}", 'group_id': callback_query.message.chat.id}, Query()['id_user'] == callback_query.from_user.id)
            sessioni.update({'total_quantity': total+1}, Query()
                            ['id_user'] == callback_query.from_user.id)

            if quantity == 10:
                app.send_message(callback_query.message.chat.id,
                                 f"{'@'+callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.first_name} ha raggiunto i 10 biscotti!🎊")
            elif quantity == 20:
                app.send_message(callback_query.message.chat.id,
                                 f"{'@'+callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.first_name} ha raggiunto i 20 biscotti!🎊")
            elif quantity == 30:
                query = group.search(
                    Query()['id'] == callback_query.message.chat.id)
                if query[0]['myfilms'] == True:
                    app.send_message(callback_query.message.chat.id, f"Complementi {'@'+callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.first_name}, sei arrivato ai 30 biscotti🎉🎊.\nHai vinto il premio messo in palio dal progetto MyFilms che collabora con noi. Per ritirare il tuo mese gratuito contatta @Mario_Myfilms, ti guiderà lui.\n\nPer tutti gli altri utenti incuriositi del progetto che vorrebbero avere ulteriori info, potete contattare @Mario_Myfilms! (anche perchè ai non vincitori spetta comunque una promo 🌚)\n\nIn bocca al lupo al prossimo vincitore 😁\n\n❕*Ovviamente il vincitore attuale è escluso dalle vincite per i prossimi mesi.*\n** *Il vincitore può anche rifiutare il premio scegliendo se passarlo al secondo classificato o ad un utente a caso;* **")
                else:
                    app.send_message(callback_query.message.chat.id,
                                     f"Complementi {'@'+callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.first_name}, sei arrivato ai 30 biscotti perciò hai vinto questa sessione!🎉🎊")
                app.send_message(
                    "<YOUR LOG GROUP ID>", f"{'@'+callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.first_name} è arrivato a 30 biscotti! Database resettato.")
                sessioni.update({'session': sessionqa+1}, Query()
                                ['id_user'] == callback_query.from_user.id)
                biscotti.update({'session': sessionqa+1}, Query()
                                ['id_user'] == callback_query.from_user.id)
                biscotti.truncate()
            group.update({'name': callback_query.message.chat.title},
                         Query()['id'] == callback_query.message.chat.id)
    try:
        app.download_media(callback_query.from_user.photo.big_file_id,
                           f"static/img/{callback_query.from_user.id}.png")
    except:
        if not (os.path.exists(f"static/{callback_query.from_user.id}.png")):
            biscotti.update({'propic': "false"}, Query()[
                            'id_user'] == callback_query.from_user.id)
        else:
            biscotti.update({'propic': "true"}, Query()[
                            'id_user'] == callback_query.from_user.id)
    return


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
            app.send_message("<YOUR LOG GROUP ID>",
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
            app.send_message("<YOUR LOG GROUP ID>",
                             f"ho inviato biscotto nel gruppo: '{gruppo.title}'")
        except:
            try:
                group.remove(Query()['id'] == chat_group)
            except:
                pass
            app.send_message("<YOUR LOG GROUP ID>",
                             f"non ho inviato il biscotto nel gruppo {gruppo.title} perchè ho avuto un problema")
            main()
            return
        try:
            scheduler.add_job(expired, 'interval',  hours=1,
                              args=(bisquit,), id='expired')
        except:
            app.send_message("<YOUR LOG GROUP ID>",
                             "non sono riuscito a creare lo scheduler per i biscotti scaduti :(")
        try:
            nbiscotti = a[0]['biscotti']
        except:
            nbiscotti = 0
        data = create_Data()
        group.update({'date': data, 'biscotti': nbiscotti+1},
                     Query()['id'] == group_id)
        temp = scommesse.all()
        if chat_group in temp:
            scommesse.update({'result': 'SI'}, Query()[
                'id_group'] == chat_group)
            removeBefore(chat_group)
    else:
        main()


def create_Data():
    data = []
    presentime = datetime.now()
    hour = {
        'hour': presentime.hour,
        'minutes': presentime.minute,
        'seconds': presentime.second
    }
    data.append(hour)
    return data


def addGroup(message):
    global admin
    if group.search(Query()['id'] == message.chat.id) == []:
        foundAdmin(message.chat.id)
        if message.from_user.id in admin:
            date = create_Data()
            chat = app.get_chat(message.chat.id)
            if chat.members_count >= 10:
                group.insert({'id': message.chat.id, 'name': chat.title, 'date': date,
                             'biscotti': 0, 'hidden': False, 'myfilms': False})
                app.send_message(
                    message.chat.id, "Gruppo aggiunto! Da adesso può ricevere biscotti in qualsiasi momento... Tenete gli occhi aperti👀")
                app.send_message("<YOUR LOG GROUP ID>",
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


def scheduler_newDate():
    random.seed(time.time())
    a = random.randrange(2, 5)  # da 2 a 4 ore
    b = random.randrange(0, 60)  # da 0 a 59 minuti
    c = random.randrange(0, 60)  # da 0 a 59 secondi
    try:
        scheduler.remove_job('biscotto')
    except:
        pass
    try:
        scheduler.add_job(biscotto, 'interval', hours=a, minutes=b,
                          seconds=c, args=(group_id,), id='biscotto')
        app.send_message("<YOUR LOG GROUP ID>",
                         f"Prossimo biscotto tra: {a}h:{b}m:{c}s")

    except:
        main()


def selectGroup():
    global group_id
    random.seed(time.time())
    query = group.all()
    selected = []
    if len(query) >= 2:
        srand = random.randrange(0, 101)
        for gruppi in query:
            temp_info = app.get_chat_members_count(gruppi['id'])
            if srand < 50:  # 0 a 49
                if temp_info > 500:  # +500
                    selected.append(gruppi['id'])
                continue
            elif srand < 50 + 2:  # 50 a 51
                if temp_info < 10:  # 0 a 9
                    selected.append(gruppi['id'])
                continue
            elif srand < 50 + 2 + 10:  # 52 a 61
                if temp_info > 10 and temp_info < 50:  # 10 a 49
                    selected.append(gruppi['id'])
                continue
            elif srand <= 50 + 2 + 10 + 38:  # 62 a 100
                if temp_info > 50 and temp_info < 500:  # da 50 a 499
                    selected.append(gruppi['id'])
                continue
        if len(selected) >= 2:
            gruppe = random.randrange(0, len(selected))
            group_id = selected[gruppe]
        elif len(selected) == 1:
            group_id = selected[0]
        else:
            ini()
            return
        printer = app.get_chat(group_id)
    elif len(query) == 1:
        group_id = query[0]['id']
    elif len(query) <= 0:
        group_id = "0"
        try:
            app.send_message("<YOUR LOG GROUP ID>",
                             "Nessun gruppo selezionato per ricevere il biscotto")
        except:
            pass
        return
    i = 0
    list_group = readFile()
    if list_group != None and len(list_group) >= 5:
        for gruppoid in list_group:
            if gruppoid != str(group_id):
                i += 1
            else:
                i = 0
        if i < 4:
            selectGroup()
            return
    f = open("last_group.txt", "a")
    f.write("\n"+str(group_id))
    f.close()
    try:
        temp = app.get_chat(group_id)
        app.send_message("<YOUR LOG GROUP ID>",
                         f"Il prossimo gruppo in cui verrà inviato il biscotto è: {temp.title}")
    except:
        pass


def findResult(chat_group):
    query = scommesse.search(Query()['id_group'] == chat_group)
    gruppo = app.get_chat(chat_group)
    if query[0]['choice'] != None:
        if query[0]['result'] == query[0]['choice']:
            if query[0]['announce'] == False:
                app.send_message(
                    chat_group, "Complimenti! Questo gruppo ha vinto la scommessa della giornata!!")
                scommesse.update({'announce': True}, Query()
                                 ['id_group'] == chat_group)
                app.send_message("<YOUR LOG GROUP ID>",
                                 f"Scommessa vinta in : {gruppo.title}")
                global takenb
                takenb = True
                biscotto(chat_group)
        else:
            if query[0]['announce'] == False:
                app.send_message(
                    chat_group, "Oh no! Hai perso la scommessa di giornata *sad cookie intensifies*")
                scommesse.update({'announce': True}, Query()
                                 ['id_group'] == chat_group)
                app.send_message("<YOUR LOG GROUP ID>",
                                 f"Scommessa persa in : {gruppo.title}")


def timeCheck():
    try:
        scheduler.remove_job('timecheck')
    except:
        app.send_message("<YOUR LOG GROUP ID>",
                         "Non sono riuscito a togliere lo scheduler che scansiona le vincite")
    temp = scommesse.all()
    for gruppi in temp:
        findResult(gruppi['id_group'])
    scommesse.truncate()


def bet(message):
    id = message.chat.id
    gruppo = app.get_chat(id)
    if scommesse.search(Query()['id_group'] == id) == []:
        id_poll = app.send_poll(
            id, "Il gruppo riceverà almeno un biscotto da questo momento fino alla mezzanotte?\n(In caso di vittoria, il gruppo riceverà un biscotto aggiuntivo)", ['SI', 'NO'], False)
        app.send_message("<YOUR LOG GROUP ID>",
                         f"Questo gruppo ha avviato un nuovo sondaggio: {gruppo.title}")
        scommesse.insert({'id_group': id, 'id_poll': id_poll['message_id'],
                         'choice': None, 'result': 'NO', 'announce': False})
    else:
        app.send_message(id,
                         "questo gruppo ha già fatto la scommessa di giornata")

    try:
        scheduler.add_job(remove, 'interval', hours=1,
                          args=(id,), id='remove'+str(id))
    except:
        pass
    return


def removeBefore(chatgroup):
    global risultato
    tp = app.get_chat(chatgroup)
    gruppo = scommesse.search(Query()['id_group'] == chatgroup)
    if gruppo[0]['announce'] == False:
        try:
            result = app.stop_poll(gruppo[0]['id_group'], gruppo[0]['id_poll'])
            temp = []
            for results in result['options']:
                temp = {
                    'value': results.text,
                    'result': results.voter_count
                }
                risultato.append(temp)
            risultato.sort(reverse=True, key=myFunc)
            if risultato[0]['result'] == risultato[1]['result']:
                app.send_message(
                    gruppo[0]['id_group'], "Wow, avete raggiunto una parità sul voto che implica l'annullamento di questa scommessa :(")
                app.send_message("<YOUR LOG GROUP ID>",
                                 f"Parità raggiunta anticipatamente in questo gruppo: {tp.title}")
            else:
                app.send_message(
                    gruppo[0]['id_group'], f"Risultato del sondaggio:\n-{risultato[0]['value']}: {risultato[0]['result']}\n-{risultato[1]['value']}: {risultato[1]['result']}\n\nHa vinto il {risultato[0]['value']}!")
                scommesse.update({'choice': risultato[0]['value']}, Query()[
                                 'id_group'] == gruppo[0]['id_group'])
                app.send_message("<YOUR LOG GROUP ID>",
                                 f"In questo gruppo, il sondaggio si è chiuso positivamente anticipatamente: {tp.title}")
            risultato = []
        except:
            app.send_message("<YOUR LOG GROUP ID>",
                             f"Non posso chiudere questo sondaggio anticipatamente: {tp.title}, {gruppo[0]['id_poll']}")
        findResult(chatgroup)


def remove(id_group):
    try:
        scheduler.remove_job('remove'+str(id_group))
    except:
        app.send_message("<YOUR LOG GROUP ID>",
                         f"Non sono riuscito a rimuovere lo scheduler della chiusura scommesse")
        pass
    global risultato
    gruppo = scommesse.search(Query()['id_group'] == id_group)
    if gruppo[0]['announce'] == False:
        group = app.get_chat(gruppo[0]['id_group'])
        try:
            result = app.stop_poll(gruppo[0]['id_group'], gruppo[0]['id_poll'])
            temp = []
            for results in result['options']:
                temp = {
                    'value': results.text,
                    'result': results.voter_count
                }
                risultato.append(temp)
            risultato.sort(reverse=True, key=myFunc)
            if risultato[0]['result'] == risultato[1]['result']:
                app.send_message(
                    gruppo[0]['id_group'], "Wow, avete raggiunto una parità sul voto che implica l'annullamento di questa scommessa :(")
                app.send_message("<YOUR LOG GROUP ID>",
                                 f"Parità raggiunta in questo gruppo: {group.title}")
            else:
                app.send_message(
                    gruppo[0]['id_group'], f"Risultato del sondaggio:\n-{risultato[0]['value']}: {risultato[0]['result']}\n-{risultato[1]['value']}: {risultato[1]['result']}\n\nHa vinto il {risultato[0]['value']}!")
                scommesse.update({'choice': risultato[0]['value']}, Query()[
                                 'id_group'] == gruppo[0]['id_group'])
                app.send_message("<YOUR LOG GROUP ID>",
                                 f"In questo gruppo, il sondaggio si è chiuso positivamente: {group.title}")
            risultato = []
        except:
            app.send_message("<YOUR LOG GROUP ID>",
                             f"Non posso chiudere questo sondaggio: {group.title}, {gruppo[0]['id_poll']}")
            pass
    today = datetime.now()
    if today.hour <= 23 and today.hour >= 0 and today.minute <= 59:
        rimuovi = datetime(today.year, today.month,
                           today.day, 23, 00, 00)
        temp = str(createDate(findSeconds(rimuovi, today)))
        temp = temp.replace('(', "")
        temp = temp.replace(')', "")
        temp = temp.replace(' ', "")
        a = temp.split(',')
        try:
            scheduler.add_job(
                timeCheck, 'interval', days=int(a[0]), hours=int(a[1]), minutes=int(a[2]), seconds=int(a[3]), id='timecheck')
        except:
            pass
    else:
        timeCheck()


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
    unicity = False
    app.send_message("<YOUR LOG GROUP ID>",
                     f"Biscotto del gruppo: {callback_query.message.chat.title} riscattato da: {callback_query.from_user.username if callback_query.from_user.username!=None else callback_query.from_user.first_name}")
    takenb = True
    total = 0
    sessionqa = 0
    bisquit = biscotti.search(
        Query()['id_user'] == callback_query.from_user.id)
    session = sessioni.search(
        Query()['id_user'] == callback_query.from_user.id)
    if bisquit == []:
        biscotti.insert({'id_user': callback_query.from_user.id, 'user': callback_query.from_user.first_name, 'quantity': 1, 'session': 0, 'username': f"{'@'+callback_query.from_user.username if callback_query.from_user.username else None}",
                        'group': f"{'@'+callback_query.message.chat.username if callback_query.message.chat.username else callback_query.message.chat.title}", 'group_id': callback_query.message.chat.id})
        if session == []:
            sessioni.insert({'id_user': callback_query.from_user.id, 'user': callback_query.from_user.first_name,
                            'username': f"{'@'+callback_query.from_user.username if callback_query.from_user.username else None}", 'total_quantity': 1, 'session': 0})
        else:
            total = session[0]['total_quantity']
            sessionqa = session[0]['session']
            sessioni.update({'total_quantity': total+1}, Query()
                            ['id_user'] == callback_query.from_user.id)
            biscotti.update({'session': sessionqa}, Query()[
                            'id_user'] == callback_query.from_user.id)
        try:
            app.download_media(callback_query.from_user.photo.big_file_id,
                               f"static/img/{callback_query.from_user.id}.png")
        except:
            if not (os.path.exists(f"static/{callback_query.from_user.id}.png")):
                biscotti.update({'propic': "false"}, Query()[
                                'id_user'] == callback_query.from_user.id)
            else:
                biscotti.update({'propic': "true"}, Query()[
                                'id_user'] == callback_query.from_user.id)
    else:
        quantity = bisquit[0]['quantity']
        quantity += 1
        total = session[0]['total_quantity']
        biscotti.update({'user': callback_query.from_user.first_name, 'quantity': quantity, 'username': f"{'@'+callback_query.from_user.username if callback_query.from_user.username else None}",
                        'group': f"{'@'+callback_query.message.chat.username if callback_query.message.chat.username else callback_query.message.chat.title}", 'group_id': callback_query.message.chat.id}, Query()['id_user'] == callback_query.from_user.id)
        sessioni.update({'total_quantity': total+1}, Query()
                        ['id_user'] == callback_query.from_user.id)
        try:
            app.download_media(callback_query.from_user.photo.big_file_id,
                               f"static/img/{callback_query.from_user.id}.png")
            biscotti.update({'propic': "true"}, Query()[
                            'id_user'] == callback_query.from_user.id)
        except:
            biscotti.update({'propic': "false"}, Query()[
                            'id_user'] == callback_query.from_user.id)
        if quantity == 10:
            app.send_message(callback_query.message.chat.id,
                             f"{'@'+callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.first_name} ha raggiunto i 10 biscotti!🎊")
        elif quantity == 20:
            app.send_message(callback_query.message.chat.id,
                             f"{'@'+callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.first_name} ha raggiunto i 20 biscotti!🎊")
        elif quantity == 30:
            query = group.search(
                Query()['id'] == callback_query.message.chat.id)
            if query[0]['myfilms'] == True:
                app.send_message(callback_query.message.chat.id, f"Complementi {'@'+callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.first_name}, sei arrivato ai 30 biscotti🎉🎊.\nHai vinto il premio messo in palio dal progetto MyFilms che collabora con noi. Per ritirare il tuo mese gratuito contatta @Mario_Myfilms, ti guiderà lui.\n\nPer tutti gli altri utenti incuriositi del progetto che vorrebbero avere ulteriori info, potete contattare @Mario_Myfilms! (anche perchè ai non vincitori spetta comunque una promo 🌚)\n\nIn bocca al lupo al prossimo vincitore 😁\n\n❕*Ovviamente il vincitore attuale è escluso dalle vincite per i prossimi mesi.*\n** *Il vincitore può anche rifiutare il premio scegliendo se passarlo al secondo classificato o ad un utente a caso;* **")
            else:
                app.send_message(callback_query.message.chat.id,
                                 f"Complementi {'@'+callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.first_name}, sei arrivato ai 30 biscotti perciò hai vinto questa sessione!🎉🎊")
            app.send_message(
                "<YOUR LOG GROUP ID>", f"{'@'+callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.first_name} è arrivato a 30 biscotti! Database resettato.")
            sessioni.update({'session': sessionqa+1}, Query()
                            ['id_user'] == callback_query.from_user.id)
            biscotti.update({'session': sessionqa+1}, Query()
                            ['id_user'] == callback_query.from_user.id)
            biscotti.truncate()
    group.update({'name': callback_query.message.chat.title},
                 Query()['id'] == callback_query.message.chat.id)
    selectGroup()
    scheduler_newDate()


@app.on_message((filters.private) & filters.command(["start"]))
def start(client, message):
    welcome(message)


@app.on_message((filters.group) & filters.command(['start']))
def startgroup(client, message):
    welcome(message)
    howWork(message)


@app.on_message(filters.command(["dev"]))
def devc(client, message):
    dev(message)


@app.on_message((filters.private) & filters.command(["add"]))
def addp(client, message):
    welcome(message)


@app.on_message((filters.group) & filters.command(["add"]))
def add(client, message):
    addGroup(message)


@app.on_message(filters.command(['remove']))
def removec(client, message):
    global admin
    if group.search(Query()['id'] == message.chat.id) != []:
        foundAdmin(message.chat.id)
        if message.from_user.id in admin:
            group.remove(Query()['id'] == message.chat.id)
            app.send_message(
                message.chat.id, "Ho rimosso questo gruppo dalla lista dei partecipanti! Se hai riscontrato problemi o non sei stato a tuo agio, contatta il creatore -> @GiorgioZa")
            app.send_message("<YOUR LOG GROUP ID>",
                             f"Ho rimosso un nuovo gruppo: {message.chat.title}")
        else:
            app.send_message(
                message.chat.id, "Per usare questo bot, devi aggiungerlo ad un gruppo in cui tu sei admin!")
    else:
        app.send_message(
            message.chat.id, "Questo gruppo non risulta nella lista dei partecipanti... L'informazione è errata? Perchè non contatti @GiorgioZa?")
    admin = []


@app.on_message((filters.group) & filters.command(["bet"]))
def betc(client, message):
    bet(message)


@app.on_message(filters.command(["list"]))
def listc(client, message):
    printlist(message)


@app.on_message((filters.group) & filters.command(["groupinfo"]))
def groupinfo(client, message):
    gruppi = group.search(Query()['id'] == message.chat.id)
    if gruppi == []:
        app.send_message(
            message.chat.id, "Gruppo non trovato *biscotto triste*")
        return
    gruppo = app.get_chat(message.chat.id)
    text = f"Nome: **{gruppo.title}**\nID: <code>{gruppo.id}</code>\nMembri: **{gruppo.members_count}**\nTotale biscotti: {0 if gruppi[0]['biscotti']==0 else gruppi[0]['biscotti']}\nPremio: {'**Disattivato**' if gruppi[0]['myfilms']==False else '**Attivato**'}\nVisibilità: {'**Visibile**' if gruppi[0]['hidden']==False else '**Nascosta**'}"
    app.send_message(message.chat.id, text, reply_markup=InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Visibilità", callback_data="setprivacy"), InlineKeyboardButton(
                "Premio", callback_data="setgift")],
            [InlineKeyboardButton(
                "Tutorial", url="https://t.me/TakeTheCookie/6")]
        ]))


@app.on_callback_query(filters.regex('setprivacy'))
def setprivacy(client, callback_query):
    global admin
    foundAdmin(callback_query.message.chat.id)
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
                    [InlineKeyboardButton("Visibilità", callback_data="setprivacy"), InlineKeyboardButton(
                        "Premio", callback_data="setgift")],
                    [InlineKeyboardButton(
                        "Tutorial", url="https://t.me/TakeTheCookie/6")]
                ]))
        except:
            pass
    else:
        callback_query.answer(
            "Non se un admin di questo gruppo!", show_alert=True)
    admin = []


@app.on_callback_query(filters.regex("setgift"))
def setgift(client, callback_query):
    global admin
    foundAdmin(callback_query.message.chat.id)
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
                    [InlineKeyboardButton("Visibilità", callback_data="setprivacy"), InlineKeyboardButton(
                        "Premio", callback_data="setgift")],
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


@app.on_message(filters.chat(["<YOUR PERSONAL ID>"]) & filters.command(["info"]))
def info(client, message):
    gruppi = group.all()
    text = f"Tutti i gruppi presenti:\n\n"
    for element in gruppi:
        temp = app.get_chat(element['id'])
        text += f"- __{temp.id}__, **{temp.title}**, n°utenti: {temp.members_count}\n"
    app.send_message(message.chat.id, text)


@app.on_message(filters.chat(["<YOUR PERSONAL ID>"]) & filters.command(["forcecookie"]))
def forceCookie(client, message):
    app.send_message("<YOUR LOG GROUP ID>",
                     "Ho avviato la scelta manuale del biscotto")
    selectGroup()
    biscotto(group_id)
    return


@app.on_message(filters.chat(["<YOUR PERSONAL ID>"]) & filters.command(["forceClose"]))
def forceResult(client, message):
    app.send_message("<YOUR LOG GROUP ID>",
                     "Ho avviato la chiusura delle scommesse manuali")
    timeCheck()

    return


@app.on_message(filters.chat(["<YOUR PERSONAL ID>"]) & filters.command(["forceGroup"]))
def forceGroup(client, message):
    app.send_message("<YOUR LOG GROUP ID>",
                     "Ho avviato la scelta di prendere un nuovo gruppo")
    selectGroup()
    scheduler_newDate()
    return


@app.on_message(filters.chat(["<YOUR PERSONAL ID>"]) & filters.command(["announce"]))
def announce(client, message):
    info = message.text
    if info == "/announce":
        return
    info = info.replace("/announce ", "")
    query = group.all()
    for gruppi in query:
        app.send_message(gruppi['id'], info)


@app.on_message((filters.group) & filters.command(["stats"]))
def stats(client, message):
    query = sessioni.search(Query()['id_user'] == message.from_user.id)
    if query == []:
        app.send_message(message.chat.id, "Utente non trovato!")
        return
    app.send_message(
        message.chat.id, f"Statisiche di {message.from_user.mention}:\n\nTotale biscotti: **{query[0]['total_quantity']}**\nTotale sessioni vinte: **{query[0]['session']}**", reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(
                    "Aggiorna", callback_data="updatestats")],
            ]))


@app.on_callback_query(filters.regex("updatestats"))
def edit(client, callback_query):
    query = sessioni.search(Query()['id_user'] == callback_query.from_user.id)
    if query == []:
        try:
            app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id, "Utente non trovato!", reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(
                        "Aggiorna", callback_data="updatestats")],
                ]))
        except:
            pass
    else:
        try:
            app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id, f"Statisiche di {callback_query.from_user.mention}:\n\nTotale biscotti: **{query[0]['total_quantity']}**\nTotale sessioni vinte: **{query[0]['session']}**", reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(
                        "Aggiorna", callback_data="updatestats")],
                ]))
        except:
            callback_query.answer(
                "Informazioni già aggiornate!", show_alert=True)


def main():
    try:
        scheduler.remove_job("main")
    except:
        pass
    selectGroup()
    start_scheduler()


def ini():
    start_scheduler()


ini()
app.run()