import requests
import asyncio

from aiohttp import ClientSession
from typing import List

from providers import MapsProviderBase, MapsRequestData, MapsRequestType
from dto import Coordinates


class OverpassProvider(MapsProviderBase):

    def __init__(self, base_url: str = "https://overpass-api.de/api/interpreter"):
        self.base_url = base_url

    def get_osm_nodes_ways(self, request_data: MapsRequestData, request_type: MapsRequestType):
        response = requests.get(self.base_url, stream=True,
                                raw=f'data={OverpassProvider.__create_request_data(request_type, request_data)}',
                                headers={'Content-Type': 'application/x-www-form-urlencoded'})
        return response

    async def get_osm_nodes_ways_async(self, request_data: MapsRequestData,
                                       request_type: MapsRequestType,
                                       requests_interval_seconds: int = 2):
        tasks = []

        async with ClientSession() as session:
            if request_type == MapsRequestType.SQUARE_COORDINATES:
                for squares_coordinate in request_data.square_coordinates:
                    task = asyncio.ensure_future(self.__fetch_nodes_ways(
                        session, OverpassProvider.__create_request_data(request_type,
                                                                        square_coordinates=squares_coordinate)))
                    tasks.append(task)
                    await asyncio.sleep(requests_interval_seconds)
            elif request_type == MapsRequestType.AROUND_POINT:
                for point_radius in request_data.points_radius.items():
                    task = asyncio.ensure_future(self.__fetch_nodes_ways(
                        session, OverpassProvider.__create_request_data(request_type,
                                                                        points_radius=point_radius)
                    ))
                    tasks.append(task)
                    await asyncio.sleep(requests_interval_seconds)

            responses = await asyncio.gather(*tasks)

        return responses

    @staticmethod
    def __create_request_data(request_type: MapsRequestType, request_data: MapsRequestData = None,
                              square_coordinates: List[Coordinates] = None, points_radius: tuple = None,
                              is_only_cities_and_towns: bool = False):
        data = ''
        only_cities_and_towns = request_data.only_cities_and_towns if request_data else is_only_cities_and_towns
        if request_type == MapsRequestType.SQUARE_COORDINATES:
            square_coordinates: List[Coordinates] = request_data.square_coordinates if request_data \
                else square_coordinates
            if only_cities_and_towns:
                data = ''.format('[out:json][timeout:60][maxsize:200370824];'
                                 '(node["type"="town"]({0},{1},{2},{3});'
                                 'node["type"="city"]({0},{1},{2},{3});'
                                 ');(._;>;);out;',
                                 square_coordinates[0].latitude, square_coordinates[0].longitude,
                                 square_coordinates[1].latitude, square_coordinates[1].longitude
                                 )
            else:
                data = ''.format('[out:json][timeout:60][maxsize:200370824];'
                                 '(node["type"="town"]({0},{1},{2},{3});'
                                 'node["type"="city"]({0},{1},{2},{3});'
                                 'node["amenity"="arts_centre"]({0},{1},{2},{3});'
                                 'node["amenity"="place_of_worship"]({0},{1},{2},{3});'
                                 ');(._;>;);out;',
                                 square_coordinates[0].latitude, square_coordinates[0].longitude,
                                 square_coordinates[1].latitude, square_coordinates[1].longitude
                                 )
        elif request_type == MapsRequestType.AROUND_POINT:
            coordinates, radius = request_data.points_radius.popitem() if request_data else points_radius
            if only_cities_and_towns:
                data = '[out:json][timeout:60][maxsize:200370824];' \
                       '(node(around:{0},{1},{2})["type"="city"]; node(around:{0},{1},{2})["type"="town"]);(._;>;);out;' \
                    .format(radius * 1000, coordinates.latitude, coordinates.longitude)
            else:
                data = '[out:json][timeout:60][maxsize:200370824];' \
                       'node(around:{0},{1},{2})["tourism"];out;'.format(radius * 1000, coordinates.latitude,
                                                                         coordinates.longitude)

        return data

    async def __fetch_nodes_ways(self, session, request_data):
        session.headers.update({"Content-Type": "application/x-www-form-urlencoded"})
        async with session.get(self.base_url, data=request_data) as response:
            return await response.content.read()
