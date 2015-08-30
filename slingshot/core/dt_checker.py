#!/usr/bin/python
from lxml import etree
import os
import sys
import getopt


class Checker(object):

    def __init__(self, xml_schema):
        self.schema = self.__open_xml_schema(xml_schema)

    def check_xml(self, xml_file):
        return self.schema.validate(self.__open_xml_file(xml_file))

    def check_tree(self, tree):
        return self.schema.validate(tree)

    def __open_xml_schema(self, schema_file):
        return etree.XMLSchema(etree.parse(schema_file))

    def __open_xml_file(self, xml_file):
        return etree.parse(xml_file)


def usage():
    print "Usage: dt_checkery.py -i <input-dir>"


def check_opts(argv):
    in_dir = None
    schema = None
    try:
        opts, args = getopt.gnu_getopt(argv, "hi:s:",\
                ["help", "input-dir", "schema-file"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        else:
            if opt in ("-i", "--input-dir"):
                in_dir = arg
            if opt in ("-s", "--schema-file"):
                schema = arg

    return in_dir, schema


def main(argv):
    in_dir, schema = check_opts(argv)

    for root, dirs, files in os.walk(in_dir):
        for f in files:
            if not Checker(schema).check_xml(os.path.join(root, f)):
                print("{0} is not valid against the schema".format(f))

if __name__ == "__main__":
    main(sys.argv[1:])
