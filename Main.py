import asyncio
from time import timezone
import pyrogram
from pyrogram import Client, filters, errors
from pyrogram import types
from pyrogram.types import (InlineQueryResultArticle, InputTextMessageContent,
                            InlineKeyboardMarkup, InlineKeyboardButton)

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import random
import os
import Bet
import Group
import Cookie
import User
import Commands
import Db
from datetime import datetime
file = open("config_file.txt", "r").readlines()
line = file[1].split(", ")
dev_stuff = [x for x in line]
app = Client(
    dev_stuff[0],  # name project
    bot_token=dev_stuff[1],
    sleep_threshold=50
)
asyncioscheduler = AsyncIOScheduler()
asyncioscheduler.start()
scheduler = BackgroundScheduler()
scheduler.start()
LOG_GROUP = int(dev_stuff[2])  # log channel's telegram id
SUPER_USER = int(dev_stuff[3])  # dev's telegram id
is_gold = False  # flag for define if the next cookie is gold
group_id = "0"
flag = None
occupied = False


def remove_scheduler(id, f):
    match f:
        case 0:  # normal scheduler
            try:
                scheduler.remove_job(id)
            except:
                return False
            return True
        case 1:  # asyncio scheduler
            try:
                asyncioscheduler.remove_job(id)
            except:
                return False
            return True


async def scheduler_new_date():
    remove_scheduler('biscotto', 1)
    a = random.randrange(3)  # da 0 a 2 ore
    b = random.randrange(10, 60)  # da 10 a 59 minuti
    c = random.randrange(60)  # da 0 a 59 secondi
    try:
        asyncioscheduler.add_job(Cookie.cookie, 'interval', hours=a, minutes=b,
                                 seconds=c, args=(group_id,), id='cookie')
        await log_message(f"Prossimo biscotto tra: {a}h:{b}m:{c}s")
    except:
        restart()


def restart():
    remove_scheduler("main", 0)
    asyncio.run(select_group())
    start_scheduler()


def start_scheduler():
    match group_id:
        case ("0" | 0 | '0'):
            scheduler.add_job(restart, 'interval',  seconds=10,
                              id='main', replace_existing=True)
        case _:
            asyncioscheduler.add_job(Cookie.cookie, 'interval',  seconds=10,
                                     args=(group_id,), id='cookie', replace_existing=True)
    bets = Db.bet.find({"closed": 0})
    for element in bets:
        try:
            asyncioscheduler.add_job(Bet.remove, 'interval', minutes=10,
                                     args=(element["_id"], False), id=f'remove{element["_id"]}')
        except:
            return
    time_scheduler()


def time_scheduler():
    if (datetime.now().hour > 0 and datetime.now().hour < 23) and ((datetime.now().minute > 0 and datetime.now().minute < 50)):
        try:
            asyncioscheduler.add_job(Bet.remove, 'cron', hour='0', args=(
                None, False), timezone="CET", id='time')
        except:
            pass


async def remove_error(group_id):
    Db.groups.delete_one({"_id": group_id})
    await log_message(f"Ho eliminato il gruppo con questo id: {group_id}")
    try:
        await app.send_message(
            group_id, f"A causa di un errore di sistema, questo gruppo è stato rimosso dal database😵‍💫, puoi riaggiungerlo usando il comando /add ;)")
    except:
        pass


async def download_propic(user):
    user_id = user.from_user.id
    try:
        await test_download_propic(user, user_id)
    except:
        return


async def test_download_propic(user, user_id):
    try:
        await app.download_media(user.from_user.photo.big_file_id,
                                 f"static/img/users/{user_id}.png")
        Db.users.update_one({"_id": user_id}, {
            "$set": {"propic": 1}})
        return True
    except:
        Db.users.update_one({"_id": user_id}, {
            "$set": {"propic": 0}})
        return False


async def download_group_pic(group_id):
    group = await app.get_chat(group_id)
    a = None
    try:
        a = await test_download_group_pic(group, group_id)
    except:
        return a


