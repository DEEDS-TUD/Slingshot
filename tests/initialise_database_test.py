from nose.tools import assert_equal
import slingshot.db.initialise_database as init_db
import StringIO
from slingshot.core.util import get_path
from bs4 import BeautifulSoup

def get_descriptor(fname):
    return open(fname, 'r')

class TestReadFunctions(object):
    def setUp(self):
        init_db.TYPE_MAPPING = { 'b_fname': '*char', 'b_int_amode': 'int'}

    def test_empty_calltable_produces_empty_list(self):
        actuall = init_db.read_functions(
                get_path('../tests/fixtures/empty_call_table.xml'))
        assert_equal(actuall, [])

    def test_parse_name(self):
        ct_descriptor = get_descriptor(
                '../tests/fixtures/one_func_call_table.xml')
        actuall = init_db.read_functions(ct_descriptor)
        assert_equal(actuall[0]['name'], 'access')

    def test_parse_header(self):
        ct_descriptor = get_descriptor(
                '../tests/fixtures/one_func_call_table.xml')
        actuall = init_db.read_functions(ct_descriptor)
        assert_equal(actuall[0]['header'], 'unistd.h')

    def test_parse_return(self):
        ct_descriptor = get_descriptor(
                '../tests/fixtures/one_func_call_table.xml')
        actuall = init_db.read_functions(ct_descriptor)
        assert_equal(actuall[0]['return'], 'int')

    def test_parse_parameter(self):
        ct_descriptor = get_descriptor(
                '../tests/fixtures/one_func_call_table.xml')
        actuall = init_db.read_functions(ct_descriptor)
        assert_equal(actuall[0]['parameter'], ['fname', 'int_amode'])

    def test_parse_parameter_c_types(self):
        ct_descriptor = get_descriptor(
                '../tests/fixtures/one_func_call_table.xml')
        actuall = init_db.read_functions(ct_descriptor)
        assert_equal(actuall[0]['parameter_c_types'], ['*char', 'int'])

    def test_create_signature(self):
        ct_descriptor = get_descriptor(
                '../tests/fixtures/one_func_call_table.xml')
        actuall = init_db.read_functions(ct_descriptor)
        assert_equal(actuall[0]['signature'], 'access-fname-int_amode')

class TestReadTestcaselist(object):
    def setUp(self):
        init_db.TYPE_MAPPING = { 'b_fname': '*char', 'b_int_amode': 'int'}

    def _get_descriptor(self, fname):
        return open(fname, 'r')

    def test_empty_testcaselist_produces_empty_list(self):
        tcl_descriptor = get_descriptor(
                '../tests/fixtures/empty_testcaselist.tcs')
        actuall = init_db.read_testcaselist(tcl_descriptor)
        assert_equal(actuall, [])

    def test_parse_signature(self):
        tcl_descriptor = get_descriptor(
                '../tests/fixtures/testcase_list_simple.tcs')
        actuall = init_db.read_testcaselist(tcl_descriptor)
        assert_equal(actuall[0], 'mkdir-fname-mode_t')

    def test_a_signature_is_added_only_once(self):
        tcl_descriptor = get_descriptor(
                '../tests/fixtures/testcase_list_simple.tcs')
        actuall = init_db.read_testcaselist(tcl_descriptor)
        assert_equal(len(actuall), 2)

    def test_respects_the_order(self):
        tcl_descriptor = get_descriptor(
                '../tests/fixtures/testcase_list_simple.tcs')
        actuall = init_db.read_testcaselist(tcl_descriptor)
        assert_equal(actuall[0], 'mkdir-fname-mode_t')
        assert_equal(actuall[1], 'access-fname-int_amode')


class TestMapping(object):
    def test_read_mapping_reads_in_file(self):
        mapping = StringIO.StringIO('b_float float\nb_fname *char\nb_int_amode int')
        actuall = init_db.read_mapping(mapping)
        assert_equal(actuall, {'b_float': 'float', 'b_fname': '*char',
            'b_int_amode': 'int'})

    def test_mapping_returns_ctype_for_b_fname(self):
        init_db.TYPE_MAPPING = {'b_fname': '*char'}
        actuall = init_db.get_ctype('b_fname')
        assert_equal(actuall, '*char')

    def test_mapping_returns_ctype_for_b_int_amode(self):
        init_db.TYPE_MAPPING = {'b_int_amode': 'int'}
        actuall = init_db.get_ctype('b_int_amode')
        assert_equal(actuall, 'int')

    def test_mapping_can_handle_multiple_lookups(self):
        init_db.TYPE_MAPPING = {'b_fname': '*char', 'b_int_amode': 'int'}
        actuall = init_db.get_ctype('b_int_amode')
        assert_equal(actuall, 'int')
        actuall = init_db.get_ctype('b_fname')
        assert_equal(actuall, '*char')


class TestParseDatatypeSpecification(object):
    def test_parse_name(self):
        datatype_descriptor = get_descriptor(
                '../tests/fixtures/b_ptr_file.xml')
        actuall = init_db.parse_datatype_specification(datatype_descriptor)
        assert_equal(actuall['name'], 'b_ptr_file')

    def test_parse_parent(self):
        datatype_descriptor = get_descriptor(
                '../tests/fixtures/b_ptr_file.xml')
        actuall = init_db.parse_datatype_specification(datatype_descriptor)
        assert_equal(actuall['parent'], 'b_ptr_void')


    def test_parse_type(self):
        datatype_descriptor = get_descriptor(
                '../tests/fixtures/b_ptr_file.xml')
        actuall = init_db.parse_datatype_specification(datatype_descriptor)
        assert_equal(actuall['type'], 'FILE*')


    def test_parse_include(self):
        datatype_descriptor = get_descriptor(
                '../tests/fixtures/b_ptr_file.xml')
        actuall = init_db.parse_datatype_specification(datatype_descriptor)
        assert_equal(actuall['include'], ("\n   #include <fcntl.h>\n#include"
        " <sys/stat.h> \n#include <unistd.h>\n#include <errno.h>\n\n  "))

    def test_parse_defines(self):
        datatype_descriptor = get_descriptor(
                '../tests/fixtures/b_ptr_file.xml')
        actuall = init_db.parse_datatype_specification(datatype_descriptor)
        assert_equal(actuall['defines'], ('#define TESTDIR "testdir"\n'
                '#define TESTFILE        "testdir/testfile_fp"'))

class TestParseDatatypeSettings(object):
    def test_parse_dial_groups(self):
        datatype_descriptor = get_descriptor(
                '../tests/fixtures/b_ptr_file.xml')
        dt_soup = BeautifulSoup(datatype_descriptor, 'xml')
        order, groups = init_db.parse_datatype_dialgroups(dt_soup)
        assert_equal(groups['STATE'], ['EMPTY', 'BEGINNING',
        'EOF', 'PAST_EOF'])
