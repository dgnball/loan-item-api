import unittest
import requests
import json
import os


class TestLoanItemApi(unittest.TestCase):
    def test_get_own_user(self):
        body, code = self.get(f"/users/{bob}", bob)
        self.assertEqual(200, code)
        self.assertEqual(
            {
                "username": "bob",
                "role": "regular",
                "phone": "+441234567890",
            },
            body["user"],
        )

    def test_register_twice(self):
        """Check we can only register a user once."""
        body, code = self.post(f"/users", bob, {"phone": "+441234567890", **bob_creds})
        self.assertEqual(400, code)
        self.assertEqual({"error": "User already exists."}, body)

    def test_bad_register(self):
        """Fail gracefully when we post a user missing information (phone)."""
        body, code = self.post(f"/users", bob, bob_creds)
        self.assertEqual(400, code)
        self.assertEqual({"error": "Invalid request."}, body)

    def test_change_pasword(self):
        body, code = self.put(f"/users/{bob}", bob, {"password": "password2"})
        self.assertEqual(200, code)
        self.assertEqual({"message": "Password successfully changed."}, body)

        body, code = self.post(
            f"/login", data={"username": bob, "password": "password2"}
        )
        self.assertEqual(200, code)
        self.bob_token = body["auth_token"]

        body, code = self.post(f"/login", data=bob_creds)
        self.assertEqual(401, code)
        self.assertEqual({"error": "Wrong username or password."}, body)

        body, code = self.put(f"/users/{bob}", bob, {"password": "password"})
        self.assertEqual(200, code)
        self.assertEqual({"message": "Password successfully changed."}, body)

    def test_change_role(self):
        # Create a loan item and check Bob can't loan it to himself
        self.post("/loan-items", admin, self.make_loan_item("1", "wheelbarrow"))
        body, code = self.put(f"/loan-items/1", bob, {"loaned-to": "bob"})
        self.assertEqual(403, code)
        self.assertEqual({"error": "Not authorized."}, body)

        # Check Bob can't make himself an admin
        body, code = self.put(f"/users/{bob}", bob, {"role": "admin"})
        self.assertEqual(403, code)
        self.assertEqual({"error": "Not authorized."}, body)

        # User the admin user to make Bob an admin and check he can then loan an item to himself
        _, code = self.put(f"/users/{bob}", admin, {"role": "admin"})
        self.assertEqual(200, code)
        _, code = self.put(f"/loan-items/1", bob, {"loaned-to": "bob"})
        self.assertEqual(200, code)

    def test_delete_user(self):
        body, code = self.delete(f"/users/{bob}", bob)
        self.assertEqual(200, code, body.get("error", ""))
        self.assertEqual({"message": "User successfully deleted."}, body)

        body, code = self.post(f"/login", data=bob_creds)
        self.assertEqual(401, code, body.get("error", ""))
        self.assertEqual({"error": "Wrong username or password."}, body)

    def setUp(self) -> None:
        self.bob_token = None
        self.admin_token = None
        self.sally_token = None

        #  use admin user to remove all users (apart from admin) and Loans
        body, code = self.get("/users", admin)
        self.assertEqual(200, code, body.get("error", ""))
        for user in body["users"]:
            if user != "admin":
                body, code = self.delete(f"/users/{user}", admin)
                self.assertEqual(200, code, body.get("error", ""))
        body, code = self.get("/loan-items", admin)
        self.assertEqual(200, code, body.get("error", ""))
        for Loan_id in body["Loans"]:
            body, code = self.delete(f"/loan-items/{Loan_id}", admin)
            self.assertEqual(200, code, body.get("error", ""))

        # Confirm Bob and Sally no longer exist then re-add them
        body, code = self.get("/users", admin)
        self.assertEqual(200, code, body.get("error", ""))
        self.assertNotIn(bob, body["users"])
        self.assertNotIn(sally, body["users"])
        body, code = self.post("/users", data={"phone": "+441234567890", **bob_creds})
        self.assertEqual(200, code, body.get("error", ""))
        body, code = self.post("/users", data={"phone": "+441234567890", **sally_creds})
        self.assertEqual(200, code, body.get("error", ""))

        # Double check Bob and Sally do exist now
        body, code = self.get("/users", admin)
        self.assertEqual(200, code, body.get("error", ""))
        self.assertIn(bob, body["users"])
        self.assertIn(bob, body["users"])
        self.current_Loan_counter = bob

    def login(self, user):
        if user == bob:
            token = self.bob_token
            creds = bob_creds
        elif user == admin:
            token = self.admin_token
            creds = admin_creds
        elif user == sally:
            token = self.sally_token
            creds = sally_creds
        else:
            self.fail()

        if not token:
            response = requests.post(url_root + "/login", json=creds)
            token = json.loads(response.content)["auth_token"]
            if user == bob:
                self.bob_token = token
            elif user == admin:
                self.admin_token = token
            else:
                self.sally_token = token
        return token

    def get(self, url, user):
        """Login if no auth tokens, then run get."""
        token = self.login(user)
        response = requests.get(url_root + url, headers={"access-token": token})
        return response.json(), response.status_code

    def post(self, url, user=None, data=None):
        """Login if no auth tokens, then run post."""
        if user:
            token = self.login(user)
            response = requests.post(
                url_root + url, headers={"access-token": token}, json=data
            )
        else:
            response = requests.post(url_root + url, json=data)
        return response.json(), response.status_code

    def delete(self, url, user):
        """Login if no auth tokens, then run delete."""
        token = self.login(user)
        response = requests.delete(url_root + url, headers={"access-token": token})
        return response.json(), response.status_code

    def put(self, url, user, data):
        """Login if no auth tokens, then run post."""
        token = self.login(user)
        response = requests.put(
            url_root + url, headers={"access-token": token}, json=data
        )
        return response.json(), response.status_code

    def make_loan_item(self, item_id, description):
        return { "id": item_id, "description": description}


admin = "admin"
bob = "bob"
sally = "sally"
bob_creds = {"username": bob, "password": "password"}
sally_creds = {"username": sally, "password": "cats"}
admin_creds = {"username": admin, "password": "admin"}
url_root = "http://127.0.0.1:5000"