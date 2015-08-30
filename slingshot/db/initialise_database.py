""" Initialise the database for use with slingshot. """
import glob
import itertools
import logging
import logging.config
import multiprocessing
import MySQLdb
import optparse
import os
import re
from bs4 import BeautifulSoup
from collections import defaultdict
from operator import itemgetter

from slingshot.core.util import get_path

TYPE_MAPPING = {}
logging.config.fileConfig(get_path('bin/logging.conf'))
logger = logging.getLogger(__name__)


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
    parser.add_option('-c', '--callTable', dest='call_table',
            default='bin/call_table.xml', help='calltable to use')
    parser.add_option('-m', '--type_mapping', dest='type_mapping',
            default='bin/type_mapping', help='type mapping to use')
    parser.add_option('-f', '--data_type_path', dest='data_type_path',
            default='bin/dataTypes', help='path to data type definition files')
    parser.add_option('-t', '--testcase_list', dest='testcase_list',
            help='List of testcases to execute')
    (opts, _) = parser.parse_args()
    return opts


def _create_function_signature(line):
    """ Create a function signature string from the given line.

    Args:
        line: Line from which the signature string is read.

    Returns:
        The function signature as a string. The signature string is constructed
        as follows 'function_name-parameter_type_1-parameter_type_n.

    """
    # Split line in a list, first entry is the name, the following entries
    # consist of the datatype used and a dial setting
    splitted_line = line.strip().split(';')
    # get function name
    function_signature_block = splitted_line.pop(0)
    function_parameter_list = function_signature_block.split(' ')
    function_name = function_parameter_list.pop(0)
    parameter_list = [ param for param in function_parameter_list ]
    return _build_signature_string(function_name, parameter_list)


def read_testcaselist(testcaselist_descriptor):
    """ Parse testcaselist for function signatures.

    Args:
        testcaselist_descriptor: File descriptor of the testcaselist.

    Returns:
        A list of all function_signatures which are found in the testcaselist.

    """
    function_signatures = []
    for line in testcaselist_descriptor:
        function_signature = _create_function_signature(line)
        if function_signature and not function_signature in function_signatures:
            function_signatures.append(function_signature)
    return function_signatures


def read_functions(call_table_descriptor, testcase_list):
    """ Parse call table for function signatures.

    Args:
        call_table_descriptor: File descriptor to the call_table.

    Returns:
        A list of dictionaries. Each dictionary represents a function record.

        Example:
            [ {'name': 'function_name',
                'header': 'foobar.h',
                'return': 'int',
                'parameter': ['b_ptr_char', 'b_int'],
                'parameter_c_types': ['*char', 'int']
                'signature': 'function_name-b_ptr_char-b_int',
                } ]

    """
    tcl_name = os.path.basename(testcase_list)
    soup = BeautifulSoup(call_table_descriptor, 'xml')
    return [create_function_record(function, tcl_name) for function in
            soup.find_all('function')]


def create_function_record(function, tcl_name):
    """ Create function record.

    Args:
        function: BeautifulSoup object representing a function.

    Returns:
        A dictionary representing a function record.

        Example:
            {'name': 'function_name',
            'header': 'foobar.h',
            'return': 'int',
            'parameter': ['b_ptr_char', 'b_int'],
            'parameter_c_types': ['*char', 'int']
            'signature': 'function_name-b_ptr_char-b_int',
            }

    """
    function_dict = {}
    function_dict['name'] = function.find('name').string
    function_dict['tcl'] = tcl_name
    function_dict['header'] = function.find('header').string
    function_dict['return'] = function.find('return').string
    # Bs4 uses unicode so we have to convert it to str for dict use
    function_dict['parameter']  = [str(param.string) for param in
        function.findAll('param')]
    function_dict['parameter_c_types'] = [get_ctype(parameter)
            for parameter in function_dict['parameter']]
    function_dict['signature'] = _build_signature_string(function_dict['name'],
            function_dict['parameter'])
    return function_dict


def get_ctype(b_type):
    """ Lookup c type for given type.

    Args:
        b_type: Name of the type to lookup.

    Returns:
        A string representing the C type matching the given b_type name.

    """
    return TYPE_MAPPING[b_type]


