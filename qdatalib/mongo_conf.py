import configparser
from io import DEFAULT_BUFFER_SIZE
import os
import pymongo
from os.path import  join
from pathlib import Path




class ConfigMongo():
    """
    
    """
    def __init__(self, confpath=None):
        self.config = configparser.ConfigParser()
        if confpath is None:
            self.config_path = join(Path(__file__).parents[0], 'conf/config.ini')
        else:
            self.config_path = confpath

        if not os.path.exists(self.config_path):
            self.write_file()

    def set_connection(self, client, db, collection):
        self.set_client(client)
        self.set_db(db)
        self.set_collection(collection)

    def set_client(self,client):
        self.update_field("MONGODB", "client",client)

    
    def set_db(self,db):
         self.update_field("MONGODB", "db",db)

    def set_collection(self,collection):
        self.update_field("MONGODB", "collection",collection)
    
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

    def set_db_local(self, db_local):
        self.update_field("SQLITE", "db_local", db_local)
    
    def set_db_shared(self, db_shared):
        self.update_field("SQLITE", "db_shared", db_shared)
    
    def set_lib_dir(self, lib_dir):
        self.update_field("LIBDIR", "lib_dir", lib_dir)

    def get_db_local(self):
        self.config.read(self.config_path)
        db_local = self.config.get("SQLITE","db_local")
        return db_local
    
    def get_db_shared(self):
        self.config.read(self.config_path)
        db_shared = self.config.get("SQLITE","db_shared")
        return db_shared
    
    def get_lib_dir(self):
        self.config.read(self.config_path)
        lib_dir = self.config.get("LIBDIR","lib_dir")
        return lib_dir

    def update_field(self, section, field, value):
        self.has_or_add_section(section)
        self.config.set(section, field, str(value))
        self.write_file()

    def has_or_add_section(self,section):
        if not self.config.has_section(section):
            self.config.add_section(section)
            
    def write_file(self):
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)
