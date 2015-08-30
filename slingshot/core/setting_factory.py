from setting import Setting


class SettingFactory(object):

    def __init__(self, database_connection):
        self.db_con = database_connection

    def create_setting(self, setting_id, work_dir):
        """ Create a Setting """

        setting = self.db_con.get_setting(setting_id)
        setting_name = "t_{0}_{1}".format(setting['name'], setting_id)
        datatype = self.db_con.get_datatype(setting_id)

        return Setting(setting['id'], setting_name,
                datatype, setting['code'], setting['commit_code'],
                setting['cleanup_code'], work_dir)
