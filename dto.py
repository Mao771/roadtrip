from typing import List
from dataclasses import dataclass, field

from providers.formulas_provider import calculate_distance


@dataclass
class SearchConfig:
    longitude: float
    latitude: float
    distance: int = field(default=-1)
    nodes_count: int = field(default=-1)


@dataclass
class Node:
    id: str
    longitude: float = field(default=-1)
    latitude: float = field(default=-1)

    def __str__(self):
        return f"'{self.latitude},{self.longitude}'"


@dataclass
class Way:
    nodes: List[Node] = field(default_factory=list)

    def find_matching_siblings(self, start_node: Node, min_distance: float) -> List[Node]:
        return [node for node in self.nodes
                if calculate_distance((start_node.longitude, start_node.latitude),
                                      (node.longitude, node.latitude)) > min_distance]
