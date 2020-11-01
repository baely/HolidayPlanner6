import sys

from flask import Flask, request
from sqlalchemy.orm import sessionmaker

from extension import Response
from plan import engine, Plan, PlanItemGeneric, PlanItemHotel, Location, PointOfInterest, Hotel

app = Flask(__name__)
Session = sessionmaker(bind=engine)
session = Session()


@app.route("/")
def index():
    return Response(None).as_response()


@app.route("/api/plan/", methods=["GET"])
def list_plans():
    plan_list = Plan.list_all()
    return Response(plan_list).as_response()


@app.route("/api/plan/<plan_id>", methods=["GET"])
def get_plan(plan_id):
    p = Plan.load(plan_id)
    return Response(p).as_response()


@app.route("/api/plan/", methods=["POST"])
def create():
    body = request.get_json()
    if "id" in body.keys():
        del body["id"]
    p = Plan.from_object(body)
    return Response(p).as_response()


@app.route("/api/plan/<plan_id>", methods=["POST"])
def save(plan_id):
    body = request.get_json()
    p = Plan.from_object(body, plan_id)
    p.save()
    return Response(p).as_response()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        # db.setup()
        # plan = Plan.get_by_id(1)
        pass
    else:
        app.run()
