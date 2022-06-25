import ini
import cookies
import db
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def stop_bet(callback_query):
    callback_query.answer(
        "Mi dispiace, non puoi più scommettere perchè è scaduto il tempo :(", show_alert=True)


def choice(callback_query):
    group_bet = db.query_db(
        "SELECT `closed` FROM `bets` WHERE `id_group` = %s", (callback_query.message.chat.id,))
    if group_bet != [] and group_bet[0][0] == 0:
        test = db.query_db("SELECT `quantity` FROM `sessions` WHERE `id_user` = %s",
                           (callback_query.from_user.id,))
        if test == [] or test[0][0] == 0:
            callback_query.answer("Mi dispiace, non puoi scommettere nessun biscotto perchè non ne possiedi :(\
                \nRiscatta biscotti per poter scommettere e vincerne altri!", show_alert=True)
            return
        else:
            match callback_query.data:
                case "yes": yes_choice(callback_query)
                case "nope": no_choice(callback_query)
            write(callback_query)
    else:
        callback_query.answer(
            "Mi dispiace, non puoi più scommettere perchè il sondaggio è terminato :(", show_alert=True)


def yes_choice(callback_query):
    is_there = db.query_db("SELECT `id_user`, `quantity` FROM `yes_bets` WHERE `id_user` = %s and `id_group` = %s", (
        callback_query.from_user.id, callback_query.message.chat.id))  # cerco se l'utente ha risposto già al sondaggio
    is_on_other_choice = db.query_db("SELECT `id_user`, `quantity` FROM `no_bets` WHERE `id_user` = %s and `id_group` = %s", (
        callback_query.from_user.id, callback_query.message.chat.id))    # cerco se l'utente ha risposto in altro modo al sondaggio nel gruppo
    if is_on_other_choice != []:
        callback_query.answer(
            "Puoi scommettere solo su una risposta... Furbetto!😝", show_alert=True)
        return
    # e il gruppo a cui si trova ha avviato un sondaggio
    group_bet_done = db.query_db(
        "SELECT `id_group`, `id_poll` FROM `bets` WHERE `id_group` = %s", (callback_query.message.chat.id,))
    if is_there == [] and group_bet_done != []:  # utente nessuna scommessa, gruppo scommessa avviata
        db.modify_db("INSERT INTO `yes_bets` VALUES (%s, %s, %s, %s)",
                     (group_bet_done[0][0], group_bet_done[0][1], callback_query.from_user.id, 1))
    # utente già scommesso nel sondaggio, gruppo scommessa avviata
    elif is_there != [] and group_bet_done != []:
        quantity = db.query_db(
            "SELECT y.quantity, s.quantity  FROM `yes_bets` y JOIN `sessions` s ON y.id_user = s.id_user WHERE y.id_user = %s", (callback_query.from_user.id,))
        if ((quantity[0][0]*2) + (quantity[0][1]-1)) < 30:
            db.modify_db("UPDATE `yes_bets` SET `quantity` = %s WHERE `id_user` = %s",
                         (quantity[0][0]+1, callback_query.from_user.id))
        else:
            callback_query.answer(
                "Hai raggiunto il massimo di puntate disponibili!")
            return


def no_choice(callback_query):
    is_there = db.query_db("SELECT `id_user`, `quantity` FROM `no_bets` WHERE `id_user` = %s and `id_group` = %s", (
        callback_query.from_user.id, callback_query.message.chat.id))  # cerco se l'utente ha risposto al sondaggio nel gruppo
    is_on_other_choice = db.query_db("SELECT `id_user`, `quantity` FROM `yes_bets` WHERE `id_user` = %s and `id_group` = %s", (
        callback_query.from_user.id, callback_query.message.chat.id))   # cerco se l'utente ha risposto in altro modo al sondaggio nel gruppo
    if is_on_other_choice != []:
        callback_query.answer(
            "Puoi scommettere solo su una risposta... Furbetto!😝", show_alert=True)
        return
    # e il gruppo a cui si trova ha avviato un sondaggio
    group_bet_done = db.query_db(
        "SELECT `id_group`, `id_poll` FROM `bets` WHERE `id_group` = %s", (callback_query.message.chat.id,))
    if is_there == [] and group_bet_done != []:  # utente nessuna scommessa, gruppo scommessa avviata
        db.modify_db("INSERT INTO `no_bets` VALUES (%s, %s, %s, %s)",
                     (group_bet_done[0][0], group_bet_done[0][1], callback_query.from_user.id, 1))
    # utente già scommesso nel sondaggio, gruppo scommessa avviata
    elif is_there != [] and group_bet_done != []:
        quantity = db.query_db(
            "SELECT y.quantity, s.quantity  FROM `no_bets` y JOIN `sessions` s ON y.id_user = s.id_user WHERE y.id_user = %s", (callback_query.from_user.id,))
        if ((quantity[0][0]*2) + (quantity[0][1])) < 30:
            db.modify_db("UPDATE `no_bets` SET `quantity` = %s WHERE `id_user` = %s",
                         (quantity[0][0]+1, callback_query.from_user.id))
        else:
            callback_query.answer(
                "Hai raggiunto il massimo di puntate disponibili!")
            return


