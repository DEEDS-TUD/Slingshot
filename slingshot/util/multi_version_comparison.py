""" python script to create testcase lists for a combined result database.

The assumed database contains the combination of multiple slingshot result
sets. For each tested function a table with the name of the function signature
is assumed. Such a table contains columns which store information for the
parameters of the function, i.e. for each parameter the name of the type in the
type hierarchy and the according dial name, as well as columns for the
different operating system (OS) versions under which the function was tested.
Such an version column holds the result of the testcase.

The script analyzes all experiment results for testcases with
different results on different OS versions. If differences are found testcase
lists are created for the appropriate OS versions.

"""
import MySQLdb
import optparse
import re

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


def _flatten_data_all(data):
    """ Return data retrieved by MySQLdb queries as a flat list.

    Args:
        data: Data retrieved by a fetchall call

    Return:
        A flat list with the data.

        Example:

        data = ( (foo,), (bar,))
        _flatter_data_all(data)
        >>> [ foo, bar ]

    """
    return [entry[0] for entry in data]


def _get_table_names(db_connection):
    """ Get name of database tables.

    Args:
        db_connection: Connection object to the database.

    Return:
        A list of table names

    """
    cursor = db_connection.cursor()
    cursor.execute("SHOW TABLES")
    data = cursor.fetchall()
    cursor.close()
    return _flatten_data_all(data)


def _get_table_header(table, db_connection, db_name):
    """ Get column names of the table. The list of the column names is the
    header of the table.

    Args:
        table: name of table
        db_connection: Connection object to the database.

    Return:
        Header of the table as a list

    """
    cursor = db_connection.cursor()
    sql = ("SELECT COLUMN_NAME FROM information_schema.COLUMNS"
            " WHERE TABLE_NAME='{}' AND TABLE_SCHEMA='{}'".format(
                table, db_name))
    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()
    return _flatten_data_all(data)


def _get_table_results(columns, table, db_connection):
    """ Get rows for the given columns of the given table.

    Args:
        columns: pre formated column names
        table: table name
        db_connection: Connection object to the database.

    Return:
        The rows of the table as a list. Each row itself is a list of values.

    """
    cursor = db_connection.cursor()
    sql = ("SELECT " + columns + "FROM `{}`".format(table))
    cursor.execute(sql)
    data = cursor.fetchall()
    return [list(row) for row in data]


def results_differ_between_versions(version_result_mapping):
    """ Return True if the results for one testcase differ between versions.

    Args:
        version_result_mapping: A dictionary in which the result is the key to
        a list of versions.

    Return:
        True if the testcase produced different results on different versions,
        False otherwise.

    """
    return len(version_result_mapping.keys()) > 1


def _map_results_to_versions(result, table_header):
    """ Create a result to versions mapping.

    Args:
        result: data values which correspond to the columns given in
            the table_header
        table_header: list of column names

    Returns:
        A dictionary which is indexed by the result code to yield a list of OS
        versions under which the result was obtained. If one OS version has no
        result None is returned instead of a dictionary.

        Example:

        {2L: ['06.10_result', '07.04_result', '07.10_result', '08.04_result',
            '08.10_result', '09.04_result', '09.10_result', '10.04_result',
            '10.10_result', '11.04_result', '11.10_result'],
        3L: ['12.04_result', '12.10_result', '13.04_result', '13.10_result']}

    """
    version_dict = defaultdict(list)
    for i, column_name in enumerate(table_header):
        # ignore parameter related columns
        if column_name.startswith('p'):
            continue
        # Check if a none is detected
        if result[i] == None:
            return None
        else:
            version_dict[result[i]].append(column_name)
    return version_dict


