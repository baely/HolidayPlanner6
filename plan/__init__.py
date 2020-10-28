from abc import ABC
from datetime import datetime
from typing import List

from db import DBObject
from plan.peripheral import Flight, Hotel, Location, PointOfInterest


class PlanItemBase(DBObject):
    start_time: str
    pass


class PlanItemFlight(PlanItemBase):
    flights: List[Flight]


class PlanItemGeneric(PlanItemBase):
    label: str


class PlanItemHotel(PlanItemBase):
    hotel: Hotel
    check_in: str
    check_out: str


class Plan(DBObject):
    poi: PointOfInterest
    items: List[PlanItemBase]
