#!/usr/bin/env python

"""
Reads a FileMaker export of the WACART database, saves python data
structures thereof.

"""

import re
import pickle
from csconstants import *

NAME_DELIMITERS = [';', ' and ']

# order important! Must match input.
COLUMNS = [
  {'name':  "condition", 'repeat': True},
  {'name':  "condition_date", 'repeat': True},
  {'name':  'iaia_subject', 'repeat': True},
  {'name':  'running_time' }, # insert if 'minutes' appears, report otherwise? Note that some will be x minutes y seconds
  {'name':  'width', 'repeat': True}, # will be inches internally.
  {'name':  'depth', 'repeat': True},
  {'name':  'height', 'repeat': True},
  {'name':  'dim_description'}, # "part" of description
  {'name':  'dimensions'}, # summary text
  {'name':  'weight', 'repeat': True},
  {'name':  'edition', 'repeat': True}, # TODO repeat characters appear, but they should be joined into one string (eg. ['A/P 4/10 (edition', 'of 250, 10 A/P)']
  {'name':  'cast_no'}, # a few weird values
  {'name':  'signature' },
  {'name':  'workshop_number', 'repeat': True},
  {'name':  'signed_location', 'repeat': True},
  {'name':  'printers_marks', 'repeat': True},
  {'name':  'foundry_marking', },
  {'name':  'inscription_location', 'repeat': True},
  {'name':  'medium', 'repeat': True},
  {'name':  'support', 'repeat': True},
  {'name':  'description', 'repeat': True},
  {'name':  'sex', 'repeat': True}, # some / dividing too. agent
  {'name':  'genre'},
  {'name':  'iaia_style'},
  {'name':  'unique_frame'},
  {'name':  'frame', 'repeat': True}, # TODO could use cleanup
  {'name':  'number_of_pages'},
  {'name':  'vol_no'},
  {'name':  'binding'},
  {'name':  'slipcase'},
  {'name':  'master'},
  {'name':  'submaster'},
  {'name':  'portfolio', 'repeat': True},
  {'name':  'media'}, # might be repeat, probably schema extension 'format'
  {'name':  'related_material_location'},
  {'name':  "acc_no"}, 
  {'name':  "old_acc_no"},
  {'name':  "lc_no"},
  {'name':  "object_id"},
  {'name':  "classification"},  # heirarchical in cspace, though WAC may not need that.
  {'name':  'status'}, # will be CSpace schema extension, as WAC needs to repeat. 
  {'name':  'title', 'repeat': True},
  {'name':  "credit_line", 'repeat': True}, # this and next 3: confusing re: acquisition databases, what's canonical
  {'name':  'initial_value'},
  {'name':  'initial_price'}, # most numbers, some more narrative
  {'name':  'current_value', 'repeat': True}, # this and following 2 are connected
  {'name':  'valuation_date', 'repeat': True},
  {'name':  'valuation_source', 'repeat': True},
  {'name':  'source', 'repeat': True}, # other stuff in another FM DB
  {'name':  'date'}, # bit more complicated. Report exceptions to JK?
  {'name':  'catalog_raisonne_ref'},
  {'name':  'fabricator'}, # next 4 are organizations
  {'name':  'foundry'}, 
  {'name':  'printer', 'repeat': True},
  {'name':  'publisher', 'repeat': True},
  {'name':  "editor"}, # agent. lots of copyright stuff though. cleanup?
  {'name':  'creator_text_inverted'}, # definitely prepare report here
  {'name':  'author'}, # agent 
  {'name':  'author_birth_year'}, # agent. gets turned into 'born'
  {'name':  'born'}, # / delimitiers. agents
  {'name':  'author_death_year'}, # agent. / delimiters but also full dates, so only slice \d{4}/\d{4}
  {'name':  'died'}, # agent
  {'name':  'author_gender'}, # agent
  {'name':  "mnartist"}, # will need to do some mapping of the different yes/no values. agent
  {'name':  "ethnicity"}, # agent. 
  {'name':  "author_nationality"}, # agent
  {'name':  'nationality'}, # agent
  {'name':  'author_birth_place'}, # agent
  {'name':  'birth_place'}, # agent
  {'name':  'last_name'}, # ignored
  {'name':  'reproduction_rights'}
 ]

def parse_line(line):
  """Parses a FileMaker export of the WACArt database, returning one
  dict for the object, one for the related agent(s).
  Expects a string."""

  # 
  # FileMaker gives us OS 9-era output.
  #
  line = line.decode('mac-roman').encode('utf-8')

  objekt = {}
  fields = line.split("\t")

  for i in range(len(COLUMNS)):
    objekt[COLUMNS[i]['name']] = fields[i]
    if COLUMNS[i].has_key('repeat'):
      break_out_multiple_objects(COLUMNS[i]['name'], objekt)

  for field in objekt.keys():
    trim_extra_spaces(field, objekt)
  agents = []
  agents = break_out_agents(objekt)

  # Other fields may benefit from this as well, but it's a prime
  # offender
  #objekt['on_view_location'] = objekt['on_view_location'].replace("\n", "")

  return objekt, agents

