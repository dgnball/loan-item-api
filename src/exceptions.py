class NotAllowedException(Exception):
    pass

class CannotDeleteLoadedItem(Exception):
    pass



class UnknownUserException(Exception):
    pass


class UnknownLoanItemException(Exception):
    pass


class InitialAdminRoleException(Exception):
    pass


class InvalidTokenException(Exception):
    pass


class InvalidRequestException(Exception):
    pass


class UserAlreadyExistsException(Exception):
    pass
