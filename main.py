import requests
import json
import datetime
import time
import urllib
import os
from db_conn import db
from fuzzywuzzy import fuzz

TOKEN = os.environ['TELEGRAM_TOKEN']
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

def url_response(url):
	response = requests.get(url)
	data = response.json()
	return data

def send_message(text, chat_id, reply_markup=None):
	text = urllib.parse.quote_plus(text)
	url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown&disable_web_page_preview=True".format(text, chat_id)
	if reply_markup:
		url += "&reply_markup={}&disable_web_page_preview=True".format(reply_markup)
	url_response(url)

def get_updates(offset=None):
	url = URL + "getUpdates"
	if offset:
		url += "?offset={}".format(offset)
	json_data = url_response(url)
	return json_data

def get_last_update_id(updates):
	updates_ids = []
	for update in updates["result"]:
		updates_ids.append(int(update["update_id"]))
	return max(updates_ids)

def get_states():
	state_name_db_obj = db["states"].find_one({"value":"state_names"})
	list_ = []
	for names in state_name_db_obj["names"]:
		list_.append(names)
	return list_

def get_institutes():
	institute_name_db_obj = db["Institute_info"]
	institute_name_list = []
	for i_name in institute_name_db_obj.find({}):
		institute_name_list.append(i_name["name"])
	return institute_name_list

def handle_updates(updates):

	state_name_list = get_states()
	institute_name_list = get_institutes()

	for update in updates["result"]:
		chat = update["message"]["chat"]["id"]
		try:
			text = update["message"]["text"]
			if text == "/start":
				send_message("Welcome to Institute Information Finder Bot.🤖\nYou can get information about NITs & IITs.\n\
				*Features* - \n\
				/search - Search for Institutes\n\
				/top10iit - Get Top 10 IITs\n\
				/top10nit - Get Top 10 NITs\n\
				/help - Get help any time\n", chat)

			elif text == "/search":
				items = ["Institute Name", "Within State"]
				keyboard = build_keyboard(items)
				send_message("Welcome to Institute Information Finder Bot.🤖\nYou can get information about NITs & IITs.\n*Begin by searching - *", chat, keyboard)

			elif text == "/help":
				send_message("Possible options -\n/search - Search for Institutes\n/top10iit - Get Top 10 IITs\n/top10nit - Get Top 10 NITs\n I'm a bot 🤖, did I just break? \nPlease Report to [@moto_man](https://t.me/moto_man)", chat)

			elif text == "Within State":
				keyboard = build_keyboard(state_name_list)
				send_message("Select State to list all NITs & IITs within ", chat, keyboard)

			elif text == "Institute Name":
				message = "Enter name of NIT/IIT you want to know about."
				send_message(message, chat)

			elif text in state_name_list:
				institutes = db["Institute_info"].find({"state":text})
				list_ = []
				for institute in institutes:
					list_.append(institute["name"])
				keyboard = build_keyboard(list_)
				send_message("Following are IITs and NITs present :\nSelect one to know more about it - ", chat, keyboard)

			elif text in institute_name_list:
				i_obj = db["Institute_info"].find_one({"name":text})
				ranking = i_obj["rankings"]
				print(text)
				msg_rank = ""
				for key, value in ranking.items():
					msg_rank += str(key)+" : "+str(value)+"\n"

				msg_dept = ""
				for value in i_obj["departments"]:
					msg_dept += value+"\n"

				message = "*{}*\n*Location* : {}\n*Established* : {}\n*Rankings* : {}*Departments* : \n{}[Website]({}), [Wiki]({})\n\
				".format(text, i_obj["location"], i_obj["established"], msg_rank,msg_dept, i_obj["website"], i_obj["wiki_link"])
				print(message)
				send_message(message, chat)
				send_message("You can always /search again\nCheck /top10nit, /top10iit or get /help.\n*Note* - Raw queries directly searches by Institute name!", chat)

			elif text == "/top10nit":
				obj = db["ranking_nit"].find({}).sort("rank").limit(10)
				message = "*Top Ranks according to National Institutional Ranking Framework(NIRF)-2018*\n"
				for value in obj:
					rank = int(value["rank"])
					message += str(rank)
					message += ". "
					message += value["name"]
					message += "\n"
				send_message(message, chat)
				send_message("You can always /search, check /top10nit, /top10iit or get /help.\n*Note* - Raw queries directly searches by Institute name!", chat)

			elif text == "/top10iit":
				obj = db["ranking_iit"].find({}).sort("rank").limit(10)
				message = "*Top Ranks according to National Institutional Ranking Framework(NIRF)-2018*\n"
				for value in obj:
					rank = int(value["rank"])
					message += str(rank)
					message += ". "
					message += value["name"]
					message += "\n"
				send_message(message, chat)
				send_message("You can always /search, check /top10nit, /top10iit or get /help.\n*Note* - Raw queries directly searches by Institute name!", chat)

			elif text.startswith("/"):
				send_message("Sorry! I don't understand this msg.\nPlease try these commands /start /help", chat)
			else:
				best_guess = get_best_match(text)
				keyboard = build_keyboard(best_guess)
				send_message("These are the best match for given query.\nSelect to find more about them.\nYou can always /start", chat, keyboard)
		except Exception as ex:
			print(ex)
			send_message("Sorry! I don't understand this msg.\nPlease try these commands /start /help", chat)


def build_keyboard(items):
	keyboard = [[item] for item in items]
	reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
	return json.dumps(reply_markup)

def getKey(item):
	return item[0]

def get_best_match(str_query):
	list_ = []
	str_query = str_query.lower()
	for i_name in db["Institute_info"].find({}):
		score = 0
		score += fuzz.partial_ratio(str_query, i_name["name"].lower())
		score += fuzz.token_sort_ratio(str_query, i_name["location"].lower())
		score += 3*(fuzz.token_set_ratio(str_query, i_name["tags"].lower()))
		list_.append([score, i_name["name"]])
	list_ = sorted(list_, key=getKey)
	# Sort in Decresing order of score
	list_ = list_[::-1]
	# Getting Top 5 best matches
	list_ = list_[:5]
	best_guess_names = []
	for name in list_:
		best_guess_names.append(name[1])
	# print(best_guess_names)
	return best_guess_names

def main():
	last_update_id = None
	while True:
		print("Listening - \n")
		print(datetime.datetime.now())
		updates = get_updates(last_update_id)
		if len(updates["result"])>0:
			last_update_id = get_last_update_id(updates) + 1
			handle_updates(updates)
			time.sleep(0.5)

if __name__ == '__main__':
	main()
