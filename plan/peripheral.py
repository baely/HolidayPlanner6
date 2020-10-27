from datetime import datetime
from decimal import Decimal
from typing import Tuple

from db import DBObject


class Location(DBObject):
    x: float
    y: float


class Airport(DBObject):
    name: str
    abbr: str
    location: Location


class FlightPoint(DBObject):
    airport: Airport
    time: datetime


class Flight(DBObject):
    departure: FlightPoint
    arrival: FlightPoint


class PointOfInterest(DBObject):
    label: str
    location: Location


class Hotel(DBObject):
    name: str
    location: Location