async def test_download_group_pic(group, group_id):
    try:
        await app.download_media(group.photo.big_file_id,
                                 f"static/img/groups/{group_id}.png")
        Db.groups.update_one({"_id": group_id}, {
            "$set": {"propic": 1}})
        return True
    except:
        Db.groups.update_one({"_id": group_id}, {
            "$set": {"propic": 0}})
        return False


async def log_message(message):
    await app.send_message(LOG_GROUP, message)


def randomic_choice(limit):
    random.seed()
    return random.randrange(limit)


async def find_group(groups):
    global group_id, flag
    choice = randomic_choice(101)
    selected = []
    for group in groups:
        try:
            group_members = await app.get_chat_members_count(group["_id"])
        except (errors.ChannelInvalid, errors.ChannelPrivate, errors.PeerIdInvalid):
            await remove_error(groups[0])
            continue
        if choice < 15:  # 15%
            flag = False  # small group
            if group_members < 30:  # 0-29
                selected.append(group["_id"])
                continue
        elif choice < 15 + 30:  # 30%
            flag = False  # small group
            if group_members >= 30 and group_members < 150:  # 30-149
                selected.append(group["_id"])
                continue
        elif choice < 15 + 30 + 35:  # 35
            flag = True  # big group
            if group_members >= 150 and group_members < 500:  # da 150 a 499
                selected.append(group["_id"])
                continue
        elif choice <= 15 + 30 + 35 + 20:  # (20%)
            flag = True  # big group
            if group_members >= 500:  # 500+
                selected.append(group["_id"])
                continue
    if len(selected) >= 2:
        random.shuffle(selected)
        text = f"Il numero randomico è: {choice}. La scelta ricade tra questi gruppi:\n"
        for element in selected:
            name = await app.get_chat(element)
            text += f"- {name.title}\n"
        await log_message(f"{text}")
        group_id = selected[randomic_choice(len(selected))]
    elif len(selected) == 1:
        group_id = selected[0]
    else:
        group_id = "0"
        await log_message("Nessun gruppo è stato scelto, continuo a cercare!")
        await select_group()
        return


async def select_group():
    global group_id, is_gold
    is_golden = randomic_choice(101)  # 0-100
    match is_golden:
        case (0 | 100): is_gold = True
        case _: is_gold = False
    groups_temp = Db.groups.find({}).sort("n_cookie", -1)
    groups = []
    for element in groups_temp:
        groups.append(element)
    if len(groups) >= 2:
        await find_group(groups)
    if len(groups) == 1:
        group_id = groups[0]["_id"]
    if len(groups) == 0:
        group_id = "0"
        await log_message("Nessun gruppo selezionato per ricevere il biscotto")
        return
    await verify_group()


async def verify_group():
    match flag:
        case True:  # big group
            query = Db.cookies.find({}).limit(6)
        case False:  # small group
            query = Db.cookies.find({}).limit(3)

    for element in query:
        if int(group_id) == int(element['group_id']):
            await log_message("Gruppo scelto uguale al precedente!")
            await select_group()
            return
        else:
            break
    group_name = await app.get_chat(group_id)
    await log_message(
        f"Il prossimo gruppo in cui verrà inviato il biscotto è: {group_name.title}")


async def delete_message(chat_id, message_id):
    try:
        await app.delete_messages(chat_id, message_id)
        return True
    except:
        return False


# reminder for user to use the bot inside group
@app.on_message((filters.private) & filters.command("add") | filters.command("start"))
async def private_add(client, message):
    await Commands.private_welcome(message.chat.id)


# /add group, this add the group inside the database
@app.on_message((filters.group) & filters.command("add"))
async def add(client, message):
    if not await delete_message(message.chat.id, message.message_id):
        await app.send_message(message.chat.id, 
            "Prima di avviare la raccolta dei biscotti devi aggiungermi come amministratore "\
            "impostando come privilegio la rimozione dei messaggi!")
        return
    await Group.add_group(message.chat.id, message.from_user.id)


