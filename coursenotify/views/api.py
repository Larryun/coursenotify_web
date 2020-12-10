from cn_v2.exception import *
from email_validator import validate_email, EmailNotValidError
from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin

from coursenotify.manager import get_watcher_manager, get_course_manager

api = Blueprint("api", __name__, url_prefix="/api")


@api.route("/add", methods=["POST"])
@cross_origin()
def add():
    result = {"status": "failed"}
    data = request.get_json()
    try:
        watcher_manager = get_watcher_manager(data["school"])
        validate_email(data["email"], check_deliverability=False)
        if watcher_manager:
            if not isinstance(data["crn"], list):
                result["status"] = "failed"
                result["crn"] = "expected list"
            else:
                for crn in data["crn"]:
                    watcher_manager.add_watchee(data["email"], str(crn))
                result["status"] = "ok"
        else:
            current_app.logger.error("<%s> school %s not valid" % (data["email"], data["school"]))
            result["school"] = "not valid"
    except CRNNotFound:
        current_app.logger.error("<%s> CRN %s not found" % (data["email"], data["crn"]))
        result["crn"] = "not valid"
    except EmailNotValidError:
        current_app.logger.error("<%s> email not valid" % (data["email"]))
        result["email"] = "not valid"
    except Exception as e:
        current_app.logger.error(str(e))
        result["server_error"] = 1
    return jsonify(result)


@api.route("/query", methods=["POST"])
@cross_origin()
def query_course():
    result = {"status": "failed"}
    data = request.get_json()
    try:
        if len(str(data["crn"])) < 3:
            result["status"] = "failed"
            result["course"] = "crn length to short"
        else:
            course_m = get_course_manager(data["school"])
            courses = course_m.course_cc.find({"crn": {"$regex": "^" + str(data["crn"])}},
                                              {"_id": 0,
                                               "title": 1,
                                               "name": 1,
                                               "crn": 1,
                                               "status": 1, })
            result["course"] = list(courses)
            result["status"] = "ok"
    except CRNNotFound:
        result["course"] = "not found"
    except Exception as e:
        print(str(e))
        result["server_error"] = 1

    return jsonify(result)
