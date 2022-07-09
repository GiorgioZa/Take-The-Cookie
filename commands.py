import cookies
import db
import ini
import bet
import group
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def welcome(message):
    ini.app.send_message(
        message.chat.id, "Questo bot ti permette di intrattenere il tuo gruppo con un gioco molto divertente.\nPer usare questo bot, aggiungilo come amministratore ad un gruppo in cui tu sei admin!")
    return


def how_work(message):
    ini.app.send_message(message.chat.id, "Per avviare la raccolta dei biscotti, utilizza il comando /add@TakeTheCookieBot, in questo modo dirai al bot che il tuo gruppo è pronto a ricevere dei gustosi biscotti! Inoltre, se vorrai rendere la sfida molto più esaltante, potrai attivare la ricezione dei premi automatici dal comando /groupinfo@TakeTheCookieBot !")
    return


def dev(message):
    ini.app.send_message(
        message.chat.id, "Versione biscotti: 2.1.0\n\nSviluppato da @GiorgioZa con l'aiuto e supporto dei suoi amiketti che lo sostengono in ogni sua minchiata ❤️\n\nUltime info sul bot -> <a href='https://t.me/TakeTheCookie'>canale ufficiale</a>")
    return


def info(message):
    groups = db.query_db_no_value("SELECT * FROM `groups`")
    if groups == []:
        ini.app.send_message(message.chat.id, "nessun gruppo presente")
        return
    text = f"Tutti i gruppi presenti:\n\n"
    for element in groups:
        members_count = ini.app.get_chat_members_count(element[0])
        text += f"- __{element[0]}__, **{element[1]}**, n°utenti: {members_count}\n"
    ini.app.send_message(message.chat.id, text)


def instant_cookie():
    ini.log_message("Ho forzato l'invio manuale del biscotto")
    cookies.biscotto(ini.group_id)
    return


def show_jobs(message):
    jobs = ini.scheduler.get_jobs()
    text = ""
    for element in jobs:
        text += element.name+" / "
    ini.app.send_message(message.chat.id, text)


def manual_close_bet():
    ini.log_message("Ho avviato la chiusura delle scommesse manuali")
    ini.time_check()
    return


def manual_open_bet():
    ini.log_message("Ho avviato le scommesse manualmente")
    query = db.query_db_no_value("SELECT `id_group` FROM `groups` WHERE `id_group` NOT IN (SELECT `id_group` FROM `bets`)")
    for element in query:
        bet.bet_fun(element[0])


def close_bet_by_id(message):
    info = message.text
    info = info.split(" ")
    if len(info) == 1:
        return
    info.pop(0)
    ini.log_message("Ho avviato la chiusura delle scommesse manuali per id")
    bet_i = db.query_db(
        "SELECT `closed` FROM `bets` WHERE `id_group` =%s", (info[0],))
    if bet_i == []:
        return
    elif bet_i[0][0] == 1 or bet_i[0][0] == 2:
        bet.remove(info[0])
    bet.find_result(info[0])
    return


def manual_choice_new_group():
    ini.log_message("Ho avviato la scelta di prendere un nuovo gruppo")
    ini.select_group()
    ini.scheduler_new_date()
    return


def manual_choice_group_by_id(message):
    info = message.text
    info = info.split(" ")
    if len(info) == 1:
        return
    info.pop(0)
    query = db.query_db(
        "SELECT `id_group`, `name` FROM `groups` WHERE `id_group` = %s", (info[0],))
    if query == []:
        ini.log_message("gruppo non trovato")
    else:
        ini.group_id = int(info[0])
        ini.log_message(f"{query[0][1]} è stato selezionato!")
        ini.scheduler_new_date()


def create_and_send_announce(message):
    info = message.text
    info = info.split("/announce")
    if len(info) == 1:
        return
    info.pop(0)
    text = ""
    for element in info:
        text += element
    query = db.query_db_no_value("SELECT `id_group` FROM `groups`")
    for gruppi in query:
        ini.app.send_message(gruppi[0], text)


