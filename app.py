import sys

from flask import Flask, request
from sqlalchemy.orm import sessionmaker
from typing_inspect import get_args, get_origin

import plan

from extension import Response, is_sa_mapped
from plan import engine, Plan, PlanItemHotel

app = Flask(__name__)
Session = sessionmaker(bind=engine)
session = Session()


def update_orm_obj(obj, data):
    for attr, t in obj.__annotations__.items():
        if is_sa_mapped(t):
            if t.__mutable__:
                # Attribute of object is mutable (Same object, update the object)
                pass
            else:
                # Attribute of object is immutable (New object / Reuse matching existing object)
                pass
        elif bt := get_origin(t):
            if bt == list:
                st = get_args(t)[0]
                if is_sa_mapped(st):
                    if st.__mutable__:
                        # Attribute is a list of objects that are mutable (List of same objects, update each object)
                        pass
                    else:
                        # Attribute is a list of objects that are immutable (List of new object / reuse matching)
                        pass
                else:
                    # (should be) Attribute is a list of basic types (List of updated values)
                    # Shouldn't be hit as per current design
                    pass
        else:
            # Attribute is a basic type (Updated value)
            pass
    return obj


@app.route("/")
def index():
    return Response(None).as_response()


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
    p = Plan.from_object(body)
    session.add(p)
    session.commit()
    return Response(p).as_response()


@app.route("/api/plan/<plan_id>", methods=["POST"])
def save(plan_id):
    body = request.get_json()
    p: Plan = session.query(Plan).get(plan_id)
    p: Plan = update_orm_obj(p, body)
    return Response(p).as_response()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        pass
        # db.setup()
        # plan = Plan.get_by_id(1)
    else:
        app.run()
