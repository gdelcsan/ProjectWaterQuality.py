from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
import time

load_dotenv()
username = os.getenv('MONGO_USR')
password = os.getenv('MONGO_PSS')
domain = os.getenv('MONGO_DOMAIN')
uri = "mongodb+srv://" + username + ":" + password + domain + "/?retryWrites=true&w=majority&appName=bbp"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client['water_quality_data']
collection = db['asv_1']

# Create a new client and connect to the server
def upload(data):
    # waits 2 seconds in case more than one user uploads data at the same time
    time.sleep(2)
    # existing entries are cleared before insertion
    if (collection.count_documents({}) > 0):
        collection.delete_many({})
    collection.insert_many(data)

def helper(field, value):
    selector = ""
    field_name = ""
    if "min" in field: selector = "$gt"
    elif "max" in field: selector = "$lt"
    substring = field[4:]
    
    match substring:
        case "temp":
            field_name = "Temperature (C)"
        case "sal":
            field_name = "Salinity (ppt)"
        case "odo":
            field_name = "ODO (mg/L)"
            
    return {field_name: {selector: value}}

def query(params):
    cursor = None
    filter_query = None
    count = 0
    s = params.pop("skip")
    l = params.pop("limit")

    sample = collection.find_one({})
    if not sample:
        return "No documents found in the collection."
    
    if len(params) == 1:
        (key, val) = params.popitem()
        filter_query = helper(key, float(val))
    elif len(params) > 1:
        temp = []
        filter_query = {"$and": temp}
        for key, val in params.items():
            temp.append(helper(key, float(val)))

    count = collection.count_documents(filter = filter_query, skip = s, limit = l)
    cursor = collection.find(filter = filter_query, skip = s, limit = l)

    return ({"count": count, "items": cursor.to_list()})
    