# /quit group, this remove the group from the database
@app.on_message((filters.group) & filters.command("quit"))
async def quit(client, message):
    await delete_message(message.chat.id, message.message_id)
    await Group.remove_group(message.chat.id, message.from_user.id)


@app.on_message((filters.private) & filters.command("quit"))
async def private_quit(client, message):
    await Commands.private_quit(message.chat.id)


@app.on_callback_query(filters.regex("quit_group"))
async def quit_group(client, callback_query):
    if not await Group.verify_admin(callback_query.from_user.id, callback_query.message.chat.id) or await User.is_user_banned(callback_query.from_user.id):
        await callback_query.answer("Non puoi usare questa funzione! Non sei admin oppure scopri se sei stato bannato usando il comando /im_banned !")
    else:
        await app.leave_chat(callback_query.message.chat.id)
        await log_message(f"Sono uscito dal gruppo {callback_query.message.chat.title}")


@app.on_message(filters.command("list"))
async def show_leaderboard(client, message):
    await delete_message(message.chat.id, message.message_id)
    await Commands.show_leaderboard(message.chat.id, 0, 0, 0)


@app.on_message((filters.group) & filters.command("bet"))
async def start_bet(client, message):
    await delete_message(message.chat.id, message.message_id)
    if not await Group.verify_admin(message.from_user.id, message.chat.id) or await User.is_user_banned(message.from_user.id):
        await app.send_message(message.chat.id, 
            "**ERRORE!** Non puoi avviare le scommesse! Le motivazioni possono essere le seguenti:"\
            "\n1) Sei stato bannato (usa il comando /im_banned per scoprirlo)\n2) Non sei admin di questo gruppo.")
        return
    await Bet.start_bet(message)


@app.on_message((filters.private) & filters.command("bet"))
async def private_bet(client, message):
    await Commands.private_bet(message.chat.id)


@app.on_message(filters.command("my_stats"))
async def my_stats(client, message):
    await delete_message(message.chat.id, message.message_id)
    await User.my_stats(message.from_user.id, message.chat.id, None, None)


@app.on_message((filters.group) & filters.command("group_info"))
async def group_info(client, message):
    await delete_message(message.chat.id, message.message_id)
    await Group.group_info(message.chat.title, message.chat.id, None)


@app.on_message((filters.private) & filters.command("group_info"))
async def private_group_info(client, message):
    Commands.private_group_info(message.chat.id)


@app.on_message((filters.chat(SUPER_USER)) & filters.command("announce"))
async def send_announce(client, message):
    await Commands.command_announce(message.text)


@app.on_message((filters.chat(SUPER_USER)) & filters.command("groups"))
async def send_groups_list(client, message):
    await Commands.send_groups_list(message.chat.id)


@app.on_message((filters.chat(SUPER_USER)) & filters.command("force_cookie"))
async def cookie(client, message):
    await log_message("Ho forzato l'inivio del biscotto!")
    match group_id:
        case ("0" | 0 | '0'):
            await select_group()
        case _:
            await Cookie.cookie(group_id)


@app.on_message((filters.chat(SUPER_USER)) & filters.command("force_close"))
async def forced_close_bet(client, message):
    await log_message("Ho forzato la chiusura delle scommesse anticipate!")
    query = Db.bet.find({})
    for element in query:
        await Bet.close_bet(element["_id"], element["bet_message"])


@app.on_message((filters.chat(SUPER_USER)) & filters.command("force_group"))
async def force_new_group(client, message):
    await log_message("Ho forzato la scelta di un nuovo gruppo!")
    await select_group()


@app.on_message((filters.chat(SUPER_USER)) & filters.command("manual_group"))
async def def_new_group(client, message):
    global group_id
    text = message.text.split("/manual_group ")
    text.pop(0)
    try:
        test = await app.get_chat(text[0])
    except:
        await app.send_message(message.chat.id, "Identificativo del gruppo errato")
        return

    query = await Db.group_query({"_id": int(text[0])}, {"_id": 1}, "_id")
    if query == None:
        await app.send_message(message.chat.id, "Gruppo non trovato all'interno del database")
    else:
        group_id = text[0]


