import db
import random
import bet
import ini
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def update_list(callback_query):
    try:
        ini.app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id, create_list(), reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(
                    "Aggiorna", callback_data="update_cookie")],
            ]))
    except:
        callback_query.answer("Informazioni già aggiornate!", show_alert=True)
    return


def print_list(message):
    ini.app.send_message(message.chat.id, create_list(), reply_markup=InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(
                "Aggiorna", callback_data="update_cookie")],
        ]))
    return


def create_list():
    totale = db.query_db_no_value(
        "SELECT u.id_user, u.name_user, u.username, s.quantity FROM `users` u JOIN `sessions` s ON u.id_user = s.id_user ORDER BY s.quantity DESC, u.name_user ASC LIMIT 3")
    if len(totale) == 0:
        return "Nessuno ha riscattato biscotti per ora :("
    text = "Podio goloso:"
    for x in range(0, 3):
        try:
            text += f"\n{'🥇' if x==0 else '🥈' if x==1 else '🥉' if x==2 else ''} {totale[x][2] if totale[x][2]!=None else totale[x][1]}: {totale[x][3]}"
        except:
            continue
    text += "\n\nPer vedere la classifica completa, visita il <a href='https://bit.ly/3ODSCXO'>sito</a>!"
    return text


def win(winner, group):
    all_group = db.query_db(
        "SELECT `id_group` FROM `groups` WHERE `id_group` != %s", (group,))
    for element in all_group:
        ini.app.send_message(
            element[0], f"E' iniziata una nuova sessione🤩. State in guardia, il biscotto è sempre dietro l'angolo🙈")


def try_biscotto(chat_group):
    # rimuovi lo scheduler che ha inviato il biscotto
    ini.remove_scheduler("biscotto")
    local_group = db.query_db(
        "SELECT `id_group`, `name`, `tot_cookie` FROM `groups` WHERE id_group = %s", (chat_group,))
    if local_group == []:
        ini.log_message(
            f"A quanto pare il gruppo scelto ({chat_group}) non esiste più nel database, cambio gruppo")
        ini.restart()
        return
    try:
        # prova a mandare il biscotto
        bisquit = ini.app.send_message(chat_group, "Oh, ma cosa c'è qui... Un biscotto?! Corri a mangiarlo prima che qualche altro utente te lo rubi👀!!",
                                       reply_markup=InlineKeyboardMarkup(
                                           [
                                               [InlineKeyboardButton(
                                                   "Mangia il biscotto!😋🍪", callback_data="taken")],
                                           ]))
        ini.log_message(
            f"ho inviato biscotto nel gruppo: '{local_group[0][1]}'")
        ini.is_taken = False  # nessuno ha ancora preso biscotto
        ini.is_first = True  # ^
    except:  # se non riesci
        db.modify_db(db.DELETE_QUERY_GROUPS, (chat_group,))
        ini.log_message(
            f"non ho inviato il biscotto nel gruppo {local_group[0][1]} perchè ho avuto un problema")
        ini.restart()
        return
    try:
        ini.scheduler.add_job(expired, 'interval',  minutes=30,
                            args=(bisquit,), id=f"expired{bisquit.message_id}")
    except:
        ini.log_message(
            "non sono riuscito a creare lo scheduler per i biscotti scaduti :(")
    try:
        nbiscotti = local_group[0][2]
    except:
        nbiscotti = 0
    db.modify_db("UPDATE `groups` SET `tot_cookie` = %s WHERE `id_group` = %s",
                 (nbiscotti+1, chat_group))
    temp_bet = db.query_db(
        "SELECT `id_group`, `announce` FROM `bets` WHERE `id_group` = %s", (chat_group,))
    if temp_bet != []:
        if temp_bet[0][1] == 0:
            db.modify_db(
                "UPDATE `bets` SET `result` = %s WHERE `id_group` = %s", ('yes', chat_group))
            bet.remove(bisquit.chat.id, True)


def biscotto(chat_group):
    if ini.is_taken == True:  # biscotto riscattato, puoi inviare
        try_biscotto(chat_group)
    else:
        ini.restart()


def expired(bisquit):
    ini.is_taken = True
    ini.app.edit_message_reply_markup(bisquit.chat.id, bisquit.message_id, InlineKeyboardMarkup([[
        InlineKeyboardButton("Mangia il biscotto!🤔🍪", callback_data="expired")]]))
    ini.app.send_message(
        ini.LOG_GROUP, f"{bisquit.chat.title} ha aspettato troppo tempo. il biscotto è andato a male!")

    if ini.remove_scheduler(f'expired{bisquit.message_id}') == False:
        ini.log_message(
            "non sono riuscito a modificare lo scheduler del biscotto marcio!")
    ini.select_group()
    if ini.group_id != "0":
        biscotto(ini.group_id)
    return


def taken_query(callback_query):
    if str(callback_query.from_user.id) in ini.banned_user:
        return
    if ini.is_first == True:  # nessuno ha ancora preso il biscotto
        ini.is_first = False
        try_taken_query(callback_query)
        ini.is_first = True
    else:
        return


