import os
import logging
import asyncio
import codecs

from typing import Tuple, List
from random import sample, choice
from uuid import uuid4
from json import loads
from requests import Response

from adapters.db_mongo_adapter import MongoDbAdapter
from providers import calculate_square, MapsProviderBase, OverpassProvider, MapsRequestType, MapsRequestData, \
    CacheProvider, calculate_squares_chunks, calculate_around_chunks
from dto import Way, Node, Coordinates, SearchConfig

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


class BasicAlgorithm:

    def __init__(self, maps_provider: MapsProviderBase,
                 maps_request_type: MapsRequestType = MapsRequestType.AROUND_POINT,
                 cache_provider: CacheProvider = None):
        self.maps_provider = maps_provider
        self.maps_request_type = maps_request_type
        self.cache_provider = cache_provider

    def search_nodes_ways(self, search_config: SearchConfig,
                          maximum_chunk_distance: float = 20,
                          maximum_geo_requests_count: int = 15,
                          maps_request_type: MapsRequestType = None) -> Tuple[list, list]:
        nodes, ways = [], []
        geo_request_count = 0
        distance = search_config.distance
        initial_coordinates = Coordinates(latitude=search_config.latitude, longitude=search_config.longitude)

        if self.cache_provider:
            result = self.cache_provider.get_api_responses(search_config)
            if result and len(result.get('responses')) > 0:
                nodes, ways = self.process_responses(result.get('responses'))

        if len(nodes) == 0:
            request_data = MapsRequestData(initial_coordinates=initial_coordinates, distance=distance)
            if maps_request_type:
                self.maps_request_type = maps_request_type

            coordinates = initial_coordinates
            if distance <= maximum_chunk_distance:
                while geo_request_count < maximum_geo_requests_count:
                    try:
                        if self.maps_request_type == MapsRequestType.AROUND_POINT:
                            request_data.points_radius = {coordinates: distance}
                        else:
                            request_data.square_coordinates = calculate_square(coordinates, distance)

                        nodes, ways = self.request_nodes_ways(request_data)
                        break
                    except ValueError as e:
                        logger.error(str(e))
                        coordinates = (coordinates[0] + 0.5, coordinates[1] + 0.5)
            else:
                if self.maps_request_type == MapsRequestType.AROUND_POINT:
                    request_data.points_radius = calculate_around_chunks(coordinates, distance, maximum_chunk_distance,
                                                                         maximum_geo_requests_count)
                else:
                    request_data.square_coordinates = calculate_squares_chunks(coordinates, distance,
                                                                               maximum_chunk_distance,
                                                                               maximum_geo_requests_count)

                nodes, ways = self.request_nodes_ways(request_data, asynchronously=True)

        return nodes, ways

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

                if self.cache_provider:
                    search_config = SearchConfig(latitude=request_data.initial_coordinates.latitude,
                                                 longitude=request_data.initial_coordinates.longitude,
                                                 distance=request_data.distance)
                    self.cache_provider.save_api_responses(search_config, responses)

                nodes, ways = self.process_responses(responses)

            except Exception as e:
                logger.error(str(e))

            return nodes, ways
        else:
            response = self.maps_provider.get_osm_nodes_ways(request_data, self.maps_request_type)

            if self.cache_provider:
                search_config = SearchConfig(latitude=request_data.initial_coordinates.latitude,
                                             longitude=request_data.initial_coordinates.longitude,
                                             distance=request_data.distance)
                self.cache_provider.save_api_responses(search_config, [response])

            return self.process_response(response)

    def process_responses(self, responses: list) -> Tuple[list, list]:
        nodes, ways = [], []
        for response in responses:
            try:
                nodes_request, ways_request = self.process_response(response)
                nodes.extend(nodes_request)
                ways.extend(ways_request)
            except ValueError as e:
                logger.error(str(e))

        return nodes, ways

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

    def generate_route(self, nodes: List[Node], ways: List[Way], search_config: SearchConfig) -> str:
        distance = search_config.distance or 15
        nodes_count = search_config.nodes_count or 3
        coordinates = Coordinates(latitude=search_config.latitude, longitude=search_config.longitude)
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

        if len(result_nodes) != nodes_count or len(result_nodes) == 1:
            try:
                result_nodes = [initial_node]
                result_nodes.extend(sample(nodes, (nodes_count - 1) if nodes_count != 1 else 1))
            except ValueError:
                pass

        route_url = 'https://www.google.com/maps/dir/'
        for node in result_nodes:
            route_url += str(node) + '/'
        route_url += f'@{str(initial_node)}'

        if self.cache_provider:
            self.cache_provider.save_user_search_results(search_config.id, result_nodes, route_url)

        return route_url


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    from uuid import uuid4
    search_config = SearchConfig(id=str(uuid4()), nodes_count=3, latitude=50.4021368, longitude=30.2525113, distance=50)
    cache_provider = CacheProvider(MongoDbAdapter(host=os.environ.get('MONGODB_HOST', '127.0.0.1'),
                                                  db_name=os.environ.get('MONGODB_DATABASE', 'road_trip'),
                                                  series_name=os.environ.get('MONGODB_SERIES', 'user_search'),
                                                  username=os.environ.get('MONGODB_USER', 'mongodbuser'),
                                                  password=os.environ.get('MONGODB_PASSWORD',
                                                                          'your_mongodb_root_password')))
    basic_algorithm = BasicAlgorithm(OverpassProvider(), cache_provider=cache_provider)
    nodes_, ways_ = basic_algorithm.search_nodes_ways(search_config=search_config,
                                                      maps_request_type=MapsRequestType.AROUND_POINT)
    print(basic_algorithm.generate_route(nodes_, ways_, search_config))
