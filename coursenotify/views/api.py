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
    status_code = 500
    # TODO add limit check
    try:
        data = request.get_json()
        watcher_manager = get_watcher_manager(data["school"])
        validate_email(data["email"], check_deliverability=False)
        if not isinstance(data["crn"], list):
            result["status"] = "failed"
            result["crn"] = "expected list"
            status_code = 400
        else:
            watcher_manager.add_all_watchee(data["email"], data["crn"], True)
            result["status"] = "ok"
            status_code = 200
    except SchoolInvalid:
        current_app.logger.error("<%s> school %s not valid" % (data["email"], data["school"]))
        result["school"] = "not valid"
        status_code = 400
    except CRNNotFound:
        #TODO response with specific not found crn
        current_app.logger.error("<%s> CRN %s not found" % (data["email"], data["crn"]))
        result["crn"] = "not valid"
        status_code = 404
    except EmailNotValidError:
        current_app.logger.error("<%s> email not valid" % (data["email"]))
        result["email"] = "not valid"
        status_code = 400
    except Exception as e:
        current_app.logger.error("add/ " + str(e))
        result["server_error"] = 1
        status_code = 500
    return jsonify(result), status_code


def validate_crn(crn):
    if len(crn) > 7:
        return False
    for i in crn:
        if not ('0' <= i <= '9'):
            return False
    return True

@api.route("/query", methods=["POST"])
@cross_origin()
def query_course():
    result = {"status": "failed"}
    status_code = 500
    try:
        data = request.get_json()
        crn = data["crn"]
        if len(str(data["crn"])) < 3:
            result["course"] = "crn length to short"
            status_code = 400
        elif not validate_crn(crn):
            result["course"] = []
            result["status"] = "ok"
            status_code = 200
        else:
            courses = get_course_manager(data["school"]).find_course_by_crn_prefix(crn)
            result["course"] = list(courses)
            result["status"] = "ok"
            status_code = 200
    except CRNNotFound as e:
        current_app.logger.error(str(e))
        result["course"] = "not found"
        status_code = 404
    except Exception as e:
        current_app.logger.error(str(e))
        result["server_error"] = 1
        status_code = 500

    return jsonify(result), status_code


@api.route("/remove", methods=["POST"])
@cross_origin()
def remove_watch():
    result = {"status": "failed"}
    status_code = 500
    try:
        data = request.get_json()
        remove_key = data["remove_key"]
        watcher_m = get_watcher_manager(data["school"])
        course_m = get_course_manager(data["school"])

        # remove
        watcher_m.remove_watchee_by_remove_key(remove_key)

        # find watcher with the remove key
        removed_watcher = watcher_m.find_watcher_by_remove_key(remove_key)

        # build json with email and the removed course
        email = removed_watcher["email_addr"]
        crn = list(filter(lambda x: x["remove_key"] == remove_key, removed_watcher["crn"]))
        result["email"] = email
        result["class_name"] = course_m.find_course_by_id(crn[0]["course_obj_id"])["name"]

        result["status"] = "ok"
        status_code = 200
    except RemoveKeyNotFound as e:
        current_app.logger.error(str(e))
        result["msg"] = "remove key not found"
        status_code = 404
    except RemoveKeyUsed as e:
        current_app.logger.error(str(e))
        result["msg"] = "removed key is used"
        status_code = 406
    except KeyError as e:
        current_app.logger.error("KeyError " + str(e))
        result["key_error"] = 1
        status_code = 400
    except Exception as e:
        current_app.logger.error(str(e))
        result["server_error"] = 1
        status_code = 500
    return jsonify(result), status_code
