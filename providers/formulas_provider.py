from math import cos, pi, asin, sqrt
from typing import Union, List
from random import sample

from dto import Coordinates

EARTH_SPHERE_DEGREE = 360
EARTH_CIRCUMFERENCE = 40057


def calculate_center_radius(coordinates: Coordinates, distance: float, count: int, left: bool = True) -> dict:
    result = {}
    last_lon, last_lat = coordinates.longitude, coordinates.latitude
    for i in range(count):
        lon_distance = abs(2 * distance * (EARTH_SPHERE_DEGREE / (cos(last_lat) * EARTH_CIRCUMFERENCE)))
        last_lon = bound_longitude(last_lon - lon_distance) if left else bound_longitude(last_lon + lon_distance)
        coordinates = Coordinates(latitude=last_lat, longitude=last_lon)
        result[coordinates] = distance

    return result


def calculate_square(coordinates: Union[Coordinates, list], distance: float, left: bool = False, right: bool = False,
                     maximum_chunk_distance: int = 5) -> List[Coordinates]:
    """
    Taken from https://stackoverflow.com/a/4000985
    """
    if left:
        longitude, latitude = coordinates.longitude, coordinates.latitude

        latitude_distance = abs(maximum_chunk_distance * EARTH_SPHERE_DEGREE / EARTH_CIRCUMFERENCE)
        longitude_distance_left = abs(distance * (EARTH_SPHERE_DEGREE / (cos(latitude) * EARTH_CIRCUMFERENCE)))
        longitude_distance_right = abs(
            maximum_chunk_distance * (EARTH_SPHERE_DEGREE / (cos(latitude) * EARTH_CIRCUMFERENCE)))

        result_lon_left = bound_longitude(longitude - longitude_distance_left)
        result_lat_left = bound_latitude(latitude)
        result_lon_right = bound_longitude(longitude - longitude_distance_left + longitude_distance_right)
        result_lat_right = bound_latitude(latitude + latitude_distance)

        return [Coordinates(longitude=result_lon_left, latitude=result_lat_left),
                Coordinates(longitude=result_lon_right, latitude=result_lat_right)]
    elif right:
        lon_top_left, lat_top_left, lon_bottom_right, lat_bottom_right = \
            coordinates[0].longitude, coordinates[0].latitude, coordinates[1].longitude, coordinates[1].latitude

        latitude_distance = abs(distance * EARTH_SPHERE_DEGREE / EARTH_CIRCUMFERENCE)
        longitude_distance = abs(distance * (EARTH_SPHERE_DEGREE / (cos(lat_top_left) * EARTH_CIRCUMFERENCE)))

        result_lon_left = bound_longitude(lon_top_left + longitude_distance)
        result_lat_left = bound_latitude(lat_top_left)
        result_lon_right = bound_longitude(lon_bottom_right + longitude_distance)
        result_lat_right = bound_latitude(lat_bottom_right)

        return [Coordinates(longitude=result_lon_left, latitude=result_lat_left),
                Coordinates(longitude=result_lon_right, latitude=result_lat_right)]
    else:
        longitude, latitude = coordinates.longitude, coordinates.latitude

        latitude_distance = abs(distance * EARTH_SPHERE_DEGREE / EARTH_CIRCUMFERENCE)
        longitude_distance = abs(distance * (EARTH_SPHERE_DEGREE / (cos(latitude) * EARTH_CIRCUMFERENCE)))

        result_lon_left = bound_longitude(longitude - longitude_distance)
        result_lat_left = bound_latitude(latitude - latitude_distance)
        result_lon_right = bound_longitude(longitude + longitude_distance)
        result_lat_right = bound_latitude(latitude + latitude_distance)

        return [Coordinates(longitude=result_lon_left, latitude=result_lat_left),
                Coordinates(longitude=result_lon_right, latitude=result_lat_right)]


def calculate_distance(point1: tuple, point2: tuple) -> float:
    """
    Taken from https://stackoverflow.com/a/21623206
    """
    lat1, lon1 = point1
    lat2, lon2 = point2
    if lat1 < 0 or lon1 < 0 or lat2 < 0 or lon2 < 0:
        return -1
    p = pi / 180
    a = 0.5 - cos((lat2 - lat1) * p) / 2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    return 12742 * asin(sqrt(a))


def calculate_squares_chunks(coordinates: Coordinates,
                             distance: float,
                             maximum_chunk_distance: float,
                             maximum_size: int) -> List[List[Coordinates]]:
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
        squares_chunks = sample(squares_chunks, maximum_size)
    except ValueError:
        pass

    return squares_chunks


def calculate_around_chunks(coordinates: Coordinates,
                            distance: float,
                            maximum_radius_distance: float,
                            maximum_size: int) -> dict:
    result = {coordinates: distance}
    extra_points = (distance - (maximum_radius_distance * 2)) / (maximum_radius_distance * 2)
    points_count = extra_points / 2
    if points_count < 1:
        result.update(calculate_center_radius(coordinates, maximum_radius_distance, 1))
    else:
        result.update(calculate_center_radius(coordinates, maximum_radius_distance, int(points_count)))
        result.update(calculate_center_radius(coordinates, maximum_radius_distance, int(points_count), left=False))

    try:
        sampled_result = sample(list(result), maximum_size)
        result = {coordinates: maximum_radius_distance for coordinates in sampled_result}
    except ValueError:
        pass

    return result


def bound_longitude(longitude: float) -> float:
    if longitude < -180:
        return 360 - abs(longitude)
    elif longitude > 180:
        return -360 + abs(longitude)
    else:
        return longitude


def bound_latitude(latitude: float) -> float:
    if latitude < -90:
        return -90 + abs(latitude)
    elif latitude > 90:
        return 180 - abs(latitude)
    else:
        return latitude
