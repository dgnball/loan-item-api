import unittest

from loans import Loans
from exceptions import NotAllowedException
import database

BOB = "bob"
ALICE = "alice"


class TestLoans(unittest.TestCase):
    def setUp(self) -> None:
        self.db_session = database.get_db_session()
        database.recreate_db()
        self.Loans = Loans(self.db_session)
        self.args = ["1", "wheelbarrow"]

    def tearDown(self):
        self.db_session.close()

    def create(self, username, role, *args, **kwargs):
        """Helper function."""
        self.Loans.set_user_session(username, role, "+441234567890")
        return self.Loans.create(*args, **kwargs)

    def read(self, username, role, *args, **kwargs):
        """Helper function."""
        self.Loans.set_user_session(username, role, "+441234567890")
        return self.Loans.read(*args, **kwargs)

    def remove(self, username, role, entry_id):
        """Helper function."""
        self.Loans.set_user_session(username, role, "+441234567890")
        return self.Loans.remove(entry_id)

    def test_create_with_other_users(self):
        self.assertRaises(
            NotAllowedException, self.create, ALICE, "regular", *self.args
        )
        self.create(ALICE, "admin", *self.args)
