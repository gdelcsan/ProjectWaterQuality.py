from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd

# Create a new client and connect to the server
def upload(data):
    password = "Yg675QwLtUN6YsVi"
    uri = "mongodb+srv://myuser:" + password + "@bbp.lh2bp4a.mongodb.net/?retryWrites=true&w=majority&appName=bbp"
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client['WaterQualityData']
    collection = db['clean_data']
    # existing entries are cleared before insertion
    if (collection.count_documents({}) > 0):
        collection.delete_many({})
    else:
        collection.insert_many(data)