def modify_manually_users(message):
    info = message.text
    info = info.split(" ")
    if len(info) == 1:
        return
    info.pop(0)
    user = db.query_db(
        "SELECT `id_user`, `quantity` FROM `sessions` WHERE `id_user` = %s", (info[0],))
    user_info = db.query_db(
        "SELECT * FROM `users` WHERE `id_user` = %s", (info[0],))
    if user_info == []:  # se l'utente non è mai esistito
        ini.app.send_message(
            message.chat.id, "L'utente non esiste nel database!")
        return
    else:
        if user == []:  # non è in sessione
            try:
                db.modify_db(
                    "INSERT INTO `sessions` (`id_user`, `quantity`) VALUES (%s, %s)", (info[0], info[1]))
            except:
                ini.app.send_message(
                    message.chat.id, "Attenzione HAI inserito troppi biscotti")
                return
            try:
                db.modify_db("UPDATE `users` SET `global_quantity` = %s WHERE `id_user` = %s",
                             (user_info[0][3]+int(info[1]), user[0][0]))
            except:
                ini.app.send_message(
                    message.chat.id, "Attenzione HAI inserito troppi biscotti")
                return
        else:  # l'utente è sia in sessione sia in generale
            try:
                db.modify_db("UPDATE `sessions` SET `quantity` = %s WHERE `id_user` = %s",
                             (user[0][1]+int(info[1]), user[0][0]))
            except:
                ini.app.send_message(
                    message.chat.id, "Attenzione HAI inserito troppi biscotti")
                return
            try:
                db.modify_db("UPDATE `users` SET `global_quantity` = %s WHERE `id_user` = %s",
                             (user_info[0][3]+int(info[1]), user[0][0]))
            except:
                ini.app.send_message(
                    message.chat.id, "Attenzione HAI inserito troppi biscotti")
                return
        ini.app.send_message(message.chat.id, "Operazione completata!")


def reboot(message, edit):
    if db.query_db("SELECT `id_group` FROM `groups` WHERE `id_group` = %s", (message.chat.id,)) == []:  # gruppo non esiste
        group.add_group(message)
    ini.app.edit_message_text(
        message.chat.id, edit.message_id, "✅Riavvio completato!✅")


def send_stats(message):
    query = db.query_db(
        "SELECT `global_quantity`, `session` FROM `users` WHERE `id_user` = %s", (message.from_user.id,))
    if query == []:
        ini.app.send_message(message.chat.id, "Utente non trovato!", reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(
                    "Aggiorna", callback_data="update_stats")],
            ]))
        return
    ini.app.send_message(
        message.chat.id, f"Statistiche globali di {message.from_user.mention}:\n\nTotale biscotti guadagnati: **{query[0][0]}**\nTotale sessioni vinte: **{query[0][1]}**", reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(
                    "Aggiorna", callback_data="update_stats")],
            ]))


def update_stats(callback_query):
    query = db.query_db("SELECT `global_quantity`, `session` FROM `users` WHERE `id_user` = %s",
                        (callback_query.from_user.id,))
    if query == []:
        try:
            ini.app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id, "Utente non trovato!", reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(
                        "Aggiorna", callback_data="update_stats")],
                ]))
        except:
            pass
    else:
        try:
            ini.app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id, f"Statistiche globali di {callback_query.from_user.mention}:\n\nTotale biscotti guadagnati: **{query[0][0]}**\nTotale sessioni vinte: **{query[0][1]}**", reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(
                        "Aggiorna", callback_data="update_stats")],
                ]))
        except:
            callback_query.answer(
                "Informazioni già aggiornate!", show_alert=True)


def send_personal_cookies_qta(message):
    query = db.query_db(
        "SELECT `quantity` FROM `sessions` WHERE `id_user` = %s", (message.from_user.id,))
    if query == []:
        ini.app.send_message(message.chat.id, "Utente non trovato!", reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(
                    "Aggiorna", callback_data="update_qta")],
            ]))
        return
    ini.app.send_message(
        message.chat.id, f"Statistiche di {message.from_user.mention}:\n\nN° biscotti guadagnati: **{query[0][0]}**", reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(
                    "Aggiorna", callback_data="update_qta")],
            ]))