@app.on_message((filters.chat(SUPER_USER)) & filters.command("ban_user"))
async def ban_user(client, message):
    text = message.text.split("/ban_user ")
    text.pop(0)
    try:
        test = await app.get_users(text[0])
    except:
        await app.send_message(message.chat.id, "Utente non trovato!")
        return
    await app.send_message(message.chat.id, User.ban_user(test.id))


@app.on_message((filters.chat(SUPER_USER)) & filters.command("modify_user_qta"))
async def modify_user(client, message):
    text = message.text.split(" ")
    text.pop(0)
    try:
        test = await app.get_users(text[0])
    except:
        await app.send_message(message.chat.id, "Utente non trovato!")
        return
    await User.modify_user_qta(test.id, int(text[1]))


@app.on_callback_query(filters.regex("update_group_stat"))
async def modify_group_info(client, callback_query):
    await Group.group_info(callback_query.message.chat.title, callback_query.message.chat.id, callback_query)


@app.on_callback_query(filters.regex("set_privacy"))
async def set_privacy(client, callback_query):
    if not await Group.verify_admin(callback_query.from_user.id, callback_query.message.chat.id) or await User.is_user_banned(callback_query.from_user.id):
        await callback_query.answer(
            "**ERRORE!** Non puoi modificare queste impostazioni! Le motivazioni possono essere le seguenti:"\
            "\n1) Sei stato bannato (usa il comando /im_banned per scoprirlo)\n2) Non sei admin di questo gruppo.")
    else:
        await Commands.change_privacy_property(
            callback_query.message.chat.id, callback_query.message.chat.title, callback_query.message.message_id)


@app.on_callback_query(filters.regex("set_gift"))
async def det_gift(client, callback_query):
    if not await Group.verify_admin(callback_query.from_user.id, callback_query.message.chat.id) or await User.is_user_banned(callback_query.from_user.id):
        await callback_query.answer("**ERRORE!** Non puoi modificare queste impostazioni! Le motivazioni possono essere le seguenti:"\
            "\n1) Sei stato bannato (usa il comando /im_banned per scoprirlo)\n2) Non sei admin di questo gruppo.")
    else:
        await Commands.change_gifts_property(
            callback_query.message.chat.id, callback_query.message.chat.title, callback_query.message.message_id)


@app.on_message(filters.command("dev"))
async def dev_info(client, message):
    await app.send_message(message.chat.id, f"Versione biscotti: 2.5"\
                                            "\nSviluppato da @GiorgioZa con l'aiuto e supporto dei suoi amiketti che lo sostengono in ogni sua minchiata ❤️."\
                                            "\nUltime info sul bot -> canale ufficiale (https://t.me/TakeTheCookie)")


# /im_banned, this show your status about ban
@app.on_message(filters.command("im_banned"))
async def is_banned(client, message):
    await delete_message(message.chat.id, message.message_id)
    await User.ban_status(message.chat.id, message.from_user.id, None, None)


@app.on_message(filters.command("bet_active"))
async def actually_bet(client, message):
    await delete_message(message.chat.id, message.message_id)
    if message.via_bot is None or message.via_bot.id != 1916037778:
        await app.send_message(message.chat.id,
                               "Puoi usare questo comando solo in inline mode."\
                                "\nAvvia una scommessa o usa i bottoni per scommettere correttamente!")
        return
    await Bet.focus_on(message)


