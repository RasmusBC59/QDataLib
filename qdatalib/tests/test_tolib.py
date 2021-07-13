import pymongo
import pytest
import os
import xarray as xr
import pandas as pd
from qcodes import (
    initialise_or_create_database_at,
    load_by_guid,
    load_or_create_experiment)
from qcodes.dataset.data_set import load_by_id
from qcodes.tests.instrument_mocks import (DummyInstrument,
                                           DummyInstrumentWithMeasurement)
from qcodes.utils.dataset.doNd import do1d
from qcodes.dataset.sqlite.database import connect
from qdatalib.tolib import Qdatalib 
from qdatalib.mongo_conf import ConfigMongo


@pytest.fixture
def tmp_config(tmp_path):
    conf_path = os.path.join(tmp_path, 'config.ini')
    config = ConfigMongo(confpath=conf_path)
    client = "mongodb://localhost:27017/"
    db = "testbase"
    col = "testcol"
    config.set_connection(client,db,col)
    source_db_path = os.path.join(tmp_path, 'source.db')
    config.set_db_local(source_db_path)
    config.set_db_shared(os.path.join(tmp_path, 'shared.db'))
    config.set_lib_dir(tmp_path)
    yield conf_path
    client = config.get_client()
    client.drop_database("testbase")
    client.close()


@pytest.fixture
def source_db_path(tmp_path):
    source_db_path = os.path.join(tmp_path, 'source.db')
    return source_db_path


@pytest.fixture(scope="function")
def source_db(source_db_path):
    initialise_or_create_database_at(source_db_path)

@pytest.fixture
def sourcetwo_db(tmp_path):
    source_db_path = os.path.join(tmp_path, 'sourcetwo.db')
    initialise_or_create_database_at(source_db_path)

@pytest.fixture(scope="function")
def set_up_station():
    exp = load_or_create_experiment('for_test', sample_name='no sample')
    yield
    exp.conn.close()


@pytest.fixture
def dac():
    dac = DummyInstrument('dac', gates=['ch1', 'ch2'])
    yield dac
    dac.close()


@pytest.fixture
def dmm(dac):
    dmm = DummyInstrumentWithMeasurement('dmm', setter_instr=dac)
    yield dmm
    dmm.close()


@pytest.fixture
def data0(source_db, set_up_station, dac, dmm):
    data = do1d(dac.ch1, 0, 1, 10, 0.01, dmm.v1, dmm.v2, show_progress=True)
    return data[0]


@pytest.fixture
def shared_db_path(tmp_path):
    return os.path.join(tmp_path, 'shared.db')


@pytest.fixture
def tmp_qdatalib(tmp_config):

    qdatalib = Qdatalib(tmp_config)
    return qdatalib


def test_uploade_to_catalog_by_id_defaults(tmp_qdatalib, data0):

    run_id = data0.run_id

    tmp_qdatalib.uploade_to_catalog_by_id(id=run_id)

    x = tmp_qdatalib.mongo_collection.find_one()

    assert x['_id'] == data0.guid
    assert x['run_id'] == data0.captured_run_id
    assert x['exp_id'] == data0.exp_id
    assert x['exp_name'] == data0.exp_name
    assert x['run_time'] == data0.run_timestamp()
    assert x['sample_name'] == data0.sample_name


def test_uploade_to_catalog_by_id_given_arguments(tmp_qdatalib, data0):

    run_id = data0 .run_id

    scientist = 'john doe'
    tag = 'testtag'
    note = 'test note'

    tmp_qdatalib.uploade_to_catalog_by_id(id=run_id,
                                         scientist=scientist,
                                         tag=tag,
                                         note=note)

    x = tmp_qdatalib.mongo_collection.find_one()

    assert x['_id'] == data0.guid
    assert x['run_id'] == data0.captured_run_id
    assert x['exp_id'] == data0.exp_id
    assert x['exp_name'] == data0.exp_name
    assert x['run_time'] == data0.run_timestamp()
    assert x['sample_name'] == data0.sample_name
    assert x['scientist'] == scientist
    assert x['tag'] == tag
    assert x['note'] == note


def test_uploade_to_catalog_by_id_add_dict(tmp_qdatalib, data0):

    run_id = data0.run_id
    guid = data0.guid

    test_dict = {'my': 'min', 'test': 'prova', 'one': 1, 'float': 1.6}

    tmp_qdatalib.uploade_to_catalog_by_id(id=run_id,
                                         dict_exstra=test_dict)

    x = tmp_qdatalib.mongo_collection.find_one({'_id': guid})
    for key in test_dict.keys():
        assert x[key] == test_dict[key]


def test_extract_run_into_db_and_catalog_by_id(tmp_qdatalib, data0):
    run_id = data0.run_id
    tmp_qdatalib.extract_run_into_db_and_catalog_by_id(run_id=run_id,)

    source_conn = connect(tmp_qdatalib.db_local)
    data_source = load_by_id(run_id, source_conn)
    shared_conn = connect(tmp_qdatalib.db_shared)
    guid = data_source.guid
    data_shared = load_by_guid(guid, shared_conn)

    assert data_source.the_same_dataset_as(data_shared)

    source_conn.close()
    shared_conn.close()


def test_extract_run_into_nc_and_catalog(tmp_qdatalib, data0):
    run_id = data0.run_id
    guid = data0.guid
    tmp_qdatalib.extract_run_into_nc_and_catalog(run_id)
    nc_path = os.path.join(tmp_qdatalib.lib_dir, guid+".nc")
    ncdata = xr.open_dataset(nc_path)
    assert ncdata.equals(data0.to_xarray_dataset())


