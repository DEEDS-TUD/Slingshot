from nose.tools import assert_equal
from testfixtures import TempDirectory
from slingshot.core.setting import Setting


class TestSetting():
    """ Test the setting class """

    def setUp(self):
        """ Setup test fixtures """

        self.setting_id = 42
        self.setting_name = 'test_setting_name'
        self.setting_position = 0
        self.dt = {'type': 'string',
                'include':
                '#include <stdio.h>\n#include "foo.h"\n#include <stdlib.h>',
                'define': '', 'init': '', 'activation': ''}
        self.setting_code = 'code'
        self.function_ref = 1
        self.tempdir = TempDirectory()
        self.work_dir = self.tempdir.path

    def tearDown(self):
        """ Remove artefacts """
        self.tempdir.cleanup()

    def test_get_name(self):
        """get_name should return the supplied name"""
        TEST_NAME = 'test_name'
        setting = Setting(self.setting_id, TEST_NAME, self.setting_position,
                self.dt, self.setting_code, self.function_ref, self.work_dir)

        assert_equal(setting.get_name(), TEST_NAME)

    def test_get_id(self):
        """get_id should return the supplied id"""
        TEST_ID = 43
        setting = Setting(TEST_ID, self.setting_name, self.setting_position,
                self.dt, self.setting_code, self.function_ref, self.work_dir)

        assert_equal(setting.get_id(), TEST_ID)

    def test_get_position(self):
        """get_position should return the supplied position"""
        TEST_POSITION = 1
        setting = Setting(self.setting_id, self.setting_name, TEST_POSITION,
                self.dt, self.setting_code, self.function_ref, self.work_dir)

        assert_equal(setting.get_position(), TEST_POSITION)

    def test_get_code(self):
        """get_code should return the supplied code"""
        TEST_CODE = 'if (foo) { bar; }'
        setting = Setting(self.setting_id, self.setting_name,
                self.setting_position, self.dt, TEST_CODE, self.function_ref,
                self.work_dir)

        assert_equal(setting.get_code(), TEST_CODE)

    def test_get_function_ref(self):
        """get_function_ref should return the supplied function_ref"""
        TEST_F_REF = 22
        setting = Setting(self.setting_id, self.setting_name,
                self.setting_position, self.dt, self.setting_code, TEST_F_REF,
                self.work_dir)

        assert_equal(setting.get_function_ref(), TEST_F_REF)

    def test_get_datatype(self):
        """get_datatype should return the supplied datatype record"""
        TEST_DT = self.dt
        setting = Setting(self.setting_id, self.setting_name,
                self.setting_position, TEST_DT, self.setting_code,
                self.function_ref, self.work_dir)

        assert_equal(setting.get_datatype(), TEST_DT)

    def test_ballista_settings_get_removed(self):
        """all ballista includes should be removed from the datatype include
        string """
        setting = Setting(self.setting_id, self.setting_name,
                self.setting_position, self.dt, self.setting_code,
                self.function_ref, self.work_dir)

        assert_equal(setting.get_datatype()['include'],
                '#include <stdio.h>\n\n#include <stdlib.h>')

    def test_generate_files(self):
        """ generating the setting files should create header and cpp files """
        setting = Setting(self.setting_id, 't_name_42',
                self.setting_position, self.dt, self.setting_code,
                self.function_ref, self.work_dir)
        setting.generate_files()
        self.tempdir.check('t_name_42.cpp', 't_name_42.h')
