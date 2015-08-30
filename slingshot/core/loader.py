from lxml import etree
from dt_checker import Checker
from t_exceptions import XMLNotValid


class Loader(object):

    def __init__(self, schema):
        self.tree = None
        self.schema = schema
        self.parser = etree.XMLParser(remove_comments=True)

    def load(self, file_name):
        self.tree = None
        tree = self.read_xml(file_name)
        self.tree = tree
        if not self.valid_xml(file_name):
            self.tree = None
            raise XMLNotValid()

        return self.tree

    def read_xml(self, file_name):
        try:
            return etree.parse(file_name, self.parser)
        except IOError as e:
            print("({}) ".format(e))

    def valid_xml(self, file_name):
        return Checker(self.schema).check_xml(file_name)

    def print_tree(self, tree):
        print(etree.tostring(tree, pretty_print=True))


class CtLoader(Loader):

    def __init__(self, schema):
        Loader.__init__(self, schema)


class ParamLoader(Loader):

    def __init__(self, schema):
        Loader.__init__(self, schema)
