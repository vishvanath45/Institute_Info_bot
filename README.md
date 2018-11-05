# Institute Information Finder Bot 🤖

This Telegram bot lets you get Information about Institutes, currently supporting all 23 IIT's and 31 NIT's which are spread across India.

Link - [College Info Finder](https://t.me/College_Info_bot)

## Features - 
- `/search` - Search for Institutes  
- `/top10iit` -  Get top 10 IITs  
- `/top10nit` - Get top 10 NITs 

You can search Institutes Statewise, it also guess the probable institutes in case, there is some spelling error in search query.

You can get following information about any Institute - 

- Location
- Year of Establishment
- Rank
- Admission Exams
- Departments
- Website
- Wikipedia page link
- Google Maps Location

## Technology Used - 

- Python 
- Telegram Bot API
- [Fuzzywuzzy(For string searching)](https://github.com/seatgeek/fuzzywuzzy)
- MongoDB as Backend

## Installation :  
 - Install all dependencies  
    `pip3 install -r requirements.txt`
 - You need to add environment variable named `TELEGRAM_TOKEN` with value as secret token obtained through [@BotFather](https://core.telegram.org/bots#botfather) 
 - You also need to add environment variable named `DB_URI` with value as URL to Database to connect to DB instance.
 - Run the Telegram Bot by `python3 main.py`  
 
**Note** - All the Information is taken from Publically available source such as Wikipedia or respective Institute's Website.

Feel free to point out any bug or to contribute.
