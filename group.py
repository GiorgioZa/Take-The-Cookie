import db
import ini
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def group_info(message):
    group = db.query_db(
        "SELECT * FROM `groups` WHERE `id_group` = %s", (message.chat.id,))
    if group == []:
        ini.app.send_message(
            message.chat.id, "Gruppo non trovato *biscotto triste*")
        return
    tot_member = ini.app.get_chat_members_count(message.chat.id)
    text = f"Nome: **{group[0][1]}**\nID: <code>{group[0][0]}</code>\nMembri: **{tot_member}**\nTotale biscotti: {group[0][2]}\nPremio: {'**Disattivato**' if group[0][4]==0 else '**Attivato**'}\nVisibilità: {'**Nascosta**' if group[0][3]==0 else '**Visibile**'}"
    ini.app.send_message(message.chat.id, text, reply_markup=InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Visibilità", callback_data="set_privacy"), InlineKeyboardButton(
                "Premio", callback_data="set_gift")],
            [InlineKeyboardButton(
                "Tutorial", url="https://t.me/TakeTheCookie/6")]
        ]))


def set_privacy(callback_query):
    group = db.query_db("SELECT * FROM `groups` WHERE `id_group` = %s",
                        (callback_query.message.chat.id,))
    if group == []:
        return
    if group[0][3] == 1:
        db.modify_db("UPDATE `groups` SET `privacy` = %s WHERE `id_group` = %s",
                     (0, callback_query.message.chat.id))
    else:
        db.modify_db("UPDATE `groups` SET `privacy` = %s WHERE `id_group` = %s",
                     (1, callback_query.message.chat.id))
    group = db.query_db("SELECT * FROM `groups` WHERE `id_group` = %s",
                        (callback_query.message.chat.id,))
    tot_member = ini.app.get_chat_members_count(
        callback_query.message.chat.id)
    try:
        ini.app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id, f"Nome: **{group[0][1]}**\nID: <code>{group[0][0]}</code>\nMembri: **{tot_member}**\nTotale biscotti: {group[0][2]}\nPremio: {'**Disattivato**' if group[0][4]==0 else '**Attivato**'}\nVisibilità: {'**Nascosta**' if group[0][3]==0 else '**Visibile**'}", reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Visibilità", callback_data="set_privacy"), InlineKeyboardButton(
                    "Premio", callback_data="set_gift")],
                [InlineKeyboardButton(
                    "Tutorial", url="https://t.me/TakeTheCookie/6")]
            ]))
    except:
        pass


def verify_admin(id_admin, id_group):
    admin_group = found_admin(id_group)
    if id_admin in admin_group:
        return True
    return False


def set_gift(callback_query):
    group = db.query_db("SELECT * FROM `groups` WHERE `id_group` = %s",
                        (callback_query.message.chat.id,))
    if group == []:
        return
    if group[0][4] == 1:
        db.modify_db("UPDATE `groups` SET `gift` = %s WHERE `id_group` = %s",
                     (0, callback_query.message.chat.id))
    else:
        db.modify_db("UPDATE `groups` SET `gift` = %s WHERE `id_group` = %s",
                     (1, callback_query.message.chat.id))
    group = db.query_db("SELECT * FROM `groups` WHERE `id_group` = %s",
                        (callback_query.message.chat.id,))
    tot_member = ini.app.get_chat_members_count(
        callback_query.message.chat.id)
    try:
        ini.app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id, f"Nome: **{group[0][1]}**\nID: <code>{group[0][0]}</code>\nMembri: **{tot_member}**\nTotale biscotti: {group[0][2]}\nPremio: {'**Disattivato**' if group[0][4]==0 else '**Attivato**'}\nVisibilità: {'**Nascosta**' if group[0][3]==0 else '**Visibile**'}", reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Visibilità", callback_data="set_privacy"), InlineKeyboardButton(
                    "Premio", callback_data="set_gift")],
                [InlineKeyboardButton(
                    "Tutorial", url="https://t.me/TakeTheCookie/6")]
            ]))
    except:
        pass


def found_admin(id):
    ad = ini.app.get_chat_members(id, filter="administrators")
    admin = []
    for a in ad:
        admin.append(int(a.user.id))
    return admin


def remove_group(group_id, group_name):
    value = db.query_db(
        "SELECT `id_group` FROM `groups` WHERE `id_group` = %s", (group_id,))
    if value != []:
        db.modify_db(db.DELETE_QUERY_GROUPS,
                     (group_id,))
        ini.app.send_message(
            group_id, "Ho rimosso questo gruppo dalla lista dei partecipanti! Tutti coloro che avevano raccolto biscotti in questa sessione da questo gruppo sono stati eliminati!")
        ini.log_message(
            f"Ho rimosso un nuovo gruppo: {group_name}")
    else:
        ini.app.send_message(
            group_id, "Questo gruppo non risulta nella lista dei partecipanti... L'informazione è errata? Perchè non contatti @GiorgioZa?")


def add_group(message):
    query = db.query_db(
        "SELECT `id_group` FROM `groups` WHERE `id_group` = %s", (message.chat.id,))
    if query == []:  # se il gruppo non è nel database
        # chi ha fatto il comando è admin?
        if verify_admin(message.from_user.id, message.chat.id) == True and str(message.from_user.id) in ini.banned_user:
            add_group_real(message)
            ini.app.send_message(
                message.chat.id, "Gruppo aggiunto! Da adesso può ricevere biscotti in qualsiasi momento... Tenete gli occhi aperti👀")
        else:  # non admin
            ini.app.send_message(
                message.chat.id, "Per usare questo bot, devi aggiungerlo ad un **GRUPPO** in cui tu sei admin!")
    else:  # gruppo già esistente
        ini.app.send_message(
            message.chat.id, "A quanto pare, hai già iscritto questo gruppo ai partecipanti!")


def add_group_real(message):
    chat = ini.app.get_chat(message.chat.id)
    db.modify_db("INSERT INTO `groups`(`id_group`, `name`) VALUES (%s, %s)",
                 (message.chat.id, chat.title))  # aggiungi il gruppo al db
    ini.log_message(
        f"Ho aggiunto un nuovo gruppo: {chat.title} da parte di: {message.from_user.username if message.from_user.username!=None else message.from_user.firstname}")


def remove_error(gruppo):
    db.modify_db(db.DELETE_QUERY_GROUPS, (gruppo,))
    ini.log_message(f"Ho elimato questo gruppo {gruppo}")
    try:
        ini.app.send_message(
            gruppo, f"Ho elimato questo gruppo {gruppo} per un errore di sistema, puoi riaggiungerlo usando il comando /add ;)")
    except:
        pass