@app.on_message(filters.command("give"))
async def give_cookie(client, message):
    await delete_message(message.chat.id, message.message_id)
    if await User.is_user_banned(message.from_user.id):
        await app.send_message(
            message.chat.id, "Non puoi donare biscotti😵‍💫! Scopri se sei stato bannato usando il comando /im_banned !")
        return
    error = "Sintassi non corretta!"\
            "\nUsa: /give <__username utente a cui inviare__> <__quantità da inviare maggiore di zero__>"\
            "\nEsempio: /give @GiorgioZa 4"
    command = message.text
    command = command.split(" ")
    command.pop(0)
    try:
        qta = int(command[1])
    except IndexError:
        await app.send_message(message.chat.id, error,
                               reply_to_message_id=message.message_id)
        return
    if int(command[1]) <= 0:
        await app.send_message(message.chat.id, error,
                               reply_to_message_id=message.message_id)
        return
    try:
        receiver = await app.get_users(command[0])
    except:
        await app.send_message(message.chat.id, error,
                               reply_to_message_id=message.message_id)
        return
    await User.give_cookie(message.chat.id,
                           message.message_id, message.from_user.id, receiver, qta)
    return


@app.on_callback_query(filters.regex("update_ban"))  # refresh the ban stat
async def update_ban(client, callback_query):
    await User.ban_status(callback_query.message.chat.id, callback_query.from_user.id,
                          callback_query.message.message_id, callback_query)


@app.on_callback_query(filters.regex("update_stats"))
async def update_stats(client, callback_query):
    await Commands.show_leaderboard(callback_query.message.chat.id, callback_query.message.message_id, 0, 1)


@app.on_callback_query(filters.regex("update"))
async def update_stats(client, callback_query):
    await User.my_stats(callback_query.from_user.id, callback_query.message.chat.id, callback_query.message.message_id, callback_query)


@app.on_callback_query(filters.regex("global_stats"))
async def global_stats(client, callback_query):
    await Commands.show_leaderboard(callback_query.message.chat.id, callback_query.message.message_id, 1, 1)


@app.on_callback_query(filters.regex("take_it"))
async def taken_cookie(client, callback_query):
    if await User.is_user_banned(callback_query.from_user.id):
        await callback_query.answer(
            "Non puoi riscattare questo biscotto😵‍💫! Scopri se sei stato bannato usando il comando /im_banned !")
        return
    await Cookie.take(callback_query)


@app.on_callback_query(filters.regex("take_expired"))
async def take_expired_cookie(client, callback_query):
    if await User.is_user_banned(callback_query.from_user.id):
        await callback_query.answer(
            "Non puoi riscattare questo biscotto😵‍💫! Scopri se sei stato bannato usando il comando /im_banned !")
        return
    await Cookie.take(callback_query)


async def donation_bill(inline_query):
    if await User.is_user_banned(inline_query.from_user.id):
        await inline_query.answer(
            results=[
                InlineQueryResultArticle(
                    title="Non puoi scommettere!",
                    input_message_content=InputTextMessageContent(
                        f"A quanto pare, mio caro {inline_query.from_user.mention}, risulti nella ban list!"\
                        "\nScopri se sei stato bannato usando il comando /im_banned !"
                    )
                )
            ],
            cache_time=1
        )
        return
    else:
        split = inline_query.query.split(";")
        split.pop(0)
        if int(split[0]) == inline_query.from_user.id:
            await inline_query.answer(
                results=[
                    InlineQueryResultArticle(
                        title="Ricevuta Donazione",
                        input_message_content=InputTextMessageContent(
                            f"Ciao!\nTi ho appena donato {split[1]} {'biscotto' if int(split[1])==1 else 'biscotti'}😋! "\
                                "Inizia anche tu la raccolta dei biscotti con @TakeTheCookieBot !"
                        ),
                        description="Invia la ricevuta di donazione all'utente.",
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [InlineKeyboardButton(
                                    "Scopri quanti biscotti possiedi!",
                                    url="https://t.me/TakeTheCookieBot?start"
                                )]
                            ]
                        )
                    )
                ],
                cache_time=1
            )


@app.on_inline_query(filters.regex("^donate_notify\;\d+;\d+$"))
async def inline_things(client, inline_query):
    await donation_bill(inline_query)