def update_qta(callback_query):
    query = db.query_db("SELECT `quantity` FROM `sessions` WHERE `id_user` = %s",
                        (callback_query.from_user.id,))
    if query == []:
        try:
            ini.app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id, "Utente non trovato!", reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(
                        "Aggiorna", callback_data="update_qta")],
                ]))
        except:
            pass
    else:
        try:
            ini.app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id, f"Statistiche di {callback_query.from_user.mention}:\n\nN° biscotti guadagnati: **{query[0][0]}**", reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(
                        "Aggiorna", callback_data="update_qta")],
                ]))
        except:
            callback_query.answer(
                "Informazioni già aggiornate!", show_alert=True)


def give(message):
    command = message.text
    command = command.split(" ")
    command.pop(0)
    if len(command) <= 1 or int(command[1]) < 0:
        ini.app.send_message(message.chat.id, "Sintassi non corretta!\nUsa: /give __username utente a cui inviare__ __quantità da inviare__ (maggiore di zero)",
                             reply_to_message_id=message.message_id)
        return
    query = db.query_db(
        "SELECT u.id_user, `quantity`, `global_quantity` FROM `sessions` s JOIN `users` u ON s.id_user = u.id_user WHERE u.id_user = %s", (message.from_user.id,))
    if query == [] or query[0][1] == 0 or int(command[1]) > query[0][1]:
        ini.app.send_message(message.chat.id, "W la beneficenza... Ma per farla devi possedere abbastanza biscotti 😆.",
                             reply_to_message_id=message.message_id)
        return
    receiver = None
    try:
        receiver = ini.app.get_users(command[0])
    except:
        ini.app.send_message(message.chat.id, "OPS! Non è consentito inviare biscotti in paradisi fiscali 👮‍♂️! Assicurati che l'username o l'id dell'utente inserito sia corretto!",
                             reply_to_message_id=message.message_id)
        return
    query_2 = db.query_db(
        "SELECT `id_user`, `quantity` FROM `sessions` WHERE `id_user` = %s", (receiver.id,))
    query_3 = db.query_db(
        "SELECT `id_user`, `global_quantity` FROM `users` WHERE `id_user` = %s", (receiver.id,))
    group_id = 0
    qta = 0
    if message.chat.type != "PRIVATE":
        group_id = message.chat.id
    if query_3 == []:
        db.modify_db("INSERT INTO `users` VALUES (%s, %s, %s, %s, %s, %s)",
                     (receiver.id, receiver.first_name, receiver.username, command[1], 0, 0))
    else:
        qta = query_3[0][1]
        db.modify_db("UPDATE `users` SET `global_quantity`= %s WHERE `id_user` = %s",
                     (qta+int(command[1]), receiver.id))
    db.modify_db("UPDATE `users` SET `global_quantity`= %s WHERE `id_user` = %s",
                 (query[0][2]-int(command[1]), message.from_user.id))
    if query_2 == []:
        if group_id == 0:
            db.modify_db(
                "INSERT INTO `sessions`(`id_user`, `quantity`) VALUES (%s, %s)", (receiver.id, command[1]))
        else:
            db.modify_db("INSERT INTO `sessions` VALUES (%s, %s, %s)",
                         (receiver.id, group_id, command[1]))
    else:
        qta = query_2[0][1]
        db.modify_db("UPDATE `sessions` SET `quantity`= %s WHERE `id_user` = %s",
                     (qta+int(command[1]), receiver.id))
    db.modify_db("UPDATE `sessions` SET `quantity`= %s WHERE `id_user` = %s",
                 (query[0][1]-int(command[1]), message.from_user.id))
    ini.app.send_message(
        message.chat.id, f"Ho correttamente donato {command[1]} biscotti a {receiver.mention}!", reply_to_message_id=message.message_id)
    cookies.verify_win(receiver.id)