def _build_signature_string(name, parameter):
    """ Build the function signature string.

    The function signature string consists of the following:
      - The name of the function.
      - The name of the function parameters.
    The function name and each of the parameters are separated by an
    minus (-).
    I.E. the signature string of the function getcwd(b_ptr_char, b_int) would be
    getcwd-ptr_char-int.

    """
    signature_string = name + '-'
    signature_string += '-'.join(parameter)
    return signature_string


def read_mapping(type_mapping_descriptor):
    """ Read type mapping.

    Args:
        type_mapping_descriptor: File descriptor to the mapping file.

    Returns:
        A dictionary mapping C types to b_types.

    """
    return dict(line.strip().split(None, 1) for line in type_mapping_descriptor)


def parse_datatype_specification(dt_descriptor, dt_includes):
    """ Parse the given xml and create a dictionary.

    Args:
        dt_descriptor: File descriptor of a datatype xml file.

    Returns:
        All datatype specific information in a dictionary

    """
    dt_soup = BeautifulSoup(dt_descriptor, 'xml')
    dt_dict = {}
    dt_dict['name'] = dt_soup.find('name').string.strip()
    dt_dict['parent'] = dt_soup.find('parent').string.strip()
    dt_dict['type'] = dt_soup.find('dt_type').string.strip()
    dt_dict['include'] = dt_includes[dt_dict['name'] + '.xml']
    def_block = dt_soup.find('defines').find('block')
    if def_block:
        dt_dict['defines'] = def_block.string.strip()
    else:
        dt_dict['defines'] = ""
    return dt_dict


def write_datatype_to_database(datatype, db_connection):
    """ Write the datatype record to database.

    Args:
        datatype: Record of the datatype which is written
        db_connection: Connection object to the database

    Returns:
        The ID of the inserted record.

    """
    cursor = db_connection.cursor()
    cursor.execute("""INSERT INTO datatype (name, type, include, define)
            VALUES(%s, %s, %s, %s)""", (datatype['name'], datatype['type'],
                datatype['include'], datatype['defines']))
    return cursor.lastrowid


def parse_datatype_dialgroups(dt_soup):
    """ Extract dial_groups and their order.

    Args:
        dt_soup: BeautifulSoup object representing a datatype xml file

    Returns:
        A tuple in which the first element contains the order of the dial
        groups as a list and the second element contains a dictionary
        representing all dial_groups. In the dial_groups dictionary the dial
        group name is the key to a list of dials.

    """
    dial_group = defaultdict(list)
    dial_group_soup = dt_soup.find('dial_groups')
    if dial_group_soup.has_attr('order'):
        order = dial_group_soup['order'].split(';')
    for group in dial_group_soup.find_all('group'):
        dial_group[group['name']] = [ dial.string.strip() for dial in
                group.find_all('dial')]
    return order, dial_group


def _parse_block(block_soup, dial_list):
    """ Parse code from block entries in soup for dials.

    Args:
        block_soup: BeautifulSoup object in which the dials are searched.
        dial_list: A list of dial names.

    Returns:
        A string holding all code blocks without a dial name as well as code
        blocks for which the name attribute matches a name in the provided dial
        list. The blocks added sequentially to the code string.

    """
    code = ""
    for block in block_soup.find_all('block'):
        # Add code of unnamed blocks and code of blocks in the dial list
        if not block.has_attr('dials'):
            code += block.string
        else:
            dials = block['dials'].split(',')
            for dial in dials:
                if dial.strip() in dial_list:
                    code += block.string
                    break
    return code


