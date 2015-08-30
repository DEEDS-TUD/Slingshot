import logging
from slingshot.core.t_exceptions import FunctionNotInDB, SlingshotSQLException


class DbConnector(object):

    def __init__(self, database_connection):

        # connection to database
        self.db_con = database_connection

        # Get logger
        self.logger = logging.getLogger(__name__)

    def get_functions(self, function_record):
        """ Return all Functions from the function table.

        Args:
            function_record: namedtuple instance to represent a function.

        Returns:
            A list of named tuples where each tuple represents a function.
            Example:

            [ Function(
                id=235,
                name='wctomb',
                tcl='testcaselist',
                header='stdlib.h',
                number_of_parameters=2,
                c_types='char*, wchar_t',
                signature='wctomb-b_ptr_char-b_wchar',
                return_type='int'
              ),
              ...,
              (...),
            ]
        Raises:
            A SQL related exception.

        """
        connection_cursor = self.db_con.cursor()
        sql = ("SELECT ID, name, tcl, header, number_of_params, c_types,"
            " signature, return_val FROM function")
        try:
            connection_cursor.execute(sql)
            data = connection_cursor.fetchall()
            return [ function_record._make(fun_tuple) for fun_tuple in data]
        except:
            self.logger.error("Could not retrieve functions from Database")
            #TODO: Custom exception?
            raise

    def get_functions_with_results(self, function_record):
        """ Return all Functions from the function table.

        Args:
            function_record: namedtuple instance to represent a function.

        Returns:
            A list of named tuples where each tuple represents a function for
            which a experiment result exists.
            Example:

            [ Function(
                id=235,
                name='wctomb',
                header='stdlib.h',
                number_of_parameters=2,
                c_types='char*, wchar_t',
                signature='wctomb-b_ptr_char-b_wchar',
                return_type='int'
              ),
              ...,
              (...),
            ]
        Raises:
            A SQL related exception.

        """
        connection_cursor = self.db_con.cursor()
        fun_id_with_results_sql = ("SELECT f_ref from result group by f_ref")
        sql = ("SELECT ID, name, header, number_of_params, c_types,"
            " signature, return_val FROM function")
        try:
            connection_cursor.execute(fun_id_with_results_sql)
            funcs = connection_cursor.fetchall()
            connection_cursor.execute(sql)
            data = connection_cursor.fetchall()
            functions = [ function_record._make(fun_tuple) for fun_tuple in data]
            for fun in functions:
                if not (fun.id,) in funcs:
                    functions.remove(fun)
            return functions
        except:
            self.logger.error("Could not retrieve functions from Database")
            #TODO: Custom exception?
            raise

    def get_function_id(self, function_signature):
        """ Get the ID of a function from the database.

        The signature of a function uniquely identifies a function.

        """
        c = self.db_con.cursor()

        mysql = ("SELECT ID FROM function "
            "WHERE signature = '{0}'".format(function_signature))

        c.execute(mysql)
        data = c.fetchone()

        if not data:
            raise FunctionNotInDB("{0} is not in the "
                                  "database!".format(function_signature))

        return data[0]

    def get_function_id_num_param(self, function_signature):
        """ Get the ID of a function from the database.

        The signature of a function uniquely identifies a function.

        """
        c = self.db_con.cursor()

        mysql = ("SELECT ID, number_of_params FROM function "
            "WHERE signature = '{0}'".format(function_signature))

        c.execute(mysql)
        data = c.fetchone()

        if not data:
            raise FunctionNotInDB("{0} is not in the "
                                  "database!".format(function_signature))

        return data

    def get_setting_ids_for_tc(self, function_id, testcase_id):
        """ Retrieve a list of setting IDs for the specified testcase of the
        specified function """

        c = self.db_con.cursor()

        table_name = self.get_function_signature(function_id)

        mysql = "SELECT * FROM `{0}` WHERE ID = '{1}';".format(
                table_name, testcase_id)

        c.execute(mysql)
        data = c.fetchone()

        # only get the setting ids
        settings = data[1:]

        # foo(p1, p2) is in settings(p2, p1) so we reverse it back
        return settings[::-1]

    def get_setting_name(self, setting_id):
        """ Resolve a setting id into the setting name """

        c = self.db_con.cursor()

        sql = "SELECT name FROM setting WHERE ID={0}".format(setting_id)

        c.execute(sql)
        data = c.fetchone()

        return data[0]

    def get_testcases(self, table_name):
        """ Return testcases for table.

        Args:
            table_name: Name of table.

        Returns:
            A n_tuple of m-tuples. Where n is the number of testcases and m is
            the number of function parameters + 1. The inner m-tuple has as
            it's first entry the id of the testcase, the following entries are
            the id's of parameter settings starting with parameter 0.
            Example:
                ( (1, 2, 5, ), (2, 80, 19, ), (3, 40, 59, ), )

        Raises:
            A SQL related exception.

        """
        connection_cursor = self.db_con.cursor()
        sql = "SELECT * FROM `{0}`".format(table_name)
        try:
            connection_cursor.execute(sql)
            return connection_cursor.fetchall()
        except:
            self.logger.error("Could not execute query {}".format(sql))
            # TODO: raise exception
            raise

    def get_datatype_id(self, name):
        """ Retrieve the id of the given datatype."""
        connection_cursor = self.db_con.cursor()

        sql = ("SELECT ID FROM datatype WHERE name = {}".format(name))

        connection_cursor.execute(sql)
        data = connection_cursor.fetchone()
        return data[0]

    def get_datatype(self, setting_id):
        """ Retrieve a dict including datatype specific values for the
        specified setting ID. """

        c = self.db_con.cursor()

        mysql = ("SELECT * FROM datatype WHERE ID = (SELECT dt_ref FROM "
                 "setting WHERE ID = {})".format(setting_id))

        c.execute(mysql)
        data = c.fetchone()

        return {'id': data[0],  'name': data[1], 'type': data[2],
                'include': data[3], 'define': data[4] }

    def get_setting_id(self, datatype_id, setting_name):
        """ Retrieve a dict containing setting data for the specified
        setting ID. """

        connection_cursor = self.db_con.cursor()

        sql = ("SELECT ID FROM setting WHERE "
                "dt_ref = {dt_ref} AND name ="
                " {name}".format(dt_ref=datatype_id, name=setting_name))

        connection_cursor.execute(sql)
        data = connection_cursor.fetchone()
        return data[0]

    def get_setting(self, setting_id):
        """ Retrieve a dict containing setting data for the specified
        setting ID. """

        c = self.db_con.cursor()

        sql = "SELECT * FROM setting WHERE ID = {}".format(setting_id)

        c.execute(sql)
        data = c.fetchone()

        setting = {'id': data[0], 'name': data[1], 'code': data[2],
                'commit_code': data[3], 'cleanup_code': data[4],
                'dt_ref': data[5] }

        return setting

    def get_ctypes(self, function_id):
        """ Retrieve a list containing the C types for the parameters of this
        function """

        c = self.db_con.cursor()

        sql = "SELECT c_types FROM function WHERE ID={}".format(function_id)

        c.execute(sql)
        c_types_str = c.fetchone()
        #self.logger.debug("Retrieved {} c_types from DB!!"
                          #.format(c_types_str))

        c_types = c_types_str[0].split(',')
        #self.logger.debug("-> {}".format(c_types))

        return c_types

    def get_return_val(self, function_id):
        """ Retrieve the return type of this function. """

        c = self.db_con.cursor()

        sql = ("SELECT return_val FROM function WHERE"
               " ID={}".format(function_id))

        c.execute(sql)
        ret_t = c.fetchone()

        return ret_t[0]

    def get_testcase_ids(self, function_id):
        """ Retrieve a list of all testcases for the specified function. """

        c = self.db_con.cursor()

        table_name = self.get_function_signature(function_id)

        sql = "SELECT ID FROM `{0}`".format(table_name)

        c.execute(sql)
        tcs = c.fetchall()

        return tcs

    def add_testcase_to_signature_table(self, signature, settings):
        connection_cursor = self.db_con.cursor()

        sql = "INSERT INTO `{signature}` "
        parameter = "("
        values = ""
        for position, setting_id in enumerate(settings):
            parameter += "parameter_{pos}, ".format(pos=position)
            values += "{id}, ".format(id=setting_id)
        # remove ', ' of last entry
        parameter = parameter[:-2] + ") VALUES ("
        values = values[:-2] + ")"

        sql += parameter + values
        try:
            connection_cursor.execute(sql)
            connection_cursor.commit()
        except:
            connection_cursor.rollback()
            # TODO: raise exception
            raise Exception('HELL')

    def create_signature_table(self, function_id, function_signature,
            num_of_params):
        connection_cursor = self.db_con.cursor()

        sql = ("CREATE TABLE `{signature}` (ID INT NOT NULL "
                "AUTO_INCREMENT,".format(function_signature))
        param_def = ""
        for pos in xrange(num_of_params):
            param_def += " parameter_{position} INT NOT NULL, ".format(
                    position=pos)
        # Remove ', ' of last param_def
        param_def = param_def[:-2]
        sql += param_def + ")"

        try:
            connection_cursor.execute(sql)
        except Exception as e:
            raise SlingshotSQLException(e)

    def get_function_name(self, function_id):
        """ Retrieve the name of the specified function """

        c = self.db_con.cursor()

        sql = "SELECT name FROM function WHERE ID={0}".format(function_id)

        c.execute(sql)
        function_name = c.fetchone()

        return function_name[0]

    def get_function_signature(self, function_id):
        """ Retrieve the signature of the specified function """

        c = self.db_con.cursor()

        sql = "SELECT signature FROM function WHERE ID={0}".format(function_id)

        c.execute(sql)
        function_signature = c.fetchone()
        #self.logger.debug("-> {}".format(function_name))

        return function_signature[0]

    def get_function_header(self, function_id):
        """ Retrieve name of header file where function with ID function_id is
        specified. """

        c = self.db_con.cursor()

        sql = "SELECT header FROM function WHERE ID={0}".format(function_id)

        c.execute(sql)
        function_header = c.fetchone()

        return function_header[0]

    def get_failure_name(self, failure_id):
        """ Get failure name for a given failure id """

        c = self.db_con.cursor()

        sql = "SELECT name FROM failures WHERE ID='{}'".format(failure_id)

        c.execute(sql)
        f_id = c.fetchone()

        return f_id[0]

    def get_failure_id(self, failure_name):
        """ Get failure ID for a given failure """

        c = self.db_con.cursor()

        sql = "SELECT ID FROM failures WHERE name='{}'".format(failure_name)

        c.execute(sql)
        f_id = c.fetchone()

        return f_id[0]

    def get_failure_names(self):
        """ Get names of all defined failures """

        c = self.db_con.cursor()

        sql = "SELECT name FROM failures"

        c.execute(sql)
        failure_names = c.fetchall()

        f_n = []
        for n in failure_names:
            f_n.append(n[0])

        return f_n

    def set_result(self, function_id, testcase_id, failure_id, tcl):
        """ Store result of testcase execution in DB. """

        c = self.db_con.cursor()

        sql = ("INSERT INTO result (f_ref, tc_ref, fail_ref, tcl) VALUES"
               " ({0}, {1}, {2}, '{3}')".format(function_id, testcase_id,
                   failure_id, tcl))

        c.execute(sql)
        c.connection.commit()

    def get_result(self, function_id, testcase_id):
        """ Return the failure id for a testcase """
        c = self.db_con.cursor()

        sql = ("SELECT fail_ref FROM result WHERE f_ref"
                " = {0} AND tc_ref = {1}".format(function_id, testcase_id))

        c.execute(sql)
        failure_ref = c.fetchone()
        if failure_ref is None:
            raise Exception

        return failure_ref[0]

    def get_number_of_parameters(self, function_id):
        """ Return the number of parameters for the function specified by
        function_id. """

        c = self.db_con.cursor()

        sql = ("SELECT number_of_params FROM function WHERE ID={0}".format(
            function_id))

        c.execute(sql)
        num_params = c.fetchone()

        return num_params[0]

    def add_function_to_testcases(self, function_id):
        """ Add the given function id to the testcase table. """
        c = self.db_con.cursor()
        sql = ("INSERT INTO testcases (f_ref) VALUES ({function_id})".
                format(function_id=function_id))

        c.execute(sql)
        c.connection.commit()
