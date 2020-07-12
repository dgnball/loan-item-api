from exceptions import (
    NotAllowedException,
    UnknownUserException,
    InitialAdminRoleException,
    UserAlreadyExistsException
)
from database import User, DBSession
from loans import Loans


initial_admin = "admin"


class UserManagement:
    def __enter__(self):
        self.db_session = DBSession()
        return Users(self.db_session)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.db_session.close()


class Users:

    # Functions used outside of a user session
    def __init__(self, db_session):
        self._storage = _Storage(db_session)
        self._current_user = None
        self._current_role = None
        self.Loans = Loans(db_session)

    def non_session_read(self, username):
        return self._storage.get(username)

    def set_user_session(self, username):
        user = self._storage.get(username)
        self._current_user = username
        self._current_role = user.role
        self.Loans.set_user_session(
            username, user.role, user.phone
        )

    def create_initial_admin(self, hashed_password):
        """Never exposed on the REST interface. Set via config at startup."""
        if not self._storage.get(initial_admin):
            user = User(
                username=initial_admin,
                hashed_password=hashed_password,
                role="admin",
                phone="+441234567890",
            )
            self._storage.create(user)

    def create(self, username, hashed_password, phone):
        user_orm = self._storage.get(username)
        if user_orm:
            raise UserAlreadyExistsException
        user = User(
            username=username,
            hashed_password=hashed_password,
            role="regular",
            phone=phone,
        )
        self._storage.create(user)
        return user

    # Functions used during a user session
    def read(self, username=None):
        self._modify_read_user_check(username)
        if username:
            user_dict = vars(self._storage.get(username))
            user_dict.pop("_sa_instance_state")
            user_dict.pop("hashed_password")
        else:
            user_dict = {}
            for user in self._storage.get_all():
                entry = vars(user)
                entry.pop("_sa_instance_state")
                entry.pop("hashed_password")
                user_dict[user.username] = entry
        return user_dict

    def remove(self, user_to_delete):
        if user_to_delete == initial_admin:
            raise InitialAdminRoleException
        self._modify_read_user_check(user_to_delete)
        self._storage.remove(user_to_delete)

    def update_password(self, user_to_change, hashed_password):
        self._modify_read_user_check(user_to_change)
        self._storage.update_field(user_to_change, "hashed_password", hashed_password)

    def update_role(self, user_to_change, new_role):
        if user_to_change == initial_admin:
            raise InitialAdminRoleException
        if self._current_role != "admin":
            raise NotAllowedException
        self._modify_read_user_check(user_to_change)
        self._storage.update_field(user_to_change, "role", new_role)

    def _modify_read_user_check(self, username=None):
        if not username:  # Means we are about to perform a global operation on the use table
            if self._current_role == "regular":
                raise NotAllowedException
            else:
                return
        user_to_access = self._storage.get(username)
        if not user_to_access:
            raise UnknownUserException
        if self._current_user != username:
            if self._current_role == "regular":
                raise NotAllowedException

    def update_phone(self, user_to_change, new_expected):
        self._modify_read_user_check(user_to_change)
        self._storage.update_field(
            user_to_change, "phone", new_expected
        )
        return self.read(user_to_change)


class _Storage:
    def __init__(self, db_session):
        self._db_session = db_session

    def remove(self, username):
        self._db_session.delete(self.get(username))
        self._db_session.commit()

    def create(self, user_obj):
        self._db_session.add(user_obj)
        self._db_session.commit()

    def get(self, username=None):
        return self._db_session.query(User).get(username)

    def get_all(self):
        return self._db_session.query(User)

    def update_field(self, username, field, value):
        user = self._db_session.query(User).filter_by(username=username).first()
        setattr(user, field, value)
        self._db_session.commit()