@app.on_inline_query(filters.regex("^bet\;\w+;\-\d+$"))
async def bet(client, inline_query):
    split = inline_query.query.split(";")
    split.pop(0)
    if await User.is_user_banned(inline_query.from_user.id):
        await inline_query.answer(
            results=[
                InlineQueryResultArticle(
                    title="Non puoi scommettere!",
                    input_message_content=InputTextMessageContent(
                        f"A quanto pare, mio caro {inline_query.from_user.mention}, risulti nella ban list!"\
                        "\nScopri se sei stato bannato usando il comando /im_banned !"
                    )
                )
            ],
            cache_time=1
        )
        return
    elif await Bet.is_closed(int(split[1])):
        await inline_query.answer(
            results=[
                InlineQueryResultArticle(
                    title="Non puoi scommettere!",
                    input_message_content=InputTextMessageContent(
                        f"A quanto pare, mio caro {inline_query.from_user.mention}, la scommessa in questo gruppo è scaduta!"\
                        "\nRicordati che una volta avviata, la scommessa accetta puntate per 1h!"
                    )
                )
            ],
            cache_time=1
        )
        return
    else:
        bet = await Db.bet_query({"_id": int(split[1])}, {"_id": 1}, "_id")
        if bet != None:
            user_qta = await Db.session_query({"_id": inline_query.from_user.id}, {"qta": 1}, "qta")
            if user_qta is None or user_qta <= 0:
                await inline_query.answer(
                    results=[
                        InlineQueryResultArticle(
                            title="Non puoi scommettere!",
                            input_message_content=InputTextMessageContent(
                            f"A quanto pare, mio caro {inline_query.from_user.mention}, non hai abbastanza biscotti!"\
                            "Per poter scommettere è necessario che tu abbia almeno un biscotto!"
                            )
                        )
                    ],
                    cache_time=1
                )
                return
            else:
                if user_qta >= 14:
                    user_qta = 14
                flag = False
                verify_previus_bet = Db.bet.find({"_id": int(split[1])}, {
                                                 "yes_users": 1, "no_users": 1})
                for element in verify_previus_bet:
                    for bets in element["yes_users"]:
                        if bets["_id"] == inline_query.from_user.id:
                            flag = True
                            continue
                    for bets in element["no_users"]:
                        if bets["_id"] == inline_query.from_user.id:
                            flag = True
                            continue
                inline_results = []
                match flag:
                    case True:
                        group_id = str(split[1]).split("-100")
                        inline_results.append(
                            InlineQueryResultArticle(
                                title=f"Non puoi scommettere!",
                                input_message_content=InputTextMessageContent(
                                    f"Hai già scommesso, se vuoi modificare la scommessa o annullarla, "\
                                     "fai riferimento a questo messaggio: https://t.me/c/{int(group_id[1])}/{bets['bet_message']}"
                                )
                            )
                        )
                    case False:
                        match split[0]:
                            case "yes":
                                for x in range(user_qta, 0, -1):
                                    inline_results.append(
                                        InlineQueryResultArticle(
                                            title=f"Scommetti {x} biscotti sul SI!",
                                            input_message_content=InputTextMessageContent(
                                                f"/bet_active {split[1]} {x} yes"
                                            )
                                        )
                                    )
                            case "no":
                                for x in range(user_qta, 0, -1):
                                    inline_results.append(
                                        InlineQueryResultArticle(
                                            title=f"Scommetti {x} biscotti sul NO!",
                                            input_message_content=InputTextMessageContent(
                                                f"/bet_active {split[1]} {x} no"
                                            )
                                        )
                                    )
                await inline_query.answer(
                    results=inline_results,
                    cache_time=1
                )
        else:
            await inline_query.answer(
                results=[
                    InlineQueryResultArticle(
                        title="Non puoi scommettere!",
                        input_message_content=InputTextMessageContent(
                            f"A quanto pare, mio caro {inline_query.from_user.mention}, non esiste alcuna scommessa per questo gruppo!"\
                            "\nAssicurati di non modificare niente durante le puntate o di verificare che il gruppo abbia avviato la scommessa!"
                        )
                    )
                ],
                cache_time=1
            )


