from pymongo import MongoClient

from adapters.db_base_adapter import BaseDbAdapter


class MongoDbAdapter(BaseDbAdapter):

    def __init__(self, db_name: str, series_name: str, username: str, password: str,
                 host: str = '127.0.0.1', port: int = 27017):
        try:
            self.db_client = MongoClient(host=host, port=port, username=username, password=password)
            self.db = self.db_client[db_name]
            self.collection = self.db[series_name]
        except Exception as e:
            raise ConnectionError('Could not connect to MongoDB. Reason:', str(e))

    def save(self, data: dict):
        try:
            return str(self.collection.insert_one(data).inserted_id)
        except Exception as e:
            raise ConnectionError('Could not insert to MongoDB. Reason:', str(e))

    def select(self, query: dict, multiple: bool = False):
        try:
            if multiple:
                results = self.collection.find(query)
                return [rs for rs in results]
            else:
                return self.collection.find_one(query)
        except Exception as e:
            raise ConnectionError('Could not select from MongoDB. Reason:', str(e))

    def update(self, old_data: dict, new_data: dict):
        try:
            self.collection.update_one(old_data, {"$set": new_data})
        except Exception as e:
            raise ConnectionError('Could not update in MongoDB. Reason:', str(e))

    def remove(self, old_data: dict):
        try:
            self.collection.remove(old_data)
        except Exception as e:
            raise ConnectionError('Could not remove in MongoDB. Reason:', str(e))
