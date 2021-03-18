import logging
import asyncio
import codecs

from os import environ
from typing import Tuple, List, Union
from random import sample, choice
from uuid import uuid4
from json import loads
from requests import Response

from providers.formulas_provider import calculate_square, calculate_distance
from providers.osm_provider import OsmProvider
from dto import Way, Node

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def request_nodes_ways(squares_chunks: Union[tuple, list], asynchronously: bool = False):
    osm_provider = OsmProvider(base_url=environ.get('OSM_URL'))

    if asynchronously:
        nodes, ways = [], []
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
        try:
            # future = asyncio.ensure_future()
            responses = loop.run_until_complete(osm_provider.get_osm_nodes_ways_async(squares_chunks))

            for response in responses:
                try:
                    nodes_request, ways_request = basic_algorithm(response)
                    nodes.extend(nodes_request)
                    ways.extend(ways_request)
                except ValueError as e:
                    logger.error(str(e))
        except Exception as e:
            logger.error(str(e))

        return nodes, ways
    else:
        response = osm_provider.get_osm_nodes_ways(squares_chunks)
        return basic_algorithm(response)


def basic_algorithm(osm_response: Response) -> Tuple[list, list]:
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
            nodes_index[node_id] = Node(node_id, float(element.get('lon')), float(element.get('lat')))
        elif element.get('type') == 'way':
            way = Way()
            for node in element.get("nodes"):
                try:
                    way.nodes.append(nodes_index[str(node)])
                except KeyError:
                    continue
            ways_list.extend([way])

    return list(nodes_index.values()), ways_list


def search_nodes_ways(coordinates: tuple, distance: int = 10,
                      maximum_chunk_distance: int = 5,
                      maximum_geo_requests_count: int = 20) -> Tuple[list, list]:
    nodes, ways = [], []
    geo_request_count = 0
    if distance <= maximum_chunk_distance:
        while geo_request_count < maximum_geo_requests_count:
            try:
                nodes, ways = request_nodes_ways(calculate_square(coordinates, distance))
                break
            except ValueError as e:
                logger.error(str(e))
                coordinates = (coordinates[0] + 0.5, coordinates[1] + 0.5)
    else:
        step_coordinates = coordinates
        chunks = int(distance / maximum_chunk_distance)
        distance /= 2

        left_coordinates = calculate_square(step_coordinates, distance, left=True)
        right_coordinates = None
        squares_chunks = [left_coordinates]

        for i in range(chunks):
            step_coordinates = right_coordinates or left_coordinates
            right_coordinates = calculate_square(step_coordinates, maximum_chunk_distance, right=True)
            squares_chunks.append(right_coordinates)
        try:
            squares_chunks = sample(squares_chunks, maximum_geo_requests_count)
        except ValueError:
            pass

        nodes, ways = request_nodes_ways(squares_chunks, asynchronously=True)

    return nodes, ways


def generate_route(nodes: List[Node], ways: List[Way],
                   coordinates: tuple, distance: int = 15, nodes_count: int = 5) -> str:
    initial_node = Node(str(uuid4()), longitude=coordinates[0], latitude=coordinates[1])
    min_node_distance = distance / 5
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
            break
    else:
        try:
            result_nodes.extend(sample(nodes, nodes_count - 1))
        except ValueError:
            pass

    route_url = 'https://www.google.com/maps/dir/'
    for node in result_nodes:
        route_url += str(node) + '/'
    route_url += f'@{str(initial_node)}'

    return route_url


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    initial_coordinates = (50.4021368, 30.2525113)
    nodes_, ways_ = search_nodes_ways(initial_coordinates, distance=1000)
    print(generate_route(nodes_, ways_, initial_coordinates, nodes_count=3))
