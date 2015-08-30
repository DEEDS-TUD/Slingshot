#!/usr/bin/python
from collections import namedtuple
import os
import optparse
from operator import itemgetter
import sys
import re
import random
import logging
import logging.config
import MySQLdb
from loader import CtLoader
from t_exceptions import FunctionNotInDB
from t_exceptions import XMLNotValid
from tc_generator import TcGenerator
from util import get_path
from detector import Detector
from testcase_factory import TcFactory
from setting_factory import SettingFactory
from ..db.db_connector import DbConnector


def parse_arguments():
    """ Specify and parse options for slingshot. """
    parser = optparse.OptionParser()

    parser.add_option('-u', '--user', dest='db_user', default='slingshot',
            help='db user')
    parser.add_option('-p', '--password', dest='db_passwd', default='slingshot',
            help='password to access db for user')
    parser.add_option('-s', '--server', dest='db_host', default='localhost',
            help='server on which db runs')
    parser.add_option('-d', '--database', dest='db_name', default='slingshot',
            help='database to use')
    parser.add_option('-w', '--work_directory', dest='work_dir', default='tmp',
            help='Directory to work in')
    parser.add_option('-t', '--timeout', dest='timeout', default=10000,
            help='Timeout how long the detector should wait before detecting'
            ' a hang')
    (opts, _) = parser.parse_args()
    return opts


def run_batch(detector, logger, function_id, tc_batch, tcl):
    """ Run all testcases in the given batch."""
    for testcase in tc_batch:
        logger.info("Running detector for testcase {0} of"
                " function {1}".format(testcase.get_id(), function_id))
        detector.run_testcase(function_id, testcase, tcl)


def test_function(tcg, detector, logger, function, do_cleanup=True):
    """ Run testcases for a function.

    Args:
        tcg: testcase generator instance.
        detector: detector instance.
        logger: logger instance.
        function: A namedtuple representing a function.
        do_cleanup: Boolean flag. Specifies if all generated files are deleted
            after the test run. Defaults to True, delete them.

    """
    tcg.load_function(function)
    while tcg.testcases_left():
        tc_batch = tcg.generate()
        run_batch(detector, logger, function.id, tc_batch, function.tcl)
        if do_cleanup:
            tcg.cleanup_batch(tc_batch)
    # After the function is tested we need to delete it's settings!
    if do_cleanup:
        tcg.cleanup_settings()


def main():
    """ Execute the test suite. """

    # Create a logger and load its config
    logging.config.fileConfig(get_path('bin/logging.conf'))
    logger = logging.getLogger(__name__)

    # parse options
    opts = parse_arguments()
    work_dir = os.path.join(os.getcwd(), opts.work_dir)
    db_connection = MySQLdb.connect(host=opts.db_host, user=opts.db_user,
                passwd=opts.db_passwd, db=opts.db_name)
    db_connection.autocommit(True)

    # Create work directory
    if not os.path.exists(work_dir):
        logger.info("Create a directory to work in.")
        os.makedirs(work_dir)

    db = DbConnector(db_connection)
    tc_factory = TcFactory(work_dir)
    s_factory = SettingFactory(db)
    tcg = TcGenerator(db, tc_factory, s_factory, work_dir, batch_size=4)
    detector = Detector(db, work_dir, timeout=opts.timeout)

    function_records = namedtuple('Function', ['id', 'name', 'tcl', 'header',
        'number_of_parameters', 'c_types', 'signature', 'return_type'])
    functions = db.get_functions(function_records)
    for function in functions:
        test_function(tcg, detector, logger, function, do_cleanup=True)
