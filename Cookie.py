
import Main
import Bet
import random
import Db
from datetime import datetime


async def cookie(group_id):
    Main.remove_scheduler("cookie", 1)  # remove the scheduler
    temp_query = Db.groups.find(
        {"_id": int(group_id)}, {"_id": 1, "name": 1, "n_cookie": 1})
    group_info = []
    for x in temp_query:
        group_info.append(x)
    try:  # try to send the cookie
        bisquit = await Main.app.send_message(group_id, "Oh, ma cosa c'è qui... Un biscotto?!\n"\
            "Corri a mangiarlo prima che qualche altro utente te lo rubi!!👀",
                                              reply_markup=Main.InlineKeyboardMarkup(
                                                  [
                                                      [Main.InlineKeyboardButton(
                                                          "Mangia il biscotto!😋🍪", callback_data="take_it")],
                                                  ]))
        match Main.is_gold:
            case True:
                Db.cookies.insert_one(
                    {"_id": bisquit.message_id, "group_id": bisquit.chat.id,  "is_taken": 0, "is_expired": 0, "value": 10, "time": datetime.now().timestamp()})
            case False:
                Db.cookies.insert_one(
                    {"_id": bisquit.message_id, "group_id": bisquit.chat.id, "is_taken": 0, "is_expired": 0, "value": 1, "time": datetime.now().timestamp()})
        await Main.log_message(
            f"ho inviato biscotto nel gruppo: '{bisquit.chat.title}'")
    except:  # cookie invalid or something else
        await Main.log_message(
            f"non ho inviato il biscotto nel gruppo {group_info[0]['name']} perchè ho avuto un problema")
        Db.groups.delete_one({"_id": group_id})
        await Main.restart()
        return
    try:
        Main.asyncioscheduler.add_job(expired, 'interval',  hours=1,
                                      args=(bisquit.message_id, bisquit.chat.id, bisquit.chat.title), id=f"expired{bisquit.message_id}")
    except:
        await Main.log_message(
            "non sono riuscito a creare lo scheduler per i biscotti scaduti :(")
    nbiscotti = group_info[0]["n_cookie"]
    Db.groups.update_one({"_id": group_id}, {
                         "$set": {"n_cookie": nbiscotti+1}})
    temp_bet = await Db.bet_query({"_id": group_id}, {"closed": 1}, "closed")
    if temp_bet != None:
        Db.bet.update_one({"_id": group_id}, {"$set": {"result": 1}})
        await Bet.remove(bisquit.chat.id, True)
    
    await Main.select_group()
    await Main.scheduler_new_date()


async def scale_cookie_session(user_id, qta):
    user_session_qta = await Db.session_query({"_id": user_id}, {"qta": 1}, "qta")
    Db.session.update_one(
        {"_id": user_id}, {"$set": {"qta": user_session_qta - int(qta)}})


async def scale_cookie_general(user_id, qta):
    user_qta = await Db.user_query({"_id": user_id}, {"tot_qta": 1}, "tot_qta")
    Db.users.update_one({"_id": user_id}, {
                        "$set": {"tot_qta": user_qta - int(qta)}})


async def add_cookie_session(user_id, qta):
    user_session_qta = await Db.session_query({"_id": user_id}, {"qta": 1}, "qta")
    Db.session.update_one(
        {"_id": user_id}, {"$set": {"qta": user_session_qta + int(qta)}})


async def add_cookie_general(user_id, qta):
    user_qta = await Db.user_query({"_id": user_id}, {"tot_qta": 1}, "tot_qta")
    Db.users.update_one({"_id": user_id}, {
                        "$set": {"tot_qta": user_qta + int(qta)}})


async def add_cookie_complete(user_id, qta):
    await add_cookie_session(user_id, qta)
    await add_cookie_general(user_id, qta)


async def scale_cookie_complete(user_id, qta):
    await scale_cookie_session(user_id, qta)
    await scale_cookie_general(user_id, qta)


async def expired(message_id, chat_id, chat_title):
    if Main.remove_scheduler(f'expired{message_id}', 1) == False:
        await Main.log_message(
            "non sono riuscito a modificare lo scheduler del biscotto marcio!")
    Db.cookies.update_one({"_id": message_id}, {"$set": {"is_expired": 1}})
    await Main.app.edit_message_reply_markup(chat_id, message_id, Main.InlineKeyboardMarkup([[
        Main.InlineKeyboardButton("Mangia il biscotto!🤔🍪", callback_data="take_expired")]]))
    await Main.app.send_message(
        Main.LOG_GROUP, f"{chat_title} ha aspettato troppo tempo e il biscotto è marcito!")


