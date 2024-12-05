from dataclasses import dataclass
import maidenhead as mh
from pyproj import Geod


class LocationUtil:
    @dataclass
    class Coordinate:
        latitude: float
        longitude: float

    @dataclass
    class DistanceAzimuth:
        distance: float
        azimuth: float

    @staticmethod
    def maidenhead_to_coordinates(loc: str) -> Coordinate:
        c = mh.to_location(loc)

        return LocationUtil.Coordinate(
            latitude=c[0],
            longitude=c[1]
        )

    @staticmethod
    def coordinates_to_maidenhead(loc: Coordinate) -> str:
        return mh.to_maiden(loc.latitude, loc.longitude)

    @staticmethod
    def calc_distance_azimuth(loc_0: Coordinate, loc_1: Coordinate) -> DistanceAzimuth:
        eod = Geod(ellps="WGS84")

        azimuth0, azimuth1, distance = eod.inv(loc_0.longitude, loc_0.latitude, loc_1.longitude, loc_1.latitude)

        azimuth0 = (azimuth0 + 360) % 360
        distance = distance / 1000

        return LocationUtil.DistanceAzimuth(
            distance=distance,
            azimuth=azimuth0
        )


if __name__ == '__main__':
    # gps_0: LocationUtil.Coordinate = LocationUtil.maidenhead_to_coordinates("JN59NK18")
    gps_0: LocationUtil.Coordinate = LocationUtil.Coordinate(latitude=49.452833, longitude=11.094333)

    maid_0 = LocationUtil.coordinates_to_maidenhead(gps_0)

    print(maid_0)

    gps_1: LocationUtil.Coordinate = LocationUtil.maidenhead_to_coordinates("JN58SD15")

    print(gps_0)
    print(gps_1)

    da = LocationUtil.calc_distance_azimuth(gps_0, gps_1)

    print(da)