def parse_datatype_settings(datatype_descriptor, dt_ref):
    """ Parse the given datatype for setting data.

    Args:
        datatype_descriptor: File descriptor to the datatype xml file
        dt_ref: ID referencing the datatype entry in the database to which the
            settings belong.

    Returns:
        A list of tuples in which each tuple represents a setting. The first
        entry in the list corresponds to the first setting. A setting tuple
        contains the elements "name, access-code, commit-code, cleanup-code,
        dt_ref" in this order.

    """
    dt_soup = BeautifulSoup(datatype_descriptor, 'xml')
    access_soup = dt_soup.find('access')
    commit_soup = dt_soup.find('commit')
    cleanup_soup = dt_soup.find('cleanup')
    group_order, dial_groups = parse_datatype_dialgroups(dt_soup)
    all_dials = (dial_groups[group] for group in group_order)
    dial_kombinations = (list(dial_names)
            for dial_names in itertools.product(*all_dials))
    return [ ( '__'.join(dial_list),
        _parse_block(access_soup, dial_list),
        _parse_block(commit_soup, dial_list),
        _parse_block(cleanup_soup, dial_list),
        dt_ref) for dial_list in dial_kombinations]


def write_settings_to_database(settings, db_connection):
    """ Write settings to database.

    Args:
        settings: List of setting tuples which are written to the database
        db_connection: Connection object to the database.

    """
    cursor = db_connection.cursor()

    cursor.executemany("""INSERT INTO setting (name, code, commit_code,
    cleanup_code, dt_ref) VALUES(%s, %s, %s, %s, %s)""", settings)
    return cursor.lastrowid


def write_function_to_database(function, db_connection):
    """ Write a function to the database.

    Args:
        function: A dictionary representing the function. The keys, 'name',
            'parameter', 'parameter_c_types', 'signature' and 'return' have to
            be present.
        db_connection: Connection object to the database.

    """
    cursor = db_connection.cursor()

    cursor.execute("""INSERT INTO function
            (name, tcl, header, number_of_params, c_types, signature, return_val)
            VALUES (%s, %s, %s, %s, %s, %s, %s)""", (function['name'],
            function['tcl'],
            function['header'],
            len(function['parameter']),
            ', '.join(function['parameter_c_types']),
            function['signature'],
            function['return'],
            ))


def process_datatype(dt_xml_file, db_connection, dt_includes, cache):
    """ Parse datatype file and write content to the database.

    Args:
        dt_xml_file: Path to the xml datatype definition which should be
            processed.
        db_connection: Connection object to the database
        cache: A nested dictionary which enables fast lookup of setting ids
            when indexed with datatype name and setting name. This argument
            serves although as a return for the cache.

    Returns:
        Returns through the argument cache. See description above.

    """
    with open(dt_xml_file, 'r') as dt_descriptor:
        file_name = os.path.basename(dt_xml_file).split('.')[0]
        datatype_record = parse_datatype_specification(dt_descriptor,
                dt_includes)
        dt_ref = write_datatype_to_database(datatype_record, db_connection)
        dt_descriptor.seek(0)
        settings = parse_datatype_settings(dt_descriptor, dt_ref)
    start_id = write_settings_to_database(settings, db_connection)
    # Fill the cache
    cache[file_name] = {s_name[0]: s_id for s_id, s_name in
            enumerate(settings, start=start_id)}

def remove_duplicates(dt_dict):
    """ Remove duplicate includes.

    Args:
        dt_dict: A dictionary

    Returns:
        A dictionary where the value string doesn't contain duplicated lines.

    """
    for key, value in dt_dict.items():
        lines = value.split('\n')
        dt_dict[key] = '\n'.join(list(set(lines)))
    return dt_dict

def _get_inc(file_name, no_include_extracted, include_dict):
    base_name = os.path.basename(file_name)
    with open(file_name, 'r') as dt_descriptor:
        soup = BeautifulSoup(dt_descriptor, 'xml')
        parent = soup.find('parent').string.strip()
        parent_name = get_path('bin/dataTypes/' + parent + '.xml')
        if not parent == 'paramAccess' or parent_name in no_include_extracted:
            if parent_name in no_include_extracted:
                no_include_extracted.remove(parent_name)
            _get_inc(parent_name, no_include_extracted, include_dict)
        inc_soup = soup.find('include')
        include_string = ""
        if inc_soup:
            inc = inc_soup.find('block')
            if inc:
                include_str = inc.string
                prog = re.compile('#include "(b_.*|bTypes.h)"', re.MULTILINE)
                include_string = re.sub(prog, '', include_str)
        if parent == 'paramAccess':
            include_dict[base_name] = include_string
        else:
            include_dict[base_name] = include_dict[
                    parent + '.xml'] + include_string


