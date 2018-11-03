import pymongo, os
import csv

# ADD URI STRING HERE #################################

uri_string =  os.environ['DB_URI']

#########################################################

client = pymongo.MongoClient(uri_string)

db = client.db
