#!/usr/bin/env python

"""
Reads the pickle files of records in CSpace and of records from the
WACArt FM export, and inserts appropriate things into CSpace.
"""

import httplib2
import pickle

from lxml import etree
from collections import defaultdict
from pprint import pprint
from csconstants import *

UNARY_OBJECT_FIELDS = [
  'running_time',
  'cast_no',
  'signature',
  'foundry_marking',
  'genre',
  'iaia_style',
  'unique_frame',
  'number_of_pages',
  'vol_no',
  'binding',
  'slipcase',
  'master',
  'submaster',
  'related_media_location',
  'acc_no',
  'old_acc_no',
  'lc_no',
  'object_id',
  'classification',
  'initial_value',
  'initial_price',
  'date',
  'catalog_raisonne_ref',
  'fabricator',
  'foundry',
  ]
REPEAT_OBJECT_FIELDS = [
  'condition',
  'condition_date',
  'iaia_subject', 
  'width',
  'depth',
  'height',
  'edition',
  'workshop_number',
  'signed_location',
  'printers_marks',
  'inscription_location',
  'medium',
  'support',
  'description',
  'sex',
  'frame'
  'portfolio',
  'media',
  'status',
  'title',
  'credit_line',
  'source',
  'printer',
  'publisher',
  ]
ARTIST_FIELDS = [
  'displayCreator',
  'sex',
  'born', 
  'died',
  'mnartist',
  'ethnicity',
  'nationality',
  'birth_place',
  ]
AUTHOR_FIELDS = [
  'author',
  'author_birth_year',
  'author_death_year',
  'author_gender',
  'author_nationality',
  'author_birth_place',
  ]
OTHER_AGENTS = [
  'editor',
  ]

def value_present(record, fieldname):
  if record.has_key(fieldname) and record[fieldname] is not None and record[fieldname] != '':
    return True
  else:
    return False
  