def try_taken_query(callback_query):
    text = ""
    ini.is_taken = True
    bisquit = db.query_db(
        "SELECT `id_user`, `quantity` FROM `sessions` WHERE `id_user` = %s", (callback_query.from_user.id,))
    general = db.query_db(
        "SELECT `id_user`, `global_quantity` FROM `users` WHERE `id_user` = %s", (callback_query.from_user.id,))
    if random.choice([False, True]) == True:  # biscotto avariato
        text = f"Avendo mangiato un biscotto avariato🤢, {callback_query.from_user.mention} ha avuto problemi di stomaco e quindi ha perso un biscotto dalla classifica generale!\n\nPress F to pay respect!"
        if bisquit == []:  # controllo se l'utente ha riscattato biscotti in questa sessione
            ini.app.send_message(callback_query.message.chat.id,
                                 f"Che sfortuna, il primo biscotto della sessione di {callback_query.from_user.mention()} era avariato *biscotto triste*. Mostrategli un pò di compassione.")
        else:
            quantity = int(bisquit[0][1])-1
            global_qta = int(general[0][1])-1
            try:
                db.modify_db("UPDATE `users` SET `global_quantity` = %s WHERE `id_user` = %s",
                             (global_qta, callback_query.from_user.id))
                db.modify_db("UPDATE `sessions` SET `quantity` = %s WHERE `id_user` = %s",
                             (quantity, callback_query.from_user.id))
            except:
                return
            callback_query.answer(
                "Mi dispiace, questo biscotto ha atteso per troppo tempo che qualcuno lo mangiasse e quindi è avariato🥺🤢... Sei stato avvelenato, hai vomitato e hai perso dei biscotti!", show_alert=True)
    else:  # biscotto sano
        text = f"Il 🍪 avariato è stato mangiato da {callback_query.from_user.mention()} senza conseguenze🎉!"
        callback_query.answer(
            f"WOW😳, caro {callback_query.from_user.first_name} che fortuna! Hai divorato il biscotto avariato senza conseguenze!", show_alert=True)
        ini.log_message(
            f"Biscotto del gruppo: {callback_query.message.chat.title} riscattato da: {callback_query.from_user.username if callback_query.from_user.username!=None else callback_query.from_user.first_name}")
        total = 0
        if bisquit == []:  # l'utente non è in sessione
            if general == []:  # l'utente non è nel db
                db.modify_db("INSERT INTO `users` VALUES (%s, %s, %s, %s, %s, %s)", (
                    callback_query.from_user.id, callback_query.from_user.first_name, f"{'@'+callback_query.from_user.username if callback_query.from_user.username else None}", 1, 0, 0))
                db.modify_db("INSERT INTO `sessions` VALUES (%s, %s, %s)",
                             (callback_query.from_user.id, callback_query.message.chat.id, 1))
            else:  # l'utente ha preso biscotti
                total = int(general[0][1])
                db.modify_db("UPDATE `users` SET `global_quantity` = %s WHERE `id_user` = %s",
                             (total+1, callback_query.from_user.id))
                db.modify_db("INSERT INTO `sessions` VALUES (%s, %s, %s)",
                             (callback_query.from_user.id, callback_query.message.chat.id, 1))
        else:  # l'utente è in sessione
            quantity = int(bisquit[0][1])+1
            global_total = int(general[0][1])+1
            db.modify_db("UPDATE `users` SET `global_quantity` = %s WHERE `id_user` = %s",
                         (global_total, callback_query.from_user.id))
            db.modify_db("UPDATE `sessions` SET `quantity` = %s WHERE `id_user` = %s",
                         (quantity, callback_query.from_user.id))
    db.modify_db("UPDATE `groups` SET `name` = %s WHERE `id_group` = %s",
                 (callback_query.message.chat.title, callback_query.message.chat.id))
    ini.download_propic(callback_query)
    ini.app.edit_message_text(
        callback_query.message.chat.id, callback_query.message.message_id, text)
    verify_win(callback_query.from_user.id, callback_query.message.chat.id)
    return


def taken(client, callback_query):
    if str(callback_query.from_user.id) in ini.banned_user:
        return
    if ini.is_first == True:
        ini.is_first = False
        try_taken(client, callback_query)
        ini.is_first = True
    else:
        return