def test_get_data_by_catalog(tmp_qdatalib, data0):
    run_id = data0.run_id
    tmp_qdatalib.extract_run_into_db_and_catalog_by_id(run_id=run_id)

    source_conn = connect(tmp_qdatalib.db_local)
    data_source = load_by_id(run_id, source_conn)
    shared_conn = connect(tmp_qdatalib.db_shared)
    guid = data_source.guid
    serch_dict = {'_id': guid}
    data_shared = tmp_qdatalib.get_data_by_catalog(serch_dict)

    assert data_shared.guid == data_source.guid 
    assert data_source.the_same_dataset_as(data_shared)

    source_conn.close()
    shared_conn.close()


def test_get_data_form_nc_by_catalog(tmp_qdatalib, data0):
    run_id = data0.run_id
    tmp_qdatalib.extract_run_into_nc_and_catalog(run_id=run_id)

    source_conn = connect(tmp_qdatalib.db_local)
    data_source = load_by_id(run_id, source_conn)
    guid = data_source.guid
    serch_dict = {'_id': guid}
    get_nc = tmp_qdatalib.get_data_from_nc_by_catalog(serch_dict)

    assert get_nc.equals(data_source.to_xarray_dataset())

    source_conn.close()

def test_read_and_write_different_databases(tmp_path, set_up_station, dac, dmm, tmp_qdatalib):
    data_one = do1d(dac.ch1, 0, 1, 10, 0.01, dmm.v1, dmm.v2, show_progress=False)
    data_one_guid = data_one[0].guid
    data_one_l = load_by_guid(data_one_guid)
    
    source_db_path = os.path.join(tmp_path, 'sourcetwo.db')
    initialise_or_create_database_at(source_db_path)
    exp = load_or_create_experiment(experiment_name='qdatalibtwo', sample_name="no sample")
    data_two = do1d(dac.ch1, 0, 0.5, 10, 0.01, dmm.v1, dmm.v2, show_progress=False)
    data_two_guid = data_two[0].guid
    data_two_l = load_by_guid(data_two_guid)

    tmp_qdatalib.db_local = data_one[0].path_to_db
    tmp_qdatalib.db_shared = os.path.join(tmp_path, 'sharedone.db')
    tmp_qdatalib.extract_run_into_db_and_catalog_by_id(run_id=data_one[0].run_id)

    tmp_qdatalib.db_local = data_two[0].path_to_db
    tmp_qdatalib.db_shared = os.path.join(tmp_path, 'sharedtwo.db')
    tmp_qdatalib.extract_run_into_db_and_catalog_by_id(run_id=data_two[0].run_id)

    tmp_qdatalib.db_shared = os.path.join(tmp_path, 'shared_random.db')

    data_shared_one = tmp_qdatalib.get_data_by_catalog({'_id': data_one_guid})
    data_shared_two = tmp_qdatalib.get_data_by_catalog({'_id': data_two_guid})
    # write to two different databses 
    # and read from two diffetent databasen 
   
    assert data_one[0].the_same_dataset_as(data_one_l)
    assert data_two[0].the_same_dataset_as(data_two_l)
    assert not data_one_l.the_same_dataset_as(data_two_l)
    assert data_one[0].the_same_dataset_as(data_shared_one)
    assert not data_shared_one.the_same_dataset_as(data_shared_two)
    assert  data_two[0].the_same_dataset_as(data_shared_two)

def test_find_file_in_subfolder(tmp_qdatalib, data0):
    run_id = data0.run_id

    tmp_lib_dir = tmp_qdatalib.lib_dir
    tmp_lib_sub_dir_path =  os.path.join(tmp_lib_dir, 'sub/')
    os.mkdir(tmp_lib_sub_dir_path)
    
    tmp_qdatalib.lib_dir = tmp_lib_sub_dir_path 
    tmp_qdatalib.extract_run_into_nc_and_catalog(run_id=run_id)
    
    nc_path = os.path.join(tmp_lib_sub_dir_path, data0.guid+".nc")
    
    assert os.path.exists(nc_path)
    x_one = xr.open_dataset(nc_path)

    tmp_qdatalib.lib_dir = tmp_lib_dir

    guid = data0.guid
    serch_dict = {'_id': guid}
    get_nc = tmp_qdatalib.get_data_from_nc_by_catalog(serch_dict)
    
    assert not tmp_lib_dir == tmp_lib_sub_dir_path
    assert get_nc.equals(x_one)
   
def test_extract_run_into_csv_and_catalog(tmp_qdatalib, data0):
    run_id = data0.run_id
    guid = data0.guid
    tmp_qdatalib.extract_run_into_csv_and_catalog(run_id)
    csv_path = os.path.join(tmp_qdatalib.lib_dir, guid+".csv")
    csv_data = pd.read_csv(csv_path, index_col=0)
    df_data =  data0.to_pandas_dataframe()
    df_data.reset_index(inplace=True)
    assert pd.testing.assert_frame_equal(csv_data, df_data) == None


def test_get_data_from_csv_by_catalog(tmp_qdatalib, data0):
    run_id = data0.run_id
    guid = data0.guid
    tmp_qdatalib.extract_run_into_csv_and_catalog(run_id)
    serch_dict = {'_id': guid}
    csv_data = tmp_qdatalib.get_data_from_csv_by_catalog(serch_dict)
    df_data =  data0.to_pandas_dataframe()
    df_data.reset_index(inplace=True)
    assert pd.testing.assert_frame_equal(csv_data, df_data) == None