import datetime
import os
import traceback

import jwt
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from exceptions import (
    InvalidTokenException,
    InvalidRequestException,
    UnknownLoanItemException,
    NotAllowedException,
    UnknownUserException,
    InitialAdminRoleException,
    UserAlreadyExistsException,
    CannotDeleteLoadedItem
)
from users import Users, UserManagement

app = Flask(__name__)
app.config["SECRET_KEY"] = (
    os.environ["SECRET_KEY"] if "SECRET_KEY" in os.environ else "bad_secret"
)
mode = "admin-operated"


def check_token_and_set_session(user_manage):
    if "access-token" in request.headers:
        token = request.headers["access-token"]
    else:
        raise InvalidTokenException
    data = jwt.decode(token, app.config["SECRET_KEY"])
    user_manage.set_user_session(data["username"])


def register(user_manager):
    """Create user."""
    request_data = request.get_json()
    if (
        "username" not in request_data
        or "password" not in request_data
        or "phone" not in request_data
    ):
        raise InvalidRequestException
    if not phonenumbers.is_valid_number(phonenumbers.parse(request_data["phone"], None)):
        raise InvalidRequestException
    hashed_password = generate_password_hash(request_data["password"])
    user_manager.create(
        request_data["username"],
        hashed_password,
        request_data["phone"],
    )
    return jsonify({"message": "Successfully registered."})


def read_users(user_manage: Users):
    user_dict = user_manage.read()
    return jsonify({"users": user_dict})


def read_user(user_manage: Users, username):
    user_dict = user_manage.read(username)
    return jsonify({"user": user_dict})


def remove_user(user_manage: Users, username):
    user_dict = user_manage.remove(username)
    return jsonify({"message": "User successfully deleted.", "user": user_dict})


def update_user(user_manage: Users, username):
    if len(request.json) != 1:
        raise InvalidRequestException
    if "password" in request.json:
        password_hash = generate_password_hash(request.json["password"])
        user_manage.update_password(username, password_hash)
    elif "phone" in request.json:
        if not phonenumbers.is_valid_number(phonenumbers.parse(request.json["phone"], None)):
            raise InvalidRequestException
        user_dict = user_manage.update_phone(
            username, request.json["phone"]
        )
        return jsonify({"user": user_dict})
    elif "role" in request.json:
        if request.json["role"] not in ["admin", "regular"]:
            raise InvalidRequestException
        user_dict = user_manage.update_role(username, request.json["role"])
        return jsonify({"user": user_dict})
    else:
        raise InvalidRequestException
    return jsonify({"message": "Password successfully changed."})


def create_loan_item(user_manager: Users):
    loan_item_dict = user_manager.Loans.create(request.json["id"], request.json["description"])
    return jsonify({"loan-item": loan_item_dict})


def read_loan_items(user_manager: Users):
    loan_item_dict = user_manager.Loans.read(request.args)
    return jsonify({"loan-items": loan_item_dict})


def read_loan_item(user_manager: Users, id):
    loan_dict = user_manager.Loans.read_single_entry(id)
    return jsonify({"loan-item": loan_dict})


def update_loan_item(user_manager: Users, id):
    """Only accepts {"loanedto": <username>}"""
    if "loanedto" not in request.json:
        raise InvalidRequestException
    loan_dict = user_manager.Loans.update_loan(id, request.json["loanedto"])
    return jsonify({"loan-item": loan_dict})


def remove_loan_item(user_manager: Users, loan_item_id):
    loan_item_dict = user_manager.Loans.remove(loan_item_id)
    return jsonify({"message": "Loan item successfully deleted.", "loan-item": loan_item_dict})


