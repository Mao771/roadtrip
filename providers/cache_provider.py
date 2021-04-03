from typing import List
from dataclasses import asdict

from adapters.db_base_adapter import BaseDbAdapter
from dto import SearchConfig, Node


class CacheProvider:

    def __init__(self, db_adapter: BaseDbAdapter):
        self.db_adapter = db_adapter

    def save_user_search(self, search_config: SearchConfig):
        self.db_adapter.remove({"user_id": search_config.id})
        self.db_adapter.save({"user_id": search_config.id, "search_config": asdict(search_config),
                              "status": "in_progress", "results": {}})

    def update_user_search(self, search_config: SearchConfig):
        self.db_adapter.update({
            "user_id": search_config.id
        }, {
            "search_config": asdict(search_config)
        })

    def save_user_search_results(self, user_id: str, result_nodes: List[Node], route: str):
        self.db_adapter.update({
            "user_id": user_id
        }, {
            "status": "finished",
            "results": {
                "nodes": [asdict(node) for node in result_nodes],
                "route": route
            }
        })

    def get_user_search(self, user_id: str = None):
        return self.db_adapter.select({
            "user_id": user_id
        })

    def save_api_responses(self, search_config: SearchConfig, api_responses: list):
        if api_responses and len(api_responses) > 0:
            # we can't use unique id because we want to save api responses for general search criteria
            search_config_dict = asdict(search_config)
            search_config_dict.pop("id")
            self.db_adapter.remove({"_id": {"search_config": search_config_dict}})
            self.db_adapter.save({"_id": {"search_config": search_config_dict},
                                  "responses": api_responses})

    def get_api_responses(self, search_config: SearchConfig):
        # we can't use unique id because we want to get api responses for general search criteria
        search_config_dict = asdict(search_config)
        search_config_dict.pop("id")
        return self.db_adapter.select({
            "_id": {"search_config": search_config_dict}
        })
