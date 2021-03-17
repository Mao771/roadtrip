from abc import ABC, abstractmethod
from typing import Union, List


class BaseDbAdapter(ABC):

    @abstractmethod
    def save(self, data: dict) -> str:
        raise NotImplementedError("Database adapter must implement save method")

    @abstractmethod
    def select(self, query: object, multiple: bool = False) -> Union[dict, List[dict]]:
        raise NotImplementedError("Database adapter must implement load method")

    @abstractmethod
    def update(self, old_data: dict, new_data: dict):
        raise NotImplementedError("Database adapter must implement update method")