def try_taken(client, callback_query):
    ini.is_taken = True
    ini.app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id,
                              f"Il 🍪 è stato mangiato da {callback_query.from_user.mention()}🎉!")
    callback_query.answer(
        f"Complimenti🥳 {callback_query.from_user.first_name}! Hai divorato il biscotto!", show_alert=True)
    ini.log_message(
        f"Biscotto del gruppo: {callback_query.message.chat.title} riscattato da: {callback_query.from_user.username if callback_query.from_user.username!=None else callback_query.from_user.first_name}")
    ini.remove_scheduler('biscotto')
    if ini.remove_scheduler(f'expired{callback_query.message.message_id}') == False:
        ini.log_message("Non sono riuscito a togliere lo scheduler ")
    
    total = 0
    bisquit = db.query_db(
        "SELECT `id_user`, `quantity` FROM `sessions` WHERE `id_user` = %s", (callback_query.from_user.id,))
    general = db.query_db(
        "SELECT `id_user`, `global_quantity` FROM `users` WHERE `id_user` = %s", (callback_query.from_user.id,))
    if bisquit == []:  # non è in session
        if general == []:  # mai preso biscotti
            db.modify_db("INSERT INTO `users` VALUES (%s, %s, %s, %s, %s, %s)", (
                callback_query.from_user.id, callback_query.from_user.first_name, f"{'@'+callback_query.from_user.username if callback_query.from_user.username else None}", 1, 0, 0))
            db.modify_db("INSERT INTO `sessions` VALUES (%s, %s, %s)",
                         (callback_query.from_user.id, callback_query.message.chat.id, 1))
        else:  # ha preso biscotti
            total = general[0][1]
            db.modify_db("UPDATE `users` SET `global_quantity` = %s WHERE `id_user` = %s",
                         (total+1, general[0][0]))
            db.modify_db("INSERT INTO `sessions` VALUES (%s, %s, %s)",
                         (callback_query.from_user.id, callback_query.message.chat.id, 1))
    else:
        quantity = bisquit[0][1]
        quantity += 1
        total = general[0][1]
        db.modify_db("UPDATE `users` SET\
                                `name_user` = %s,\
                                `username` = %s, \
                                `global_quantity` = %s WHERE `id_user` = %s ", (callback_query.from_user.first_name, f"{'@'+callback_query.from_user.username if callback_query.from_user.username else None}", total+1, general[0][0]))
        db.modify_db("UPDATE `sessions` SET\
                                    `id_group` = %s,\
                                    `quantity` = %s WHERE `id_user` = %s", (callback_query.message.chat.id, quantity, callback_query.from_user.id))
        verify_win(callback_query.from_user.id, callback_query.message.chat.id)
    ini.download_propic(callback_query)
    db.modify_db("UPDATE `groups` SET `name` = %s WHERE `id_group` = %s",
                 (callback_query.message.chat.title, callback_query.message.chat.id))
    ini.select_group()
    ini.scheduler_new_date()


def verify_win(user_id, group_id):
    bisquit = db.query_db(
        "SELECT `quantity`, `id_group` `session` FROM `sessions` s JOIN `users` u ON s.id_user = u.id_user WHERE s.id_user = %s", (user_id,))
    if bisquit == []:
        return

    if group_id == 0:
        group_id = bisquit[0][1]
        
    quantity = int(bisquit[0][0])
    sessionqa = int(bisquit[0][1])
    user = ini.app.get_users(user_id)
    match quantity:
        case 10:    ini.app.send_message(group_id,f"{user.mention} ha raggiunto i 10 biscotti!🎊")
        case 20:    ini.app.send_message(group_id,f"{user.mention} ha raggiunto i 20 biscotti!🎊")
    if quantity >= 30:    
        query = db.query_db("SELECT `gift` FROM `groups` WHERE `id_group` = %s", (group_id,))
        ini.last_winner = user_id
        win(user, group_id)
        if query[0][0] == 1 and win_check(user_id) == True:  # si + vittoria confermata
            ini.app.send_message(group_id, f"Complementi {user.mention}, sei arrivato ai 30 biscotti🎉🎊.\nHai vinto il premio messo in palio dal progetto MyFilms che collabora con noi. Per ritirare il premio, contatta in privato @Mario_Myfilms.\n\nPer tutti gli altri utenti incuriositi dal progetto, potete contattare @Mario_Myfilms! (anche perchè ai non vincitori spetta comunque una promo 🌚).\n\nIn bocca al lupo al prossimo vincitore 😁\n\n❕*Ovviamente il vincitore attuale è escluso dalle vincite per i prossimi mesi.*\n***Il vincitore può anche rifiutare il premio!* **")
        else:  # no
            ini.app.send_message(group_id,
                                 f"Complementi {user.mention}, sei arrivato ai 30 biscotti perciò hai vinto questa sessione!🎉🎊")
        ini.log_message(
            f"{user.mention} è arrivato a 30 biscotti! Database resettato.")
        
        db.modify_db("UPDATE `users` SET `session` = %s WHERE `id_user` = %s",
                     (sessionqa+1, user.id))
        db.modify_db_no_value("DELETE FROM `sessions`")


def win_check(winner_id):
    f = open("last_winners.txt", "r")
    winners = f.read().split(",")
    while len(winners) > 3:
        winners.pop(0)
    all = winners.copy()
    f.close()
    if str(winner_id) in winners:
        ini.log_message("Il vincitore ha già vinto nelle 3 sessioni passate!")
        return False
    else:
        ini.log_message("Vittoria confermata!")
        all.append(winner_id)
        f1 = open("last_groups.txt", "w")
        for x in all:
            f1.write(str(x)+",")
        f1.close()
        return True

            