import logging
import os
import random
import shutil
import subprocess
import sys
from sets import Set


class TcGenerator(object):

    def __init__(self, database, tc_factory, setting_factory,
            work_dir, batch_size=2):

        # batch_size specifies the number of testcases returned by generate
        self.batch_size = batch_size

        # connection to the database
        self.db = database

        # Number of testcases needed to completely test this function
        self.remaining_tcs = 0

        # Get logger
        self.logger = logging.getLogger(__name__)

        # Set working directory for file creation, compilation
        self.work_dir = work_dir

        # Factory for testcases
        self.tc_factory = tc_factory

        # Factory for settings
        self.s_factory = setting_factory

        # function record
        self.function = None
        self.testcases = None
        self.testcases_iter = None
        self.created_setting_ids = []
        self.all_settings = Set()
        self.compiled_settings = []

    def _compile_tcs(self, tc_list):
        """ Compile the testcases specified in the list of testcase ids and
        return a list containing the file names of the compiled testcases."""

        #self.logger.debug("Start compilation of testcases")

        tcs_to_compile = []
        compiled_tcs_names = []

        # For each testcase in the testcase list we generate the necessary call
        # to the compiler to compile this testcase. A list of all these calls
        # is then given to _run_all_processes to run in parallel.
        for tc in tc_list:

            # file name which should be compiled
            testcase_fname = os.path.join(self.work_dir,
                                "{0}.cpp".format(tc.get_name()))
            # file name of result of compilation
            testcase_oname = os.path.join(self.work_dir,
                                    "{0}.o".format(tc.get_name()))

            # save names of compilation results for later return
            compiled_tcs_names.append(testcase_oname)

            # Construct the call to the compiler
            compiler_call = ["g++", "-g", "-c", "-fpic", testcase_fname, "-o",
                    testcase_oname]

            # Add call to the list of calls
            tcs_to_compile.append(compiler_call)

        log = os.path.join(self.work_dir, "compile.log")

        # Run compilation of testcases in parallel
        self._run_all_processes(tcs_to_compile, log)

    def _create_shared_lib(self, compiled_testcase_ids):
        """ Create share libraries for a batch of testcases. Each testcase
        gets its own lib! """

        setting_file_paths = []
        comp = []

        for tc in compiled_testcase_ids:

            # Get settings for this tc:
            settings = tc.get_settings()

            for s in settings:
                setting_file_paths.append(os.path.join(self.work_dir,
                    "{0}.o".format(s.get_name())))

            # A setting should be only added once
            setting_file_paths = list(set(setting_file_paths))

            # Create compiler call
            compiler_call = ["g++", "-g", "-shared", "-fpic"]
            compiler_call += setting_file_paths
            compiler_call += ["{0}.o".format(tc.get_name()),
                    "-o", "libexec_tc_{0}_{1}.so".format(self.function.name,
                        tc.get_id())]

            comp.append(compiler_call)
            setting_file_paths = []

        log = os.path.join(self.work_dir, "compile.log")

        # Run compilation of shared libraries in paralles
        self._run_all_processes(comp, log)

    def _compile_settings(self, settings):
        """ Compile all setting files for the function under test. """

        settings_to_compile = []

        # Add settings
        for setting in settings:
            # Add setting to list of settings which should be compiled
            if not setting in self.compiled_settings:
                stc = os.path.join(self.work_dir, "{0}.cpp"
                        .format(setting.get_name()))
                settings_to_compile.append(stc)

        # remove duplicates
        settings_to_compile = list(set(settings_to_compile))

        compiler_call = []

        # For each setting create call to the compiler
        for setting in settings_to_compile:
            call = ["g++", "-g", "-c", "-fpic", setting]
            compiler_call.append(call)

        log = os.path.join(self.work_dir, "compile.log")

        # Run compilation in parallel
        self._run_all_processes(compiler_call, log)

    def _run_all_processes(self, process_call_list, log):
        """ Run the list of given commands. For each command a new process is
        created.
        This function returns if all processes have returned. """

        running_subprocesses = [
            subprocess.Popen(process_call,
                             stdout=open(log, 'a'),
                             stderr=open(log, 'a'),
                             cwd=self.work_dir)
            for process_call in process_call_list]

        # Create list of all running child pids
        pids = set()
        for rs in running_subprocesses:
            pids.add(rs.pid)

        # wait until all children have finished
        while pids:
            pid, returncode = os.wait()
            if returncode != 0:
                self.logger.error("Compile error\n")
                #sys.exit()
            pids.remove(pid)

    def _delete_generated_files(self):

        self.cleanup_batch
        self.cleanup_settings

    def _reset(self):
        """ Resete all class members and delete generated files """

        self.function = None
        self.testcases_iter = None
        self.testcases = None
        self.remaining_tcs = 0
        self.created_setting_ids = []
        self.all_settings = Set()

    def load_function(self, function):
        """ Load function into testcase generator.

        Args:
            function: Function which is loaded as a named Function tuple.

        """

        self._reset()
        self.function = function
        self.testcases = self.db.get_testcases(self.function.signature)
        self.remaining_tcs = len(self.testcases)
        self.logger.info("Loaded function {}. {} testcases found.".format(
            self.function.name, self.remaining_tcs))
        self.testcases_iter = iter(self.testcases)

    def testcases_left(self):
        """ Check if there are remaining testcases for this function.

        Returns:
            True if there are remaining testcases, False otherwise.

        """
        return self.remaining_tcs > 0

    def _next_testcase_batch(self):
        """ Get the next batch of testcases.

        Args:
            testcase_iter: Iterator object over the testcase tuple.

        Returns:
            A list containing self.batch_size tuples. In which each tuple
            represents a testcase.

        """
        tc_batch = []
        while len(tc_batch) < self.batch_size:
            try:
                testcase = self.testcases_iter.next()
                tc_batch.append(testcase)
                self.remaining_tcs -= 1
            except StopIteration:
                break
        return tc_batch

    def _create_settings(self, setting_ids):
        """ Create setting objects for the given setting ids.

        Args:
            setting_ids: Tuple contining setting ids

        Returns:
            A list of setting objects.

        """
        setting_obj = []
        for setting_id in setting_ids:
            if setting_id in self.created_setting_ids:
                # Get object from created_setting_ids
                setting_obj.append(self._get_setting(setting_id))
            else:
                setting_obj.append(self.s_factory.create_setting(
                    setting_id, self.work_dir))

        return setting_obj

    def _get_setting(self, setting_id):
        for setting in self.all_settings:
            if setting.get_id() == setting_id:
                return setting

    def generate(self):
        """ Generate 'batch_size' testcases from the set of remaining
        testcases.

        """
        tc_batch = self._next_testcase_batch()
        # Generate all testcases in this batch
        testcases = []
        for testcase in tc_batch:
            testcase_id, setting_ids = testcase[0], testcase[1:]
            settings = self._create_settings(setting_ids)
            for s in settings:
                s.generate_files()
                self.created_setting_ids.append(s.get_id)
                self.all_settings.add(s)
            self._compile_settings(settings)
            tc = self.tc_factory.create_testcase(self.function,
                    testcase_id, settings)
            tc.generate_files()
            testcases.append(tc)

        # Compile all testcases and associated settings in this batch
        self._compile_tcs(testcases)

        # Create shared libraries for testcases
        self._create_shared_lib(testcases)

        return testcases

    def cleanup_batch(self, testcase_batch):
        for tc in testcase_batch:
            tc_id = tc.get_id()

            tc_name = os.path.join(self.work_dir,
                                   "TC_{0}_{1}".format(self.function.name,
                                                       tc_id))
            if os.path.exists(tc_name + ".o"):
                os.remove(tc_name + ".o")

            if os.path.exists(tc_name + ".cpp"):
                os.remove(tc_name + ".cpp")

            if os.path.exists(tc_name + ".h"):
                os.remove(tc_name + ".h")

    def cleanup_settings(self):
        """ Remove all settings for the function under test."""
        # Get all settings for this function.
        for s in self.all_settings:
            full_path = os.path.join(self.work_dir, s.get_name())

            if os.path.exists(full_path + ".cpp"):
                os.remove(full_path + ".cpp")

            if os.path.exists(full_path + ".h"):
                os.remove(full_path + ".h")
            if os.path.exists(full_path + ".o"):
                os.remove(full_path + ".o")
