import requests
import asyncio

from aiohttp import ClientSession


class OsmProvider:

    def __init__(self, base_url: str = "https://api.openstreetmap.org/api/0.6/map"):
        self.base_url = base_url

    def get_osm_nodes_ways(self, square_coordinates: tuple):
        url = "{0}?bbox={1},{2},{3},{4}".format(
            self.base_url,
            *square_coordinates
        )
        response = requests.get(url, stream=True, headers={'Accept': 'application/json'})
        return response

    async def get_osm_nodes_ways_async(self, squares_coordinates: list):
        tasks = []
        url = "{0}?bbox={1},{2},{3},{4}"

        async with ClientSession() as session:
            for squares_coordinate in squares_coordinates:
                task = asyncio.ensure_future(OsmProvider.__fetch(
                    url.format(self.base_url, *squares_coordinate), session)
                )
                tasks.append(task)

            responses = await asyncio.gather(*tasks)

        return responses

    @staticmethod
    async def __fetch(url, session):
        session.headers.update({"Accept": "application/json"})
        async with session.get(url) as response:
            return await response.content.read()
