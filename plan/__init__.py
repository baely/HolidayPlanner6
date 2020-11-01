from abc import ABC
from datetime import datetime
from typing import List

from sqlalchemy import create_engine, Column, DateTime, Integer, Float, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


engine = create_engine("postgresql://postgres:100598@localhost:5432/postgres", echo=True)
Base = declarative_base()


class Location(Base):
    __tablename__ = "Location"
    id: int = Column(Integer, primary_key=True)

    x: float = Column(Float)
    y: float = Column(Float)


class Airport(Base):
    __tablename__ = "Airport"
    id: int = Column(Integer, primary_key=True)

    name: str = Column(String)
    abbr: str = Column(String)
    location_id: int = Column(Integer, ForeignKey('Location.id'))
    location: Location = relationship(Location)


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
    departure: FlightPoint = relationship(FlightPoint)
    arrival_id: int = Column(Integer, ForeignKey('FlightPoint.id'))
    arrival: FlightPoint = relationship(FlightPoint)


class PointOfInterest(Base):
    __tablename__ = "PointOfInterest"
    id: int = Column(Integer, primary_key=True)

    label: str = Column(String)
    location_id: int = Column(Integer, ForeignKey('Location.id'))
    location: Location = relationship(Location)


class Hotel(Base):
    __tablename__ = "Hotel"
    id: int = Column(Integer, primary_key=True)

    name: str = Column(String)
    location_id: int = Column(Integer, ForeignKey('Location.id'))
    location: Location = relationship(Location)


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

    hotel: Hotel
    check_in: datetime = Column(DateTime)
    check_out: datetime = Column(DateTime)

    __mapper_args__ = {
        'polymorphic_identity': 'PlanItemHotel',
    }


class Plan(Base):
    __tablename__ = "Plan"
    id: int = Column(Integer, primary_key=True)

    poi_id: int = Column(Integer, ForeignKey('PointOfInterest.id'))
    poi: PointOfInterest = relationship(PointOfInterest)
    items: List[PlanItemBase] = relationship(PlanItemBase)


Base.metadata.create_all(engine)
