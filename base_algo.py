import logging
import asyncio
import codecs

from typing import Tuple, List
from random import sample, choice
from uuid import uuid4
from json import loads
from requests import Response

from providers import calculate_square, MapsProviderBase, OverpassProvider, MapsRequestType, MapsRequestData, \
    calculate_squares_chunks, calculate_around_chunks
from dto import Way, Node, Coordinates

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


class BasicAlgorithm:

    def __init__(self, maps_provider: MapsProviderBase,
                 maps_request_type: MapsRequestType = MapsRequestType.AROUND_POINT):
        self.maps_provider = maps_provider
        self.maps_request_type = maps_request_type

    def request_nodes_ways(self, request_data: MapsRequestData, asynchronously: bool = False):
        if asynchronously:
            nodes, ways = [], []
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
            try:
                # future = asyncio.ensure_future()
                responses = loop.run_until_complete(
                    self.maps_provider.get_osm_nodes_ways_async(request_data, self.maps_request_type))

                for response in responses:
                    try:
                        nodes_request, ways_request = self.process_response(response)
                        nodes.extend(nodes_request)
                        ways.extend(ways_request)
                    except ValueError as e:
                        logger.error(str(e))
            except Exception as e:
                logger.error(str(e))

            return nodes, ways
        else:
            response = self.maps_provider.get_osm_nodes_ways(request_data, self.maps_request_type)
            return self.process_response(response)

    def process_response(self, osm_response: Response) -> Tuple[list, list]:
        try:
            if osm_response.status_code == 400:
                raise ValueError('Api call error: {}'.format(codecs.decode(osm_response.raw.data)))

            osm_response.raw.decode_content = True
            osm_response = codecs.decode(osm_response.raw.data)
        except AttributeError:
            osm_response = codecs.decode(osm_response, encoding="UTF-8")

        nodes_index, ways_list = {}, []
        try:
            osm_response = loads(osm_response)
        except:
            raise ValueError('Api call error: {}'.format(str(osm_response)))
        for element in osm_response.get('elements'):
            if element.get('type') == 'node':
                node_id = str(element.get('id'))
                nodes_index[node_id] = Node(node_id, longitude=float(element.get('lon')),
                                            latitude=float(element.get('lat')))
            elif element.get('type') == 'way':
                way = Way()
                for node in element.get("nodes"):
                    try:
                        way.nodes.append(nodes_index[str(node)])
                    except KeyError:
                        continue
                ways_list.extend([way])

        return list(nodes_index.values()), ways_list

    def search_nodes_ways(self,
                          coordinates: Coordinates,
                          distance: float = 10,
                          maximum_chunk_distance: float = 20,
                          maximum_geo_requests_count: int = 10,
                          maps_request_type: MapsRequestType = None) -> Tuple[list, list]:
        nodes, ways = [], []
        geo_request_count = 0
        if maps_request_type:
            self.maps_request_type = maps_request_type

        if distance <= maximum_chunk_distance:
            while geo_request_count < maximum_geo_requests_count:
                try:
                    if self.maps_request_type == MapsRequestType.AROUND_POINT:
                        request_data = MapsRequestData(points_radius={coordinates: distance})
                    else:
                        request_data = MapsRequestData(square_coordinates=calculate_square(coordinates, distance))
                    nodes, ways = self.request_nodes_ways(request_data)
                    break
                except ValueError as e:
                    logger.error(str(e))
                    coordinates = (coordinates[0] + 0.5, coordinates[1] + 0.5)
        else:
            if self.maps_request_type == MapsRequestType.AROUND_POINT:
                request_data = MapsRequestData(
                    points_radius=calculate_around_chunks(coordinates, distance, maximum_chunk_distance,
                                                          maximum_geo_requests_count))
            else:
                request_data = MapsRequestData(
                    square_coordinates=calculate_squares_chunks(coordinates, distance, maximum_chunk_distance,
                                                                maximum_geo_requests_count))

            nodes, ways = self.request_nodes_ways(request_data, asynchronously=True)

        return nodes, ways

    def generate_route(self, nodes: List[Node], ways: List[Way],
                       coordinates: Coordinates, distance: int = 15, nodes_count: int = 5) -> str:
        initial_node = Node(str(uuid4()), longitude=coordinates.longitude, latitude=coordinates.latitude)
        min_node_distance = distance / (nodes_count if nodes_count != 1 else 2)
        result_nodes = [initial_node]

        max_search_iterations = len(ways)
        search_iteration = 0

        while search_iteration < max_search_iterations:
            search_iteration += 1
            way = choice(ways)
            try:
                random_node = choice(way.nodes)
                matching_siblings = way.find_matching_siblings(random_node, min_node_distance)
                result_nodes.extend(sample(matching_siblings, nodes_count - 1))
            except ValueError:
                continue
            if len(result_nodes) == nodes_count:
                print("nodes found.")
                break
        else:
            try:
                result_nodes.extend(sample(nodes, (nodes_count - 1) if nodes_count != 1 else 1))
            except ValueError:
                pass

        route_url = 'https://www.google.com/maps/dir/'
        for node in result_nodes:
            route_url += str(node) + '/'
        route_url += f'@{str(initial_node)}'

        return route_url


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    initial_coordinates = Coordinates(latitude=50.4021368, longitude=30.2525113)
    basic_algorithm = BasicAlgorithm(OverpassProvider())
    nodes_, ways_ = basic_algorithm.search_nodes_ways(initial_coordinates, distance=50,
                                                      maps_request_type=MapsRequestType.AROUND_POINT)
    print(basic_algorithm.generate_route(nodes_, ways_, initial_coordinates, nodes_count=3))
