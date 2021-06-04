import pymongo
import os
from pymongo import collection
import qcodes as qc
import xarray as xr
from qcodes.dataset.plotting import plot_dataset
from qcodes.dataset.database_extract_runs import extract_runs_into_db
from qcodes.dataset.data_set import load_by_id, load_by_guid


def extract_run_into_db_and_catalog_by_id(run_id: int,
                                          db_source: str = None,
                                          db_target: str = None,
                                          collection: collection = None,
                                          scientist: str = 'john doe',
                                          tag: str = '',
                                          note: str = ''
                                          ) -> None:

    uploade_to_catalog_by_id(run_id,
                             collection,
                             scientist,
                             tag,
                             note)
    extract_runs_into_db(db_source,  db_target, run_id)

    return None


def extract_run_into_nc_and_catalog(run_id: int,
                                    db_source: str = None,
                                    target_dir: str = '',
                                    collection=None,
                                    scientist: str = 'john doe',
                                    tag: str = '',
                                    note: str = ''
                                    ) -> None:

    uploade_to_catalog_by_id(run_id,
                             collection,
                             scientist,
                             tag,
                             note)

    data = load_by_id(run_id)
    x_data = data.to_xarray_dataset()
    nc_path = os.path.join(target_dir, data.guid+".nc")
    x_data.to_netcdf(nc_path)

    return None


def uploade_to_catalog_by_id(id: int,
                             collection,
                             scientist: str = 'john doe',
                             tag: str = '',
                             note: str = '',
                             dict_exstra={}) -> None:
    data = load_by_id(id)
    file = data.path_to_db.split('\\')[-1]
    run_id = data.captured_run_id
    exp_id = data.exp_id
    exp_name = data.exp_name
    run_time = data.run_timestamp()
    sample_name = data.sample_name
    parameters = [(par.name, par.unit) for par in data.get_parameters()]
    post = {"_id": data.guid, 'file': file,
            'run_id': run_id,
            'exp_id': exp_id,
            'exp_name': exp_name,
            'run_time': run_time,
            'sample_name': sample_name,
            'parameters': parameters,
            'scientist': scientist,
            'tag': tag,
            'note': note}
    post.update(dict_exstra)
    filter = {"_id": data.guid}
    newvalues = {"$set": post}
    collection.update_one(filter, newvalues, upsert=True)


def get_data_by_catalog(digt, collection):
    results = collection.find(digt)
    ids = [result['_id'] for result in results]
    if len(ids) > 1:
        for result in results:
            print(result)
        return None

    return load_by_guid(ids[0])


def get_data_from_nc_by_catalog(digt, collection, target_dir):
    results = collection.find(digt)
    ids = [result['_id'] for result in results]
    if len(ids) > 1:
        print(ids)
        return None
    nc_path = os.path.join(target_dir, ids[0]+".nc")
    return xr.open_dataset(nc_path)
