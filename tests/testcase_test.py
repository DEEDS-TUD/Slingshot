from nose.tools import assert_equal
from testfixtures import TempDirectory
from slingshot.core.testcase import Testcase
from slingshot.core.setting import Setting


class TestTestcase():
    """ Test the testcase class """

    def __init__(self):
        self.tempdir = TempDirectory()
        self.work_dir = self.tempdir.path

    def setUp(self):

        self.dt = {'type': 'string',
                'include':
                '#include <stdio.h>\n#include "foo.h"\n#include <stdlib.h>',
                'define': '', 'init': '', 'activation': ''
                }

        self.testcase_id = 42
        self.function_name = 'test_function_name'

        self.c_types = [1, 2]

        setting = Setting(42, 'setting', 0, self.dt, 'code',
                21, self.work_dir)
        self.settings = [setting]
        self.ret_val = 'ret_type'
        self.fun_header = '#include <stdio.h>\n'

    def tearDown(self):
        self.tempdir.cleanup()

    def test_get_id(self):
        """ get_id should return the supplied id """
        TEST_ID = 21
        tc = Testcase(TEST_ID, self.function_name,
                self.settings, self.work_dir, self.c_types, self.ret_val,
                self.fun_header)
        assert_equal(tc.get_id(), TEST_ID, 'ID is not matching')

    def test_get_setting(self):
        """ get_setting should return supplied setting """
        TEST_SETTING = self.settings
        tc = Testcase(self.testcase_id, self.function_name,
                TEST_SETTING, self.work_dir, self.c_types, self.ret_val,
                self.fun_header)
        assert_equal(tc.get_settings(), TEST_SETTING,
                'Setting is not matching')

    def test_get_name(self):
        """ get_name should return supplied name """
        TEST_NAME = 'TC_bar_42'
        tc = Testcase(self.testcase_id, 'bar', self.settings,
                self.work_dir, self.c_types, self.ret_val, self.fun_header)
        assert_equal(tc.get_name(), TEST_NAME,
        'Name is not matching: {0} != {1}'.format(tc.get_name(), TEST_NAME))

    def test_generate_files(self):
        """ generate_files should create the header file for
        this testcase """
        tc = Testcase(self.testcase_id, self.function_name,
                self.settings, self.work_dir, self.c_types, self.ret_val,
                self.fun_header)
        tc.generate_files()
        self.tempdir.check('TC_test_function_name_42.cpp',
                'TC_test_function_name_42.h')