def just_space(field):
  """Is the field only whitespace?"""
  match = re.search(r'^\s*$', field)
  if match is None:
    return False
  return True

def break_out_multiple_objects(field, target): 
  """Given the name of a potentially repeating field, fix up that field
  appropriately"""

  # Due to multiple possible delimeters in the export from FM, the
  # object in question could already be a list. Assume that a given
  # field will only have one type of delimiters.
  for delimiter in ["", ""]:
    if type(target[field]) == type(""):
      if target[field].find(delimiter) > -1:
        all_values = target[field].split(delimiter)
        return_values = []
        for i in range(len(all_values)):
          if not just_space(all_values[i]):
            return_values.append(all_values[i])
        if len(return_values) == 1:
          target[field] = return_values[0]
        else:
          target[field] = return_values
  # Wrap single values in arrays so that code down the line isn't
  # confused
  if type(target[field]) != type([]):
    target[field] = [ target[field] ]

def trim_extra_spaces(field, target):
  if type(target[field]) != type("") and type(target[field]) != type(u''):
    # TODO might want to handle lists here, as their constituents might
    # have funky spaces. Revisit if it's a problem in practice.
    return
  target[field] = strip_spaces(target[field])

def has_delimiter(namesstring):
  for delim in NAME_DELIMITERS:
    if namesstring.find(delim) >= 0:
      return True
  return False

def split_on_common_name_delim(namesstring):
  for delim in NAME_DELIMITERS:
    if namesstring.find(delim) >= 0:
      return namesstring.split(delim)

def looks_like_commas_between_names(namesstring):
  match = re.search(r'[A-Z]\S+\s+\S+,', namesstring)
  if match is None:
    return False
  else:
    return True

def strip_spaces(string):
  string = re.sub(r'^\s*', '', string)
  string = re.sub(r'\s*$', '', string)
  return string
  
def unpack_agent_names(namestuff):
  """Given a string containing all the agent names, return a list of
    the names in whatever form they occur (inverted or not)"""

  if type(namestuff) == type([]):
    # ironically, the creator_text_inverted never intentionally uses the
    #  divider
    namestuff = namestuff[0]
  if namestuff.find(';') >= 0:
    first, sep, rest = namestuff.partition(';')
    names = [first]
    if has_delimiter(rest):
      names += split_on_common_name_delim(rest)
    else:
      if looks_like_commas_between_names(rest):
        names += rest.split(',')
      else:
        names.append(rest)
  else:
    if namestuff.find(' and ') >= 0:
      names = namestuff.split(' and ')
    else:
      if looks_like_commas_between_names(namestuff):
        names = namestuff.split(',')
      else:
        names = [namestuff]
  names = [strip_spaces(name) for name in names]
  return names

def break_out_agents(agentdict):
  """
  Given a dict of agent-related info from FM export, returns a list of
  dicts, one per agent. Order: artist(s)/author(s)/editor.
  TODO there's lots of overlap in the artist / author sections, which might be
  worth breaking out to a function
  """

  # Name delimiters could be [';', 'and']. Sometimes names after the
  # first are inverted, sometimes they ain't.  More strangly, sometimes
  # the names aren't inverted and they're separated by commas! On top of
  # all that, subsequent fields (born, died, nationality, etc.) have their
  # own delimiter rules.

  agents = []

  artists = unpack_agent_names(agentdict['creator_text_inverted'])
  artists = [guess_name_order(name) for name in artists]

  for delim in ['/', ';', ',']:
    if agentdict.has_key('born') and agentdict['born'].find(delim) >= 0:
      dates = agentdict['born'].split(delim)
      for i in range(len(dates)):
        if len(artists) > i:
          artists[i]['born'] = dates[i]

  if agentdict.has_key('born') and not artists[0].has_key('born'):
    artists[0]['born'] = agentdict['born']
      
  for field in ['birth_place', 'sex']:
    if agentdict.has_key(field) and type(agentdict[field]) == type([]):
      for i in range(len(agentdict[field])):
        if len(artists) > i:
          artists[i][field] = agentdict[field][i]
        else:
          print "This record has a birth place / sex that is perplexing: %s %s, from %s" \
            % (field, agentdict[field], agentdict['creator_text_inverted'])
      
  # These fields rarely, if ever, repeat
  for field in ['died', 'ethnicity', 'nationality']:
    if agentdict.has_key(field):
      artists[0][field] = agentdict[field]

  for artist in artists:
    artist['agent_type'] = 'artist'
    agents.append(artist)

  if agentdict.has_key('author') and agentdict['author'] != '':
    authors = unpack_agent_names(agentdict['author'])
    authors = [guess_name_order(name) for name in authors]

    for delim in ['/', ';', ',']:
      if agentdict.has_key('author_birth_place') and agentdict['author_birth_place'].find(delim) >= 0:
        dates = agentdict['author_birth_place'].split(delim)
        for i in range(len(dates)):
          if len(authors) > i:
            authors[i]['author_birth_place'] = dates[i]

    if agentdict.has_key('author_birth_year'):
      authors[0]['born'] = agentdict['author_birth_year']
        
    for field in ['author_birth_place', 'author_gender']:
      if agentdict.has_key(field) and type(agentdict[field]) == type([]):
        for i in range(len(agentdict[field])):
          if len(authors) > i:
            authors[i][field] = agentdict[field][i]
        
    # These fields rarely, if ever, repeat
    for field in ['author_death_year', 'author_nationality']:
      if agentdict.has_key(field):
        authors[0][field] = agentdict[field]

    for author in authors:
      author['agent_type'] = 'author'
      agents.append(author)

  if agentdict.has_key('editor') and agentdict['editor'] != '':
    editor = guess_name_order(agentdict['editor'])
    editor['agent_type'] = 'editor'
    agents.append(editor)

  for gent in agents:
    for field in gent.keys():
      trim_extra_spaces(field, gent)
  return agents