def get_includes(data_type_path):
    """ Get include entries for all datatypes.

    Args:
        data_type_path: Path to the directory which is scanned for xml files

    Returns:
        A dictionary in which the file_name serves as a key. The value is a
        string containing the includes of the file and all it's parents.

    """
    include_dict = {}
    no_include_extracted = glob.glob(os.path.join(data_type_path,"*.xml"))
    while no_include_extracted:
        dt_xml_file = no_include_extracted.pop()
        _get_inc(dt_xml_file, no_include_extracted, include_dict)
    return include_dict


def add_datatypes_and_settings_to_db(data_type_path, db_connection,
        dt_includes, out_q):
    """ Add all datatype xml definitions which can be found to the database.

    Args:
        data_type_path: Path to the directory which is scanned for xml files

        db_connection: Database connections which is used to write datatype
        definitions and settings.

        out_q: A Queue which transports the cache dictionary back to the
            creator of the Process which called this function. The cache
            dictionary enables lookup of a setting id through, first keying in
            with the name of the datatype and than with the setting name.

    Returns:
        Returns through the argument out_q. See description above

    """
    cache = defaultdict(dict)
    file_names = glob.glob(os.path.join(data_type_path,"*.xml"))
    file_names.sort()
    for dt_xml_file in file_names:
        file_name = os.path.basename(dt_xml_file)
        logger.info("Add datatype and settings for file {}".format(file_name))
        process_datatype(dt_xml_file, db_connection, dt_includes, cache)
    out_q.put(cache)


def add_functions_to_database(call_table, db_connection, testcase_list=None):
    """ Add functions to the database.

    All functions which are specified in the call_table as well as in the
    testcase_list are added. If no testcase_list is given all functions in the
    call_table are added.

    Args:
        call_table: Path to XML call_table
        db_connection: Connection object to the database
        testcase_list: Path to a testcase_list. Defaults to None

    """
    with open(call_table, 'r') as call_table:
        function_list = read_functions(call_table, testcase_list)
    with open(testcase_list, 'r') as testcaselist:
        function_signatures_to_test = read_testcaselist(testcaselist)

    for signature in function_signatures_to_test:
        for function in function_list:
            if signature == function['signature']:
                if signature == 'map-b_ptr_void-b_unsigned_long-b_prot_flag-b_map_flag-b_fd-b_int':
                    function['name'] = 'mmap'
                logger.info("Add function {} to database".
                            format(signature))
                write_function_to_database(function, db_connection)


def get_function_signatures(db_connection):
    """ Get all function signatures.

    Args:
        db_connection: Connection object to the database.

    Returns:
        A list of tuples. Each tuple contains a function signature string.

    """
    connction_cursor = db_connection.cursor()

    sql = "SELECT signature from function;"
    connction_cursor.execute(sql)
    return list(connction_cursor.fetchall())


def _get_setting_name(parameter):
    """ Construct setting name from parameter.

    Args:
        parameter: A string from which the setting name is extracted.

    Returns:
        A string representing the setting name for the provided parameter.

    """
    plist = parameter.split(' ', 1)
    # remove type name
    del plist[0]
    params = plist[0]
    # remove braces
    params = re.sub('\(', '', params)
    params = re.sub('\)', '', params)
    # connect dial names with __
    setting_string = re.sub(' ', '__', params)
    return setting_string


def _get_parameter_type(parameter):
    """ Get the datatype name from parameter.

    Args:
        parameter: A string from which the name of the datatype is extracted.

    Returns:
        A string representing the datatype of the provided parameter.

    """
    plist = parameter.split(' ')
    return plist[0]


def _parse_parameters(line):
    """ Parse parameters from the given line.

    Args:
            line - A string which is parsed for the paramters.

    Returns:
            A list of parameters. A parameter is represented as a dictionary
            with the keys parameter_position, parameter_type and
            setting_name.
    """
    splitted_line = line.strip().split(';')
    # remove signature part of string
    del splitted_line[0]
    parameters = []
    for position, parameter in enumerate(splitted_line):
        parameters.append({
        'parameter_position' : position,
        'parameter_type' : _get_parameter_type(parameter.strip()),
        'setting_name' : _get_setting_name(parameter.strip()),
        })
    return parameters