async def take(callback_query):
    query_temp = Db.cookies.find(
        {"_id": callback_query.message.message_id}, {"_id": 0})
    cookie_info = []
    for x in query_temp:
        cookie_info.append(x)
    if cookie_info == []:
        await Main.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        await Main.log_message(f'Ho dovuto eliminare il biscotto nel gruppo {callback_query.message.chat.title} per un problema!')
        return False
    if cookie_info[0]["is_taken"] == 0:  # taken cookie
        if Main.remove_scheduler(f'expired{callback_query.message.message_id}', 1) == False:
            await Main.log_message("Non sono riuscito a togliere lo scheduler del biscotto scaduto!")
        session_qta = await Db.session_query({"_id": callback_query.from_user.id}, {"qta": 1}, "qta")
        general_qta = await Db.user_query({"_id": callback_query.from_user.id}, {"tot_qta": 1}, "tot_qta")
        match cookie_info[0]["is_expired"]:
            case 1:  # cookie expired
                a = await modify_expired_cookie_message(callback_query)
                if not a:
                    return False
            case 0:  # cookie not expired
                match cookie_info[0]["value"]:
                    case 1:
                        a = await modify_cookie_message(callback_query)
                        if not a:
                            return False 
                        await cookie_stuff_after_taken(callback_query, 1, session_qta, general_qta)
                    case 10:
                        a = await modify_golden_cookie_message(callback_query)
                        if not a:
                            return False 
                        await cookie_stuff_after_taken(callback_query, 10, session_qta, general_qta)
    else:
        return True


def update_cookie_quantity(query_receiver_global, query_receiver_session, qta, chat_id, user):
    # user never take a cookie in his life
    if query_receiver_global == None and query_receiver_session == None:
        # insert the receiver in the db with the qta
        Db.users.insert_one({"_id": user.id, "name": user.first_name, "username": f"@{user.username}",
                            "tot_qta": qta, "session_count": 0, "propic": 0})
        Db.session.insert_one(
            {"_id": user.id, "group_id": chat_id, "qta": qta})
    # user took cookie in the past but not in this session
    elif query_receiver_global != None and query_receiver_session == None:
        # insert the receiver in the db with the qta
        Db.users.update_one({"_id": user.id}, {
                            "$set": {"tot_qta": query_receiver_global+qta}})
        Db.session.insert_one(
            {"_id": user.id, "group_id": chat_id, "qta": qta})
    else:
        # user is just in db, so update it
        if query_receiver_session+qta > 30:
            query_receiver_session = 30
        else:
            query_receiver_session += qta
        Db.users.update_one({"_id": user.id}, {
                            "$set": {"tot_qta": query_receiver_global+qta}})
        Db.session.update_one({"_id": user.id}, {
                              "$set": {"qta": query_receiver_session}})


async def cookie_stuff_after_taken(callback_query, qta, session_qta, general_qta):
    user = await Main.app.get_users(callback_query.from_user.id)
    update_cookie_quantity(general_qta, session_qta, qta,
                           callback_query.message.chat.id, user)
    await win_complete(callback_query.from_user.id, callback_query.message.chat.id)
    await Main.download_propic(callback_query.from_user.id)
    Db.groups.update_one({"_id": callback_query.message.chat.id}, {
                         "$set": {"name": callback_query.message.chat.title}})


async def verify_win(user_id):
    session_qta = await Db.session_query({"_id": user_id}, {"qta": 1}, "qta")
    if session_qta >= 30:
        return True
    return False


async def victory(user_id, group_id):
    user = await Main.app.get_users(user_id)
    text = ""
    gift_status = await Db.group_query({"_id": group_id}, {"gift": 1}, "gift")
    if gift_status == 1:
       text = f"\
       🔝Complementi {user.mention}🔝, sei arrivato per primo a quota 30 biscotti🎉🎊."\
       "\nHai vinto il premio messo in palio dal progetto MyFilms che finanzia Take The Cookie. "\
       "Per ritirare il premio, contatta in privato @Mario_Myfilms."\
       "\n\nIn bocca al lupo al prossimo vincitore 💯😁"\
       "\n***Il vincitore può rifiutare il premio e scegliere il suo destinatario!***"
    else:
       text = f"🔝Complementi {user.mention}🔝, sei arrivato a quota 30 biscotti e hai vinto questa sessione!🎉🎊"
    text = f"🔝Complementi {user.mention}🔝, sei arrivato a quota 30 biscotti e hai vinto questa sessione!🎉🎊"
    await Main.log_message(f"{user.mention} è arrivato a 30 biscotti! Database resettato.")
    session_qta = await Db.user_query({"_id": user_id}, {"session_count": 1}, "session_count")
    Db.users.update_one({"_id": user_id}, {
                        "$set": {"session_count": session_qta+1}})
    await alert_win(user.mention, group_id)
    await Db.session_reset()  # database reset
    await Main.app.send_message(group_id, text)


async def achievement(user_id, group_id):
    session_qta = await Db.session_query({"_id": user_id}, {"qta": 1}, "qta")
    user = await Main.app.get_users(user_id)
    text = None
    match session_qta:
        case 10:
            text = f"{user.mention} ha raggiunto i 10 biscotti!🎊"
        case 20:
            text = f"{user.mention} ha raggiunto i 20 biscotti!🎊"
    if text != None:
        await Main.app.send_message(group_id, text)


