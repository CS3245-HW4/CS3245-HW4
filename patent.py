import lib.xmltodict as xmltodict
import unittest

# coding=utf-8
__author__ = 'Tang'

"""
Models each XML patent file using a Patent object with a dictionary attribute
that stores the XML file's element-content pairs for easier access and
manipulation.

The xmltodict module was chosen as it is "makes working with XML feel like you
are working with JSON" (https://github.com/martinblech/xmltodict)
Running this python module on its own just runs the unit tests defined within.
"""


class Patent:
    """Patent data as extracted from an XML patent file using xmltodict."""

    def __init__(self, filename):
        """Initializes Patent object with data from XML file mentioned in arg,
        and stores that data in a dictionary attribute for easier access and
        manipulation.

        :param filename: Filename of XML patent file to extract data from.
        """
        with open(filename, 'r') as infile:
            # Ensure that data only resides on a single line
            data = infile.read().replace('\n', '')

        if data is not None:

            self.dict = dict()
            # All XML contents are within 'doc' and 'str' tags consecutively,
            # hence after parsing with xmltodict, all other tags are nested
            # under a list of ordered dictionaries with u'@name' or u'#text'
            # keys and XML element or content values respectively.
            temp_dict = xmltodict.parse(data)['doc']['str']

            for ord_dict in temp_dict:
                # Ignore empty fields
                if u'#text' in ord_dict.keys():
                    # Simplify dictionary structure
                    self.dict[ord_dict[u'@name']] = ord_dict[u'#text']

        else:
            # File is empty
            raise PatentFileException(filename)

    def get_data(self):
        """Returns python dictionary with key-value pairs based on XML
        element-content pairs from the original XML patent file.

        :return: Python dictionary with key-value pairs based on XML
        element-content pairs from the original XML patent file.
        """
        return self.dict


class PatentFileException(Exception):
    """Raised when patent file is empty"""

    def __init__(self, filename):
        """Initializes exception object with the attribute containing the
        empty file's filename.

        :param filename: The empty patent file that raised this exception.
        """
        self.filename = filename


class TestPatentClass(unittest.TestCase):
    """Test case ensuring XML patent files are parsed as expected"""

    def test_read_patent(self):
        """Ensures Patent class parses XML patent files in an expected format.

        Compares the result from parsing the XML file "EP0049154B2.xml" (from
        PatSnap corpus), with the test file "patent_class_test1.txt".
        "patent_class_test1.txt" contains a human-vetted python dictionary
        in JSON format, with key-value pairs based on XML element-content
        pairs. "EP0049154B2.xml" is the XML file which
        patent_class_test1.txt was based off.
        """
        with open("tests/json/patent_class_test1.txt", 'r') as infile:
            output = infile.read().replace('\n', '')
        p = Patent("corpus/patsnap-corpus/EP0049154B2.xml")
        self.assertEqual(output, str(p.get_data()))


if __name__ == '__main__':
    unittest.main()