def _map_column_names_to_row_entries(result, table_header):
    """ Create a column names to row entries mapping.

    Args:
        result: data values which correspond to the columns given in
            the table_header
        table_header: list of column names

    Returns:
        A dictionary which is indexed by the column name and yields the value
        from the corresponding row.

        Example:

            {'p0_type': 'b_int', '07.04_result': 7L, 'p0': 'MAXINT',
            '13.10_result': 7L, '06.10_result': 7L, '12.10_result': 7L,
            '08.10_result': 7L, '11.04_result': 7L, '11.10_result': 7L,
            '13.04_result': 7L, '09.10_result': 7L, '12.04_result': 7L,
            '07.10_result': 7L, '08.04_result': 7L, '09.04_result': 7L,
            '10.10_result': 7L, '10.04_result': 7L}

    """
    column_dict = dict()
    for i, column_name in enumerate(table_header):
        column_dict[column_name] = result[i]
    return column_dict


def find_version_boundaries(version_dict, ordering):
    """ Return a list of versions which are boundaries.

    Args:
        version_dict: dictionary

    Returns:
        A list of versions

    """
    versions_boundaries = set()
    for _, version_list in version_dict.iteritems():
        version_list = sorted(version_list)
        _add_start_and_end_of_list_if_boundary(versions_boundaries,
                version_list, ordering,)
        last_version = version_list[0]
        for version in version_list[1:]:
            _add_if_boundary(versions_boundaries, last_version, version,
                    ordering)
            last_version = version
    return versions_boundaries

def _add_if_boundary(versions_boundaries, last_version, version, ordering):
    """ Add last_version and version to versions_boundaries if a boundary is
    found.

    Args:
        versions_boundaries: set to which boundaries are added
        last_version, version: versions between which boundaries are checked
        ordering: ordered list of all versions

    """
    if not _continuous(last_version, version, ordering):
        versions_boundaries.add(last_version)
        versions_boundaries.add(version)

def _add_start_and_end_of_list_if_boundary(versions_boundaries, version_list, ordering):
    """ Check if first and last elements in a list are boundaries and add them
    to the boundary set.

    Args:
        version_list: sorted list of versions
        ordering: sorted list of all versions
        versions_boundaries: set to which boundaries are added

    """
    first_in_list = version_list[0]
    last_in_list = version_list[-1]
    if len(version_list) == 1:
        versions_boundaries.add(first_in_list)
        return
    if first_in_list != ordering[0]:
        versions_boundaries.add(first_in_list)
    if last_in_list != ordering[-1]:
        versions_boundaries.add(last_in_list)

def _continuous(last_version, version, ordering):
    """ Check if transition from last version to actual version is continuous.

    Args:
        last_version: last version
        version: version
        ordering: ordered list

    Returns:
        True if the transition is continuous False otherwise.
    """
    ord_idx = ordering.index(last_version)
    if ordering[ord_idx+1] != version:
        return False
    return True


def process_differences(table_header, results, function_signature):
    """ Print out a notice if a testcase produced different results in
    different OS versions.

    Args:
        table_header: list of column names
        results: list of lists, the inner lists contain data entries
            corresponding to the column names given in table_header
        function_signature: signature of the function

    """
    version_ordering = [ '06.10_result', '07.04_result', '07.10_result',
            '08.04_result', '08.10_result', '09.04_result', '09.10_result',
            '10.04_result', '10.10_result', '11.04_result', '11.10_result',
            '12.04_result', '12.10_result', '13.04_result', '13.10_result',]
    none_count = 0
    for testcase_results in results:
        version_dict = _map_results_to_versions(testcase_results, table_header)
        if not version_dict:
            none_count += 1
            continue
        if not results_differ_between_versions(version_dict):
            continue
        # the testcase results differ between versions
        versions = find_version_boundaries(version_dict, version_ordering)
        column_name_mapping = _map_column_names_to_row_entries(testcase_results,
                table_header)
        write_testcase_lists(versions, function_signature,
                column_name_mapping)
    print("None count: {}".format(none_count))


def write_testcase_lists(versions, function_signature, column_name_mapping):
    """ Write testcase to the testcase lists of the given versions.

    Args:
        versions: list of versions to which the testcase should be added
        function_signature: function signature
        column_name_mapping: dictionary representing a testcase

    """
    testcase_string = _get_tc_string(function_signature, column_name_mapping)
    for version_testcase_list in versions:
        with open(version_testcase_list + '.tcl', 'a+') as tcl:
            tcl.write(testcase_string)
            tcl.write('\n')