def find_result(group_id):
    query = db.query_db(
        "SELECT `id_group`, `announce`, `result` FROM `bets` WHERE `id_group` = %s", (group_id,))
    if query[0][1] == 1:  # si
        return
    prologue = "I vincitori della scommessa sono:"
    text = ""
    if query[0][2] == None:
        winner = db.query_db(
            "SELECT `id_user`, `quantity` FROM `no_bets` WHERE `id_group` = %s ORDER BY `quantity` DESC", (group_id,))
    else:
        winner = db.query_db(
            "SELECT `id_user`, `quantity` FROM `yes_bets` WHERE `id_group` = %s ORDER BY `quantity` DESC", (group_id,))
    for element in winner:
        user = db.query_db(
            "SELECT `quantity`, `global_quantity` FROM `users` u JOIN `sessions` s ON u.id_user = s.id_user WHERE u.id_user = %s", (element[0],))
        user_i = ini.app.get_users(element[0])
        text += f"\n- {user_i.mention()} "
        text += f"x{element[1]} -> x{element[1]*2}; Totale: {user[0][0]+(element[1]*2)}"
        qta = user[0][0] + element[1]*2
        db.modify_db(
            "UPDATE `sessions` SET `quantity` = %s WHERE `id_user` = %s", (qta, element[0]))
        tot = user[0][1]
        db.modify_db("UPDATE `users` SET `global_quantity` = %s WHERE `id_user` = %s",
                     (tot+element[1]*2, element[0]))
    value = ""
    if winner != []:
        value += "\nTroverete i biscotti accreditati direttamente, potete utilizzare il comando /quantity per poter vedere la vostra quantità posseduta in questa sessione :)"
        ini.app.send_message(group_id, prologue+text+value)
    else:
        ini.app.send_message(
            group_id, "Nessuna scommessa è risultata la vincente :(\nSarà per la prossima volta 😣 *biscotto triste*")
    db.modify_db(
        "UPDATE `bets` SET `announce` = %s WHERE `id_group` = %s", (1, query[0][0]))
    query = db.query_db(
        "SELECT `id_user` FROM `sessions` WHERE `id_group` = %s", (group_id,))
    for element in query:
        cookies.verify_win(element[0], group_id)


def remove(id_group, state):
    bet = db.query_db(
        "SELECT `id_group`, `id_poll`, `closed` FROM `bets` WHERE `id_group` =%s", (id_group,))
    if bet != []:
        if bet[0][2] == 0:
            if ini.remove_scheduler(f'remove{id_group}') == False:
                ini.log_message(
                    f"Non sono riuscito a rimuovere lo scheduler della chiusura scommesse")
            try:
                ini.app.edit_message_reply_markup(id_group, bet[0][1], InlineKeyboardMarkup(
                    [[InlineKeyboardButton("❌SCOMMESSE CHIUSE❌", callback_data="end")]]))
                # 1 = chiuso senza errori
                db.modify_db(
                    "UPDATE `bets` SET `closed` = %s WHERE `id_group` =%s", (1, id_group))
            except ini.errors.MessageNotModified:
                # 2 = chiuso senza aver modificato il messaggio per errori
                db.modify_db(
                    "UPDATE `bets` SET `closed` = %s WHERE `id_group` =%s", (2, id_group))
                pass
            yes = db.query_db(
                "SELECT `id_user`, `quantity` FROM `yes_bets` WHERE id_group = %s ORDER BY `quantity` DESC", (id_group,))
            no = db.query_db(
                "SELECT `id_user`, `quantity` FROM `no_bets` WHERE id_group = %s ORDER BY `quantity` DESC", (id_group,))
            text = "Risultato del sondaggio:\nSI:"
            if yes == []:
                text += "\n**NESSUNO**"
            else:
                for element in yes:
                    user = ini.app.get_users(element[0])
                    text += f"\n- {user.mention()} "
                    text += f"x{element[1]}"
            text += "\nNO:"
            if no == []:
                text += "\n**NESSUNO**"
            else:
                for element in no:
                    user = ini.app.get_users(element[0])
                    text += f"\n- {user.mention()} "
                    text += f"x{element[1]}"
            ini.app.send_message(id_group, text)
        if state == True:  # biscotto prima della scadenza
            find_result(id_group)
        else:
            ini.time_scheduler()


