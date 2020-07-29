from exceptions import NotAllowedException, UnknownLoanItemException, UnknownUserException
from database import LoanItem
from sqlalchemy import exc

class Loans:
    def __init__(self, db_session):
        self._storage = _Storage(db_session)
        self._current_user = None
        self._current_role = None
        self._phone = None

    def set_user_session(self, username, role, exp_cal_pd):
        self._current_user = username
        self._current_role = role
        self._phone = exp_cal_pd

    def create(self, item_id, description):
        if self._current_role != "admin":
            raise NotAllowedException

        loan_item = LoanItem(id=item_id, description=description)
        cal_dict = self._storage.create(loan_item).__dict__.copy()
        cal_dict.pop("_sa_instance_state")
        return cal_dict

    def remove(self, entry_id):
        entry = self._storage.get(entry_id)
        if not entry:
            raise UnknownLoanItemException
        if self._current_role != "admin":
            raise NotAllowedException
        self._storage.remove(entry_id)

    def read_single_entry(self, entry_id):
        entry = self._storage.get(entry_id)
        if not entry:
            raise UnknownLoanItemException
        if self._current_role != "admin":
            raise NotAllowedException
        entry_dict = vars(entry)
        entry_dict.pop("_sa_instance_state")
        return entry_dict

    def read(self, request_args):
        # TODO - ensure we only get combinations of things that work here
        if "loanedto" in request_args:
            entries = self._storage.get_by_username(request_args["loanedto"])
        elif "limit" in request_args:
            if "offset" in request_args:
                entries = self._storage.get_by_limit_and_offset(request_args["limit"], request_args["offset"])
            else:
                entries = self._storage.get_by_limit_and_offset(request_args["limit"], 0)
        elif "offset" in request_args:
            entries = self._storage.get_by_limit_and_offset(None, request_args["offset"])
        elif "contains" in request_args:
            entries = self._storage.get_by_description(request_args["contains"])
        else:
            entries = self._storage.get_all()
        ret_val = []
        for entry in entries:
            entry_dict = vars(entry)
            entry_dict.pop("_sa_instance_state")
            ret_val.append(entry_dict)
        return ret_val

    def update_loan(self, id, username):
        # TODO Do database connection pool
        if self._current_role != "admin":
            raise NotAllowedException
        entry = self._storage.get(id)
        if not entry:
            raise UnknownLoanItemException
        entry.loanedto = username
        try:
            self._storage.update()
        except exc.IntegrityError:
            raise UnknownUserException
        entry_dict = vars(entry)
        entry_dict.pop("_sa_instance_state")
        return entry_dict


class _Storage:
    def __init__(self, db_session):
        self._db_session = db_session

    def update(self):
        self._db_session.commit()

    def remove(self, entry_id):
        self._db_session.query(LoanItem).filter(LoanItem.id == entry_id).delete()
        self._db_session.commit()

    def create(self, cal_obj):
        self._db_session.add(cal_obj)
        self._db_session.commit()
        return self._db_session.query(LoanItem).get(cal_obj.id)

    def get(self, entry_id):
        return self._db_session.query(LoanItem).get(entry_id)

    def get_all(self):
        return self._db_session.query(LoanItem)

    def get_by_username(self, username):
        return self._db_session.query(LoanItem).filter(LoanItem.loanedto == username)

    def get_by_limit_and_offset(self, limit, offset):
        if limit:
            return self._db_session.query(LoanItem).limit(limit).offset(offset)
        else:
            return self._db_session.query(LoanItem).offset(offset)

    def get_by_description(self, partial):
        return self._db_session.query(LoanItem).filter(LoanItem.description.ilike(f"%{partial}%"))