def guess_name_order(namestring):
   """given a name, guess what part is first and which is last. return
   hash with keys first_name, last_name"""

   names = {}
   if (namestring.find(',') > -1) and (namestring.find(',') < (len(namestring) - 1)):
     names['last_name'], names['first_name'] = namestring.split(',', 1)
     trim_extra_spaces('first_name', names)
     match = re.search(r'^(\S+)\s+(\S+)$', names['first_name'])
     if match is None:
       return names
     else:
       names['first_name'], names['middle_name'] = match.groups()[0], match.groups()[1]
       return names

   match = re.search(r'^(\S+)\s+(\S+)$', namestring)
   if match is not None:
     names['last_name'], names['first_name'] = match.groups()[1], match.groups()[0]
     return names

   match = re.search(r'^(\S+)\s+(\S+\s?\S?)\s(\S+)$', namestring)
   if match is not None:
     names['last_name'], names['first_name'], names['middle_name'] = (match.groups()[2], 
       match.groups()[0], match.groups()[1])
     return names

   return {'last_name': namestring}

def some_agent_names_from_string(string, delimiter):
  if string.find(delimiter) > -1:
    some_agents = string.split(delimiter)
    if some_agents[-1] == "":
      some_agents.pop()
    return some_agents
  return []

def note_oddities(objekt):
  """
  TODO something smoother re: opening these files. And/or emptying them
  out at first.
  """
  RUNTIME = open('runtime.log', 'a')
  FRAME = open('frame.log', 'a')
  ETHNICITY = open('ethnicity.log', 'a')
  AGENTS = open('agents.log', 'a')
  EDITORS = open('editors.log', 'a')

  weird_name = False
  for agent in objekt['agents']:
    for prob in [';', '&', ':', '(', 'et al']:
      if agent.has_key('last_name') and agent['last_name'].find(prob) > -1:
        weird_name = True

  if weird_name:
    AGENTS.write("for object %s, we parsed '%s' as:\n" % (objekt['object_id'], objekt['creator_text_inverted']))
    for agent in objekt['agents']:
      for field in ['first_name', 'middle_name', 'last_name']:
        if agent.has_key(field):
          AGENTS.write("  %s: %s\n" % (field, agent[field]))
          if field == 'last_name':
            AGENTS.write("\n")

  if type(objekt['running_time']) == type(''):
    if objekt['running_time'] != '' and objekt['running_time'].find('inute') < 0:
      RUNTIME.write("%s: %s\n" % (objekt['object_id'], objekt['running_time']))

  match = re.search(r'\d', objekt['ethnicity'])
  if match is not None:
    ETHNICITY.write("%s: %s\n" % (objekt['object_id'], objekt['ethnicity']))

  understood_frames = ['Artist Specified Framing', 'Yes', 'yes', 'No',
    'no', 'No Frame', 'Unique Frame', 'Frame', ['no', 'No Frame'],
    ['yes', 'Frame'], ['Yes', 'Frame'], ['No', 'No Frame'], ['N.A.',
    'No Frame'], ['Frame', 'Artist Specified Framing']]
  if objekt['frame'] != '' and not objekt['frame'] in understood_frames:
    FRAME.write("%s: %s\n" % (objekt['object_id'], objekt['frame']))

  match = re.search(r'the undersigned', objekt['editor'])
  if match is not None:
    EDITORS.write("%s: %s\n" % (objekt['object_id'], objekt['editor']))

if __name__ == "__main__":
  TABFILE = open('wacart.tab')
  BADLINES = open('badlines.log', 'w')

  objects = []

  for line in TABFILE:
    try:
      objekt, agents = parse_line(line)
    except ValueError as err:
      BADLINES.write("%s: %s" % (err, line))

    print "--------------------"
    for row in COLUMNS:
      field = row['name']
      if type(objekt[field]) == type([]):
        for datum in objekt[field]:
          print "%s -- '%s'" % (field, datum)
      else:
        print "%s -- '%s'" % (field, objekt[field])
    print "--------------------"
    print "Agent details:"
    for agent in agents:
      for field in agent.keys():
        print "%s -- '%s'" % (field,  agent[field])
    objekt['agents'] = agents
    objects.append(objekt)

    note_oddities(objekt)

  TABFILE.close()

  output = open(WAC_OBJECTS_FILE, 'wb')
  pickle.dump(objects, output)
  output.close()
