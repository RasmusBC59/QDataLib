import pytest
import os
import pymongo
from qdatalib.mongo_conf import ConfigMongo

def test_make_con_file(tmp_path):
    config = ConfigMongo(tmp_path)
    assert os.path.exists(config.config_path) == True


def test_write_to_config(tmp_path):
    conf_path = os.path.join(tmp_path, 'config.ini')
    config = ConfigMongo(confpath=conf_path)
    client = "mongodb://localhost:27017/"
    db = "testbase"
    col = "testcol"
    config.set_connection(client,db,col)
    source_db_path = os.path.join(tmp_path, 'source.db')
    config.set_db_local(source_db_path)
    shared_db_path = os.path.join(tmp_path, 'shared.db')
    config.set_db_shared(os.path.join(tmp_path, 'shared.db'))
    config.set_lib_dir(tmp_path)

    assert config.config.get("MONGODB","client") == client
    assert config.config.get("MONGODB","db") == db
    assert config.config.get("MONGODB","collection") == col

    assert config.config.get("SQLITE","db_local") == str(source_db_path)
    assert config.config.get("SQLITE","db_shared") == str(shared_db_path)
    assert config.config.get("LIBDIR", "lib_dir") == str(tmp_path)

def test_read_from_config(tmp_path):
    conf_path = os.path.join(tmp_path, 'config.ini')
    config = ConfigMongo(confpath=conf_path)
    client = "mongodb://localhost:27017/"
    db = "testbase"
    col = "testcol"
    config.set_connection(client,db,col)
    source_db_path = os.path.join(tmp_path, 'source.db')
    config.set_db_local(source_db_path)
    shared_db_path = os.path.join(tmp_path, 'shared.db')
    config.set_db_shared(shared_db_path)
    config.set_lib_dir(tmp_path)

    assert type(config.get_client()) == pymongo.MongoClient
    assert config.get_client() == pymongo.MongoClient(client)
    assert type(config.get_db()) == pymongo.database.Database
    assert config.get_db() == config.get_client()[db]
    assert type(config.get_collection()) == pymongo.collection.Collection
    assert config.get_collection() == config.get_db()[col]

    assert config.get_db_local() == source_db_path
    assert config.get_db_shared() == shared_db_path
    assert config.get_lib_dir() == str(tmp_path) 
