from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union, List, Dict

from dto import Coordinates


class MapsRequestType(Enum):
    SQUARE_COORDINATES = 'sc'
    AROUND_POINT = 'around_point'


@dataclass
class MapsRequestData:
    square_coordinates: Union[List[List[Coordinates]], List[Coordinates]] = None
    points_radius: Dict[Coordinates, float] = None
    only_cities_and_towns: bool = False


class MapsProviderBase(ABC):

    @abstractmethod
    def get_osm_nodes_ways(self, request_data: MapsRequestData, request_type: MapsRequestType):
        raise NotImplementedError('Method get_osm_nodes_ways must be implemented for MapsProviderBase instance')

    @abstractmethod
    async def get_osm_nodes_ways_async(self, request_data: MapsRequestData, request_type: MapsRequestType,
                                       requests_interval_seconds: int = 3):
        raise NotImplementedError('Method get_osm_nodes_ways_async must be implemented for MapsProviderBase instance')
