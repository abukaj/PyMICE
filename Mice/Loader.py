#!/usr/bin/env python
# encoding: utf-8
"""
MiceLoader.py

Created by Szymon Łęski on 2012-10-11.

Seriously damaged, then refactored and restored to glory by Jakub Kowalski on
14-15.01.2013.

Copyright (c) 2012-2013 Laboratory of Neuroinformatics. All rights reserved.
"""

import sys
import os
from matplotlib import rc
import time

from datetime import datetime

import zipfile
import csv
import warnings
import operator

from .Data import MiceData, deprecated

try:
  from NeuroinfMice import emptyStringToNone

except Exception as e:
  print type(e), e

  def emptyStringToNone(l):
    for i, x in enumerate(l):
      if type(x) is list:
        emptyStringToNone(x)

      elif x == '':
        l[i] = None

    return l


EPOCH = datetime(1970,1,1)
UTC_OFFSET = time.mktime(EPOCH.timetuple())

def convertTime(tStr):
  tSplit = tStr.replace('-', ' ').replace(':', ' ').split()
  subSec = float(tSplit[5]) if len(tSplit) == 6 else 0.
  return (datetime(*map(int, tSplit[:5])) - EPOCH).total_seconds() + subSec + UTC_OFFSET # a hook for backward compatibility

  #try:
  #  return time.mktime(time.strptime(tSplit[0], '%Y-%m-%d %H:%M:%S'))\
  #         + subSec

  #except ValueError:
  #  return time.mktime(time.strptime(tSplit[0], '%Y-%m-%d %H:%M'))\
  #         + subSec

#def convertFloat(x):
#  return None if x == '' else float(x.replace(',', '.'))

convertFloat = operator.methodcaller('replace', ',', '.')

def convertInt(x):
  return None if x == '' else int(x)


def convertStr(x):
  return None if x == '' else x