def get_testcases_for_function(function_signature, testcaselist):
    """ Read testcase list.

    Args:
            Filedescriptor to a testcaselist.

    Returns:
            A list in which each entry is a dictionary representing a testcase.
            The dictionary has the keys 'function_signature' and 'parameters' in
            which the parameters entry is a dictionary representing the
            paramters with the keys 'parameter_position', 'parameter_type' and
            'setting_name'.
    """
    line = testcaselist.readline()
    testcases = []
    while _create_function_signature(line) == function_signature:
        testcases.append(_parse_parameters(line))
        last_pos = testcaselist.tell()
        line = testcaselist.readline()
    testcaselist.seek(last_pos)
    return testcases


def get_number_of_function_params(function_signature, db):
    """ Get the ID and the number of parameters of function.

    Args:
        function_signature: function signature as a string.
        db: Database connection object.

    Returns:
        The number of function parameters.

    Raises:
        An SQL related exception if the query fails.

    """
    c = db.cursor()

    sql = ("SELECT number_of_params FROM function "
        "WHERE signature = '{0}'".format(function_signature))

    try:
        c.execute(sql)
        data = c.fetchone()
        return data[0]
    except:
        # TODO: Decide what to do here
        logger.error("COULD NOT EXECUTE: {}".format(sql))
        raise


def create_signature_table(function_signature, num_of_params, db):
    """ Create a testcase table for the specified function.

    Args:
        function_signature: The signature of the function as a string.
        num_of_params: The number of parameters the function has.
        db: Database connection object.

    Raises:
        An SQL related exception if the creation of the table failed.

    """
    connection_cursor = db.cursor()

    sql = ("CREATE TABLE `{signature}`( ID INT NOT NULL "
            "AUTO_INCREMENT,".format(signature=function_signature))
    param_def = ""
    for pos in xrange(num_of_params):
        param_def += " parameter_{position} INT NOT NULL, ".format(
                position=pos)
    # Remove ', ' of last param_def
    sql += param_def + " PRIMARY KEY (ID))"

    try:
        connection_cursor.execute(sql)
    except:
        # TODO: Decide what to do here
        logger.error("COULD NOT EXECUTE: {}".format(sql))
        raise


def _create_records(testcases, cache):
    """ Translate testcases in paramter form to a list of settings.

    Args:
        testcases: A list of testcases. Each testcase in this list is a
            dictionary representing a testcase.
        cache: A dictionary serving as a cache for setting ids.

    Returns:
        A list of tuples, in which each tuple represents a testcase. An element
        in the tuple corresponds to the id of the setting at this position in
        the functions arguments.

    """
    rows = []
    for testcase in testcases:
        settings = []
        for parameter in sorted(testcase,
                                key=itemgetter('parameter_position')):
            settings.append(cache[parameter['parameter_type']]
                    [parameter['setting_name']])
        rows.append(tuple(settings))
    return rows


def add_testcases_to_signature_table(signature,
        num_params, testcase_records, db):
    """ Add all testcases of a function to its signature table.

    Args:
        signature: The signature of the function as a string.
        num_params: Number of function arguments/parameters.
        testcase_records: A list of tuples in which each tuple correspond to
            one testcase.
        db: Database connection object.

    Raises:
        An SQL related exception if the creation of the table failed.

    """
    connection_cursor = db.cursor()
    sql = "INSERT INTO `{signature}` ".format(signature=signature)
    parameter = "("
    value_place_holder = ""
    for position in  xrange(num_params):
        parameter += "parameter_{pos}, ".format(pos=position)
        value_place_holder += "%s, "
    # remove ', ' of last entry
    parameter = parameter[:-2] + ") VALUES ("
    value_place_holder =  value_place_holder[:-2] + ")"

    sql += parameter + value_place_holder
    try:
        connection_cursor.executemany(sql, testcase_records)
        db.commit()
    except:
        db.rollback()
        # TODO: Decide what should be done in this case
        logger.error("Could not execute sql: {}".format(sql))
        raise


