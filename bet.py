import Db
import Main
import Cookie


async def start_bet(message_entity):
    # the group doesn't exist
    if await Db.group_query({"_id": message_entity.chat.id}, {"_id": 1}, "_id") is None:
        await Main.app.send_message(
            message_entity.chat.id, "Gruppo non trovato :(\nAssicurati di aver segnalato il gruppo al bot con il comando /add !")
    elif await Db.bet_query({"_id": message_entity.chat.id}, {"_id": 1}, "_id") != None:
        await Main.app.send_message(
            message_entity.chat.id, "Una scommessa è già stata avviata!")
        return
    else:
        # group doesn't start the bet
        if await Db.bet_query({"_id": message_entity.chat.id}, {"_id": 1}, "_id") is None:
            message = await Main.app.send_message(message_entity.chat.id,
                                                  "💸Nuova scommessa avviata!💯\
                \nQuesto gruppo riceverà almeno un biscotto entro mezzanotte?",
                                                  reply_markup=Main.InlineKeyboardMarkup(
                                                      [
                                                          [Main.InlineKeyboardButton(
                                                              "🤑Scommetti sul 'SI'💸", switch_inline_query_current_chat=f"bet;yes;{message_entity.chat.id}"),
                                                              Main.InlineKeyboardButton(
                                                              "🤑Scommetti sul 'NO'☘️", switch_inline_query_current_chat=f"bet;no;{message_entity.chat.id}")]
                                                      ])
                                                  )
            Db.bet.insert_one({"_id": message_entity.chat.id, "bet_message": message.message_id,  "yes_users": [
            ], "no_users": [], "result": 0, "closed": 0, "announce": 0})
    Main.asyncioscheduler.add_job(close_bet, 'interval', hours=1,
                                  args=(message_entity.chat.id, message.message_id), id=f'bet{message_entity.chat.id}')


async def close_bet(group_id, bet_id):
    Main.remove_scheduler(f"bet{group_id}", 1)
    await Main.app.edit_message_reply_markup(group_id, bet_id, Main.InlineKeyboardMarkup([
        [Main.InlineKeyboardButton(
            "📛SCOMMESSE CHIUSE📛", callback_data=f"bet_expired")]
    ]))
    Db.bet.update_one({"_id": group_id}, {"$set": {"closed": 1}})
    await confirm_bet(group_id)
    await bet_recap(group_id)


async def is_closed(group_id):
    return True if await Db.bet_query({"_id": group_id}, {"closed": 1}, "closed") == 1 else False


async def bet_recap(group_id):
    flag = await Db.bet_query({"_id": group_id}, {"announce"}, "announce")
    if flag == 0:
        Db.bet.update_one({"_id": group_id}, {"$set": {"announce": 1}})
        text = f"Riassunto delle scommesse nel gruppo **{await Db.group_query({'_id': group_id}, {'name'},'name')}**:\n"
        yes_bet = await Db.bet_query({"_id": group_id}, {"yes_users"}, "yes_users")
        no_bet = await Db.bet_query({"_id": group_id}, {"no_users"}, "no_users")
        if (yes_bet == [] or yes_bet == None) and (no_bet == [] or no_bet == None):
            text += "**Nessuna scommessa è stata registrata!**"
        elif (yes_bet != [] or yes_bet != None) and (no_bet == [] or no_bet == None):
            text += "SI:\n"
            for element in yes_bet:
                text += f"- {await Db.user_query({'_id': element['_id']}, {'username'}, 'username')} -> 🍪 x{element['qta']}\n"
            text += "NO:\n **Nessuna scommessa è stata registrata!**"
        elif (yes_bet == [] or yes_bet == None) and (no_bet != [] or no_bet != None):
            text += "NO:\n"
            for element in no_bet:
                text += f"- {await Db.user_query({'_id': element['_id']}, {'username'}, 'username')} -> 🍪 x{element['qta']}\n"
            text += "SI:\n **Nessuna scommessa è stata registrata!**"
        else:
            text += "SI:\n"
            for element in yes_bet:
                text += f"- {await Db.user_query({'_id': element['_id']}, {'username'}, 'username')} -> 🍪 x{element['qta']}\n"
            text += "NO:\n"
            for element in no_bet:
                text += f"- {await Db.user_query({'_id': element['_id']}, {'username'}, 'username')} -> 🍪 x{element['qta']}\n"
        await Main.app.send_message(group_id, text)
        Main.time_scheduler()


async def confirm_bet(group_id):
    x = 0
    yes_bet = await Db.bet_query({"_id": group_id}, {"yes_users"}, "yes_users")
    y = len(yes_bet)
    no_bet = await Db.bet_query({"_id": group_id}, {"no_users"}, "no_users")
    for element in yes_bet + no_bet:
        user = Db.users.find({"_id": element["_id"]})
        try:
            await Main.app.edit_message_text(group_id, element["bet_message"],
                                             f"✅{user[0]['username']} ha confermato la scommessa di {element['qta']} biscotti sul '{'SI' if x<y else 'NO'}'!")
        except:
            pass
        x += 1


