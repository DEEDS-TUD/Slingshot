from freshen import *
import MySQLdb
from slingshot.db.db_connector import DbConnector
from slingshot.core.testcase_factory import TcFactory
from slingshot.core.setting_factory import SettingFactory
from slingshot.core.tc_generator import TcGenerator
from slingshot.core.detector import Detector
from testfixtures import TempDirectory


@Before
def before(sc):
    DATABASE = MySQLdb.connect(
            host="localhost",
            user="slingshot_test",
            db="slingshot_testing",
            passwd='slingshot')
    ftc.test_db = DbConnector(DATABASE)
    ftc.test_dir = TempDirectory()
    ftc.tc_factory = TcFactory(ftc.test_db, ftc.test_dir.path)
    ftc.s_factory = SettingFactory(ftc.test_db)
    batch_size = 1
    ftc.tcg = TcGenerator(ftc.test_db, ftc.tc_factory, ftc.s_factory,
            batch_size, ftc.test_dir.path)
    ftc.detector = Detector(ftc.test_db, 10000, ftc.test_dir.path)


@After
def after(sc):
    ftc.test_dir.cleanup()


@Given("The function under test has the signature ([a-zA-Z0-9_-]+)")
def load_function(function_signature):
    f_id = ftc.test_db.get_function_id(function_signature)
    ftc.tcg.load_function(f_id)


@Given("the specified testcase is (\d+)")
def set_testcase(tc_id):
    scc.testcase_id = int(tc_id)
    ftc.tcg.rand_tc_list = [(scc.testcase_id,)]


@When("running the testcase")
def running():
    scc.fun_id, scc.batch = ftc.tcg.generate()
    scc.result = ftc.detector.run_testcase(scc.fun_id, scc.batch[0])


@Then("slingshot is detecting a (\w+)")
def result(expected_result):
    failure_id = ftc.test_db.get_result(scc.fun_id, scc.testcase_id)
    actual_result = ftc.test_db.get_failure_name(failure_id)
    assert_equals(expected_result, actual_result,
        "{} is NOT Equal: {}".format(expected_result, actual_result))
