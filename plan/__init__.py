from abc import ABC
from datetime import datetime
from typing import List

from db import DBObject
from plan.peripheral import Flight, Hotel, Location, PointOfInterest


class PlanItemBase(ABC, DBObject):
    pass


class PlanItemFlight(PlanItemBase):
    flights: List[Flight]


class PlanItemGeneric(PlanItemBase):
    label: str


class PlanItemHotel(PlanItemBase):
    hotel: Hotel
    check_in: datetime
    check_out: datetime


class Plan(DBObject):
    poi: PointOfInterest
    items: List[PlanItemBase]
