import Main
import User
import pymongo
import Db
import asyncio
from datetime import datetime


async def group_info(group_name, group_id, callback_query):
    text = f"Statistiche del gruppo **{group_name}**\n"
    group_info_temp = Db.groups.find({"_id": group_id})
    group_info = []
    for x in group_info_temp:
        group_info.append(x)
    group = await Main.app.get_chat(group_id)
    text += f"- id: __{group_id}__\n"\
            f"- n° utenti: __{group.members_count}__\n"\
            f"- n° biscotti ricevuti: __{group_info[0]['n_cookie']}__\n"\
            f"- Privacy: **{'Nascosta' if group_info[0]['privacy']==0 else 'Visibile'}**\n"\
            f"- Premi: **{'Non attivi' if group_info[0]['gift']==0 else 'Attivi'}**"
    match group_info[0]["propic"]:
        case 0:
            propic = "static/img/groups/group_default.png"
        case 1:
            propic = f"static/img/groups/{group_info[0]['_id']}.png"

    match callback_query:
        case None:
            await Main.app.send_photo(group_id,
                                      propic,
                                      text,
                                      reply_markup=Main.InlineKeyboardMarkup(
                                        [
                                            [Main.InlineKeyboardButton(
                                                "Aggiorna", callback_data="update_group_stat")],
                                            [Main.InlineKeyboardButton(
                                                "Cambia Privacy", callback_data="set_privacy"),
                                             Main.InlineKeyboardButton(
                                                "Ricezione Premio", callback_data="set_gift")]
                                        ]))
        case _:
            try:
                await Main.app.edit_message_media(group_id, callback_query.message.message_id,
                                                  Main.types.InputMediaPhoto(propic))
                await Main.app.edit_message_text(group_id, callback_query.message.message_id, text, reply_markup=Main.InlineKeyboardMarkup(
                    [
                        [Main.InlineKeyboardButton(
                            "Aggiorna", callback_data="update_group_stat")],
                        [Main.InlineKeyboardButton(
                            "Cambia Privacy", callback_data="set_privacy"),
                         Main.InlineKeyboardButton(
                            "Ricezione Premio", callback_data="set_gift")]
                    ]))
            except Main.errors.MessageNotModified:
                await callback_query.answer("Informazioni già aggiornate!", show_alert=True)
                return


async def found_admin(id):
    all_admin = await Main.app.get_chat_members(id, filter="administrators")
    admin = []
    for x in all_admin:
        admin.append(int(x.user.id))
    return admin


async def verify_admin(id_admin, id_group):
    admins = await found_admin(id_group)
    return True if int(id_admin) in admins else False


async def insert_group_in_db(group_id, user_id):
    chat = await Main.app.get_chat(group_id)
    user = await Main.app.get_users(user_id)
    try:
        Db.groups.insert_one({"_id": group_id, "name": chat.title, "n_cookie": 0,
                             "privacy": 1, "gift": 1, "propic": 0, "date": datetime.now()})  # add the group in the db
    except pymongo.errors.DuplicateKeyError:
        return None
    except:
        await Main.log_message(
            f"Ho avuto un problema ad inserire il gruppo: {chat.title}!")
        return False
    if not await Main.download_group_pic(group_id):
        return False
    user_name = user.username if user.username != None else user.mention()
    await Main.log_message(
        f"Ho aggiunto un nuovo gruppo: {chat.title} da parte di: {user_name}!")
    return True


async def add_group(group_id, user_id):
    # if user is not admin or is banned
    if not await verify_admin(user_id, group_id) or await User.is_user_banned(user_id):
        await Main.app.send_message(group_id, "**ERRORE!** Non puoi aggiungere il bot al gruppo! Le motivazioni possono essere le seguenti:"\
                                    "\n1) Sei stato bannato (usa il comando /im_banned per scoprirlo)\n2) Non sei admin di questo gruppo.")
        return
    else:
        match await insert_group_in_db(group_id, user_id):
            case True: await Main.app.send_message(group_id, "Gruppo aggiunto correttamente! Iniziate a tenere gli occhi aperti👀, il biscotto è dietro l'angolo😋!")
            case False: await Main.app.send_message(group_id, "Non sono riuscito ad aggiungere il gruppo🥺! Riprova o contatta @GiorgioZa👌.")
            case None: await Main.app.send_message(group_id, "A quanto pare, hai già iscritto questo gruppo ai partecipanti!\nL'informazione non è corretta?🧐 Contatta @GiorgioZa👌.")


async def remove_group(group_id, user_id):
    # if user is not admin or is banned
    if not await verify_admin(user_id, group_id):
        await Main.app.send_message(group_id, "**ERRORE!** Non puoi rimuovere il bot dal gruppo perchè non sei admin di questo gruppo!")
        return
    else:
        query = await Db.group_query({"_id": group_id}, {"_id": 1}, "_id")
        if query == None:
            await Main.app.send_message(group_id, "**ERRORE!** Il gruppo non risulta nel database! Riprova o contatta @GiorgioZa👌.")
            return
        else:
            Db.groups.delete_one({"_id": group_id})
            await Main.app.send_message(group_id, "Gruppo rimosso correttamente!",
                                        reply_markup=Main.InlineKeyboardMarkup(
                                            [
                                                [Main.InlineKeyboardButton(
                                                    "Rimuovi dal gruppo!", callback_data="quit_group")],
                                            ]))

            group = await Main.app.get_chat(group_id)
            user = await Main.app.get_users(user_id)
            await Main.log_message(f"Ho rimosso il gruppo {group.title} da parte di {user.mention()}")
            return
