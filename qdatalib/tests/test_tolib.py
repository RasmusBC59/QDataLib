import pymongo
import pytest
import os
import xarray as xr
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


@pytest.fixture
def tmp_collection():
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["testbase"]
    col = db["testcol"]
    yield col
    client.drop_database("testbase")
    client.close()


@pytest.fixture
def source_db_path(tmp_path):
    source_db_path = os.path.join(tmp_path, 'source.db')
    return source_db_path


@pytest.fixture
def source_db(source_db_path):
    initialise_or_create_database_at(source_db_path)


@pytest.fixture
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
def target_db_path(tmp_path):
    return os.path.join(tmp_path, 'target.db')


@pytest.fixture
def tmp_qdatalib(tmp_collection, source_db_path, target_db_path, tmp_path):

    qdatalib = Qdatalib(tmp_collection, source_db_path, target_db_path,
                        tmp_path)
    return qdatalib


def test_uploade_to_catalog_by_id_defaults(tmp_qdatalib, data0):

    run_id = data0.run_id

    tmp_qdatalib.uploade_to_catalog_by_id(id=run_id)

    x = tmp_qdatalib.collection.find_one()

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

    x = tmp_qdatalib.collection.find_one()

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

    x = tmp_qdatalib.collection.find_one({'_id': guid})
    for key in test_dict.keys():
        assert x[key] == test_dict[key]


def test_extract_run_into_db_and_catalog_by_id(tmp_qdatalib, data0):
    run_id = data0.run_id
    tmp_qdatalib.extract_run_into_db_and_catalog_by_id(run_id=run_id,)

    source_conn = connect(tmp_qdatalib.db_source)
    data_source = load_by_id(run_id, source_conn)
    target_conn = connect(tmp_qdatalib.db_target)
    guid = data_source.guid
    data_target = load_by_guid(guid, target_conn)

    assert data_source.the_same_dataset_as(data_target)

    source_conn.close()
    target_conn.close()


def test_extract_run_into_nc_and_catalog(tmp_qdatalib, data0):
    run_id = data0.run_id
    guid = data0.guid
    tmp_qdatalib.extract_run_into_nc_and_catalog(run_id)
    nc_path = os.path.join(tmp_qdatalib.target_dir, guid+".nc")
    ncdata = xr.open_dataset(nc_path)
    assert ncdata == data0.to_xarray_dataset()


def test_get_data_by_catalog(tmp_qdatalib, data0):
    run_id = data0.run_id
    tmp_qdatalib.extract_run_into_db_and_catalog_by_id(run_id=run_id)

    source_conn = connect(tmp_qdatalib.db_source)
    data_source = load_by_id(run_id, source_conn)
    target_conn = connect(tmp_qdatalib.db_target)
    guid = data_source.guid
    serch_dict = {'_id': guid}
    data_target = tmp_qdatalib.get_data_by_catalog(serch_dict)

    assert data_source.the_same_dataset_as(data_target)

    source_conn.close()
    target_conn.close()


def test_get_data_form_nc_by_catalog(tmp_qdatalib, data0):
    run_id = data0.run_id
    tmp_qdatalib.extract_run_into_nc_and_catalog(run_id=run_id)

    source_conn = connect(tmp_qdatalib.db_source)
    data_source = load_by_id(run_id, source_conn)
    guid = data_source.guid
    serch_dict = {'_id': guid}
    get_nc = tmp_qdatalib.get_data_from_nc_by_catalog(serch_dict)

    assert get_nc == data_source.to_xarray_dataset()

    source_conn.close()