def bet_fun(message):
    id = message.chat.id
    if db.query_db("SELECT `id_group` FROM `groups` WHERE `id_group` = %s", (id,)) == []:
        ini.app.send_message(
            id, "Gruppo non trovato :(\nAssicurati di aver segnalato il gruppo al bot con il comando /add !")
        return
    gruppo = ini.app.get_chat(id)
    if db.query_db("SELECT `id_group` FROM `bets` WHERE `id_group` = %s", (id,)) == []:
        ini.app.send_message(id, "Hai avviato una scommessa!\
            \nRegole:\
            \n1)Per giocare puoi usare i tuoi biscotti riscattati durante la sessione.\
            \n2)Puoi scegliere **solo** una delle due opzioni; In caso di vittoria, la quantità puntata ti verrà doppiata!\
            \n3)Hai solo 1h di tempo (o meno se il biscotto arriva prima della chiusura del sondaggio) per poter scommettere.\
            \n4)Non puoi ritirare il voto quindi vota con attenzione 😝.\
            \n5)Puoi puntare al massimo il quantitativo di biscotti necessario per arrivare al totale di 29 biscotti (sempre che tu ne abbia così tanti a disposizione ;) )")

        id_poll = ini.app.send_message(id, f"**'Il gruppo riceverà almeno un biscotto entro la mezzanotte?'**", reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("SI!🍪", callback_data="yes"), InlineKeyboardButton(
                    "NO!🥠", callback_data="nope")]
            ]))

        ini.log_message(
            f"Questo gruppo ha avviato un nuovo sondaggio: {gruppo.title}")
        db.modify_db("INSERT INTO `bets`(`id_group`, `id_poll`, `result`) VALUES (%s, %s, %s)",
                     (id, id_poll.message_id, None))

        try:
            ini.scheduler.add_job(remove, 'interval', hours=1,
                                  args=(id, False), id='remove'+str(id))
        except:
            pass
    else:
        ini.app.send_message(id,
                             "questo gruppo ha già fatto la scommessa di giornata")
        return


def write(cquery):
    text = "**'Il gruppo riceverà almeno un biscotto entro la mezzanotte?'**"
    nusers = db.query_db(
        "SELECT `id_user`, `quantity` FROM `no_bets` WHERE `id_group` = %s", (cquery.message.chat.id,))
    yusers = db.query_db(
        "SELECT `id_user`, `quantity` FROM `yes_bets` WHERE `id_group` = %s", (cquery.message.chat.id,))
    for element in yusers:
        user = ini.app.get_users(element[0])
        text += f"\n- {user.mention}: "
        for x in range(element[1]):
            text += "🍪"
    for element in nusers:
        user = ini.app.get_users(element[0])
        text += f"\n- {user.mention}: "
        for x in range(element[1]):
            text += "🥠"
    user_qta = db.query_db(
        "SELECT `quantity`, `global_quantity` FROM `sessions` s JOIN `users` u ON s.id_user = u.id_user WHERE u.id_user = %s ", (cquery.from_user.id,))
    db.modify_db("UPDATE `sessions` SET `quantity` = %s WHERE `id_user` = %s",
                 (user_qta[0][0]-1, cquery.from_user.id))
    db.modify_db("UPDATE `users` SET `global_quantity` = %s WHERE `id_user` = %s",
                 (user_qta[0][1]-1, cquery.from_user.id))
    try:
        ini.app.edit_message_text(cquery.message.chat.id, cquery.message.message_id, text,
                                  reply_markup=InlineKeyboardMarkup(
                                      [
                                          [InlineKeyboardButton("SI!🍪", callback_data="yes"), InlineKeyboardButton(
                                              "NO!🥠", callback_data="nope")]
                                      ]))
    except:
        pass
