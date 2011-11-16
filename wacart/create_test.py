#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import create_cspace_records
import unittest

class TestParsing(unittest.TestCase):

  def testXmlBuild(self):
     """should be able to find the object's title and author's birthdate"""

     simpleRecord = {'title': ['Unspeakable Test Object Of Blinding Clarity'],
       'acc_no': '2020.142.1',
       'date': '11/14/2020',
       'description': ['for testing']
     }
     some_xml = create_cspace_records.xml_from(simpleRecord)
     self.assertTrue(some_xml.find('Clarity') > -1)
     self.assertTrue(some_xml.find('2020.142') > -1)

if __name__ == "__main__":
    unittest.main()   
