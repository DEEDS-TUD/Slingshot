from util import get_path
import logging
import os
import re


# TODO: NO get methods!! This is python!
class Testcase(object):
    """ Encapsulates a single testcase """

    def __init__(self, testcase_id, function_name, settings,
            work_dir, c_types, ret_val, fun_header):
        self.logger = logging.getLogger(__name__)
        self.__work_dir = work_dir
        self.__id = testcase_id
        self.__settings = settings
        self.__name = "TC_{0}_{1}".format(function_name, testcase_id)
        self.__c_types = c_types
        self.__ret_val = ret_val
        self.__fun_header = fun_header
        self.__function_name = function_name

    def get_id(self):
        """ Return ID of this testcase """
        return self.__id

    def get_settings(self):
        """ Return list of setting in this testcase. """
        return self.__settings

    def get_name(self):
        """ Return name of this testcase as a string. """
        return self.__name

    def generate_files(self):
        """ Create cpp and header files for this testcase """

        self.__gen_header()
        self.__gen_cpp()

    def __gen_header(self):
        """ Create header file for this testcase """

        # Filename of header file
        fn = os.path.join(self.__work_dir,
                          "{0}.h".format(self.__name))

        # List holding all setting declaration lines
        setting_declarations = []

        # Fill setting declaration list
        for setting in self.__settings:
            # Get dt record
            dt = setting.get_datatype()

            # Add setting definition
            # access
            setting_declarations.append('\n{0} *{1}_access();'.format(
                dt['type'], setting.get_name()))
            # commit
            setting_declarations.append('\nvoid {0}_commit();'.format(
                setting.get_name()))
            # cleanup
            setting_declarations.append('\nvoid {0}_cleanup();'.format(
                setting.get_name()))

        with open(fn, "w") as f:
            # Write minimal include set to header
            f.write(self.__minimal_dt_include_set_for_tc(self.__settings))

            # Write setting declarations to header
            for s in setting_declarations:
                f.write(s)

            # Write declaration for signal catch function
            f.write('\nvoid setup_catch_signal();\n')

            # Write declaration of function exec_tc as extern to header
            f.write('extern "C" int exec_tc();')

            f.closed

    def __gen_cpp(self):
        """ Create cpp file for this testcase """

        # Template for testcase cpp files
        template = get_path("bin/tc_cpp_template")
        # file name
        fn = os.path.join(self.__work_dir, "{0}.cpp".format(self.__name))

        # Construct setting values
        s_call = ""
        commit_call = ""
        cleanup_call = ""
        temp = ""

        for i, s in enumerate(self.__settings):
            s_name = s.get_name()
            dt = s.get_datatype()
            setting_type = dt['type']
            # Cast to setting type
            s_call += "{0}* temp{1} = ({0}*) {2}_access();\n".format(
                    setting_type, i, s_name)
            if s.is_pointer or s.is_jmp_buf:
                # Cast to function parameter type
                s_call += "{0}* tmp{1} = ({0}*) temp{1};\n".format(
                        self.__c_types[i], i)
                # Still got a ptr to a ptr, we have to dereference in function
                # call
                temp += ("*tmp{0}, ".format(i))
            else:
                # The setting cast of the ptr to a non ptr type results in a
                # ptr of the setting type. If this setting type is 'smaller'
                # than the function parameter type (i.e. setting type is short,
                # function parameter type is int), A cast of the ptr could
                # introduce non-determinism, because the second half of the
                # memory that is going to be dereferenced is not controlled by
                # the setting. Above all the indented value would not be
                # tested.
                # So we have to dereference the ptr first and only cast the
                # value of the setting to the function parameter typ.
                s_call += "{0} tmp{1} = ({0}) *temp{1};\n".format(
                        self.__c_types[i], i)
                # ptr allready dereferenced before cast, use value
                temp += ("tmp{0}, ".format(i))

            commit_call += "{0}_commit();\n".format(s_name)
            cleanup_call += "{0}_cleanup();\n".format(s_name)

        temp = re.sub(r', $', '', temp)

        # These types can not be used as return values.
        can_not_be_used_as_return = ['void', 'Null', 'div_t', 'ldiv_t']

        # Add testcase specific values to the template
        with open(fn, "w") as f:
            for line in open(template):
                # Add include of function header
                line = line.replace('FUNC_HEADER', '{}'.format(
                    self.__fun_header))
                # Add include of testcase header
                line = line.replace('HEADER_NAME', '{}'.format(self.__name))
                line = line.replace('MAXP', '{}'.format(len(self.__settings)))
                # Add type of return value of the function under test
                if not self.__ret_val in can_not_be_used_as_return:
                    line = line.replace('RETURN_VAL', '{} rval;'.format(
                        self.__ret_val))
                    line = line.replace('VALUE_RETURN', 'rval = ')
                    line = line.replace('OUTPUT', 'std::cout << rval <<'
                        ' std::endl;\n')
                else:
                    line = line.replace('RETURN_VAL', '')
                    line = line.replace('VALUE_RETURN', '')
                    line = line.replace('OUTPUT', '\n')

                # Add setting casting
                line = line.replace('S_CALLS', '{}'.format(s_call))
                # Add commit call
                line = line.replace('COMMIT_CALLS', '{}'.format(commit_call))
                # Add cleanup call
                line = line.replace('CLEANUP_CALLS', '{}'.format(cleanup_call))

                # Add function call: name of function
                line = line.replace('FUN_NAME', '{}'.format(
                    self.__function_name))
                # Add function call: parameters
                line = line.replace('TEMP', '{}'.format(temp))
                # replace marker with value
                f.write(line)
        f.closed

    def __minimal_dt_include_set_for_tc(self, settings):
        """ Given a list of setting ids this function creates a minimal set of
        includes """

        dt_includes = []

        # Extract all include definitions from settings and save them in a list
        for s in settings:
            # Get dt record
            dt = s.get_datatype()

            # datatype include files still have ballista dependent includes
            # these are not needed anymore so we remove them
            prog = re.compile('#include ".*"', re.MULTILINE)
            dt_include = re.sub(prog, '', dt['include'])

            # Append include to include list
            if dt_include not in dt_includes:
                dt_includes.append(dt_include)

        includes_no_empty_lines_no_duplicates = []

        for inc_string in dt_includes:
            # split each include string on newlines -> create a list of strings
            lines = inc_string.split('\n')
            # Remove leading and trailing whitespace of entries and remove
            # empty entries.
            empty = [line.strip() for line in lines if line.strip()]
            # Add list for this include string
            includes_no_empty_lines_no_duplicates += empty

        # Now we have a big list where each include string is a element in this
        # list. Remove duplicates:
        min_includes = list(set(includes_no_empty_lines_no_duplicates))

        # now include holds a set with nonempty unique include lines!
        # Join them as a string:
        min_includes_string = '\n'.join(min_includes)

        #self.logger.debug("Created min_set: {}".format(min_includes_string))

        return min_includes_string
