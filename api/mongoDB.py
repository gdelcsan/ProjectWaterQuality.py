from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
import time

# Create a new client and connect to the server
def upload(data):
    username = os.getenv('MONGO_USR')
    password = os.getenv('MONGO_PSS')
    domain = os.getenv('MONGO_DOMAIN')
    uri = "mongodb+srv://" + username + ":" + password + domain + "/?retryWrites=true&w=majority&appName=bbp"
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client['water_quality_data']
    collection = db['asv_1']

    # waits 2 seconds in case more than one user uploads data at the same time
    time.sleep(2)
    # existing entries are cleared before insertion
    if (collection.count_documents({}) > 0):
        collection.delete_many({})
    collection.insert_many(data)