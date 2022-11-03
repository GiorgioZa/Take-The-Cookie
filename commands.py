import Db
import Main
import Group


async def command_announce(message_text):
    groups = Db.groups.find({}, {"_id": 1})
    text = message_text.split("/announce ")
    text.pop(0)
    text = text[0]
    for element in groups:
        await Main.app.send_message(element["_id"], text)


async def create_groups_list():
    groups = Db.groups.find({}, {"_id": 1})
    text = "Lista gruppi in cui il biscotto è attivo:\n"
    for element in groups:
        group_info = await Main.app.get_chat(element["_id"])
        text += f"- {element['_id']}, {group_info.title}, {group_info.members_count}\n"
    return text


async def send_groups_list(chat_id):
    text = await create_groups_list()
    await Main.app.send_message(chat_id, text)


async def private_welcome(chat_id):
    await Main.app.send_message(chat_id, "Ciao, grazie per aver avviato @TakeTheCookie."\
                                        "\nQuesto bot è nato per rendere divertente l'atmosfera all'interno dei gruppi. "\
                                        "Una volta aggiunto il bot al gruppo, lui manderà biscotti ad intervalli randomici. "\
                                        "Il vostro compito è collezionarne il più possibile per poter vincere la sessione!"\
                                        "\nIn bocca al lupo!")
    await Main.app.send_message(chat_id, "Se vuoi giocare con il bot devi aggiungerlo ad un gruppo.")


async def private_quit(chat_id):
    await Main.app.send_message(chat_id, "Mi dispiace, questo comando può essere usato solamente all'interno dei gruppi!"\
                                        "\n\nAggiungimi ad un gruppo!")


async def private_bet(chat_id):
    await Main.app.send_message(chat_id, "Puoi scommettere solo all'interno dei gruppi!"\
                                        "\nAggiungimi ad un gruppo per poter scommettere!")


async def private_group_info(chat_id):
    await Main.app.send_message(chat_id, "Non posso mostrarti le statistiche del gruppo in questa chat!"\
                                        "\nAggiungimi ad un gruppo per poter visualizzare le stue statistiche!")


async def show_leaderboard(chat_id, message_id, flag, callbackquery):
    search_key = ""
    match flag:
        case 0:
            search_key = "qta"
            podium_temp = Db.session.find().sort(search_key, -1).limit(3)
            text = "Podio goloso di sessione:\n"
            reply_markup = Main.InlineKeyboardMarkup([
                [
                    Main.InlineKeyboardButton(
                        "Aggiorna", callback_data="update_stats"), Main.InlineKeyboardButton(
                        "Passa alla visione globale", callback_data="global_stats")
                ],
            ])
        case 1:
            search_key = "tot_qta"
            podium_temp = Db.users.find().sort(search_key, -1).limit(3)
            text = "Podio goloso globale:\n"
            reply_markup = Main.InlineKeyboardMarkup([
                [
                    Main.InlineKeyboardButton(
                        "Aggiorna", callback_data="update_stats")
                ],
            ])
    c = 1
    for x in podium_temp:
        user = await Main.app.get_users(x["_id"])
        text += f"{'🥇' if c == 1 else '🥈' if c==2 else '🥉'} {user.username}: {x[search_key]}🍪\n"
        c += 1
    if c != 1:  # there are user in db
        text += "\nPer vedere la classifica completa, visita il sito (https://bit.ly/3ODSCXO)!"
    else:
        text = "**NESSUN UTENTE HA ANCORA RISCATTATO BISCOTTI. LA CLASSIFICA NON PUO' ESSERE GENERATA!"
    match callbackquery:
        case None:
            await Main.app.send_message(chat_id, text, reply_markup=reply_markup)
        case _:
            try:
                await Main.app.edit_message_text(chat_id, message_id, text, reply_markup=reply_markup)
            except:
                callbackquery.answer("Informazioni gia' aggiornate!", show_alert=True)


async def change_privacy_property(chat_id, chat_title, message_id):
    current_set = await Db.group_query({"_id": chat_id}, {"privacy": 1}, "privacy")
    match current_set:
        case 0:  # hidden
            Db.groups.update_one({"_id": chat_id}, {"$set": {"privacy": 1}})
        case 1:  # showed
            Db.groups.update_one({"_id": chat_id}, {"$set": {"privacy": 0}})
    await Group.group_info(chat_title, chat_id, message_id)


async def change_gifts_property(chat_id, chat_title, message_id):
    current_set = await Db.group_query({"_id": chat_id}, {"gift": 1}, "gift")
    match current_set:
        case 0:  # hidden
            Db.groups.update_one({"_id": chat_id}, {"$set": {"gift": 1}})
        case 1:  # showed
            Db.groups.update_one({"_id": chat_id}, {"$set": {"gift": 0}})
    await Group.group_info(chat_title, chat_id, message_id)
