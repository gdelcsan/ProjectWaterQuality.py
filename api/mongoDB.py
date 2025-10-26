from pymongo import ASCENDING, ReplaceOne
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
import time

load_dotenv()
try:
    USERNAME = os.getenv('MONGO_USR')
    PASSWORD = os.getenv('MONGO_PSS')
    DOMAIN = os.getenv('MONGO_DOMAIN')
    uri = "mongodb+srv://" + USERNAME + ":" + PASSWORD + DOMAIN + "/?retryWrites=true&w=majority&appName=bbp"
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client['water_quality_data']
    collection = db['asv_1']
    mongo_OK = True
except Exception:
    mongo_OK = False
    print(f"Error connecting to Mongo: {Exception}")

# Create a new client and connect to the server
def upload_MONGO(documents):
    # waits 1 seconds in case more than one user uploads data at the same time
    time.sleep(1)

    # essentially tells it to override OLD duplicates with new duplicates
    # if there's no duplicates, then just insert
    # upsert = update if possible, insert if not 
    operations = [
        ReplaceOne(filter = {"Time":doc["Time"]}, replacement = doc, upsert = True)
        for doc in documents
    ]
    
    result = collection.bulk_write(operations)
    return f"Number of documents upserted: {result.upserted_count}, Number of documents modified: {result.modified_count}"


def helper(field, value):
    selector = ""
    field_name = ""
    substring = field[4:]
    if "min" in field: selector = "$gte"
    elif "max" in field: selector = "$lte"
    
    match substring:
        case "time":
            field_name = "Time hh:mm:ss"
        case "temp":
            field_name = "Temperature (c)"
        case "sal":
            field_name = "pH"
        case "odo":
            field_name = "ODO mg/L"
            
    return {field_name: {selector: value}}

def query(params):
    cursor = None
    filter_query = None
    count = 0
    s = params.pop("skip")
    l = params.pop("limit")
    
    if len(params) == 0:
        filter_query = {}
    elif len(params) == 1:
        (key, val) = params.popitem()
        if not "time" in key:
            val = float(val)
        filter_query = helper(key, val)
    elif len(params) > 1:
        temp = []
        filter_query = {"$and": temp}
        for key, val in params.items():
            if not "time" in key:
                val = float(val)
            temp.append(helper(key, val))

    count = collection.count_documents(filter = filter_query, skip = s, limit = l)
    cursor = collection.find(filter = filter_query, skip = s, limit = l)

    return ({"count": count, "items": cursor.to_list()})
    

