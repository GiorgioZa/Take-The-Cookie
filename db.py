# schema for mongodb table
import pymongo
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
cookie_db = myclient["cookie"]

# all mongodb collection:

# --cookies
cookies = cookie_db["cookies"]
# formate
# {"_id": message_id, "group_id": group_id, "is_taken": flag 0/1, "is_expired": flag 0/1, "value": 1 or 10, "time": current date in seconds}

#-- user
users = cookie_db["users"]
# formate:
# {"_id": user_id, "name": name_user, "username": @username,
#  "tot_qta": tot cookie quantity, "session_count": n° session win, "propic": propic flag}

# --group
groups = cookie_db["groups"]
# formate:
# {"_id": group_id, "name": group_name, "n_cookie": cookie quantity,
# "privacy": flag for privacy, "gift": flag for gifts, "propic": flag for propic, "date": adding date}

# --session
session = cookie_db["session"]
# formate:
# {"_id": user_id, "group_id": group_id, "qta": tot cookie quantity in session}


# --bet
bet = cookie_db["bet"]
# formate:
# {"_id": group_id, "bet_message": message with the bet,  "yes_users": [], "no_users": [], "result": 0, "closed":0, "announce":0}
# for users instead:
# {"_id": user_id, "bet_message": message with bet bill, "qta": qta cookies stacked}


async def session_reset():
    session.delete_many({})
    bet.delete_many({})


async def user_query(query_dictionary, dictionary_to_search, searched_value):
    temp = users.find(query_dictionary, dictionary_to_search)
    for element in temp:
        return element[searched_value]


async def cookie_query(query_dictionary, dictionary_to_search, searched_value):
    temp = cookies.find(query_dictionary, dictionary_to_search)
    for element in temp:
        return element[searched_value]


async def session_query(query_dictionary, dictionary_to_search, searched_value):
    temp = session.find(query_dictionary, dictionary_to_search)
    for element in temp:
        return element[searched_value]


async def group_query(query_dictionary, dictionary_to_search, searched_value):
    temp = groups.find(query_dictionary, dictionary_to_search)
    for element in temp:
        return element[searched_value]


async def bet_query(query_dictionary, dictionary_to_search, searched_value):
    temp = bet.find(query_dictionary, dictionary_to_search)
    for element in temp:
        return element[searched_value]


async def bet_query_sorted(query_dictionary, dictionary_to_search, searched_value, param, order):
    match order:
        case -1:
            temp = bet.find(query_dictionary,
                            dictionary_to_search).sort(param, order)
        case _:
            temp = bet.find(query_dictionary, dictionary_to_search).sort(param)
    for element in temp:
        return element[searched_value]