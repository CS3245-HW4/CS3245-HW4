import lib.xmltodict as xmltodict
import unittest

# coding=utf-8
__author__ = 'Tang'

"""
Models each XML information need file using an InformationNeed object with
a dictionary attribute that stores the XML file's element-content pairs for
easier access and manipulation.

The xmltodict module was chosen as it is "makes working with XML feel like you
are working with JSON" (https://github.com/martinblech/xmltodict)
Running this python module on its own just runs the unit tests defined within.
"""


class InformationNeed:
    """Patent data as extracted from an XML information need (query) file
    using xmltodict."""

    def __init__(self, filename):
        """Initializes InformationNeed object with data from XML file
        mentioned in arg, and stores that data in a dictionary attribute for
        easier access and manipulation.

        :param filename: Filename of XML file to extract data from.
        """
        with open(filename, 'r') as infile:
            # Ensure that data only resides on a single line
            data = infile.read().replace('\n', '')

        if data is not None:

            self.dict = dict()
            # All XML contents are within 'query' tags, hence all other tags
            # are nested under another dictionary with 'query' key value
            # after parsing with xmltodict.
            temp_dict = xmltodict.parse(data)['query']
            # Convert from ordered dictionary to dictionary data structure
            temp_dict = dict(temp_dict)

            for key in temp_dict:
                if key == u'description':
                    # Remove "Relevant documents will describe " (33 chars)
                    # which appears in all information need files' description
                    self.dict[key] = temp_dict[key][33:]
                else:
                    self.dict[key] = temp_dict[key]

        else:
            # File is empty
            raise InformationNeed(filename)

    def get_data(self):
        """Returns python dictionary with key-value pairs based on XML
        element-content pairs from the original XML information need file.

        :return: Python dictionary with key-value pairs based on XML
        element-content pairs from the original XML information need file.
        """
        return self.dict


class InformationNeedFileException(Exception):
    """Raised when file is empty"""

    def __init__(self, filename):
        """Initializes exception object with the attribute containing the
        empty file's filename.

        :param filename: The empty information need file that raised this
        exception.
        """
        self.filename = filename


class TestInformationNeedClass(unittest.TestCase):
    """Test case ensuring XML information need files are parsed as expected"""

    def test_read_patent(self):
        """Ensures InformationNeed class parses XML information need files in
        an expected format.

        Compares the result from parsing the XML file "q1.xml" (provided test
        query), with the test file "information_need_class_test1.txt".
        "information_need_class_test1.txt" contains a human-vetted python
        dictionary in JSON format, with key-value pairs based on XML
        element-content pairs. "q1.xml" is the XML file which
        information_need_class_test1.txt was based off.
        """
        with open("tests/json/information_need_class_test1.txt", 'r') \
                as infile:
            output = infile.read().replace('\n', '')
        p = InformationNeed("corpus/q1.xml")
        self.assertEqual(output, str(p.get_data()))


if __name__ == '__main__':
    unittest.main()
