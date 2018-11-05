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
	"""
	Returns a Python List containing names of all Indian States,
	fetched from DB.
	"""
	state_name_db_obj = db["states"].find_one({"value":"state_names"})
	list_ = []
	for names in state_name_db_obj["names"]:
		list_.append(names)
	return list_

def get_institutes():
	"""
	Returns a Python List containing names of all Institutes,
	fetched from DB.
	"""
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
				/top10iit -  Get Top 10 IITs\n\
				/top10nit - Get Top 10 NITs\n\
				/help - Get help any time\n", chat)

			elif text == "/search":
				"""
				User can search either via Inputting names directly
				or Statewise Institutes
				"""
				items = ["Institute Name search", "Statewise search"]
				keyboard = build_keyboard(items)
				send_message("Welcome to College Knowledge Bot.🤖\nYou can get information about NITs & IITs.\n*Begin by searching - *", chat, keyboard)

			elif text == "/help":
				send_message("Available options -\n/search - Search for Institutes\n/top10iit  - Get Top 10 IITs\n/top10nit - Get Top 10 NITs\nI'm a bot 🤖, did I just break? \nPlease Report to [@moto_man](https://t.me/moto_man)", chat)

			elif text == "Statewise search":
				"""
				Generates a customized Keyboard, gives option to User to choose
				State.
				"""
				keyboard = build_keyboard(state_name_list)
				send_message("Select State to list all NITs & IITs within ", chat, keyboard)

			elif text == "Institute Name search":
				"""
				Let's User Input name of Institute he/she wishes to search.
				"""
				message = "Enter name of NIT/IIT you want to know about."
				send_message(message, chat)

			elif text in institute_name_list:
				"""
				If Input given by User is found in List of Institutes,
				this part of code sends complete details of Institute to user as reply.
				"""
				i_obj = db["Institute_info"].find_one({"name":text})
				ranking = i_obj["rankings"]
				msg_rank = ""
				for key, value in ranking.items():
					msg_rank += str(key)+" : "+str(value)+"\n"

				msg_dept = ""
				for value in i_obj["departments"]:
					msg_dept += value+"\n"

				message = "*{}*\n*Location* : {}\n*Established* : {}\n*Rankings* : {}*Admission Exams* : {}\n*Departments* : \n{}[Website]({}), [Wikipedia]({})\n\
				".format(text, i_obj["location"], i_obj["established"], msg_rank, i_obj["admission_process"], msg_dept, i_obj["website"], i_obj["wiki_link"])
				send_message(message, chat)
				send_message("You can always /search again.\nCheck /top10nit, /top10iit or get /help.\n*Note* - Raw queries directly searches by Institute name!", chat)

			elif text in state_name_list:
				"""
				If Input given by User is found in List of States,
				this part of code sends User the name of Institutes in that state and
				creates customized keyboard for user to choose between them.
				"""
				institutes = db["Institute_info"].find({"state":text})
				list_ = []
				for institute in institutes:
					list_.append(institute["name"])
				keyboard = build_keyboard(list_)
				message = "Following are IITs and NITs present in {} :\nSelect one to know more about it - ".format(text)
				send_message(message, chat, keyboard)

			elif text.lower() == "/top10nit":
				"""
				Sends List of Top 10 NITs according to NIRF ranking,
				Directly fetches data from DB, and sorts it according to rank.
				"""
				obj = db["ranking_nit"].find({}).sort("rank").limit(10)
				message = "*Top 10 Ranks according to National Institutional Ranking Framework (NIRF), 2018*\n"
				for value in obj:
					rank = int(value["rank"])
					message += str(rank)
					message += ". "
					message += value["name"]
					message += "\n"
				send_message(message, chat)
				send_message("You can always /search.\nCheck /top10nit, /top10iit or get /help.\n*Note* - Raw queries directly searches by Institute name!", chat)

			elif text.lower() == "/top10iit":
				"""
				Sends List of Top 10 NITs according to NIRF ranking,
				Directly fetches data from DB, and sorts it according to rank.
				"""
				obj = db["ranking_iit"].find({}).sort("rank").limit(10)
				message = "*Top 10 Ranks according to National Institutional Ranking Framework (NIRF), 2018*\n"
				for value in obj:
					rank = int(value["rank"])
					message += str(rank)
					message += ". "
					message += value["name"]
					message += "\n"
				send_message(message, chat)
				send_message("You can always /search.\nCheck /top10nit, /top10iit or get /help.\n*Note* - Raw queries directly searches by Institute name!", chat)

			elif text.startswith("/"):
				send_message("Sorry! I don't understand this msg.\nPlease try these commands /start /help", chat)
			else:
				"""
				If nothing matches above option then, we assume that user wants to search by name
				and according make our best guess.
				More details are given in get_best_match()
				It returns Top 5 most probable Institute and creates a customized Keyboard to allow user to choose
				between them
				"""
				best_guess = get_best_match(text)
				keyboard = build_keyboard(best_guess)
				send_message("These are the best match for given query.\nSelect to find more about them.\nYou can always /start", chat, keyboard)
		except Exception as ex:
			print(ex)
			send_message("Sorry! I don't understand this msg.\nPlease /search again or get /help", chat)


def build_keyboard(items):
	"""
	Build Customized Telegram Keyboard
	"""
	keyboard = [[item] for item in items]
	reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
	return json.dumps(reply_markup)

def getKey(item):
	return item[0]

def get_best_match(str_query):
	"""
	Argument : A string
	Returns : List of 5 most Institute name matching with given string

	Method : I use Fuzzy String Matching Package provied in python.

	The search is made between the given string and 3 parameter and then
	net score(string_matching) is calculated.

	Parameter 1 : Name of Institute
	Parameter 2 : Location
	Parameter 3 : Tags(NITDGP, IITK)

	Here tags are given more weightage over other two.

	Example - National Institute of Technology, Durgapur
				is popularly known as NIT-DGP, NITD.
			  Indian Institute of Technology, Kanpur
				is popularly known as IITK.

	and finally we are choosing 5 Institute names with highest matching
	score.
	"""
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
	return best_guess_names

def main():
	last_update_id = None
	while True:
		print("Listening -")
		print(datetime.datetime.now())
		updates = get_updates(last_update_id)
		if len(updates["result"])>0:
			last_update_id = get_last_update_id(updates) + 1
			handle_updates(updates)
			time.sleep(0.5)

if __name__ == '__main__':
	main()