async def win_complete(user_id, group_id):
    match await verify_win(user_id):
        case True:
            await victory(user_id, group_id)
            return True
        case False:
            await achievement(user_id, group_id)
            return False


# find the first winner of in the bet
async def find_winner_in_bet(group_id, type):
    users = await Db.bet_query_sorted({"_id": group_id}, {type: 1}, type, "qta", -1)
    for element in users:
        user = Db.session.find({"_id": element["_id"]})
        for elements in user:
            if await verify_win(elements['_id']):
                await victory(elements['_id'], group_id)
                return


async def alert_win(winner, group):
    all_group = Db.groups.find({"_id": {"$ne": group}}, {"_id": 1})
    for element in all_group:
        try:
            await Main.app.send_message(
                element["_id"], f"La sessione corrente è appena terminata ed ha visto come vincitore {winner}🤩! "\
                    "I biscotti, però, non hanno tregua e anche durante i festeggiamenti, "\
                    "continuano ad apparire nei gruppi e a corgliervi di sorpresa. "\
                    "Per questo motivo dovreste tenere sempre gli occhi aperti👀, "\
                    "il prossimo biscotto è dietro l'angolo🌚 che aspetta solo di essere divorato😋."\
                    "\nGood Luck❤️")
        except:
            pass


async def modify_golden_cookie_message(callback_query):
    try:
        await Main.app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id,
                                         f"Il 🍪 d'oro è stato mangiato da {callback_query.from_user.mention()}🎉!")
    except:
        return False
    await callback_query.answer(
        f"Complimenti🥳 {callback_query.from_user.first_name}! Hai divorato il biscotto d'oro 🌕!", show_alert=True)
    await Main.log_message(
        f"Biscotto d'oro del gruppo: {callback_query.message.chat.title} riscattato da: @{callback_query.from_user.username if callback_query.from_user.username!=None else callback_query.from_user.first_name}")
    return True

async def modify_cookie_message(callback_query):
    try:
        await Main.app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id,
                                         f"Il 🍪 è stato mangiato da {callback_query.from_user.mention()}🎉!")
    except:
        return False
    await callback_query.answer(
        f"Complimenti🥳 {callback_query.from_user.first_name}! Hai divorato il biscotto 🤤!", show_alert=True)
    await Main.log_message(
        f"Biscotto del gruppo: {callback_query.message.chat.title} riscattato da: @{callback_query.from_user.username if callback_query.from_user.username!=None else callback_query.from_user.first_name}")
    return True

async def modify_expired_cookie_message(callback_query):
    session_qta = await Db.session_query({"_id": callback_query.from_user.id}, {"qta": 1}, "qta")
    general_qta = await Db.user_query({"_id": callback_query.from_user.id}, {"tot_qta": 1}, "tot_qta")
    if random.choice([False, True]):  # biscotto avariato
        try:
            await Main.app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id,
                                             f"Oh no🥺! {callback_query.from_user.mention} ha mangiato un biscotto avariato 🤢.\n"\
                                              "Press F to pay respect 🙏.")
        except:
            return False
        if session_qta != None:
            qta = 0 if session_qta-1 < 0 else session_qta-1
            tot_qta = 0 if general_qta-1 < 0 else general_qta-1
            Db.session.update_one({"_id": callback_query.from_user.id}, {
                                  "$set": {"qta": qta}})
            Db.users.update_one({"_id": callback_query.from_user.id}, {
                                "$set": {"tot_qta": tot_qta}})
        await callback_query.answer(
            f"Che peccato. Questo biscotto ha atteso per troppo tempo che qualcuno lo mangiasse ed è avariato🥺🤢... "\
            "Sei stato avvelenato, hai vomitato e hai perso un biscotto!😵‍💫", show_alert=True)
        await Main.log_message(
            f"Biscotto avariato del gruppo: {callback_query.message.chat.title} riscattato da: @{callback_query.from_user.username if callback_query.from_user.username!=None else callback_query.from_user.first_name}")
    else:
        qta = await Db.cookie_query({"_id": callback_query.message.message_id}, {"value": 1}, "value")
        try:
            await Main.app.edit_message_text(callback_query.message.chat.id, callback_query.message.message_id,
                                             f"Che fortuna!🍀 {callback_query.from_user.mention} ha mangiato un biscotto avariato senza subire conseguenze.\n"\
                                            "Che utente fortunato😮‍💨.")
        except:
            return False
        await cookie_stuff_after_taken(callback_query, qta, session_qta, general_qta)
        await callback_query.answer(
            f"WOW😳, caro {callback_query.from_user.first_name} che fortuna! "\
                "Hai divorato il biscotto avariato senza conseguenze!", show_alert=True)
        await Main.log_message(
            f"Biscotto del gruppo: {callback_query.message.chat.title} riscattato da: {callback_query.from_user.username if callback_query.from_user.username!=None else callback_query.from_user.first_name}")
