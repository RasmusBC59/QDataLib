import os
from pymongo import collection
import xarray as xr
from qcodes.dataset.database_extract_runs import extract_runs_into_db
from qcodes.dataset.data_set import load_by_id, load_by_guid


class Qdatalib:

    def __init__(self, collection: collection = None,
                 db_source: str = None,
                 db_target: str = None,
                 target_dir: str = None):

        self.db_source = db_source
        self.db_target = db_target
        self.target_dir = target_dir
        self.collection = collection

    def extract_run_into_db_and_catalog_by_id(self, run_id: int,
                                              scientist: str = 'john doe',
                                              tag: str = '',
                                              note: str = ''
                                              ) -> None:

        self.uploade_to_catalog_by_id(run_id,
                                      scientist,
                                      tag,
                                      note)

        extract_runs_into_db(self.db_source,  self.db_target, run_id)

    def extract_run_into_nc_and_catalog(self, run_id: int,
                                        scientist: str = 'john doe',
                                        tag: str = '',
                                        note: str = ''
                                        ) -> None:

        self.uploade_to_catalog_by_id(run_id,
                                      scientist,
                                      tag,
                                      note)

        data = load_by_id(run_id)
        x_data = data.to_xarray_dataset()
        nc_path = os.path.join(self.target_dir, data.guid+".nc")
        x_data.to_netcdf(nc_path)

        return None

    def uploade_to_catalog_by_id(self,
                                 id: int,
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
        self.collection.update_one(filter, newvalues, upsert=True)

    def get_data_by_catalog(self, digt):
        results = self.collection.find(digt)
        ids = [result['_id'] for result in results]
        if len(ids) > 1:
            for result in results:
                print(result)
            return None

        return load_by_guid(ids[0])

    def get_data_from_nc_by_catalog(self, digt):
        results = self.collection.find(digt)
        ids = [result['_id'] for result in results]
        if len(ids) > 1:
            print(ids)
            return None
        nc_path = os.path.join(self.target_dir, ids[0]+".nc")
        return xr.open_dataset(nc_path)
