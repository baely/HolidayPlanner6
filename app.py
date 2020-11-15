import sys

from flask import Flask, request
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import UnmappedInstanceError
from typing import Optional, Type
from typing_inspect import get_args, get_origin

from extension import Response, is_sa_mapped
from plan import engine, Airport, Base, Plan, PlanItemBase, PlanItemFlight, PlanItemGeneric, PlanItemHotel

app = Flask(__name__)
Session = sessionmaker(bind=engine)
session = Session()


def new_object(t: Type[Base], data) -> Base:
    if issubclass(t, PlanItemBase):
        if "flights" in data:
            t = PlanItemFlight
        elif "hotel" in data:
            t = PlanItemHotel
        else:
            t = PlanItemGeneric

    return t()


def new_orm_obj(t: Type[Base], data) -> Base:
    obj = new_object(t, data)
    obj = update_orm_obj(obj, data)
    session.add(obj)
    return obj


def search_orm_obj(t: Type[Base], data) -> Optional[Base]:
    return t.search_orm(session, data)


def new_or_existing_orm_obj(t: type, data: dict) -> Base:
    # Search for ORM of type t that looks exactly like data
    if obj := search_orm_obj(t, data):
        return obj
    return new_orm_obj(type, data)


def update_orm_obj(obj: Base, data: dict):
    for attr, attr_type in obj.__annotations__.items():
        if not (data_value := data.get(attr)) or attr == "id":
            continue
        new_value = None
        if is_sa_mapped(attr_type):
            if attr_type.__mutable__:
                # Attribute of object is mutable (Same object, update the object)
                existing_attr = getattr(obj, attr)
                if existing_attr:
                    new_value = update_orm_obj(getattr(obj, attr), data_value)
                else:
                    new_value = new_orm_obj(attr_type, data_value)
            else:
                # Attribute of object is immutable (New object / Reuse matching existing object)
                new_value = new_or_existing_orm_obj(attr_type, data_value)
        elif attr_base_type := get_origin(attr_type):
            if attr_base_type is list:
                # This doesn't work for some reason at this stage
                # continue
                attr_sub_type = get_args(attr_type)[0]
                if is_sa_mapped(attr_sub_type):
                    if attr_sub_type.__mutable__:
                        # Attribute is a list of objects that are mutable (List of same objects, update each object)
                        new_value = [new_orm_obj(attr_sub_type, element) for element in data_value]
                    else:
                        # Attribute is a list of objects that are immutable (List of new object / reuse matching)
                        new_value = [new_or_existing_orm_obj(attr_sub_type, element) for element in data_value]
                else:
                    # (should be) Attribute is a list of basic types (List of updated values)
                    # Shouldn't be hit as per current design
                    pass
        else:
            # Attribute is a basic type (Updated value)
            new_value = data_value
            pass
        setattr(obj, attr, new_value)
    return obj


@app.route("/")
def index():
    return Response(None).as_response()


@app.route("/api/airport/search/<text>", methods=["GET"])
def airport_search(text: str):
    airport_list = session.query(Airport).filter(Airport.name.ilike(f"%{text}%")).limit(20).all()

    result_list = [
        {"label": airport.name, "value": airport.id} for airport in airport_list
    ]

    return Response(result_list).as_response()


@app.route("/api/plan/", methods=["GET"])
def list_plans():
    plan_list = [
        {"id": p.id, "name": p.poi} for p in session.query(Plan).all()
    ]
    return Response(plan_list).as_response()


@app.route("/api/plan/<int:plan_id>", methods=["GET"])
def get_plan(plan_id: int):
    p: Plan = session.query(Plan).get(plan_id)
    return Response(p).as_response()


@app.route("/api/plan/", methods=["POST"])
def create():
    body = request.get_json()
    if "id" in body.keys():
        del body["id"]
    p = Plan(**body)
    session.add(p)
    session.commit()
    return Response(p).as_response()


@app.route("/api/plan/<plan_id>", methods=["POST"])
def save(plan_id):
    body = request.get_json()
    p: Plan = session.query(Plan).get(plan_id)
    p: Plan = update_orm_obj(p, body)
    session.commit()
    return Response(p).as_response()


@app.route("/api/plan/<plan_id>", methods=["DELETE"])
def delete_plan(plan_id):
    p: Plan = session.query(Plan).get(plan_id)
    try:
        session.delete(p)
        session.commit()
        return "Deleted"
    except UnmappedInstanceError:
        return "Plan does not exist"


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        pass
        # db.setup()
        # plan = Plan.get_by_id(1)
    else:
        app.run()
