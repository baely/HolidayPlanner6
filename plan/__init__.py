from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import create_engine, Column, DateTime, Integer, Float, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


engine = create_engine("postgresql://postgres:100598@localhost:5432/postgres", echo=False)
Base = declarative_base()


class Airport(Base):
    __tablename__ = "Airport"
    id: int = Column(Integer, primary_key=True)

    name: str = Column(String)
    icao: str = Column(String)
    lat: float = Column(Float)
    lon: float = Column(Float)


class FlightPoint(Base):
    __tablename__ = "FlightPoint"
    id: int = Column(Integer, primary_key=True)

    airport_id: int = Column(Integer, ForeignKey('Airport.id'))
    airport: Airport = relationship(Airport)
    time: datetime = Column(DateTime)


class Flight(Base):
    __tablename__ = "Flight"
    id: int = Column(Integer, primary_key=True)

    flight_plan: int = Column(Integer, ForeignKey('PlanItemFlight.id'))
    departure_id: int = Column(Integer, ForeignKey('FlightPoint.id'))
    departure: FlightPoint = relationship(FlightPoint, foreign_keys=[departure_id])
    arrival_id: int = Column(Integer, ForeignKey('FlightPoint.id'))
    arrival: FlightPoint = relationship(FlightPoint, foreign_keys=[arrival_id])


class PointOfInterest(Base):
    __tablename__ = "PointOfInterest"
    id: int = Column(Integer, primary_key=True)

    label: str = Column(String)
    lat: float = Column(Float)
    lon: float = Column(Float)


class Hotel(Base):
    __tablename__ = "Hotel"
    id: int = Column(Integer, primary_key=True)

    name: str = Column(String)
    lat: float = Column(Float)
    lon: float = Column(Float)


class PlanItemBase(Base):
    __tablename__ = "PlanItemBase"
    id: int = Column(Integer, primary_key=True)

    start_time: str = Column(String)
    plan: int = Column(Integer, ForeignKey('Plan.id'))

    discriminator = Column('type', String)
    __mapper_args__ = {'polymorphic_on': discriminator}


class PlanItemFlight(PlanItemBase):
    __tablename__ = "PlanItemFlight"
    id: int = Column(Integer, ForeignKey('PlanItemBase.id'), primary_key=True)

    flights: List[Flight] = relationship(Flight)

    __mapper_args__ = {
        'polymorphic_identity': 'PlanItemFlight',
    }


class PlanItemGeneric(PlanItemBase):
    __tablename__ = "PlanItemGeneric"
    id: int = Column(Integer, ForeignKey('PlanItemBase.id'), primary_key=True)

    label: str = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'PlanItemGeneric',
    }


class PlanItemHotel(PlanItemBase):
    __tablename__ = "PlanItemHotel"
    id: int = Column(Integer, ForeignKey('PlanItemBase.id'), primary_key=True)

    hotel_id: int = Column(Integer, ForeignKey('Hotel.id'))
    hotel: Hotel = relationship(Hotel)
    check_in: datetime = Column(DateTime)
    check_out: datetime = Column(DateTime)

    __mapper_args__ = {
        'polymorphic_identity': 'PlanItemHotel',
    }


class Plan(Base):
    __tablename__ = "Plan"
    id: int = Column(Integer, primary_key=True)

    poi: str = Column(String)
    items: List[PlanItemBase] = relationship(PlanItemBase)

    @staticmethod
    def from_object(o: Any, plan_id: Optional[int] = None) -> 'Plan':
        print(o)
        p = Plan(**o)
        print(p)
        return p

    def update_from_object(self, o: Any):
        pass


Base.metadata.create_all(engine)
