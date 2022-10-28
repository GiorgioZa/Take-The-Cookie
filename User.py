import Cookie
import Main
import User
import Db


def create_banned_list():
    b_user = open("banned.txt", "r").read().split(", ")
    banned_user = [x for x in b_user]
    return banned_user


async def ban_user(user_id):
    a = create_banned_list()
    if a != []:
        file = open("banned.txt", "a")
        file.write(f",{user_id}")
    else:
        file = open("banned.txt", "w")
        file.write(f"{user_id},")
    file.close()
    return "Utente bannato correttamente"


async def modify_user_qta(user_id, qta):
    user = await Db.user_query({"_id": user_id}, {"tot_qta": 1}, "tot_qta")
    if user == None:
        return "Utente non trovato nel database"
    else:
        user_s = await Db.session_query({"_id": user_id}, {"qta": 1}, "qta")
        if user_s == None:
            return "L'utente non ha ancora preso biscotti in questa sessione!"
        else:
            Db.session.update_one(
                {"_id": user_id}, {"$set": {"qta": user_s+qta}})
            Db.users.update_one({"_id": user_id}, {
                                "$set": {"tot_qta": user+qta}})
        group = await Db.session_query({"_id": user_id}, {"group_id": 1}, "group_id")
        await Cookie.win_complete(user_id, group)


async def my_stats(user_id, chat_id, message_id, callback_query):
    user = await Main.app.get_users(user_id)
    text = f"Statistiche di {user.mention}:\n"
    cookie_session_qta = await Db.session_query({"_id": user_id}, {"qta": 1}, "qta")
    user_other_stats_temp = Db.users.find({"_id": user_id}, {})
    user_other_stats = []
    for element in user_other_stats_temp:
        user_other_stats.append(element)
    if user_other_stats == []:
        if message_id != None:
            await Main.delete_message(chat_id, message_id)
        await Main.app.send_message(chat_id, "Utente non trovato!",reply_markup=Main.InlineKeyboardMarkup(
                                          [
                                              [Main.InlineKeyboardButton(
                                                  "Aggiorna!", callback_data="update", user_id=user_id)],
                                          ]))
        return
    else:
        text += f"- id: __{user_other_stats[0]['_id']}__"\
        f"\n- username: __{user_other_stats[0]['username']}__"\
        f"\n- biscotti in sessione: {'0' if cookie_session_qta == None else cookie_session_qta}"\
        f"\n- biscotti complessivi: {'0' if user_other_stats[0]['tot_qta'] == None else user_other_stats[0]['tot_qta']}"\
        f"\n- n° sessioni vinte:    {'0' if user_other_stats[0]['session_count'] == None else user_other_stats[0]['session_count']}"
        match user_other_stats[0]["propic"]:
            case 0:
                propic = "static/img/users/user_default.png"
            case 1:
                propic = f"static/img/users/{user_other_stats[0]['_id']}.png"
        match message_id:
            case None:
                await Main.app.send_photo(chat_id,
                                          propic,
                                          text,
                                          reply_markup=Main.InlineKeyboardMarkup(
                                              [
                                                  [Main.InlineKeyboardButton(
                                                      "Aggiorna!", callback_data="update", user_id=user_id)],
                                              ]))
            case _:
                try:
                    await Main.app.edit_message_media(chat_id, message_id,
                                                      Main.types.InputMediaPhoto(propic))
                    await Main.app.edit_message_caption(chat_id, message_id, text,
                                                        reply_markup=Main.InlineKeyboardMarkup(
                                                            [
                                                                [Main.InlineKeyboardButton(
                                                                    "Aggiorna!", callback_data="update", )],
                                                            ]))
                except Main.errors.MessageNotModified:
                    await callback_query.answer("Informazioni già aggiornate!", show_alert=True)
                    return
                except Main.errors.MessageEmpty:
                    await Main.delete_message(chat_id, message_id)
                    await Main.app.send_photo(chat_id,
                                          propic,
                                          text,
                                          reply_markup=Main.InlineKeyboardMarkup(
                                              [
                                                  [Main.InlineKeyboardButton(
                                                      "Aggiorna!", callback_data="update", user_id=user_id)],
                                              ]))


async def is_user_banned(user_id):
    return True if str(user_id) in create_banned_list() else False


