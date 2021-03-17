from typing import List
from dataclasses import asdict

from adapters import BaseDbAdapter
from data_classes import Way, Node, SearchConfig


class CacheProvider:

    def __init__(self, db_adapter: BaseDbAdapter):
        self.db_adapter = db_adapter

    def save_user_search(self, user_id: str, search_config: SearchConfig,
                         nodes: List[Node] = None, ways: List[Way] = None):
        if nodes is None:
            nodes = []
        if ways is None:
            ways = []

        search_results = {
            "user_id": user_id,
            "lon": search_config.longitude,
            "lat": search_config.latitude,
            "nodes": [asdict(node) for node in nodes],
            "ways": [asdict(way) for way in ways],
            "search_config": asdict(search_config)
        }
        self.db_adapter.save(search_results)

    def update_user_search(self, user_id: str, search_config: SearchConfig,
                           nodes: List[Node] = None, ways: List[Way] = None):
        if nodes is None:
            nodes = []
        if ways is None:
            ways = []

        if len(nodes) == 0 and len(ways) == 0:
            self.db_adapter.update({
                "user_id": user_id
            }, {
                "search_config": asdict(search_config)
            })
        elif len(nodes) != 0:
            self.db_adapter.update({
                "user_id": user_id
            }, {
                "nodes": nodes,
                "search_config": asdict(search_config)
            })
        elif len(ways) != 0:
            self.db_adapter.update({
                "user_id": user_id
            }, {
                "ways": ways,
                "search_config": asdict(search_config)
            })
        else:
            self.db_adapter.update({
                "user_id": user_id
            }, {
                "nodes": nodes,
                "ways": ways,
                "search_config": asdict(search_config)
            })

    def get_search_results(self, user_id: str = None, coordinates: tuple = None):
        if not user_id and not coordinates:
            return None
        elif user_id and coordinates:
            return self.db_adapter.select({
                "user_id": user_id,
                "lon": coordinates[0],
                "lat": coordinates[1]
            })
        elif user_id:
            return self.db_adapter.select({
                "user_id": user_id
            })
        else:
            return self.db_adapter.select({
                "lon": coordinates[0],
                "lat": coordinates[1]
            })
