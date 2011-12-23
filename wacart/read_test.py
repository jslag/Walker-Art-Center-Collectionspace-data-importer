#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import wacart
import unittest

def mockExport(fielddict):
   all_fields = []
   mock_fields = fielddict.keys()
   for i in range(len(wacart.COLUMNS)):
     field = wacart.COLUMNS[i]['name']
     if field in mock_fields:
       all_fields.append(fielddict[field])
     else:
       all_fields.append('')
   return "\t".join(all_fields)

class ObjectStuff(unittest.TestCase):

  def testSomeFields(self):
     """should be able to find the object's title and author's
     birthdate. Should not pass empty values."""

     oneLineExport = mockExport(
       {'title':'foo', 'born':'1900', 
        'creator_text_inverted':'Bob, Jim',
        'running_time': ''})

     objekt, agents = wacart.parse_line(oneLineExport)
     self.assertEqual(['foo'], objekt['title'])
     self.assertEqual('1900', agents[0]['born'])
     self.assertEqual(False, objekt.has_key('running_time'))

  def testRepeats(self):
    """Some works have multiple titles, measurements, etc. And there can
    be multiple agents."""

    title_repeat = mockExport(
      {'title':'foobar', 'creator_text_inverted':'Doe, John; Roe, Jane',
       'born':'1900/1998'})

    objekt, agents = wacart.parse_line(title_repeat)
    self.assertEqual('foo', objekt['title'][0])
    self.assertEqual('bar', objekt['title'][1])
    self.assertEqual('Doe', agents[0]['last_name'])
    self.assertEqual('John', agents[0]['first_name'])
    self.assertEqual('artist', agents[0]['agent_type'])
    self.assertEqual('Roe', agents[1]['last_name'])
    self.assertEqual('Jane', agents[1]['first_name'])
    self.assertEqual('artist', agents[1]['agent_type'])
    self.assertEqual('Roe', agents[1]['last_name'])
    self.assertEqual('1900', agents[0]['born'])

  def testIgnoreSpuriousRepeats(self):
    """sometimes the record contains a repeat character but then no
    subsequent values."""
    
    lame_repeat = mockExport( {'title':'foo',
      'creator_text_inverted':'Sprat, Max ' })
    objekt, agents = wacart.parse_line(lame_repeat)
    self.assertEqual(['foo'], objekt['title'])
    self.assertEqual('Sprat', agents[0]['last_name'])
    self.assertEqual(1, len(agents))

    lamer_repeat = mockExport( {'title':'foo',
      'creator_text_inverted':'Sprat, Max ',
      'inscription_location':'great!'})
    objekt, agents = wacart.parse_line(lamer_repeat)
    self.assertEqual(['great!'], objekt['inscription_location'])
    self.assertEqual('Max', agents[0]['first_name'])
    self.assertEqual(1, len(agents))

  def testArtistAuthorsAndEditor(self):
    lame_repeat = mockExport( {'birth_place':'BostonAntigua',
      'creator_text_inverted':'Bob, Jim; Bob, Jane',
      'author':'Bennett, John; Thomas Cassidy',
      'author_birth_year':'1975',
      'editor':'Mekas, Jonas'})
    objekt, agents = wacart.parse_line(lame_repeat)
    self.assertEqual('Bob', agents[0]['last_name'])
    self.assertEqual('Bob', agents[1]['last_name'])
    self.assertEqual('artist', agents[0]['agent_type'])
    self.assertEqual('Bennett', agents[2]['last_name'])
    self.assertEqual('author', agents[2]['agent_type'])
    self.assertEqual('1975', agents[2]['born'])
    self.assertEqual('Cassidy', agents[3]['last_name'])
    self.assertEqual('Mekas', agents[4]['last_name'])
    self.assertEqual('editor', agents[4]['agent_type'])

  def testCleanSpuriousSpaces(self):
    """fields may have opening or trailing spaces, which we should
    ditch"""

    extra_spaces = mockExport( 
      {'acc_no':' 2011.404', 'old_acc_no':'11.404 ',
      'creator_text_inverted':' Doe, John ' })

    objekt, agents = wacart.parse_line(extra_spaces)
    self.assertEqual('2011.404', objekt['acc_no'])
    self.assertEqual('11.404', objekt['old_acc_no'])
    self.assertEqual('Doe', agents[0]['last_name'])

  def testUnpackNames(self):
    agentstring1 = "Adams, Alice; Paul D'Andrea, Rita Mae Brown"
    self.assertEqual('Adams, Alice', wacart.unpack_agent_names(agentstring1)[0])
    self.assertEqual("Paul D'Andrea", wacart.unpack_agent_names(agentstring1)[1])
    self.assertEqual("Rita Mae Brown", wacart.unpack_agent_names(agentstring1)[2])

    agentstring2 = 'Abramovic, Marina and Ulay Abramovic'
    self.assertEqual("Abramovic, Marina", wacart.unpack_agent_names(agentstring2)[0])
    self.assertEqual("Ulay Abramovic", wacart.unpack_agent_names(agentstring2)[1])
    
    agentstring3 = 'Adal, Pepe Calvo; Jacques Charlier; Rose Farrell; George Parkin'
    self.assertEqual("Adal, Pepe Calvo", wacart.unpack_agent_names(agentstring3)[0])
    self.assertEqual("Rose Farrell", wacart.unpack_agent_names(agentstring3)[2])

    agentstring4 = 'Abts, Tomma'
    self.assertEqual("Abts, Tomma", wacart.unpack_agent_names(agentstring4)[0])

    agentstring5 = 'von Mies, Tomma; Smith, John'
    self.assertEqual("von Mies, Tomma", wacart.unpack_agent_names(agentstring5)[0])

    agentstring6 = 'von Mies, Tomma'
    self.assertEqual("von Mies, Tomma", wacart.unpack_agent_names(agentstring6)[0])

  def testStripUnicode(self):
    self.assertEqual('foo', wacart.strip_spaces(u' foo '))

  # 
  # to run just this one try:
  #   python read_test.py ObjectStuff.testAgentNameExtractor
  #
  def testAgentNameExtractor(self):
    agentstring1 = {'creator_text_inverted':"Adams, Alice; Paul D'Andrea, Rita Mae Brown"}
    self.assertEqual('Adams', wacart.break_out_agents(agentstring1)[0]['last_name'])
    self.assertEqual('Alice', wacart.break_out_agents(agentstring1)[0]['first_name'])
    self.assertEqual("D'Andrea", wacart.break_out_agents(agentstring1)[1]['last_name'])
    self.assertEqual('Paul', wacart.break_out_agents(agentstring1)[1]['first_name'])
    self.assertEqual("Brown", wacart.break_out_agents(agentstring1)[2]['last_name'])
    self.assertEqual('Rita', wacart.break_out_agents(agentstring1)[2]['first_name'])

    agentstring2 = {'creator_text_inverted':'Abramovic, Marina and Ulay Abramovic'}
    self.assertEqual('Marina', wacart.break_out_agents(agentstring2)[0]['first_name'])
    self.assertEqual('Abramovic', wacart.break_out_agents(agentstring2)[0]['last_name'])
    self.assertEqual('Abramovic', wacart.break_out_agents(agentstring2)[1]['last_name'])
    self.assertEqual('Ulay', wacart.break_out_agents(agentstring2)[1]['first_name'])

    agentstring3 = { 'creator_text_inverted':'Adal, Pepe Calvo; Jacques Charlier; Rose Farrell; George Parkin'}
    self.assertEqual('Adal', wacart.break_out_agents(agentstring3)[0]['last_name'])
    self.assertEqual('Pepe', wacart.break_out_agents(agentstring3)[0]['first_name'])
    self.assertEqual('Calvo', wacart.break_out_agents(agentstring3)[0]['middle_name'])
    self.assertEqual('Parkin', wacart.break_out_agents(agentstring3)[3]['last_name'])
    self.assertEqual('George', wacart.break_out_agents(agentstring3)[3]['first_name'])

    agentstring4 = { 'creator_text_inverted':'Abts, Tomma' }
    self.assertEqual('Abts', wacart.break_out_agents(agentstring4)[0]['last_name'])
    self.assertEqual('Tomma', wacart.break_out_agents(agentstring4)[0]['first_name'])

    agentstring5 = { 'creator_text_inverted': u"Vostell, Wolf; Becker, Jürgen"}
    self.assertEqual('Vostell', wacart.break_out_agents(agentstring5)[0]['last_name'])
    self.assertEqual('Wolf', wacart.break_out_agents(agentstring5)[0]['first_name'])
    self.assertEqual('Becker', wacart.break_out_agents(agentstring5)[1]['last_name'])
    self.assertEqual(u'Jürgen', wacart.break_out_agents(agentstring5)[1]['first_name'])

    agentstring6 = { 'creator_text_inverted': u"Cher" }
    self.assertEqual('Cher', wacart.break_out_agents(agentstring6)[0]['last_name'])

    agentstring7 = { 'creator_text_inverted': 'von Wiegand, Charmion' }
    self.assertEqual('von Wiegand', wacart.break_out_agents(agentstring7)[0]['last_name'])

  def testGuessNameOrder(self):
    namestring1 = "Smith, Bob"
    self.assertEqual("Smith", wacart.guess_name_order(namestring1)['last_name'])
    self.assertEqual("Bob", wacart.guess_name_order(namestring1)['first_name'])
  
    namestring2 = "Bob Smith"
    self.assertEqual("Smith", wacart.guess_name_order(namestring2)['last_name'])
    self.assertEqual("Bob", wacart.guess_name_order(namestring2)['first_name'])
  
    namestring3 = "Bob Midname Smith"
    self.assertEqual("Smith", wacart.guess_name_order(namestring3)['last_name'])
    self.assertEqual("Bob", wacart.guess_name_order(namestring3)['first_name'])
    self.assertEqual("Midname", wacart.guess_name_order(namestring3)['middle_name'])
  
    namestring4 = "Smith, Bob Midname"
    self.assertEqual("Smith", wacart.guess_name_order(namestring4)['last_name'])
    self.assertEqual("Bob", wacart.guess_name_order(namestring4)['first_name'])
    self.assertEqual("Midname", wacart.guess_name_order(namestring4)['middle_name'])

    namestring5 = "D'Smith, Bob"
    self.assertEqual("D'Smith", wacart.guess_name_order(namestring5)['last_name'])
    self.assertEqual("Bob", wacart.guess_name_order(namestring5)['first_name'])

    namestring6 = "Bob"
    self.assertEqual("Bob", wacart.guess_name_order(namestring6)['last_name'])

    namestring7 = "von Smith, Bob"
    self.assertEqual("von Smith", wacart.guess_name_order(namestring7)['last_name'])
    self.assertEqual("Bob", wacart.guess_name_order(namestring7)['first_name'])
  
if __name__ == "__main__":
    unittest.main()   
