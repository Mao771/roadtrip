from typing import List, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel


@dataclass
class Coordinates:
    latitude: float
    longitude: float

    def __hash__(self):
        return hash((self.latitude, self.longitude))

    def __eq__(self, other):
        return (self.latitude, self.longitude) == (other.latitude, other.longitude)


class SearchConfigModel(BaseModel):
    id: Optional[str]
    latitude: float
    longitude: float
    distance: float
    nodes_count: int

    def construct_search_config(self) -> "SearchConfig":
        return SearchConfig(id=self.id, latitude=self.latitude, longitude=self.longitude, distance=self.distance,
                            nodes_count=self.nodes_count)


@dataclass
class SearchConfig:
    latitude: float
    longitude: float
    id: str = field(default='')
    distance: float = field(default=0)
    nodes_count: int = field(default=0)


@dataclass
class Node:
    id: str
    latitude: float = field(default=-1)
    longitude: float = field(default=-1)

    def __str__(self):
        return f"'{self.latitude},{self.longitude}'"


@dataclass
class Way:
    nodes: List[Node] = field(default_factory=list)

    def find_matching_siblings(self, start_node: Node, min_distance: float) -> List[Node]:
        from providers import calculate_distance

        return [node for node in self.nodes
                if calculate_distance((start_node.longitude, start_node.latitude),
                                      (node.longitude, node.latitude)) > min_distance]
