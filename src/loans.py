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

    def read(self, filter_offset_args):
        # TODO Do input validation on filter args
        entries = self._storage.get_filter_offset(**filter_offset_args)
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

    def get_filter_offset(self, loanedto=None, contains=None, limit=None, offset=None):
        query = self._db_session.query(LoanItem)
        if loanedto:
            query = query.filter(LoanItem.loanedto == loanedto)
        if contains:
            query = query.filter(LoanItem.description.ilike(f"%{contains}%"))
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        return query