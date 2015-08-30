from nose.tools import *
import mock
from slingshot.core.setting_factory import SettingFactory


class TestSettingFactory():

    def setUp(self):
        """ Setup test fixtures """
        self.setting = {'id': 42, 'position': 0, 'name': 'mock_name', 'code':
            'if (1) { printf("1"); }', 'f_ref': 21, 'dt_ref': 84}
        self.dt = {'type': 'string', 'include': '#include <stdio.h>',
                'define': '', 'init': '', 'activation': ''}
        db_mock = mock.Mock()
        db_mock.get_setting.return_value = self.setting
        db_mock.get_datatype.return_value = self.dt
        self.factory = SettingFactory(db_mock)

    def test_create_setting_uses_given_setting_id_in_name_creation(self):
        """ The setting factory should use the supplied setting id to craft the
        setting name. """
        se = self.factory.create_setting(43, '/tmp')
        assert_not_equal(se.get_name(), 't_' + self.setting['name'] + '_42')
        assert_equal(se.get_name(), 't_' + self.setting['name'] + '_43')

    def test_create_setting_adds_prefix_to_setting_name(self):
        """ The setting factory should add the prefix t_ to the setting name
        """
        se = self.factory.create_setting(42, '/tmp')
        assert_equal(se.get_name(), 't_' + self.setting['name'] + '_42')

    def test_create_setting_adds_datatype_record(self):
        """ The setting factory should add the appropriate datatype record for
        the setting """
        se = self.factory.create_setting(42, '/tmp')
        assert_equal(se.get_datatype(), self.dt)
