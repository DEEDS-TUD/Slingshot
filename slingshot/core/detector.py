import logging
import os
import shutil
import subprocess
import sys
from util import get_path


class Detector(object):

    def __init__(self, database, work_dir, timeout=10000):
        self.logger = logging.getLogger(__name__)
        self.work_dir = work_dir
        self.timeout = timeout
        self.db = database
        self._compile_executer()
        self.executer_binary = os.path.join(self.work_dir, "testcase_executer.out")

    def _compile_executer(self):
        # Copy header to work dir
        shutil.copy2(get_path("bin/testcase_executer.h"), os.path.join(self.work_dir,
        "testcase_executer.h"))
        # Copy source to work dir
        executer_source = os.path.join(self.work_dir, "testcase_executer.cpp")
        shutil.copy2(get_path("bin/testcase_executer.cpp"), executer_source)

        # Compile the executer
        log = os.path.join(self.work_dir, "c.log")
        compiler_call = ["g++", "-g", executer_source] + ["-ldl"]
        compiler_call += ["-lrt", "-o", "testcase_executer.out"]
        subprocess.Popen(compiler_call,
                         stdout=open(log, 'a'),
                         stderr=open(log, 'a'),
                         cwd=self.work_dir)

        pid, ret = os.wait()

        if ret != 0:
            self.logger.error("The testcase executer could not be compiled!"
                    " Aborting all tests!\n")
            sys.exit()

    def _construct_shared_lib_name(self, function_id, testcase_id):
        """ Create file name for shared lib without a suffix."""
        f_name = self.db.get_function_name(function_id)
        return "libexec_tc_{0}_{1}.so".format(f_name, testcase_id)

    def _run(self, path_to_testcase_binary):
        """ Run Testcase """
        sp = subprocess.Popen([self.executer_binary, path_to_testcase_binary],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         cwd=self.work_dir)

        (std_out, std_err) = sp.communicate()
        # Strip newlines from output
        std_out = std_out.strip()
        std_err = std_err.strip()

        self.logger.debug("EXEC_out: {0}".format(std_out))
        self.logger.debug("EXEC_err: {0}".format(std_err))
        self.logger.debug("ex_tc.out retcode: {}".format(sp.returncode))

        # Retrive testcase staus to result mapping from db
        possible_results = self.db.get_failure_names()

        # Check if we anticipated this result if not return 424242
        if not std_out in possible_results:
            self.logger.error("Testcase returned unexpected value! {}".format(
                std_out))
            return self.db.get_failure_id("COMPILE")
        else:
            if std_out:
                exp_return = self.db.get_failure_id(std_out)

        # TODO: handle std_err

        return exp_return

    def run_testcase(self, function_id, tc, tcl):

        shared_lib = self._construct_shared_lib_name(function_id,
                tc.get_id())

        self.logger.info("Running testcase {0}!!!".
                format(tc.get_name()))
        path_to_shared_lib = os.path.join(self.work_dir, shared_lib)
        exp_result = self._run(path_to_shared_lib)
        self.logger.info("Storing result: {0}, {1}, {2}".format(function_id,
                                                            tc.get_id(),
                                                            exp_result))
        self.db.set_result(function_id, tc.get_id(), exp_result, tcl)
        self._cleanup(shared_lib)
        return exp_result

    def _cleanup(self, shared_lib):
        """ Removes files created for testing """

        full_path = os.path.join(self.work_dir, shared_lib)
        if os.path.exists(full_path):
            os.remove(full_path)
