import os
import re
import types


class Setting(object):

    def __init__(self, setting_id, setting_name,
            dt, code, commit_code, cleanup_code,
            work_dir):

        self.__id = setting_id
        self.__name = setting_name
        self.__code = code
        self._commit_code = commit_code
        self._cleanup_code = cleanup_code
        self.__datatype = dt
        self.__work_dir = work_dir
        self._is_created = False
        self.is_pointer = self._is_ptr_in_name()
        self.is_jmp_buf = self._is_jmp_buf_in_name()

    def _is_ptr_in_name(self):
        prog = re.compile("b_ptr")
        found = prog.match(self.__datatype['name'])
        if found:
            return True
        else:
            return False

    def _is_jmp_buf_in_name(self):
        prog = re.compile(".*jmp_buf.*")
        found = prog.match(self.__datatype['name'])
        if found:
            return True
        else:
            return False

    def get_datatype(self):
        return self.__datatype

    def get_name(self):
        return self.__name

    def get_id(self):
        return self.__id


    def get_code(self):
        return self.__code

    def generate_files(self):
        """ Create cpp and header files for this setting """

        if not self._is_created:
            self.__gen_cpp()
            self.__gen_header()
            self._is_created = True
        else:
            pass

    def __gen_cpp(self):
        """ Create cpp file for this setting """

        cpp_file_name = os.path.join(self.__work_dir,
                "{0}.cpp".format(self.__name))

        with open(cpp_file_name, 'w') as f:
            # Add datatype include files
            f.write(self.__datatype['include'])
            f.write('\n#include <stdio.h>\n')
            f.write('#include <stdlib.h>\n')
            f.write('#include <fstream>\n')
            f.write('#include <iostream>\n')
            f.write('#include <string.h>\n')
            f.write('#include <sys/types.h>\n')
            f.write('#include <sys/stat.h>\n')
            f.write('//#include <sys/errno.h>\n')
            f.write('#include <errno.h>\n')
            f.write('#include <unistd.h>\n')


            # Include setting header file
            f.write('\n#include "{0}.h"'.format(self.__name))

            # Declare type of return variable _theVariable in the namespace
            # of this setting (Since a function call can include more than
            # one setting, and the return variable of all settings is
            # _theVariable a namespace is necessary)
            f.write("\nnamespace {\n")
            f.write('\t{} _theVariable;\n'.format(self.__datatype['type']))
            # Add defines
            f.write(self.__datatype['define'])
            f.write("\n}\n")

            # Define setting function. All manipulations are done here
            # Add function signature for this setting
            f.write("\n{0} *{1}_access() {{".format(self.__datatype['type'],
                self.__name))

            f.write(self.__code)

            f.write('return &_theVariable;')
            f.write('\n}\n')

            # Add commit block
            f.write('void {0}_commit() {{\n'.format(self.__name))
            f.write(self._commit_code)
            f.write('}\n')

            # Add cleanup block
            f.write('void {0}_cleanup() {{\n'.format(self.__name))
            f.write(self._cleanup_code)
            f.write('}\n')

        f.closed

    def __gen_header(self):
        """ Create header file for this setting """

        header_file_name = os.path.join(self.__work_dir,
                "{0}.h".format(self.__name))

        with open(header_file_name, 'w') as f:
            # Write includes
            f.write(self.__datatype['include'])
            # Add function declaration
            f.write("\n{0} *{1}_access();\n".format(self.__datatype['type'], self.__name))
            f.write("void {0}_commit();\n".format(self.__name))
            f.write("void {0}_cleanup();".format(self.__name))

        f.closed
