from nose.tools import assert_equal
import slingshot.util.multi_version_comparison as mvc

class TestBounderies():
    """ Test boundary method """

    def __init__(self):
        self.version_ordering = [ '06.10', '07.04',
                '07.10', '08.04', '08.10', '09.04',
                '09.10', '10.04', '10.10', '11.04',
                '11.10', '12.04', '12.10', '13.04',
                '13.10',]

    def test_list_with_one_element_is_boundery(self):
        """ A list with one element is always a boundary"""
        test_dict = {
                '1': ['06.10', ], '2': ['07.04', ], '3':
                ['07.10', ], '4': ['08.04', ], '5':
                ['08.10', ], '6': ['09.04', ], '7':
                ['09.10', ], '8': ['10.04', ], '9':
                ['10.10', ], '10': ['11.04', ], '11':
                ['11.10', ], '12': ['12.04', ], '13':
                ['12.10', ], '14': ['13.04', ], '15':
                ['13.10', ],
                }
        expected = set(['06.10', '07.04', '07.10',
                '08.04', '08.10', '09.04', '09.10',
                '10.04', '10.10', '11.04', '11.10',
                '12.04', '12.10', '13.04', '13.10',
                ])
        assert_equal(
                mvc.find_version_boundaries(test_dict, self.version_ordering),
            expected)


    def test_the_first_and_last_elements_are_bounderies(self):
        """ The first element in a list is a boundary except the element is
        06.10 which has no predecessor. The same is true for the last element
        except for 13.10 which has no successor. 06.10 and 13.10 are only
        boundaries if they appear alone in a list"""
        test_dict = {
                '1': ['06.10', '07.04', ],
                '2': ['07.10', '08.04', '08.10', ],
                '3': ['09.04', '09.10', '10.04',
                    '10.10', '11.04', '11.10',
                    '12.04', '12.10', '13.04',
                    '13.10',]
                }
        expected = set(['07.04', '07.10', '08.10', '09.04'])
        assert_equal(
                mvc.find_version_boundaries(test_dict, self.version_ordering),
            expected)

    def test_lists_with_all_boundaries_are_recognized(self):
        """ A list which contains only boundary elements is recognized"""
        test_dict = {
                '1': ['06.10', '07.04', ],
                '2': ['07.10', '08.04', '09.04', ],
                '3': ['08.10', '09.10', '10.04',
                    '10.10', '11.04', '11.10',
                    '12.04', '12.10', '13.04',
                    '13.10',]
                }
        expected = set(['07.04', '07.10', '08.04', '08.10', '09.04', '09.10'])
        assert_equal(
                mvc.find_version_boundaries(test_dict, self.version_ordering),
            expected)

    def test_respect_continuous_parts_of_a_list(self):
        """ A list which has boundary elements can have continuous slices"""
        test_dict = {
                '1': ['06.10', '07.04', ],
                '2': ['07.10', '08.04', '09.04', ],
                '3': ['08.10', '09.10', '10.04', '10.10', '11.04', '11.10', '12.04', ],
                '4': ['12.10', '13.04', '13.10',],
                }
        expected = set(['07.04', '07.10', '08.04', '08.10', '09.04', '09.10',
            '12.04', '12.10'])
        assert_equal(
                mvc.find_version_boundaries(test_dict, self.version_ordering),
            expected)

    def test_respect_continuous_parts_of_a_list_if_last_is_no_boundary(self):
        """ A list which has boundary elements can have continuous slices"""
        test_dict = {
                '1': ['06.10', '07.04', ],
                '2': ['07.10', '08.04', '09.04', ],
                '3': ['08.10', '09.10', '10.04', '10.10', '11.04', '11.10',
                    '12.10', '13.04', '13.10',],
                '4': ['12.04', ],
                }
        expected = set(['07.04', '07.10', '08.04', '08.10', '09.04', '09.10',
            '11.10', '12.04', '12.10'])
        assert_equal(
                mvc.find_version_boundaries(test_dict, self.version_ordering),
            expected)

    def test_no_boundaries_are_respected(self):
        """ Only one list without boundary results in empty set """
        test_dict = {
                '1': ['06.10', '07.04', '07.10', '08.04', '08.10', '09.04',
                    '09.10', '10.04', '10.10', '11.04', '11.10', '12.04',
                    '12.10', '13.04', '13.10',],
                }
        expected = set([])
        assert_equal(
                mvc.find_version_boundaries(test_dict, self.version_ordering),
            expected)

    def test_strong_partiotioned_bondaries(self):
        """ Only one list without boundary results in empty set """
        test_dict = {
                '1': ['06.10', '07.04',],
                '2': ['07.10', '08.04', '09.04', '10.04', '12.04',],
                '3': ['09.10', '10.10', '11.04', '11.10',
                    '12.10', '13.04', '13.10',],
                '4': [ '08.10',],
                }
        expected = set(['07.04', '07.10', '08.04', '08.10', '09.04', '09.10',
            '10.04', '10.10', '11.10', '12.04', '12.10' ])
        assert_equal(
                mvc.find_version_boundaries(test_dict, self.version_ordering),
            expected)