def _get_tc_string(function_signature, column_name_mapping):
    """ Create a testcase string.

    Args:
        function_signature: function signature
        column_name_mapping: dictionary representing a testcase

    Returns:
        A string representing the given testcase.

    """
    signature = _format_signature(function_signature)
    parameters = _get_parameter_and_dial_string(column_name_mapping)
    return signature + parameters


def _get_parameter_and_dial_string(column_name_mapping):
    """ Extract parameter type and dials from a testcase.

    Args:
        testcase: Dictionary representing a testcase. The description of the
        field is the key to its value.

    Returns:
        A string formated such that for each parameter the type is listed
        before the chosen dial. Parameters are separated by a semicolon.

        Example:
        _get_parameter_and_dials({'p1_type': 'b_ptr_char',
                                'p0': 'BUF_MED',
                                'p0_type' : 'b_ptr_buf',
                                'p1' : 'AT',
                                '08.10_result' : '7L'})
        >> ' b_ptr_buf (BUF_MED); b_ptr_char (AT)'
    """
    type_dict, dial_dict = _get_type_and_dial_dicts(column_name_mapping)
    parameter_string = ' '
    for parameter_number in xrange(0, len(type_dict)):
        parameter_string += type_dict[str(parameter_number)] + ' ('
        parameter_string += dial_dict[str(parameter_number)] + '); '
    return parameter_string[:-2]


def _get_type_and_dial_dicts(column_name_mapping):
    """ Create dictionaries for parameter types and dials.

    Args:
        column_name_mapping: A dictionary representation of a testcase.

    Return:
        A tuple of dictionaries. Both dictionaries are indexed by the parameter
        number. The first dictionary is the type dict, it yields the type of
        the parameter. The second dictionary is the dial dict which yields the
        dial of the parameter.

    """
    param_number_pattern = re.compile('.*(\d+).*')
    type_pattern = re.compile('.*type')
    type_dict = dict()
    dial_dict = dict()
    for column_name in column_name_mapping.keys():
        if not column_name.startswith('p'):
            continue
        parameter_number = param_number_pattern.match(column_name).group(1)
        type_match = type_pattern.match(column_name)
        if type_match:
            type_dict[parameter_number] = column_name_mapping[column_name]
        else:
            dial_dict[parameter_number] = column_name_mapping[column_name]
    return type_dict, dial_dict


def _format_signature(function_signature):
    """ Format the function signature.

    Args:
        function_signature: the function signature as a string where elements
        are separated by a dash.

    Returns:
        A string containing the formated function signature where elements are
        separated by spaces.

    """
    return ' '.join(function_signature.split('-')) + ';'


def generate_testcase_lists_for_different_results(table_name,
        db_connection, db_name):
    """ Create testcase lists for the different versions if a result change can
    be detected on a version boundary.

    Args:
        table: name of the table which is processed
        db_connection: Connection object to the database.
        db_name: name of the used database

    """
    table_header = _get_table_header(table_name, db_connection, db_name)
    column_string = "`" + "`, `".join(table_header) + "`"
    table_results = _get_table_results(column_string, table_name, db_connection)
    process_differences(table_header, table_results, table_name)


def analyse_tables(tables, db_connection, db_name):
    """ Analyze the given tables in the database.

    Args:
        tables: list of table names.
        db_connection: Connection object to the database.
        db_name: name of the database to analyze.

    """
    for table_name in tables:
        print("Process table: {}".format(table_name))
        generate_testcase_lists_for_different_results(table_name, db_connection,
                db_name)


def main():
    """ Main function. Is executed when the script is run. """
    opts = parse_arguments()
    db_connection = MySQLdb.connect(host=opts.db_host, user=opts.db_user,
                passwd=opts.db_passwd, db=opts.db_name)
    db_connection.autocommit(True)
    tables = _get_table_names(db_connection)
    analyse_tables(tables, db_connection, opts.db_name)


if __name__ == '__main__':
    main()
