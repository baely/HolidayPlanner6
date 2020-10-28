import sys

from flask import Flask, request

from db import DB, DBObject
from extension import Response
from plan import Plan, PlanItemGeneric, PlanItemHotel
from plan.peripheral import Location, PointOfInterest, Hotel

app = Flask(__name__)
db = DB()


@app.route("/")
def index():
    return Response(None).as_response()


@app.route("/api/plan/", methods=["GET"])
def list_plans():
    plan_list = Plan.list_all(db)
    return Response(plan_list).as_response()


@app.route("/api/plan/<plan_id>", methods=["GET"])
def get_plan(plan_id):
    p = Plan.load(db, plan_id)
    return Response(p).as_response()


@app.route("/api/plan/", methods=["POST"])
def create():
    body = request.get_json()
    if "id" in body.keys():
        del body["id"]
    p = Plan.from_object(body, db)
    return Response(p).as_response()


@app.route("/api/plan/<plan_id>", methods=["POST"])
def save(plan_id):
    body = request.get_json()
    p = Plan.from_object(body, db, plan_id)
    p.save()
    return Response(p).as_response()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        db.setup()
        # plan = Plan.get_by_id(1)

        melbourne_location = Location(x=-37.8137564, y=144.9621251)
        melbourne_poi = PointOfInterest(label="Melbourne", location=melbourne_location)
        melbourne_plan = Plan(poi=melbourne_poi)

        print("Melbourne Coordinates", melbourne_location.__dict__)
        print("Melbourne POI", melbourne_poi.__dict__)
        print("Holiday to Melbourne", melbourne_plan.__dict__)

        generic_plan = PlanItemGeneric(label="Generic Plan", start_time="never.")
        hotel_item = PlanItemHotel(hotel=Hotel(name="Big Hotel", location=melbourne_location), check_in="now", checkout="later")

        print(generic_plan.__dict__)
        print(type(generic_plan).__bases__)

    else:
        app.run()
