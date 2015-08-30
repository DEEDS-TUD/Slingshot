from testcase import Testcase


class TcFactory(object):
    """ Create a new testcase """

    def __init__(self, work_dir):
        self.work_dir = work_dir

    def create_testcase(self, function, testcase_id, settings):
        """ Create a instance of a testcase.

        Args:
            function: Function which is loaded as a named Function tuple.
            testcase_id: Id of the testcase in the functions signature table.
            settings: list of setting objects

        Returns:
            An Testcase instance.

        """
        return Testcase(testcase_id, function.name,
                settings, self.work_dir, function.c_types.split(','), function.return_type, function.header)
