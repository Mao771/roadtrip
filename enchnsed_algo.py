##
# !WARN! It is not finished yet, has errors
##
import codecs
from itertools import product
from random import sample
from typing import List
from dataclasses import dataclass, field

from providers.formulas_provider import calculate_distance


@dataclass
class Node:
    id: str
    longitude: float = field(default=-1)
    latitude: float = field(default=-1)
    __nodes: List["Node"] = field(default_factory=list)

    def __repr__(self):
        return f"Node({self.id},{self.longitude},{self.latitude})"

    def __str__(self):
        return f"{self.longitude},{self.latitude}"

    def __eq__(self, other):
        try:
            return self.id == other.id
        except AttributeError:
            return self.id == str(other)

    def get_siblings(self):
        return self.__nodes

    def add_node(self, node: "Node"):
        if node not in self.__nodes:
            self.__nodes.append(node)

    def modify_node(self, node: "Node"):
        try:
            node_index = self.__nodes.index(node)
            self.__nodes[node_index] = node
        except Exception:
            pass

    def node_exists(self, node: "Node"):
        return node in self.__nodes

    def find_matching_siblings(self, min_distance):
        print("finding..")

        matching_siblings = [node for node in self.__nodes
                             if calculate_distance((self.longitude, self.latitude),
                                                   (node.longitude, node.latitude)) > min_distance]

        return matching_siblings


def enhanced_algo(osm_response):
    from json import loads

    try:
        osm_response.raw.decode_content = True
    except:
        osm_response = codecs.decode(osm_response, encoding="UTF-8")
    node_coordinates = []
    osm_response = loads(osm_response)
    max_node_iterations = 800
    max_way_iterations = 10
    current_node_iteration = 0
    current_way_iteration = 0
    for element in osm_response.get('elements'):
        if current_node_iteration <= max_node_iterations and element.get('type') == 'node':
            print("node")
            current_node_iteration += 1
            node = Node(str(element.get('id')), float(element.get('lon')), float(element.get('lat')))
            if node not in node_coordinates:
                node_coordinates.append(node)
            for node_coord in node_coordinates:
                node_coord.modify_node(node)
        elif current_way_iteration <= max_way_iterations and element.get('type') == 'way':
            print("way")
            current_way_iteration += 1
            ref_nodes = [ref_node for ref_node in element.get('nodes')]
            try:
                ref_nodes = sample(ref_nodes, 40)
            except ValueError:
                pass
            for ref_i, ref_j in product(ref_nodes, repeat=2):
                if ref_i != ref_j:
                    try:
                        node_i: Node = node_coordinates[node_coordinates.index(ref_i)]
                        node_j = Node(ref_j) if ref_j not in node_coordinates else node_coordinates[
                            node_coordinates.index(ref_j)]
                        node_i.add_node(node_j)
                    except:
                        continue

    return node_coordinates