def insert_into_cspace(record):
  """
  return 1 on success, 0 on failure
  TODO split out at least preprocessing, which could become its own, testable method
  """
  object_values = defaultdict(lambda: None)

  for fieldname in UNARY_OBJECT_FIELDS:
    print "looking at std field '%s'" % fieldname
    if value_present(record, fieldname):
      print "  it's '%s'" % record[fieldname]
      object_values[fieldname] = record[fieldname]

  for fieldname in REPEAT_OBJECT_FIELDS:
    print "looking at repeating field '%s'" % fieldname
    object_values[fieldname] = []
    for element in record[fieldname]:
      print "checking element '%s'', which is the value for '%s'" % (element, fieldname)
      object_values[fieldname].append(element)
      #object_values[fieldname].append(element.text)

  # 
  # Can't have bare ampersands. There don't seem to be any encoded
  # ampersands coming our way, so we just do a replace.
  #
  for k in object_values.keys():
    if type(object_values[k]) != type([]) and object_values[k] is not None:
      object_values[k] = object_values[k].replace("&", "&amp;")
    if type(object_values[k]) == type([]):
      for i in range(len(object_values[k])):
        object_values[k][i] = object_values[k][i].replace("&", "&amp;")

  # TODO handle creators
  """
  Need to do this for artist, author, and editor, each of which has its
    own fields.
  Maybe it's time for agent to be classes? Or just a hash with type in
    [artist|author|editor]?
  Anyhow, for each do this:
  - see if they're in cspace already
  - if not, insert them
  - save away the relevant info so we can insert them into the
    collectionobject appropriately
  """
  #creators = record.findall(".//{http://www.getty.edu/CDWA/CDWALite/}indexingCreatorSet")
  #for creator in creators:
  #  person = {}
  #  for field in ARTIST_FIELDS:
  #    element = record.find(".//{http://www.getty.edu/CDWA/CDWALite/}%s" % field)
  #    if element is not None:
  #      person[field] = (element.text)
  #  creator_values.append(person)

  #
  # TODO these lines suggest that we might want to handle possibly
  # repeating values a little more intelligently, if we end up
  # tracking more of them
  #
  concepts = []
  for concept in object_values['iaia_subject']:
    concepts.append("<contentConcept>%s</contentConcept>" % concept)

  #
  # Schema is at https://source.collectionspace.org/collection-space/src/services/tags/v1.5/services/collectionobject/jaxb/src/main/resources/collectionobjects_common.xsd
  #
  # updated to account for
  # http://wiki.collectionspace.org/display/collectionspace/Imports+Service+Home
  #     
  object_xml = u'''
  <imports>
    <import seq="1" service="CollectionObjects" type="CollectionObject">
      <schema xmlns:collectionobjects_common="http://collectionspace.org/collectionobject/" name="collectionobjects_common">
        <collectionobjects_common:objectNumber>%s</collectionobjects_common:objectNumber>
        <collectionobjects_common:titleGroupList>
            <collectionobjects_common:titleGroup>
                <collectionobjects_common:title>%s</collectionobjects_common:title>
                <collectionobjects_common:titleLanguage>eng</collectionobjects_common:titleLanguage>
            </collectionobjects_common:titleGroup>
        </collectionobjects_common:titleGroupList>
        <collectionobjects_common:objectProductionDates>
          <collectionobjects_common:objectProductionDate>%s</collectionobjects_common:objectProductionDate>
        </collectionobjects_common:objectProductionDates>
        <collectionobjects_common:materialGroupList>
          <collectionobjects_common:materialGroup>
            <collectionobjects_common:material>%s</collectionobjects_common:material>
          </collectionobjects_common:materialGroup>
        </collectionobjects_common:materialGroupList>
        <collectionobjects_common:contentConcepts>
          %s
        </collectionobjects_common:contentConcepts>
        <collectionobjects_common:objectNameList>
          <collectionobjects_common:objectNameGroup>
            <collectionobjects_common:objectName>%s</collectionobjects_common:objectName>
            <collectionobjects_common:objectNameCurrency>current</collectionobjects_common:objectNameCurrency>
            <collectionobjects_common:objectNameType>classified</collectionobjects_common:objectNameType>
            <collectionobjects_common:objectNameSystem>In-house</collectionobjects_common:objectNameSystem>
            <collectionobjects_common:objectNameLanguage>eng</collectionobjects_common:objectNameLanguage>
          </collectionobjects_common:objectNameGroup>
        </collectionobjects_common:objectNameList>
        <collectionobjects_common:physicalDescription>%s</collectionobjects_common:physicalDescription>
        <collectionobjects_common:editionNumber>%s</collectionobjects_common:editionNumber>
        <collectionobjects_common:dimensionSummary>%s</collectionobjects_common:dimensionSummary>
        <collectionobjects_common:inscriptionContent>%s</collectionobjects_common:inscriptionContent>
        <collectionobjects_common:owners>
          <collectionobjects_common:owner>%s</collectionobjects_common:owner>
        </collectionobjects_common:owners>
      </schema>
    </import>
  </imports>
  ''' % (object_values['acc_no'], 
         object_values['title'],
         object_values['date'],
         object_values['displayMaterialsTech'], 
         "\n".join(concepts),
         object_values['objectWorkType'], 
         object_values['descriptiveNote'], 
         object_values['edition'], 
         object_values['dimensionSummary'], 
         object_values['inscription_location'], 
         object_values['locationName'], 
         )

  h = httplib2.Http()
  h.add_credentials(CSPACE_USER, CSPACE_PASS)
  resp, content = h.request(
    CSPACE_URL + 'imports',
    'POST',
    body = object_xml.encode('utf-8'),
    headers = {'Content-Type': 'application/xml'}
    )

  if resp['status'] == '200':
    if object_values['title'] is None:
      print "Inserted '%s' into collectionspace\n" % object_values['acc_no'].encode('utf-8')
    else:
      print "Inserted '%s' into collectionspace\n" % object_values['title'].encode('utf-8')
    return 1
  else:
    print "\nSomething went wrong with %s:" % object_values['acc_no'].encode('utf-8')
    print "record:"
    ovd = {}
    for key in object_values.keys():
      ovd[key] = object_values[key]
    pprint(ovd)
    print "Response: %s" % resp
    print "Content: %s\n" % content
    return 0

def load_cspace_objectids():
  pickle_file = open(CS_OBJECT_FILE, 'rb')
  cobjects = pickle.load(pickle_file)
  pickle_file.close()
  return cobjects

def load_wacart_objectids():
  pickle_file = open(WAC_OBJECTS_FILE, 'rb')
  cobjects = pickle.load(pickle_file)
  pickle_file.close()
  return cobjects

def prune_existing_records(objects, existing_objectids):
  return [obj for obj in objects if not obj['acc_no'] in existing_objectids]

def split_records_by_artist_count(records):
  """When there are multiple artists associated with a record, those
  other than the first one or two tend to not have any demographic info.
  Since those artists may appear elsewhere in the collection with said
  demographic info, we handle all the single artist records first.
  """
  single_artist_records = []
  multi_artist_records = []
  for record in records:
    if record.has_key('artists') and len(record['artists']) > 1:
      multi_artist_records.append(record)
    else:
      single_artist_records.append(record)
  return (single_artist_records, multi_artist_records)

if __name__ == "__main__":
  existing_cspace_records = load_cspace_objectids()
  print "existing records loaded"
  wacart_records = load_wacart_objectids()
  print "records to insert loaded"
  records_to_create = prune_existing_records(wacart_records, existing_cspace_records)
  print "records pruned"
  single_artist_records, multi_artist_records = split_records_by_artist_count(records_to_create)
  print "records split"

  total_records_created = 0

  for record in single_artist_records:
    total_records_created += insert_into_cspace(record)
    print "now have %s single artist records" % len(single_artist_records)
  for record in multi_artist_records:
    total_records_created += insert_into_cspace(record)
    print "now have %s multi artist records" % len(multi_artist_records)

  print "All records processed. Created %s new records.\n" % total_records_created
