import os
import pprint
import qcodes as qc
from typing import Tuple, Optional, Dict, Union, List, Any
from pymongo import collection
import xarray as xr 
from qcodes.dataset.database_extract_runs import extract_runs_into_db
from qcodes.dataset.data_set import load_by_id, load_by_guid, DataSet
pp = pprint.PrettyPrinter(indent=4)


class Qdatalib:

    def __init__(self, mongo_collection: collection = None,
                 db_local: Optional[str] = None,
                 db_shared: str = 'shared.db',
                 lib_dir: str = '.') -> None:
        self.db_local = db_local
        self.db_shared = db_shared
        self.lib_dir = lib_dir
        self.mongo_collection: collection = mongo_collection

    def extract_run_into_db_and_catalog_by_id(self, run_id: int,
                                              scientist: str = 'john doe',
                                              tag: str = '',
                                              note: str = '',
                                              dict_exstra={}) -> None:

        self.uploade_to_catalog_by_id(run_id,
                                      scientist,
                                      tag,
                                      note,
                                      dict_exstra)

        extract_runs_into_db(self.db_local,  self.db_shared, run_id)

    def extract_run_into_nc_and_catalog(self, run_id: int,
                                        scientist: str = 'john doe',
                                        tag: str = '',
                                        note: str = '',
                                        dict_exstra={}
                                        ) -> None:

        self.uploade_to_catalog_by_id(run_id,
                                      scientist,
                                      tag,
                                      note,
                                      dict_exstra)

        data = self.load_by_id_local(run_id)
        x_data = data.to_xarray_dataset()
        nc_path = os.path.join(self.lib_dir, data.guid+".nc")
        x_data.to_netcdf(nc_path)

        return None

    def uploade_to_catalog_by_id(self,
                                 id: int,
                                 scientist: str = 'john doe',
                                 tag: str = '',
                                 note: str = '',
                                 dict_exstra={}) -> None:

        data = self.load_by_id_local(id)
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
        self.mongo_collection.update_one(filter, newvalues, upsert=True)

    def get_data_by_catalog(self, search_digt: Dict[str, Union[str, float]]) -> Union[List, DataSet]:

        results = list(self.mongo_collection.find(search_digt))

        tjek_number_of_results = self.number_of_results(results)

        if tjek_number_of_results[0]:
            return tjek_number_of_results[1]
        else:
            return self.load_shared(results[0]['_id'])


    def get_data_from_nc_by_catalog(self, search_digt: Dict[str, Union[str, float]]) -> Union[List, Any]:
        results = list(self.mongo_collection.find(search_digt))
        tjek_number_of_results = self.number_of_results(results)

        if tjek_number_of_results[0]:
            return tjek_number_of_results[1]
        else:
            nc_path = os.path.join(self.lib_dir, results[0]['_id']+".nc")
            return xr.open_dataset(nc_path)

    def number_of_results(self, results: List) -> Tuple[bool,List]:
        number_of_results = len(results)
        if number_of_results > 10:
            print('The query returned {} results'.format(number_of_results))
            return (True, results)
        elif number_of_results > 1:
            print('The query returend {} results'.format(number_of_results))
            pp.pprint(results)
            return (True, results)
        else:
            return (False, results)

    def load_by_id_local(self, id: int) -> DataSet:
        db_location_stored = qc.config.core.db_location
        qc.config["core"]["db_location"] = self.db_local
        data = load_by_id(id)
        qc.config["core"]["db_location"] = db_location_stored
        return data

    def load_shared(self, guid: str) -> DataSet:
        db_location_stored = qc.config.core.db_location
        qc.config["core"]["db_location"] = self.db_shared
        data = load_by_guid(guid)
        qc.config["core"]["db_location"] = db_location_stored
        return data
