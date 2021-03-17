from math import cos, pi, asin, sqrt
from typing import Tuple


def calculate_square(coordinates: tuple, distance: float, left: bool = False, right: bool = False,
                     maximum_chunk_distance: int = 15) -> Tuple[float, float, float, float]:
    EARTH_SPHERE_DEGREE = 360
    EARTH_CIRCUMFERENCE = 40057

    if left:
        longitude, latitude = coordinates

        latitude_distance = abs(maximum_chunk_distance * EARTH_SPHERE_DEGREE / EARTH_CIRCUMFERENCE)
        longitude_distance_left = abs(distance * (EARTH_SPHERE_DEGREE / (cos(latitude) * EARTH_CIRCUMFERENCE)))
        longitude_distance_right = abs(
            maximum_chunk_distance * (EARTH_SPHERE_DEGREE / (cos(latitude) * EARTH_CIRCUMFERENCE)))

        result_lon_left = bound_longitude(longitude - longitude_distance_left)
        result_lat_left = bound_latitude(latitude)
        result_lon_right = bound_longitude(longitude - longitude_distance_left + longitude_distance_right)
        result_lat_right = bound_latitude(latitude + latitude_distance)

        return result_lon_left, result_lat_left, result_lon_right, result_lat_right
    elif right:
        lon_top_left, lat_top_left, lon_bottom_right, lat_bottom_right = coordinates

        latitude_distance = abs(distance * EARTH_SPHERE_DEGREE / EARTH_CIRCUMFERENCE)
        longitude_distance = abs(distance * (EARTH_SPHERE_DEGREE / (cos(lat_top_left) * EARTH_CIRCUMFERENCE)))

        result_lon_left = bound_longitude(lon_top_left + longitude_distance)
        result_lat_left = bound_latitude(lat_top_left)
        result_lon_right = bound_longitude(lon_bottom_right + longitude_distance)
        result_lat_right = bound_latitude(lat_bottom_right)

        return result_lon_left, result_lat_left, result_lon_right, result_lat_right
    else:
        longitude, latitude = coordinates

        latitude_distance = abs(distance * EARTH_SPHERE_DEGREE / EARTH_CIRCUMFERENCE)
        longitude_distance = abs(distance * (EARTH_SPHERE_DEGREE / (cos(latitude) * EARTH_CIRCUMFERENCE)))

        result_lon_left = bound_longitude(longitude - longitude_distance)
        result_lat_left = bound_latitude(latitude - latitude_distance)
        result_lon_right = bound_longitude(longitude + longitude_distance)
        result_lat_right = bound_latitude(latitude + latitude_distance)

        return result_lon_left, result_lat_left, result_lon_right, result_lat_right


def calculate_distance(point1: tuple, point2: tuple) -> float:
    lat1, lon1 = point1
    lat2, lon2 = point2
    if lat1 < 0 or lon1 < 0 or lat2 < 0 or lon2 < 0:
        return -1
    p = pi / 180
    a = 0.5 - cos((lat2 - lat1) * p) / 2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    return 12742 * asin(sqrt(a))


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