def create_and_fill_signature_table(function_signature, testcases, db, cache):
    """ Creates a table for the provided function and fills it with testcases.

    Args:
        function_signature: The signature of the function as a string.
        testcases: A list in which each entry represents a testcase.
        db: Database connection object.
        cache: A dictionary serving as a cache for setting ids.

    """
    num_param = get_number_of_function_params(function_signature, db)
    create_signature_table(function_signature, num_param, db)
    logger.info("Created table: {}".format(function_signature))
    testcase_records = _create_records(testcases, cache)
    add_testcases_to_signature_table(function_signature, num_param,
            testcase_records, db)
    logger.info("Added {} testcases to table {}".format(len(testcase_records),
        function_signature))


def add_error_model(failure_categories, db):
    """ Add error model to database.

    Args:
        failure_categories: A list of failure categories.
        db: Database connection object.

    """
    connection_cursor = db.cursor()

    for failure in failure_categories:
        connection_cursor.execute("""INSERT INTO failures (id, name) VALUES(%s, %s)""",
                (failure))
        db.commit()


def main():
    """ Main function. Is executed when the script is run. """
    global TYPE_MAPPING

    logger.info("Initialise database")

    opts = parse_arguments()
    opts.data_type_path = get_path(opts.data_type_path)
    opts.type_mapping = get_path(opts.type_mapping)
    opts.call_table = get_path(opts.call_table)

    # read in global type mapping
    with open(opts.type_mapping, 'r') as type_mapping:
        TYPE_MAPPING = read_mapping(type_mapping)

    # Adding functions and datatypes is completely independent so do it in
    # separate processes with different database connections
    dt_db_connection = MySQLdb.connect(host=opts.db_host, user=opts.db_user,
                passwd=opts.db_passwd, db=opts.db_name)
    dt_db_connection.autocommit(True)
    fun_db_connection = MySQLdb.connect(host=opts.db_host, user=opts.db_user,
                passwd=opts.db_passwd, db=opts.db_name)
    fun_db_connection.autocommit(True)

    fun_proc = multiprocessing.Process(
            target=add_functions_to_database,
            args=(opts.call_table, fun_db_connection, opts.testcase_list))
    dt_includes = get_includes(opts.data_type_path)
    dt_includes = remove_duplicates(dt_includes)
    # To get a return value of a function executed by multiprocessing.Process a
    # queue has to be provided as an argument to the function and the result
    # has to be put in the queue. After the process has been started the result
    # can be retrieved from the queue.
    out_q = multiprocessing.Queue()
    dt_proc = multiprocessing.Process(
            target=add_datatypes_and_settings_to_db,
            args=(opts.data_type_path, dt_db_connection, dt_includes, out_q))
    fun_proc.start()
    dt_proc.start()
    # retrieve cache from the queue
    cache = out_q.get()
    # Before further execution all functions, datatypes and settings have to be
    # present in the database so wait for them
    dt_proc.join()
    fun_proc.join()
    dt_db_connection.close()
    fun_db_connection.close()

    # New connection to the database for creating the function signature tables
    db_connection = MySQLdb.connect(host=opts.db_host, user=opts.db_user,
                passwd=opts.db_passwd, db=opts.db_name)
    db_connection.autocommit(True)

    # Get all function signatures from the database
    function_signatures = get_function_signatures(db_connection)
    # Create function signature tables. Entries are in the order specified in
    # the testcaselist
    with open(opts.testcase_list, 'rt') as testcaselist:
        for signature in function_signatures:
            # signature is a one tuple (thanks mysqldb). We really only want
            # the signature string so use signature[0]
            testcases = get_testcases_for_function(signature[0], testcaselist)
            create_and_fill_signature_table(signature[0], testcases,
                    db_connection, cache)
    logger.info("Function signature tables have been created")


    error_model = [(1, "ABORT"), (2, "ABORT_DUMPED"), (3, "RESTART"), (4, "SETUP"), (5, "STOPPED"),
            (6, "UNDEF"), (7, "PASS"), (424242, "COMPILE")]
    add_error_model(error_model, db_connection)
