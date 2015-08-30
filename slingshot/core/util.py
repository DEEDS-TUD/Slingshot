from pkg_resources import resource_filename


def get_path(name):
    """ Produces a path which works when builded. all paths have to be
    specified as if called in slingshot/slingshot, meaning you have to include
    the subpackage. Like foo/bar for file bar in package foo"""
    name = '../' + name
    base_name = resource_filename(__name__, name)
    return base_name
