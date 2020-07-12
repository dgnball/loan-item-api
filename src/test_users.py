import unittest

from users import Users
from exceptions import NotAllowedException, UnknownUserException
import database

BOB = "bob"
ALICE = "alice"
ADMIN = "admin"
PASSWORD_1 = "hash1"
PASSWORD_2 = "hash2"


class TestUsers(unittest.TestCase):
    def setUp(self) -> None:
        self.db_session = database.get_db_session()
        self.users = Users(self.db_session)
        self.users.create_initial_admin(PASSWORD_1)
        self.users.create(BOB, PASSWORD_1, "+441234567890")
        self.users.create(ALICE, PASSWORD_1, "+441234567890")

    def tearDown(self):
        self.db_session.close()
        database.recreate_db()

    def test_read_user(self):
        actual = self.read(BOB, BOB)
        expected = {
            "username": BOB,
            "role": "regular",
            "phone": "+441234567890",
        }
        self.assertEqual(expected, actual)

    def test_read_all_users(self):
        actual = self.read(ADMIN)
        expected = {
            BOB: {
                "username": BOB,
                "role": "regular",
                "phone": "+441234567890",
            },
            ALICE: {
                "username": ALICE,
                "role": "regular",
                "phone": "+441234567890",
            },
            ADMIN: {
                "username": ADMIN,
                "role": "admin",
                "phone": "+441234567890",
            },
        }
        self.assertEqual(expected, actual)

    def test_remove_user(self):
        self.remove(BOB, BOB)
        self.assertRaises(UnknownUserException, self.users.read, BOB)

    def test_update_user(self):
        self.update_password(BOB, BOB, PASSWORD_2)
        expected = {
            "username": BOB,
            "role": "regular",
            "phone": "+441234567890",
        }
        actual = self.read(BOB, BOB)
        self.assertEqual(expected, actual)
        user_obj = self.users.non_session_read(BOB)
        self.assertEqual(BOB, user_obj.username)
        self.assertEqual(PASSWORD_2, user_obj.hashed_password)

    def test_read_regular_user(self):
        self.assertRaises(NotAllowedException, self.read, ALICE, BOB)
        self.read(ADMIN, BOB)

    def test_read_admin(self):
        # First make ALICE an ADMIN user
        self.update_role(ADMIN, ALICE, "admin")

        self.assertRaises(NotAllowedException, self.read, BOB, ADMIN)
        self.read(ALICE, ADMIN)

    def test_remove_regular_user(self):
        self.assertRaises(NotAllowedException, self.read, ALICE, BOB)
        self.remove(ADMIN, ALICE)

    def test_change_regular_user_password(self):
        self.assertRaises(
            NotAllowedException, self.update_password, ALICE, BOB, PASSWORD_2
        )
        self.update_password(ADMIN, BOB, PASSWORD_2)

    def update_role(self, logged_in_user, user_to_change, new_role):
        """Helper function."""
        self.users.set_user_session(logged_in_user)
        self.users.update_role(user_to_change, new_role)

    def update_password(self, logged_in_user, user_to_change, hashed_password):
        """Helper function."""
        self.users.set_user_session(logged_in_user)
        self.users.update_password(user_to_change, hashed_password)

    def read(self, logged_in_user, username=None):
        """Helper function."""
        self.users.set_user_session(logged_in_user)
        return self.users.read(username)

    def remove(self, logged_in_user, username):
        """Helper function."""
        self.users.set_user_session(logged_in_user)
        return self.users.remove(username)
