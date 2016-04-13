# coding=utf-8
__author__ = 'Tang'

import lib.xmltodict as xmltodict
import unittest


class InformationNeedFileException(Exception):
    """Raised when file is empty"""
    def __init__(self, filename):
        self.filename = filename


class InformationNeed:
    """Information need data as extracted from XML"""
    def __init__(self, filename):
        with open(filename, 'r') as infile:
            data = infile.read().replace('\n', '')
        if data is not None:
            temp_dict = xmltodict.parse(data)
            self.dict = dict()
            temp_dict = dict(temp_dict['query'])
            for item in temp_dict:
                if item == u'description':
                    self.dict[item] = temp_dict[item][33:]
                else:
                    self.dict[item] = temp_dict[item]
        else:
            raise InformationNeed(filename)

    def get_data(self):
        return self.dict


class TestInformationNeedClass(unittest.TestCase):

    def test_read_patent(self):
        with open("tests/json/information_need_class_test1.txt", 'r') as infile:
            output = infile.read().replace('\n', '')
        p = InformationNeed("corpus/q1.xml")
        self.assertEqual(output, str(p.get_data()))

if __name__ == '__main__':
    unittest.main()