async def ban_status(chat_id, user_id, update_message_id, callback_query):
    user = await Main.app.get_users(user_id)
    match update_message_id:
        case None:
            match await is_user_banned(user_id):
                case True: await Main.app.send_message(chat_id, f"📛 {user.mention()} è **BANNATO**!📛\n"\
                    "📯Non potrà raccogliere biscotti e/o aggiungere nuovi gruppi!",
                                                       reply_markup=Main.InlineKeyboardMarkup(
                                                           [
                                                               [Main.InlineKeyboardButton(
                                                                   "Update", callback_data="update_ban")]
                                                           ]))
                case False: await Main.app.send_message(chat_id, f"✅ {user.mention()} è **LIBERO**!✅\n"\
                    "📯Può continuare a raccogliere biscotti e/o aggiungere nuovi gruppi!",
                                                        reply_markup=Main.InlineKeyboardMarkup(
                                                            [
                                                                [Main.InlineKeyboardButton(
                                                                    "Update", callback_data="update_ban")]
                                                            ]))
        case _:
            match await is_user_banned(user_id):
                case True:
                    try:
                        await Main.app.edit_message_text(chat_id, update_message_id, f"📛 {user.mention()} è **BANNATO**!📛\n"\
                            "📯Non potrà raccogliere biscotti e/o aggiungere nuovi gruppi!",
                                                         reply_markup=Main.InlineKeyboardMarkup(
                                                             [
                                                                 [Main.InlineKeyboardButton(
                                                                     "Update", callback_data="update_ban")]
                                                             ]))
                    except Main.errors.MessageNotModified:
                        await callback_query.answer(
                            "Informazioni già aggiornate!", show_alert=True)

                case False:
                    try:
                        await Main.app.edit_message_text(chat_id, update_message_id, f"✅ {user.mention()} è **LIBERO**!✅\n"\
                            "📯Può continuare a raccogliere biscotti e/o aggiungere nuovi gruppi!",
                                                         reply_markup=Main.InlineKeyboardMarkup(
                                                             [
                                                                 [Main.InlineKeyboardButton(
                                                                     "Update", callback_data="update_ban")]
                                                             ]))
                    except Main.errors.MessageNotModified:
                        await callback_query.answer(
                            "Informazioni già aggiornate!", show_alert=True)


async def give_cookie(chat_id, command_message_id, sender, receiver, qta):
    error1 = "Quali biscotti pensavi di donare? Non ne possiedi abbastanza 😆."\
        "Cerca di riscattarne il più possibile per permetterti donazioni così cospique!"
    if await User.is_user_banned(receiver.id):
        await Main.app.send_message(chat_id, f"Non puoi donare biscotti ad una persona bannata 😵‍💫!", reply_to_message_id=command_message_id)
        return
    if receiver.id == sender:
        await Main.app.send_message(chat_id, 'Bella mossa... Ma non puoi donare a te stesso ;)')
    query_sender_qta = await Db.user_query({"_id": sender}, {"tot_qta": 1}, "tot_qta")
    query_sender_session_qta = await Db.session_query({"_id": sender}, {"qta": 1}, "qta")
    if query_sender_qta == None:
        # if the query is null...
        await Main.app.send_message(chat_id, error1, reply_to_message_id=command_message_id)
        return
    else:
        # if doesn't have enough cookie for complete the donation...
        if qta > query_sender_session_qta:
            await Main.app.send_message(chat_id, error1, reply_to_message_id=command_message_id)
            return
    query_receiver_global = await Db.user_query({"_id": receiver.id}, {"tot_qta": 1}, "tot_qta")
    query_receiver_session = await Db.session_query({"_id": receiver.id}, {"qta": 1}, "qta")
    # reduce the qta from the donator account
    Db.session.update_one(
        {"_id": sender}, {"$set": {"qta": query_sender_session_qta-qta}})
    Db.users.update_one(
        {"_id": sender}, {"$set": {"tot_qta": query_sender_qta-qta}})
    Cookie.update_cookie_quantity(
        query_receiver_global, query_receiver_session, qta, chat_id, receiver)
    await Main.app.send_message(chat_id,
                                f"✅Donazione Effettuata!✅\nFai sapere a {receiver.mention} della tua generosità sfruttando il bottone "\
         "sotto questo messaggio🥳.",
                                reply_to_message_id=command_message_id, reply_markup=Main.InlineKeyboardMarkup(
                                    [
                                        [Main.InlineKeyboardButton(
                                            "Ricevuta donazione", switch_inline_query=f"donate_notify;{sender};{qta}")]
                                    ]))
