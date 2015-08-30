class XMLNotValid(Exception):
    """XML is not valid against shema"""
    pass


class FunctionNotInDB(Exception):
    """Function is not in the database"""
    pass


class SlingshotSQLException(Exception):
    """ An exception occured while executing an sql statement """
    pass
