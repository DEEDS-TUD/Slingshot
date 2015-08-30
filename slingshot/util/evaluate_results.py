""" Evaluates the database """
import MySQLdb
import optparse
# matplotlib is not compiling on jaunty so don't use it
#import matplotlib.mlab as mlab
#import matplotlib.pyplot as plt
import numpy as np
import operator

from collections import namedtuple, defaultdict
from slingshot.db.db_connector import DbConnector

FAILURES = ['ABORT', 'ABORT_DUMPED', 'STOPPED', 'RESTART']

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
    (opts, _) = parser.parse_args()
    return opts


def get_failure_classes(db_connection):
    """ Receive the error classification from the database.

    Args:
        db_connection: Connection object to the database.

    Returns:
        A dictionary, in which the error number is the key into the dictionary
        and the value is the name of the error.

    """
    connection_cursor = db_connection.cursor()
    sql = "SELECT * from failures;"
    connection_cursor.execute(sql)
    data = connection_cursor.fetchall()
    return dict(data)


def get_function_results(function_id, db_connection):
    """ Receive results for a function from the database.

    Args:
        db_connection: Connection object to the database.

    Returns:
        A dictionary, in which the error number is the key into the dictionary
        and the value is the number of occurences of this error.

    """
    connection_cursor = db_connection.cursor()
    sql = ("SELECT fail_ref, count(*) FROM result"
            " where f_ref = '{}' GROUP BY fail_ref".format(function_id))
    connection_cursor.execute(sql)
    data = connection_cursor.fetchall()
    initialised_data = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}
    if data:
        for failure_set in data:
            fail_ref, occurence = failure_set
            initialised_data[fail_ref] = occurence
        return initialised_data
    else:
        return {}


def get_failure_rates(per_function):
    """ Get failure rates for all functions.

    Args:
        per_function: Dictionary in which the function signature is the key to
        the result dictionary for a function.

    Returns:
        A tuple with two elements. The first element is a dictionary which
        holds the failure rate for each function, in which the function
        signature is the key into the dict. The second element is the number of
        functions for which no testcases have been executed (all testcases
        where either SETUP or COMPILE)

    """
    failure_rate_per_function = {}
    not_tested_functs = []
    for fun_sig, result in per_function.iteritems():
        testcases_in_function = sum(result.values())
        setup_failure_rate = result['SETUP'] / float(testcases_in_function)
        if 'COMPILE' in result:
            compile_failure_rate = result['COMPILE'] / float(testcases_in_function)
            testcases_in_function_which_executed = testcases_in_function - result['SETUP'] - result['COMPILE']
        else:
            testcases_in_function_which_executed = testcases_in_function - result['SETUP']
        # There can be functions for which all testcases could not be compiled
        if not testcases_in_function_which_executed:
            not_tested_functs.append(fun_sig)
            continue
        abort_failures = result['ABORT'] + result['ABORT_DUMPED']
        abort_failure_rate = abort_failures / float(testcases_in_function_which_executed)
        restart_failure_rate = result['RESTART'] / float(testcases_in_function_which_executed)
        stopped_failure_rate = result['STOPPED'] / float(testcases_in_function_which_executed)
        pass_failure_rate = result['PASS'] / float(testcases_in_function_which_executed)
        setup_failure_rate = result['SETUP'] / float(testcases_in_function_which_executed)
        function_overall_failure_rate = abort_failure_rate + restart_failure_rate + stopped_failure_rate
        failure_rate_per_function[fun_sig] = function_overall_failure_rate
    return failure_rate_per_function, not_tested_functs


def get_results(functions, failure_classes, db_connection):
    """ Get results from database.

    Args:
        functions:
        failure_classes:
        db_connection: Connection object to the database.

    Returns:
        A tuple with two elements.
            The first element is a dictionary which contains for each function
            a dictionary with the failures of this function, by failure class.

            The second element is a dictionary which contains the overall
            observed failures indexed by the failure class.

    """
    all_fail_by_class = defaultdict(int)
    all_func_fail_by_class = {}
    for function in functions:
        func_fail_by_class = {}
        function_results = get_function_results(function.id, db_connection)
        for fail_id, occurence in function_results.iteritems():
            func_fail_by_class[failure_classes[fail_id]] = occurence
            all_fail_by_class[failure_classes[fail_id]] += occurence
        if function_results:
            all_func_fail_by_class[function.signature] = func_fail_by_class
    return all_func_fail_by_class, all_fail_by_class


def get_statistics(functions, failure_classes, db_connection):
    """Get statistics on test results.

    Args:
        functions: 
        failure_classes:
        db_connection: Connection object to the database.

    Returns:
        A dictionary containing statistics over all testcases. I.e:
        'num_tc': Number of testcases (sum of testcases of all functions)
        'not_tested_functs': number of functions which could not be tested (all
                                SETUP or COMPILE)
        'fail_rate_per_fun': dictionary which is indexed with the function
                                signature and yields the failure rate of the
                                function
        'avg_fail_rate': Average failure rate of over all functions
        'std_fail_rate': Standard deviation  of the failure rate over all functions

    """
    all_function_failures_by_failure_class, overall_failures_by_failure_class = get_results(
            functions, failure_classes, db_connection)

    fail_rate_per_function, not_tested_functs = get_failure_rates(
            all_function_failures_by_failure_class)

    statistics = {
        'num_tc': sum(overall_failures_by_failure_class.values()),
        'not_tested_functs': not_tested_functs,
        'fail_rate_per_fun': fail_rate_per_function,
        'avg_fail_rate': np.average(fail_rate_per_function
            .values()),
        'std_fail_rate': np.std(fail_rate_per_function
            .values()),
        }
    return statistics