def login_user(user_manager):
    json = request.get_json()
    user_orm = user_manager.non_session_read(json["username"])
    if not user_orm:
        return jsonify({"error": "Wrong username or password."}), 401
    if check_password_hash(user_orm.hashed_password, json["password"]):
        payload = {
            "username": json["username"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
        }
        token = jwt.encode(payload, app.config["SECRET_KEY"])
        return jsonify({"auth_token": token.decode()})
    return jsonify({"error": "Wrong username or password."}), 401


def get_mode(user_manager: Users):
    role = user_manager.get_current_role()
    if role == "admin":
        return jsonify({"mode": mode})
    else:
        raise NotAllowedException


def change_mode(user_manager: Users):
    global mode
    role = user_manager.get_current_role()
    if role == "admin":
        request_data = request.get_json()
        if "mode" in request_data and request_data["mode"] in ["self-service", "admin-operated"]:
            mode = request_data["mode"]
            return jsonify({"mode": mode})
        else:
            raise InvalidRequestException
    else:
        raise NotAllowedException


def eval_and_respond(user_manage, funcs):
    ret_val = {}
    try:
        for func in funcs:
            if isinstance(func, list):
                ret_val = func[0](user_manage, *func[1:])
            else:
                ret_val = func(user_manage)
    except UnknownLoanItemException:
        return jsonify({"error": "Loan not found."}), 404
    except NotAllowedException:
        return jsonify({"error": "Not authorized."}), 403
    except UserAlreadyExistsException:
        return jsonify({"error": "User already exists."}), 400
    except (InvalidRequestException, NumberParseException):
        return jsonify({"error": "Invalid request."}), 400
    except UnknownUserException:
        return jsonify({"error": "User not found."}), 404
    except InitialAdminRoleException:
        return jsonify({"error": "Can't change admin username or role."}), 400
    except CannotDeleteLoadedItem:
        return jsonify({"error": "Cannot delete loan item that is loaned."}), 403
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return ret_val


def create_admin_user():
    with UserManagement() as user_management:
        password_hash = generate_password_hash(
            os.environ["ADMIN_PASSWORD"] if "ADMIN_PASSWORD" in os.environ else "admin"
        )
        user_management.create_initial_admin(password_hash)


@app.route("/login", methods=["POST"])
def login():
    with UserManagement() as user_manage:
        return eval_and_respond(user_manage, [login_user])


@app.route("/users", methods=["GET", "POST"])
def users():
    with UserManagement() as user_manage:
        if request.method == "GET":
            funcs = [check_token_and_set_session, read_users]
        else:  # POST
            funcs = [register]
        response = eval_and_respond(user_manage, funcs)
    return response


@app.route("/users/<username>", methods=["GET", "PUT", "DELETE"])
def user(username):
    with UserManagement() as user_manage:
        if request.method == "GET":
            funcs = [check_token_and_set_session, [read_user, username]]
            response = eval_and_respond(user_manage, funcs)
        elif request.method == "DELETE":
            funcs = [check_token_and_set_session, [remove_user, username]]
            response = eval_and_respond(user_manage, funcs)
        else:  # PUT
            funcs = [check_token_and_set_session, [update_user, username]]
            response = eval_and_respond(user_manage, funcs)
    return response


@app.route("/loan-items", methods=["GET", "POST"])
def loan_items():
    with UserManagement() as user_manage:
        if request.method == "GET":
            funcs = [check_token_and_set_session, read_loan_items]
        else:  # POST
            funcs = [check_token_and_set_session, create_loan_item]
        response = eval_and_respond(user_manage, funcs)
    return response


@app.route("/loan-items/<item_id>", methods=["GET", "PUT", "DELETE"])
def loan_item(item_id):
    with UserManagement() as user_manage:
        if request.method == "GET":
            funcs = [check_token_and_set_session, [read_loan_item, item_id]]
            response = eval_and_respond(user_manage, funcs)
        elif request.method == "PUT":
            funcs = [check_token_and_set_session, [update_loan_item, item_id]]
            response = eval_and_respond(user_manage, funcs)
        else:  # DELETE:
            funcs = [check_token_and_set_session, [remove_loan_item, item_id]]
            response = eval_and_respond(user_manage, funcs)
    return response


@app.route("/mode", methods=["GET", "PUT"])
def mode():
    with UserManagement() as user_manage:
        if request.method == "GET":
            funcs = [check_token_and_set_session, get_mode]
            response = eval_and_respond(user_manage, funcs)
        else:   # PUT
            funcs = [check_token_and_set_session, change_mode]
            response = eval_and_respond(user_manage, funcs)
    return response


create_admin_user()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)