class MiceLoader(MiceData):
  _legacy = {'Animals': {'Name': 'AnimalName',
                         'Tag': 'AnimalTag',
                         'Group': 'GroupName',
                         'Notes': 'AnimalNotes',
                        },
             'Groups': {'Name': 'GroupName',
                        'Notes': 'GroupNotes',
                       },
             'Visits': {'Animal': 'AnimalTag',
                        'ID': 'VisitID',
                        'Module': 'ModuleName',
                       },
             'Nosepokes': {'LicksNumber': 'LickNumber',
                           'LicksDuration': 'LickDuration',
                          },
             'Log': {'Type': 'LogType',
                     'Category': 'LogCategory',
                     'Notes': 'LogNotes',
                    },
             'HardwareEvents': {'Type': 'HardwareType',
                               },
            }

  _aliasesZip = {'Animals': {'AnimalName': 'Name',
                             'AnimalTag': 'Tag',
                             'GroupName': 'Group',
                             'AnimalNotes': 'Notes',
                            },
                 'Groups': {'GroupName': 'Name',
                            'GroupNotes': 'Notes',
                            'ModuleName': 'Module',
                           },
                 'IntelliCage/Groups': {'GroupName': 'Name',
                                        'GroupNotes': 'Notes',
                                        'ModuleName': 'Module',
                                       },
                 'IntelliCage/Visits': {'AnimalTag': 'Tag',
                                        'Animal': 'Tag', 
                                        'ID': '_vid',
                                        'VisitID': '_vid',
                                        'ModuleName': 'Module',
                                       },
                 'IntelliCage/Nosepokes': {'LicksNumber': 'LickNumber',
                                           'LicksDuration': 'LickDuration',
                                           'VisitID': '_vid',
                                          },
                 'IntelliCage/Log': {'LogType': 'Type',
                                     'Log': 'Type',
                                     'LogCategory': 'Category',
                                     'LogNotes': 'Notes',
                                    },
                 'IntelliCage/HardwareEvents': {'HardwareType': 'Type',
                                               },
                }
  _convertZip = {'Animals': {'Tag': int,
                             'Group': convertStr,
                             'Notes': convertStr,
                             'Sex': convertStr,
                            },
                 'Groups': {#'Name': convertStr,
                            'Notes': convertStr,
                           },
                 'IntelliCage/Groups': {#'Name': convertStr,
                                        'Notes': convertStr,
                                       },
                 'IntelliCage/Visits': {'Tag': int,
                                        '_vid': int,
                                        'Start': convertTime,
                                        'End': convertTime,
                                        #'ModuleName': convertStr,
                                        #'Cage': int,
                                        #'Corner': int,
                                        'CornerCondition': convertFloat,
                                        'PlaceError': convertFloat,
                                        #'AntennaNumber': convertInt,
                                        'AntennaDuration': convertFloat,
                                        #'PresenceNumber': convertInt,
                                        'PresenceDuration': convertFloat,
                                        #'VisitSolution': convertInt,
                                       },
                 'IntelliCage/Nosepokes': {'_vid': int,
                                           'Start': convertTime,
                                           'End': convertTime,
                                           #'Side': int,
                                           #'LickNumber': int,
                                           'LickContactTime': convertFloat,
                                           'LickDuration': convertFloat,
                                           'SideCondition': convertFloat,
                                           'SideError': convertFloat,
                                           'TimeError': convertFloat,
                                           'ConditionError': convertFloat,
                                           #'AirState': convertInt,
                                           #'DoorState': convertInt,
                                           #'LED1State': convertInt,
                                           #'LED2State': convertInt,
                                           #'LED3State': convertInt,
                                          },
                 'IntelliCage/Log': {'DateTime': convertTime,
                                     #'Category': convertStr,
                                     #'Type': convertStr,
                                     #'Cage': convertInt,
                                     #'Corner': convertInt,
                                     #'Side': convertInt,
                                     #'Notes': convertStr,
                                    },
                 'IntelliCage/Environment': {'DateTime': convertTime,
                                             'Temperature': convertFloat,
                                             #'Illumination': convertInt,
                                             #'Cage': convertInt,
                                            },
                 'IntelliCage/HardwareEvents': {'DateTime': convertTime,
                                                'Type': convertInt,
                                                'Cage': convertInt,
                                                'Corner': convertInt,
                                                'Side': convertInt,
                                                'State': convertInt,
                                               },
                }

  def _loadZip(self, fname, getNpokes=False, getLogs=False, getEnvironment=False, source=None):
    zf = zipfile.ZipFile(fname)
    animalsLabels = set()
    animals = self._fromZipCSV(zf, 'Animals', oldLabels=animalsLabels)
    legacyFormat = 'Tag' in animalsLabels

    animalGroup = animals.pop('Group')
    animals = self._makeDicts(animals)

    animalNames = set()
    groupMembers = {}
    tag2Animal = {}
    for group, animal in zip(animalGroup, animals):
      tag = animal['Tag']
      assert tag not in tag2Animal
      name = animal['Name']
      assert name not in animalNames
      tag2Animal[tag] = name
      animalNames.add(name)

      if group is not None:
        try:
          groupMembers[group][name] = animal

        except KeyError:
          groupMembers[group] = {name: animal}


    try:
      groups = self._fromZipCSV(zf,
                            'IntelliCage/Groups' if legacyFormat else 'Groups')

    except KeyError as e:
      warnings.warn(str(e))
      groups = {}

    else:
      groupNames = groups['Name']
      groups = dict(zip(groupNames, self._makeDicts(groups)))

    for group, members in groupMembers.items():
      try:
        groups[group]['Animals'] = members

      except KeyError as e:
        warnings.warn(str(e))
        groups[group] = {'Name': group,
                         'Members': members.keys()}

    groups = groups.values()
    for group in groups:
      if 'Animals' not in group:
        group['Animals'] = []

    visits = self._fromZipCSV(zf, 'IntelliCage/Visits', source=source)
    tags = visits.pop('Tag')
    vids = visits.pop('_vid')

    visits['Animal'] = [tag2Animal[tag] for tag in tags]

    orphans = []
    if getNpokes:
      visitNosepokes = [[] for vid in vids]
      vid2nps = dict(zip(vids, visitNosepokes))

      nosepokes = self._fromZipCSV(zf, 'IntelliCage/Nosepokes', source=source)
      npVids = nosepokes.pop('_vid')

      nosepokes = self._makeDicts(nosepokes)
      for vid, nosepoke in zip(npVids, nosepokes):
        try:
          vid2nps[vid].append(nosepoke)

        except KeyError:
          nosepoke['VisitID'] = vid
          orphans.append(nosepoke)

      map(operator.methodcaller('sort',
                                key=operator.itemgetter('Start', 'End')),
          visitNosepokes)
      visits['Nosepokes'] = visitNosepokes


    else:
      visits['Nosepokes'] = [None] * len(tags)
      
    visits = self._makeDicts(visits)
    result = {'animals': animals,
              'groups': groups,
              'visits': visits,
              'nosepokes': orphans,
             }

    if getLogs:
      logs = self._fromZipCSV(zf, 'IntelliCage/Log', source=source)
      result['logs'] = self._makeDicts(logs)

    if getEnvironment:
      environment = self._fromZipCSV(zf, 'IntelliCage/Environment', source=source)
      result['environment'] = self._makeDicts(environment)

    return result

  @staticmethod
  def _makeDicts(data):
    keys = data.keys()
    data = [data[k] for k in keys]
    return [dict(zip(keys, values)) for values in zip(*data)]


  def _fromZipCSV(self, zf, path, source=None, oldLabels=None):
    return self._fromCSV(zf.open(path + '.txt'), source=source,
                         aliases=self._aliasesZip.get(path),
                         convert=self._convertZip.get(path),
                         oldLabels=oldLabels)

  @staticmethod
  def _fromCSV(fname, source=None, aliases=None, convert=None, oldLabels=None):
    if isinstance(fname, basestring):
      fname = open(fname, 'rb')

    reader = csv.reader(fname, delimiter='\t')
    data = list(reader)
    fname.close()

    return MiceLoader.__fromCSV(data, source, aliases, convert, oldLabels)

  @staticmethod
  def __fromCSV(data, source, aliases, convert, oldLabels):
    if len(data) == 0:
      return

    labels = data.pop(0)
    if isinstance(oldLabels, set):
      oldLabels.clear()
      oldLabels.update(labels)

    if aliases is not None:
      labels = [aliases.get(l, l) for l in labels]

    n = len(data)
    if n == 0:
      return dict((l, []) for l in labels)
    
    #noneMapper = lambda x: x or None
    #data = map(lambda row: map(noneMapper, row), data)
    #data = [[x or None for x in row] for row in data]
    emptyStringToNone(data)
    data = dict(zip(labels, zip(*data)))
    if source is not None:
      assert '_source' not in data
      data['_source'] = [source] * n

      assert '_line' not in data
      data['_line'] = range(1, n + 1)

    if convert is not None:
      for label, f in convert.items():
        if label in data:
          data[label] = map(f, data[label])

    return data

  def __init__(self, fname, **kwargs):
    """
    getNpokes = False,
    bin = 3600,
    verbose = False.
    """
    MiceData.__init__(self, verbose = kwargs.get('verbose', False),
                      getNpokes=kwargs.get('get_npokes',
                                           kwargs.get('getNpokes', False)),
                      getLogs=kwargs.get('getLogs'),
                      getEnv=kwargs.get('getEnv'))

    self._getHardware = kwargs.get('getHardware', False)
    self._get_SB = kwargs.get('get_SB', False)
    self._get_AG = kwargs.get('get_AG', False)

    self._initCache()

    self.envdata = []

    self._fnames = (fname,)



    self.appendData(fname)

    for t, msg in self.getSQL("""
                              SELECT "DateTime", "LogNotes"
                              FROM log
                              WHERE "LogCategory" = 'Info' AND "LogType" = 'Application';
                              """, unwrap=False):
      if msg == 'Session is started':
        self.icSessionStart = t

      elif msg == 'Session is stopped':
        self.icSessionEnd = t

      else:
        print 'unknown Info/Application message: %s' % msg




    self._logAnalysis(kwargs.get('loganalyzers', []))

    rc('mathtext', fontset='stixsans')



  def __repr__ (self):
    """
    Nice string representation for prtinting this class.
    """
    mystring = 'IntelliCage data loaded from: %s' %\
               self._fnames.__str__()
    return mystring

  def appendData(self, fname):
    """
    Process one input file and append data to self.data
    """
    fname = fname.encode('utf-8') # stupid users!
    print 'loading data from %s' % fname
    #sid = self._registerSource(fname.decode('utf-8'))

    if fname.endswith('.zip'):
      data = self._loadZip(fname,
                           getNpokes=self._getNpokes,
                           getLogs=self._getLogs,
                           getEnvironment=self._getEnv,
                           source=fname.decode('utf-8'))
      animals = data['animals']
      groups = data['groups']
      visits = data['visits']
      orphans = data['nosepokes']

      if len(orphans) > 0:
        warnings.warn('Unmatched nosepokes: %s' % orphans)


      for animal in animals:
        self._registerAnimal(animal)

      for group in groups:
        self._registerGroup(**group)
        #members = group['Animals']
        #for animal in members:
        #  self._addMember(group['Name'], animal)

      self._insertVisits(visits)

      if self._getLogs:
        self._insertLogs(data['logs'])

      if self._getEnv:
        self._insertEnvironment(data['environment'])

      #self.loadZip(fname,
      #             getNpokes=self._getNpokes,
      #             getHardware = self._getHardware,
      #             get_sb=self._get_SB,
      #             get_ag=self._get_AG,
      #             sid = sid)

    else:
      # Is that the right thing to do with directories?
      if os.path.isdir(fname):
        fname = os.path.join(fname, 'Visits.txt')

      visits = self.fromCSV(fname, True)

      startDate = visits.pop('StartDate')
      startTime = visits.pop('StartTime')
      #start = ['%s %s' % x for x in zip(startDate, startTime)]
      #visits['Start'] = convertTime(start)
      # Daylight saving time issue -_-

      time0 = convertTime(startDate[0] + ' ' + startTime[0])
      startTimecode = visits.pop('StartTimecode')
      offset = time0 - float(startTimecode[0])
      visits['Start'] = [offset + float(x) for x in startTimecode]

      #endDate = visits.pop('EndDate')
      #endTime = visits.pop('EndTime')
      #end = ['%s %s' % x for x in zip(endDate, endTime)]
      #visits['End'] = convertTime(end)
      endTimecode = visits.pop('EndTimecode')
      visits['End'] = [offset + float(x) for x in endTimecode]
      del visits['EndDate']
      del visits['EndTime']

      del visits['VisitDuration'] # maybe some validation?
      visits['ModuleName'] = visits.pop('Module')
      animalTag = map(int, visits.pop('Tag'))
      visits['AnimalTag'] = animalTag

      ccMap = {'Neutral': 0.,
               'Correct': 1.,
               'Incorrect': -1.}

      cc = visits['CornerCondition']
      visits['CornerCondition'] = [(ccMap[c] if c in ccMap else convertFloat(c)) for c in cc]

      aGroups = visits.pop('Group')
      aNames = visits.pop('Animal')
      aSexes = visits.pop('Sex')

      # registering animals and groups
      tag2aid = {}
      for name, tag, sex in list(set(zip(aNames, animalTag, aSexes))):
        if sex not in ('Male', 'Female', 'Unknown'):
          print "Unknown sex: %s" % sex

        aid = self._registerAnimal(name, tag,
                                   sex if sex != 'Unknown' else None)
        tag2aid[tag] = aid

      group2gid = {}
      for group in list(set(aGroups)):
        self._registerGroup(group)

      for tag, group in list(set(zip(animalTag, aGroups))):
        aid = tag2aid[tag]
        self._addMember(group, aid)

      fakeNpokes = {}
      fakeNpokes['VisitID'] = list(visits['VisitID'])
      fakeNpokes['_line'] = list(visits['_line'])
      fakeNpokes['SideError'] = visits.pop('SideErrors')
      fakeNpokes['TimeError'] = visits.pop('TimeErrors')
      fakeNpokes['ConditionError'] = visits.pop('ConditionErrors')
      fakeNpokes['NosepokeNumber'] = visits.pop('NosepokeNumber')
      fakeNpokes['NosepokeDuration'] = visits.pop('NosepokeDuration')
      fakeNpokes['LickNumber'] = visits.pop('LickNumber')
      fakeNpokes['LickDuration'] = visits.pop('LickDuration')
      fakeNpokes['LickContactTime'] = visits.pop('LickContactTime')

      vidMapping = self._insertVisits(visits, tag2aid, 'AnimalTag',
                                      'VisitID', sid = sid)

      if self._get_npokes:
        self._insertNosepokes(fakeNpokes, vidMapping, 'VisitID', sid = sid)

      try:
        fh = open(os.path.join(os.path.dirname(fname),
                               'Environment.txt'))
        env = self.fromCSV(fh, True)
        fh.close()

        env['DateTime'] = convertTime(env['DateTime'])
        self._insertDataSid(env, 'environment', sid)

      except IOError:
        print "'Environment.txt' not found."

      try:
        fh = open(os.path.join(os.path.dirname(fname),
                               'Log.txt'))
        self.loadLog(fh, sid=sid)

      except IOError:
        print "'Log.txt' not found."

    self._buildCache()


  @staticmethod
  def convert_time(ll):
    print "WARNING: Deprecated method convert_time() called."
    return convertTime(ll)

  @staticmethod
  def fromCSV(fname, lines = False):
    """
    Read data from the CSV file into directory of lists.

    @type fname: str or file object
    """
    result = None

    if type(fname) is str:
      fname = open(fname)

    reader = csv.reader(fname, delimiter='\t')
    try:
      labels = reader.next()
      data = [x for x in reader]
      n = len(data)
      if n > 0:
        data = zip(*data)

      else:
        data = [[] for x in labels]

      result = dict(zip(labels, data))
      if lines:
        assert 'line' not in result
        result['_line'] = range(1, n + 1)

    except StopIteration:
      pass

    finally:
      fname.close()

    return result

  def loadZip(self, fname, getNpokes=False, get_sb=False, get_ag=False, sid=None,
              getHardware = False):
    zf = zipfile.ZipFile(fname)

    # loading file Animals.txt, checking legacy format
    animals = self.fromCSV(zf.open('Animals.txt'))
    if 'AnimalTag' not in animals:
      legacy_format = True
      animals = self._legacyUpdate(animals, 'Animals')

    aNames = animals['AnimalName']
    aTags = map(int, animals['AnimalTag'])
    aGroup = animals['GroupName']
    aNotes = animals['AnimalNotes']
    aSexes = animals['Sex']

    # registering animals
    aIds = []
    for name, tag, sex, notes in zip(aNames, aTags, aSexes, aNotes):
      if sex not in ('Male', 'Female', 'Unknown'):
        print "Unknown sex: %s" % sex

      aid = self._registerAnimal(name, tag,
                                 sex if sex != 'Unknown' else None,
                                 notes if notes != '' else None)
      aIds.append(aid)

    tag2aid = dict(zip(aTags, aIds))

    # loading file Groups.txt
    try:
      if legacy_format:
        groups = self.fromCSV(zf.open('IntelliCage/Groups.txt'))
        groups = self._legacyUpdate(groups, 'Groups')

      else:
        groups = self.fromCSV(zf.open('Groups.txt'))

    except KeyError:
      pass

    else:
      gNames = groups['GroupName']
      gNotes = groups['GroupNotes']
      gModules = groups['ModuleName']

      for name, notes, module in zip(gNames, gNotes, gModules):
        self._registerGroup(name, notes if notes != '' else None,
                                  module if module != '' else None)

      for aid, group in zip(aIds, aGroup):
        self._addMember(group, aid)

    

    visits = self.fromCSV(zf.open('IntelliCage/Visits.txt'), True)

    if visits == None:
      return

    if legacy_format:
      visits = self._legacyUpdate(visits, 'Visits')

    visits['Start'] = convertTime(visits['Start'])
    visits['End'] = convertTime(visits['End'])
    visits['AnimalTag'] = map(int, visits['AnimalTag'])
    vidMapping = self._insertVisits(visits, tag2aid, 'AnimalTag',
                                    'VisitID', sid = sid)

    if getNpokes:
      npokes = self.fromCSV(zf.open('IntelliCage/Nosepokes.txt'), True)
      if legacy_format:
        npokes = self._legacyUpdate(npokes, 'Nosepokes')

      start = convertTime(npokes['Start'])
      end = convertTime(npokes['End'])
      npokes['Start'] = start
      npokes['End'] = end

      # prepare redundant data just for compatibility
      npokes['NosepokeDuration'] = [e - s for (e, s) in zip(end, start)]
      npokes['NosepokeNumber'] = [1] * len(start)

      self._insertNosepokes(npokes, vidMapping, 'VisitID', sid = sid)

    if getHardware:
      hardware = self.fromCSV(zf.open('IntelliCage/HardwareEvents.txt'))
      if legacy_format:
        hardware = self._legacyUpdate(hardware, 'HardwareEvents')

      hardware['DateTime'] = convertTime(hardware['DateTime'])
      self._insertDataSid(hardware, 'HardwareEvents', sid)

    # TODO: take care of SB & AG
    if get_sb:
      data = self.fromCSV(zf.open('SocialBox/SocialBoxRegistrations.txt'), True)
      start = convertTime(data['Start'])
      end = convertTime(data['End'])
      data['Start'] = start
      data['End'] = end
      self.insertData(data, 'socialboxregistrations')

    if get_ag:
      data = self.fromCSV(zf.open('AnimalGate/AnimalGateSessions.txt'), True)
      start = convertTime(data['Start'])
      end = convertTime(data['End'])
      data['Start'] = start
      data['End'] = end
      self.insertData(data, 'animalgatesessions')
    # END TODO

    try:
      env = self.fromCSV(zf.open('IntelliCage/Environment.txt'), True)

    except KeyError as e:
      print e

    else:
      env['DateTime'] = convertTime(env['DateTime'])
      self._insertDataSid(env, 'environment', sid)

    self.loadLog(zf.open('IntelliCage/Log.txt'), sid = sid)

  def loadLog(self, fname, sid = None):
    log = self.fromCSV(fname, True)
    if log == None:
      print 'Unable to read log'
      return

    if 'Type' in log: #legacy_format
      log = self._legacyUpdate(log, 'Log')

    #print log
    log['DateTime'] = convertTime(log['DateTime'])
    self._insertDataSid(log, 'log', sid)

    try:
      # TODO: Make it more intuitive
      # Process log
      errors = [(date, note, logtype) for date, note, category, logtype in
            zip(log['DateTime'], log['LogNotes'], log['LogCategory'],
            log['LogType']) if category == 'Error'
            and logtype not in ['Lickometer', 'Nosepoke']]


      if errors:
        print 'Errors in %s' %fname
        # for date, note, logtype in errors:
        #     print date, note #, logtype


      warnings = [(date, note, logtype) for date, note, category, logtype in
              zip(log['DateTime'], log['LogNotes'], log['LogCategory'],
              log['LogType']) if note.startswith('Unregistered tag')
              or note.startswith('Presence signal')]

      if warnings:
        print '%d warnings in %s' %(len(warnings), fname)
        notes = [note for _, note, _ in warnings]
        for note in set(notes):
          print "%s: %d time(s)" %(note, notes.count(note))

    except KeyError:
      print "ERROR: Invalid log"

if __name__ == '__main__':
  import doctest
  testDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../data/test'))
  ml_a1 = MiceLoader(os.path.join(testDir, 'analyzer_data.txt'))
  ml_l1 = MiceLoader(os.path.join(testDir, 'legacy_data.zip'))
  doctest.testmod(extraglobs={'ml_a1': ml_a1, 'ml_l1': ml_l1})