async def focus_on(message):
    command = message.text
    command = command.split(" ")
    command.pop(0)
    bet_bill = await Main.app.send_message(message.chat.id,
                                           f"{message.from_user.mention} ha scommesso {command[1]} biscotti sul '{'SI' if command[2] == 'yes' else 'NO'}'!\
            \nSe vuoi cambiare puntata o eliminarla del tutto, usa le impostazioni allegate al messagio!",
                                           reply_markup=Main.InlineKeyboardMarkup([
                                               [Main.InlineKeyboardButton(
                                                   "❗️Elimina puntata❗️", callback_data=f"delete_user_bet;{command[0]};{command[2]}")],
                                               [Main.InlineKeyboardButton(
                                                   f"👀Sposta puntata👀", callback_data=f"change_bet;{command[0]};{command[2]}")],
                                               [Main.InlineKeyboardButton(
                                                   f"✅Conferma puntata✅", callback_data=f"def_bet;{command[0]};{command[2]}")]
                                           ])
                                           )
    await Cookie.scale_cookie_complete(message.from_user.id, command[1])
    match command[2]:
        case "yes":
            all_users = await Db.bet_query({"_id": int(command[0])}, {"yes_users": 1}, "yes_users")
            if all_users is None:
                all_users = []
            all_users.append({"_id": message.from_user.id,
                             "bet_message": bet_bill.message_id, "qta": command[1]})
            Db.bet.update_one({"_id": int(command[0])}, {
                              "$set": {"yes_users": all_users}})
        case "no":
            all_users = await Db.bet_query({"_id": int(command[0])}, {"no_users": 1}, "no_users")
            if all_users is None:
                all_users = []
            all_users.append({"_id": message.from_user.id,
                             "bet_message": bet_bill.message_id, "qta": command[1]})
            Db.bet.update_one({"_id": int(command[0])}, {
                              "$set": {"no_users": all_users}})


async def iterate_all_bet_user_except_selected(group_id, user_id, bet_selected):
    users = await Db.bet_query({"_id": group_id}, {bet_selected: 1}, bet_selected)
    def_users = []
    user_info = None
    for element in users:
        if element["_id"] != user_id:
            def_users.append(element)
        user_info = element
    # save all the users in the bet selected without our user target
    Db.bet.update_one({"_id": group_id}, {"$set": {bet_selected: def_users}})
    return user_info


async def find_user(group_id, bet_selected, user_id):
    users = await Db.bet_query({"_id": group_id}, {bet_selected: 1}, bet_selected)
    for element in users:
        if element["_id"] == user_id:
            return element


async def iterate_all_bet_users_and_append_new(group_id, new_user_set, bet_selected):
    users = await Db.bet_query({"_id": group_id}, {bet_selected: 1}, bet_selected)
    def_users = []
    for element in users:
        def_users.append(element)
    def_users.append(new_user_set)
    Db.bet.update_one({"_id": group_id}, {"$set": {bet_selected: def_users}})


async def delete_user_from_bet(group_id, user_id, bet_selected):
    info = await iterate_all_bet_user_except_selected(group_id, user_id, bet_selected)
    try:
        await Cookie.add_cookie_complete(user_id, info["qta"])
        return True
    except TypeError:
        return False


async def change_user_bet(group_id, user_id, bet_selected):
    user = await iterate_all_bet_user_except_selected(group_id, user_id, bet_selected)
    if user == None:
        return user
    match bet_selected:
        case "yes_users":
            await iterate_all_bet_users_and_append_new(group_id, user, "no_users")
        case "no_users":
            await iterate_all_bet_users_and_append_new(group_id, user, "yes_users")
    return user


async def remove_single_group(group_id, flag):
    if flag:  # bet still open
        await bet_recap(group_id)
        id = await Db.bet_query({"_id": group_id}, {"bet_message": 1}, "bet_message")
        await close_bet(group_id, id)
    query = await Db.bet_query({"_id": group_id}, {"result": 1}, "result")
    users = []
    flag = False
    match query:
        case 1:  # result is yes
            users = await Db.bet_query_sorted({"_id": group_id}, {"yes_users": 1}, "yes_users", "qta", -1)
            flag = True
        case _:  # result is no
            users = await Db.bet_query_sorted({"_id": group_id}, {"no_users": 1}, "no_users", "qta", -1)
    text = f"Scommessa terminata!\nIl risultato di questo gruppo è **{'SI, il biscotto è arrivato' if flag else 'NO, nessun biscotto.'}**.\nI vincitori, con la corrispettiva vincita, sono i seguenti:\n"
    if users == None or users == []:
        text += "**NESSUN VINCITORE**"
    else:
        for element in users:
            username = await Db.user_query({"_id": element["_id"]}, {"username": 1}, "username")
            await Cookie.add_cookie_complete(element["_id"], int(element['qta'])*2)
            text += f"- {username} -> 🍪 x{int(element['qta'])*2}\n"
    await Main.app.send_message(group_id, text)
    await Cookie.find_winner_in_bet(group_id, f"{'yes_users' if query==1 else 'no_users'}")


async def remove_all_group():
    query = Db.bet.find({})
    users = []
    flag = False
    for element in query:
        match element["result"]:
            case 1:  # result is yes
                users = await Db.bet_query_sorted({"_id": element["_id"]}, {"yes_users": 1}, "yes_users", "qta", -1)
                flag = True
            case _:  # result is no
                users = await Db.bet_query_sorted({"_id": element["_id"]}, {"no_users": 1}, "no_users", "qta", -1)
        text = f"Scommessa terminata!\nIl risultato di questo gruppo è **{'SI, il biscotto è arrivato' if flag else 'NO, nessun biscotto.'}**.\nI vincitori, con la corrispettiva vincita, sono i seguenti:\n"
        for element_u in users:
            username = await Db.user_query({"_id": element_u["_id"]}, {"username": 1}, "username")
            await Cookie.add_cookie_complete(element_u["_id"], int(element_u["qta"])*2)
            text += f"- {username} -> 🍪 x{int(element_u['qta'])*2}\n"
        await Main.app.send_message(element["_id"], text)
        await Cookie.find_winner_in_bet(element["_id"], element["result"])


async def remove(group_id, flag):
    Main.remove_scheduler("time", 1)
    match group_id:
        case None:  # remove all group
            await remove_all_group()
        case _:
            await remove_single_group(group_id, flag)
    Db.bet.delete_one({"_id": group_id})
