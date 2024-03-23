
from pymongo import MongoClient

mongo_uri = 'mongodb+srv://vicolee1363:KHw5zZkg8JirjK0E@cluster0.c0yyh6f.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'

# Create a new client and connect to the server
client = MongoClient(mongo_uri)

db = client.Cluster0

collection = db['sensor.permitted_ips']
documents=collection.find()
for doc in documents:
    print(doc)

client.close()