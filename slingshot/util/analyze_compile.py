import MySQLdb
import optparse

from collections import namedtuple
from collections import defaultdict


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


def _get_compile_failures(db_connection):
    """ Get compile failures from result.

    Args:
        db_connection: Connection object to the database.

    Returns:
        Something
    """
    cursor = db_connection.cursor()

    sql = """ SELECT * from result WHERE fail_ref = 424242"""

    cursor.execute(sql)
    data = cursor.fetchall()
    return data


def _get_id_signature_mapping(db_connection):
    """ Get mapping of id to signature for all functions.

    Args:
        db_connection: Connection object to the database.

    Returns:
        A mapping dictionary in which the function id is the index to the
        signature.
    """
    cursor = db_connection.cursor()
    sql = """ Select id, signature from function """
    cursor.execute(sql)
    data = cursor.fetchall()
    mapping = dict(data)
    return mapping


def _get_settings(db_connection, signature, tc_ref):
    """Get settings for this testcase from setting table.

    Args:
        db_connection: Connection object to the database.
        signature: table name
        tc_ref: reference to entry

    Returns:
        A tuple of setting_ids.

    """
    cursor = db_connection.cursor()
    sql = """ SELECT * FROM `{signature}` WHERE ID = {tc_ref}""".format(
            signature=signature, tc_ref=tc_ref)
    cursor.execute(sql)
    data = cursor.fetchone()
    return list(data)[1:]


def get_parameter_entry(db_connection, setting_id):
    cursor = db_connection.cursor()
    sql = """ SELECT setting.name, datatype.name FROM setting
        INNER JOIN datatype ON setting.dt_ref = datatype.id 
        WHERE setting.id = {}""".format(setting_id)
    cursor.execute(sql)
    setting_name, dt_name = cursor.fetchone()
    return dt_name, setting_name


def write_tcl(db_connection, signature, testcases):
    with open(signature + '.tcs', 'a') as tcl:
        for tc in testcases:
            tcl.write("{};".format(' '.join(signature.split('-'))))
            parameter_string = ""
            for setting_id in tc:
                datatype_name, setting_name = get_parameter_entry(db_connection, setting_id)
                parameter_string += " {} ({});".format(datatype_name, ' '.join(setting_name.split('-')))
            tcl.write("{}".format(parameter_string[:-1]))
            tcl.write("\n")

def main():
    """ Main function. Is executed when the script is run. """
    opts = parse_arguments()
    db_connection = MySQLdb.connect(host=opts.db_host, user=opts.db_user,
                passwd=opts.db_passwd, db=opts.db_name)
    compile_failures_db = _get_compile_failures(db_connection)
    compile_failure_record = namedtuple('CompileFailure', ['id', 'f_ref',
        'tc_ref', 'fail_ref',])
    compile_failures = [ compile_failure_record._make(com_tuple) for com_tuple
            in compile_failures_db]
    id_to_signature_mapping = _get_id_signature_mapping(db_connection)
    per_signature = defaultdict(list)
    for failure in compile_failures:
        signature = id_to_signature_mapping[failure.f_ref]
        per_signature[signature].append(_get_settings(db_connection, signature,
            failure.tc_ref))

    for testcase_list in per_signature.keys():
        print("Write tcl for {}.tcs".format(testcase_list))
        write_tcl(db_connection, testcase_list, per_signature[testcase_list])


if __name__ == '__main__':
    main()
