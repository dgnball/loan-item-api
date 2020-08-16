from flask_testing import TestCase
import app


class TestLoanItemApi(TestCase):
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

    def test_check_invalid_user_put(self):
        # Check we can't change the password and phone number at the same time.
        body, code = self.put(f"/users/{bob}", bob, {"password": "password2", "phone": "+441234567891"})
        self.assertEqual(400, code)
        self.assertEqual({"error": "Invalid request."}, body)

        # Check we can't input an invalid phone number
        body, code = self.put(f"/users/{bob}", bob, {"phone": "+1"})
        self.assertEqual(400, code)
        self.assertEqual({"error": "Invalid request."}, body)
        body, code = self.put(f"/users/{bob}", bob, {"phone": "a"})
        self.assertEqual(400, code)
        self.assertEqual({"error": "Invalid request."}, body)

        # Check we can't set an invalid role
        body, code = self.put(f"/users/{bob}", bob, {"role": "banana"})
        self.assertEqual(400, code)
        self.assertEqual({"error": "Invalid request."}, body)

    def test_check_user_change_phone(self):
        # Check we can't change the password and phone number at the same time.
        body, _ = self.put(f"/users/{bob}", bob, {"phone": "+441234567891"})
        expected = {"username": bob, "role": "regular", "phone": "+441234567891"}
        self.assertEqual(expected, body["user"])
        body, _ = self.get(f"/users/{bob}", bob)
        self.assertEqual(expected, body["user"])

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
        body, code = self.put(f"/loan-items/1", bob, {"loanedto": "bob"})
        self.assertEqual(403, code)
        self.assertEqual({"error": "Not authorized."}, body)

        # Check Bob can't make himself an admin
        body, code = self.put(f"/users/{bob}", bob, {"role": "admin"})
        self.assertEqual(403, code)
        self.assertEqual({"error": "Not authorized."}, body)

        # User the admin user to make Bob an admin and check he can then loan an item to himself
        _, code = self.put(f"/users/{bob}", admin, {"role": "admin"})
        self.assertEqual(200, code)
        _, code = self.put(f"/loan-items/1", bob, {"loanedto": "bob"})
        self.assertEqual(200, code)

    def test_delete_user(self):
        body, code = self.delete(f"/users/{bob}", bob)
        self.assertEqual(200, code, body.get("error", ""))
        self.assertEqual({
            "message": "User successfully deleted.",
            "user": {"phone": "+441234567890", "role": "regular", "username": "bob"}
        }, body)

        body, code = self.post(f"/login", data=bob_creds)
        self.assertEqual(401, code, body.get("error", ""))
        self.assertEqual({"error": "Wrong username or password."}, body)

    def test_url_params_input_validation(self):
        body, code = self.get("/loan-items?limite=5", admin)
        self.assertEqual(400, code, body.get("error", ""))
        self.assertEqual({"error": "Invalid request."}, body)

    def test_pagination_and_filter(self):
        self.post("/loan-items", admin, {"id": "01", "description": "wheelbarrow"})
        self.post("/loan-items", admin, {"id": "02", "description": "drill"})
        self.post("/loan-items", admin, {"id": "03", "description": "digger"})
        self.post("/loan-items", admin, {"id": "04", "description": "carpet cleaner"})
        self.post("/loan-items", admin, {"id": "05", "description": "floor sander"})
        self.post("/loan-items", admin, {"id": "06", "description": "orbital sander"})
        self.post("/loan-items", admin, {"id": "07", "description": "pressure washer"})
        self.post("/loan-items", admin, {"id": "08", "description": "nail gun"})
        self.post("/loan-items", admin, {"id": "09", "description": "impact wrench"})
        self.post("/loan-items", admin, {"id": "10", "description": "air conditioner"})
        self.post("/loan-items", admin, {"id": "11", "description": "fan"})

        body, _ = self.get("/loan-items?limit=5&offset=5", admin)
        expected = [
            {"id": "06", "loanedto": None, "description": "orbital sander"},
            {"id": "07", "loanedto": None, "description": "pressure washer"},
            {"id": "08", "loanedto": None, "description": "nail gun"},
            {"id": "09", "loanedto": None, "description": "impact wrench"},
            {"id": "10", "loanedto": None, "description": "air conditioner"}
        ]
        self.assertEqual(expected, body["loan-items"])

        body, _ = self.get("/loan-items?limit=2", admin)
        expected = [
            {"id": "01", "loanedto": None, "description": "wheelbarrow"},
            {"id": "02", "loanedto": None, "description": "drill"}
        ]
        self.assertEqual(expected, body["loan-items"])

        body, _ = self.get("/loan-items?offset=09", admin)
        expected = [
            {"id": "10", "loanedto": None, "description": "air conditioner"},
            {"id": "11", "loanedto": None, "description": "fan"}
        ]
        self.assertEqual(expected, body["loan-items"])

        body, code = self.get("/loan-items?contains=sander", admin)
        expected = [
            {"id": "05", "loanedto": None, "description": "floor sander"},
            {"id": "06", "loanedto": None, "description": "orbital sander"}
        ]
        self.assertEqual(200, code, body.get("error", ""))
        self.assertEqual(expected, body["loan-items"])

        body, code = self.get("/loan-items?contains=sander&limit=1", admin)
        expected = [
            {"id": "05", "loanedto": None, "description": "floor sander"}
        ]
        self.assertEqual(200, code, body.get("error", ""))
        self.assertEqual(expected, body["loan-items"])

        body, code = self.get("/loan-items?contains=sander&limit=1&offset=1", admin)
        expected = [
            {"id": "06", "loanedto": None, "description": "orbital sander"}
        ]
        self.assertEqual(200, code, body.get("error", ""))
        self.assertEqual(expected, body["loan-items"])

    def test_loaning(self):
        self.post("/loan-items", admin, {"id": "01", "description": "wheelbarrow"})
        self.post("/loan-items", admin, {"id": "02", "description": "drill"})
        self.post("/loan-items", admin, {"id": "03", "description": "digger"})
        self.post("/loan-items", admin, {"id": "04", "description": "carpet cleaner"})
        self.post("/loan-items", admin, {"id": "05", "description": "floor sander"})
        self.post("/loan-items", admin, {"id": "06", "description": "orbital sander"})
        self.post("/loan-items", admin, {"id": "07", "description": "pressure washer"})
        self.post("/loan-items", admin, {"id": "08", "description": "nail gun"})
        self.post("/loan-items", admin, {"id": "09", "description": "impact wrench"})
        self.post("/loan-items", admin, {"id": "10", "description": "air conditioner"})
        self.post("/loan-items", admin, {"id": "11", "description": "fan"})

        self.put("/loan-items/07", admin, {"loanedto": "bob"})
        self.put("/loan-items/10", admin, {"loanedto": "bob"})
        self.put("/loan-items/11", admin, {"loanedto": "bob"})

        body, _ = self.get("/loan-items?loanedto=bob", admin)
        expected = [
            {"id": "07", "loanedto": bob, "description": "pressure washer"},
            {"id": "10", "loanedto": bob, "description": "air conditioner"},
            {"id": "11", "loanedto": bob, "description": "fan"}
        ]
        self.assertEqual(expected, body["loan-items"])

        body, _ = self.get("/loan-items?loanedto=bob&limit=1&offset=1", admin)
        expected = [
            {"id": "10", "loanedto": bob, "description": "air conditioner"}
        ]
        self.assertEqual(expected, body["loan-items"])

        body, _ = self.get("/loan-items?loanedto=bob&contains=n", admin)
        expected = [
            {"id": "10", "loanedto": bob, "description": "air conditioner"},
            {"id": "11", "loanedto": bob, "description": "fan"}
        ]
        self.assertEqual(expected, body["loan-items"])

        body, _ = self.get("/loan-items?loanedto=bob&contains=n&limit=1", admin)
        expected = [
            {"id": "10", "loanedto": bob, "description": "air conditioner"}
        ]
        self.assertEqual(expected, body["loan-items"])

        body, _ = self.get("/loan-items?loanedto=bob&contains=n&limit=1&offset=1", admin)
        expected = [
            {"id": "11", "loanedto": bob, "description": "fan"}
        ]
        self.assertEqual(expected, body["loan-items"])

        # Try loaning to a non-existant user
        body, code = self.put("/loan-items/07", admin, {"loanedto": "steve"})
        self.assertEqual(404, code)
        self.assertEqual({"error": "User not found."}, body)

    def test_deleting_loan_items(self):
        self.post("/loan-items", admin, {"id": "07", "description": "pressure washer"})
        self.post("/loan-items", admin, {"id": "08", "description": "nail gun"})

        self.put("/loan-items/07", admin, {"loanedto": "bob"})

        body, code = self.delete("/loan-items/07", admin)
        self.assertEqual(403, code)
        expected = {"error": "Cannot delete loan item that is loaned."}
        self.assertEqual(expected, body)

        body, code = self.delete("/loan-items/08", admin)
        self.assertEqual(200, code)
        expected = {
            "loan-item": {"id": "08", "loanedto": None, "description": "nail gun"},
            "message": "Loan item successfully deleted."
        }
        self.assertEqual(expected, body)


    def setUp(self) -> None:
        self.bob_token = None
        self.admin_token = None
        self.sally_token = None

        #  use admin user to remove all users (apart from admin) and Loans
        body, code = self.get("/loan-items", admin)
        self.assertEqual(200, code, body.get("error", ""))
        for loan_item in body["loan-items"]:
            body, code = self.put(f"/loan-items/{loan_item['id']}", admin, {"loanedto": None})
            self.assertEqual(200, code, body.get("error", ""))
            body, code = self.delete(f"/loan-items/{loan_item['id']}", admin)
            self.assertEqual(200, code, body.get("error", ""))
        body, code = self.get("/users", admin)
        self.assertEqual(200, code, body.get("error", ""))
        for user in body["users"]:
            if user != admin:
                body, code = self.delete(f"/users/{user}", admin)
                self.assertEqual(200, code, body.get("error", ""))
        # Confirm Bob no longer exist then re-add him
        body, code = self.get("/users", admin)
        self.assertEqual(200, code, body.get("error", ""))
        self.assertNotIn(bob, body["users"])
        body, code = self.post("/users", data={"phone": "+441234567890", **bob_creds})
        self.assertEqual(200, code, body.get("error", ""))

        # Double check Bob exists now
        body, code = self.get("/users", admin)
        self.assertEqual(200, code, body.get("error", ""))
        self.assertIn(bob, body["users"])
        self.assertIn(bob, body["users"])
        self.current_Loan_counter = bob

    def login(self, user):
        token = None
        creds = bob_creds if user == bob else admin_creds
        if user == bob and self.bob_token:
            token = self.bob_token
        elif user == admin and self.admin_token:
            token = self.admin_token

        if not token:
            response = self.client.post("/login", json=creds)
            token = response.json["auth_token"]
            if user == bob:
                self.bob_token = token
            else:
                self.admin_token = token
        return token

    def get(self, url, user):
        """Login if no auth tokens, then run get."""
        token = self.login(user)
        response = self.client.get(url, headers={"access-token": token})
        return response.json, response.status_code

    def delete(self, url, user):
        """Login if no auth tokens, then run delete."""
        token = self.login(user)
        response = self.client.delete(url, headers={"access-token": token})
        return response.json, response.status_code

    def post(self, url, user=None, data=None):
        """Login if no auth tokens, then run post."""
        if user:
            token = self.login(user)
            response = self.client.post(url, headers={"access-token": token}, json=data)
        else:
            response = self.client.post(url, json=data)
        self.assertIsNotNone(response.json, response.status_code)
        return response.json, response.status_code

    def put(self, url, user, data):
        """Login if no auth tokens, then run post."""
        token = self.login(user)
        response = self.client.put(url, headers={"access-token": token}, json=data)
        return response.json, response.status_code

    def create_app(self):
        return app.app

    def make_loan_item(self, item_id, description):
        return { "id": item_id, "description": description}


admin = "admin"
bob = "bob"
bob_creds = {"username": bob, "password": "password"}
admin_creds = {"username": admin, "password": "admin"}
