import requests
import json
import datetime
import time
import urllib
import os

TOKEN = os.environ['TELEGRAM_TOKEN']
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

def url_response(url):
	response = requests.get(url)
	data = response.json()
	return data

def send_message(text, chat_id, reply_markup=None):
	text = urllib.parse.quote_plus(text)
	url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
	if reply_markup:
		url += "&reply_markup={}".format(reply_markup)
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

def echo_all(updates):
	for update in updates["result"]:
		try:
			text = update["message"]["text"]
			chat = update["message"]["chat"]["id"]
			send_message(text,chat)
		except Exception as e:
			print(e)

def main():
	last_update_id = None
	while True:
		print("Listening - \n")
		print(datetime.datetime.now())
		updates = get_updates(last_update_id)
		# print(updates)
		if len(updates["result"])>0:
			last_update_id = get_last_update_id(updates) + 1
			echo_all(updates)
			time.sleep(0.5)

if __name__ == '__main__':
	main()
