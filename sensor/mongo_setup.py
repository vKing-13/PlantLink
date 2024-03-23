from pymongo import MongoClient

def connect_to_mongodb(database_name, collection_name=None,mongo_uri = 'mongodb+srv://vicolee1363:KHw5zZkg8JirjK0E@cluster0.c0yyh6f.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'):
    try:
        # Connect to MongoDB server
        client = MongoClient(mongo_uri)
        
        # Select the specified database
        db = client[database_name]
        
        # If collection_name is provided, select the collection
        if collection_name:
            collection = db[collection_name]
        else:
            collection = None
        
        # Return the database and collection
        return db, collection
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None, None