def partition_on_avg(statistics):
    """docstring for partition_on_avg"""
    higher_than_avg_fail_rate = {}
    higher_than_avg_fail_rate_high_part = {}
    lower_than_avg_fail_rate_high_part = {}
    lower_eq_than_avg_fail_rate = {}
    no_failures = []
    all_failures = []
    for f_sig, fail_rate in statistics['fail_rate_per_fun'].iteritems():
        if fail_rate > statistics['avg_fail_rate']:
            higher_than_avg_fail_rate[f_sig] = fail_rate
            if fail_rate == 1.0:
                all_failures.append(f_sig)
        elif fail_rate == 0:
            no_failures.append(f_sig)
        else:
            lower_eq_than_avg_fail_rate[f_sig] = fail_rate

    fun_with_failures = higher_than_avg_fail_rate.copy()
    fun_with_failures.update(lower_eq_than_avg_fail_rate)
    print("avg {}, std {} of functions with failures".format(
        np.average(fun_with_failures.values()),
        np.std(fun_with_failures.values()),
        ))
    high_avg = np.average(higher_than_avg_fail_rate.values())
    for f_sig, fail_rate in higher_than_avg_fail_rate.iteritems():
        if fail_rate > high_avg:
            higher_than_avg_fail_rate_high_part[f_sig] = fail_rate
        else:
            lower_than_avg_fail_rate_high_part[f_sig] = fail_rate

    print("{num_no} functions have no robustness failures\n"
            "{num_all} functions have a failure rate of 0.1:\n"
            "{fail_all}\n"
            "{num_high} functions have a failure rate higher than average\n"
            "\tThe average failure rate of these functions is {avg_high} with"
            " an standard deviation of {std_dev_high} \n"
            "\t\t{num_high_high} functions have a failure rate higher than average\n"
            "\t\t\tThe average failure rate of these functions is {avg_high_high} with"
            " an standard deviation of {std_dev_high_high} \n"
            "\t\t{num_high_low} functions have a failure rate lower than average\n"
            "\t\t\tThe average failure rate of these functions is {avg_high_low} with"
            " an standard deviation of {std_dev_high_low} \n"
            "{num_low} functions have a failure rate lower average\n"
            "\tThe average failure rate of these functions is {avg_low} with"
            " an standard deviation of {std_dev_low} \n".format(
                num_no=len(no_failures),
                num_all=len(all_failures),
                fail_all=all_failures,
                num_high=len(higher_than_avg_fail_rate.values()),
                avg_high=high_avg,
                std_dev_high=np.std(higher_than_avg_fail_rate.values()),
                num_high_high=len(higher_than_avg_fail_rate_high_part.values()),
                avg_high_high=np.average(higher_than_avg_fail_rate_high_part.values()),
                std_dev_high_high=np.std(higher_than_avg_fail_rate_high_part.values()),
                num_high_low=len(lower_than_avg_fail_rate_high_part.values()),
                avg_high_low=np.average(lower_than_avg_fail_rate_high_part.values()),
                std_dev_high_low=np.std(lower_than_avg_fail_rate_high_part.values()),
                num_low=len(lower_eq_than_avg_fail_rate.values()),
                avg_low=np.average(lower_eq_than_avg_fail_rate.values()),
                std_dev_low=np.std(lower_eq_than_avg_fail_rate.values()),
                ))

def write_statistics(statistics):
    with open('slingshot_results.txt', 'w') as f:
        for f_sig, fail_rate in statistics['fail_rate_per_fun'].iteritems():
            f.write("{}\t{:.4}\n".format(f_sig.split('-')[0], fail_rate*100))


def main():
    """ Main function. Is executed when the script is run. """
    opts = parse_arguments()
    db_connection = MySQLdb.connect(host=opts.db_host, user=opts.db_user,
                passwd=opts.db_passwd, db=opts.db_name)
    db = DbConnector(db_connection)
    function_records = namedtuple('Function', ['id', 'name', 'header',
        'number_of_parameters', 'c_types', 'signature', 'return_type'])
    failure_classes = get_failure_classes(db_connection)
    if not failure_classes.has_key(424242):
        failure_classes[424242] = 'COMPILE'

    functions = db.get_functions_with_results(function_records)
    statistics = get_statistics(functions, failure_classes, db_connection)

    partition_on_avg(statistics)
    print statistics['avg_fail_rate']
    print statistics['std_fail_rate']

    write_statistics(statistics)

if __name__ == '__main__':
    main()
