import configparser
from io import DEFAULT_BUFFER_SIZE
import os
import pymongo
from os.path import  join
from pathlib import Path




class ConfigMongo():
    """
    
    """
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_path = join(Path(__file__).parents[0], 'conf/config.ini')
        if not os.path.exists(self.config_path):
            self.write_file()

    def set_connection(self, client, db, collection):
        self.set_client(client)
        self.set_db(db)
        self.set_collection(collection)

    def set_client(self,client):
        self.update_field("client",client)

    
    def set_db(self,db):
         self.update_field("db",db)

    def set_collection(self,collection):
        self.update_field("collection",collection)

    def update_field(self, field, value):
        self.has_mongodb()
        self.config.set("MONGODB", field, value)
        self.write_file()

    def has_mongodb(self):
        if not self.config.has_section("MONGODB"):
            self.config.add_section("MONGODB")
            
    def write_file(self):
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)
    
    def get_client(self):
        self.config.read(self.config_path)
        client_str = self.config.get("MONGODB","client")
        client = pymongo.MongoClient(client_str)
        return client
    
    def get_db(self):
        client = self.get_client()
        db_str = self.config.get("MONGODB","db")
        db = client[db_str]
        return db

    def get_collection(self):
        db = self.get_db()
        collection_str = self.config.get("MONGODB","collection")
        collection = db[collection_str]
        return collection