@app.on_callback_query(filters.regex("^delete_user_bet\;\-\d+\;\w+$"))
async def delete_bet(client, callback_query):
    split = callback_query.data.split(";")
    split.pop(0)
    if await Bet.is_closed(int(split[0])):
        await callback_query.answer("Le scommesse sono chiuse, non puoi ritirare la tua puntata!")
        return
    match split[1]:
        case "yes":
            if await Bet.delete_user_from_bet(int(split[0]), callback_query.from_user.id, "yes_users"):
                await callback_query.answer("Scommessa rimossa con successo")
                await delete_message(split[0], callback_query.message.message_id)
            else:
                await callback_query.answer("Non ci sono scommesse a tuo nome sul 'SI' in questo gruppo!")

        case "no":
            if await Bet.delete_user_from_bet(int(split[0]), callback_query.from_user.id, "no_users"):
                await callback_query.answer("Scommessa rimossa con successo")
                await delete_message(split[0], callback_query.message.message_id)
            else:
                await callback_query.answer("Non ci sono scommesse a tuo nome sul 'NO' in questo gruppo!")


@app.on_callback_query(filters.regex("^change_bet\;\-\d+\;\w+$"))
async def change_bet_qta(client, callback_query):
    split = callback_query.data.split(";")
    split.pop(0)
    if await Bet.is_closed(int(split[0])):
        await callback_query.answer("Le scommesse sono chiuse, non puoi modificare la tua puntata!")
        return
    match split[1]:
        case "yes":
            split[1] = "no"
            user_db_info = await Bet.change_user_bet(int(split[0]), callback_query.from_user.id, "yes_users")
        case "no":
            split[1] = "yes"
            user_db_info = await Bet.change_user_bet(int(split[0]), callback_query.from_user.id, "no_users")
    if user_db_info == None:
        await callback_query.answer("Non hai fatto tu questa scommessa.")
        return
    await app.edit_message_text(int(split[0]), user_db_info["bet_message"],
                                f"{callback_query.from_user.mention} ha scommesso {user_db_info['qta']} biscotti sul '{'SI' if split[1] == 'yes' else 'NO'}'!"\
            "\nSe vuoi cambiare puntata o eliminarla del tutto, usa le impostazioni allegate al messagio!",
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton(
                                        "❗️Elimina puntata❗️", callback_data=f"delete_user_bet;{split[0]};{split[1]}")],
                                    [InlineKeyboardButton(
                                        f"👀Sposta puntata👀", callback_data=f"change_bet;{split[0]};{split[1]}")],
                                    [InlineKeyboardButton(
                                        f"✅Conferma puntata✅", callback_data=f"def_bet;{split[0]};{split[1]}")]
                                ]))


@app.on_callback_query(filters.regex("^def_bet\;\-\d+\;\w+$"))
async def confirm_bet(client, callback_query):
    split = callback_query.data.split(";")
    split.pop(0)
    if await Bet.is_closed(int(split[0])):
        await callback_query.answer("Le scommesse sono chiuse, questa puntata è stata già considerata!")
        return
    match split[1]:
        case "yes":
            user = await Bet.find_user(callback_query.message.chat.id, "yes_users", callback_query.from_user.id)
        case "no":
            user = await Bet.find_user(callback_query.message.chat.id, "no_users", callback_query.from_user.id)
    if user == None:
        await callback_query.answer("Non hai fatto tu questa scommessa.")
    else:
        await callback_query.answer("Scommessa confermata. Da questo momento non puoi più modificarla!")
        await app.edit_message_text(int(split[0]), user["bet_message"],
                                    f"✅{callback_query.from_user.mention} ha confermato la scommessa di {user['qta']} biscotti sul '{'SI' if split[1] == 'yes' else 'NO'}'!")
