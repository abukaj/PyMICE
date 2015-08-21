#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2015 Jakub M. Kowalski, S. Łęski (Laboratory of            #
#    Neuroinformatics; Nencki Institute of Experimental Biology)              #
#                                                                             #
#    This software is free software: you can redistribute it and/or modify    #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This software is distributed in the hope that it will be useful,         #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this software.  If not, see http://www.gnu.org/licenses/.     #
#                                                                             #
###############################################################################
from unittest import TestCase


def allInstances(instances, cls):
  return all(isinstance(x, cls) for x in instances)


class Mock(object):
  def __init__(self, callers={}, **kwargs):
    self.sequence = []
    self.__callers = dict(callers)
    for k, v in kwargs.items():
      setattr(self, k, v)

  def __getattr__(self, item):
    def method(*args):
      self._registerCall(((item,) + args) if args else item)
      if item in self.__callers:
        try:
          return self.__callers[item][args]

        except TypeError:
          print item, args
          raise

    return method

  def _registerCall(self, call):
    self.sequence.append(call)


class MockDictManager(Mock):
  def __init__(self, *args, **kwargs):
    super(MockDictManager, self).__init__(*args, **kwargs)
    self.managers = {}

  def getManager(self, item):
    self._registerCall(('getManager', item))
    try:
      return self.managers[item]

    except KeyError:
      manager = self.Manager()
      self.managers[item] = manager
      return manager

  def get(self, item):
    self._registerCall(('get', item))
    return self.Cls(item)


class MockIntDictManager(MockDictManager):
  def __init__(self, *args, **kwargs):
    super(MockIntDictManager, self).__init__(*args, **kwargs)
    self.Manager = MockIntDictManager

    class Cls(int):
      pass

    self.Cls = Cls


class MockCageManager(MockIntDictManager):
  def getCageCorner(self, cage, corner):
    return (self.get(cage),
            self.getManager(cage).get(corner))

  def getSideManager(self, cage, corner):
    return self.getManager(cage).getManager(corner)


class MockStrDictManager(MockDictManager):
  def __init__(self, *args, **kwargs):
    super(MockStrDictManager, self).__init__(*args, **kwargs)

    class Cls(str):
      pass

    self.Cls = Cls


# class MockAnimalManager(MockStrDictManager):
#   def getByTag(self, tag):
#     self._registerCall(('getByTag', tag))
#     return self.Cls(tag)


class MockCloneable(Mock):
  def clone(self, *args):
    self._registerCall((('clone',) + args) if args else 'clone')
    return Mock(_cloneOf=self)


class BaseTest(TestCase):
  def checkAttribute(self, obj, name, value=None, cls=None):
    try:
      attr = getattr(obj, name)
      if value is None:
        self.assertIs(attr, None,)

      else:
        self.assertEqual(attr, value)
        if cls is not None:
          self.assertIsInstance(attr, cls)

    except AssertionError:
      print name
      raise

  def checkAttributes(self, obj, testList):
    for test in testList:
      if isinstance(test, basestring):
        self.checkAttribute(obj, test)

      else:
        self.checkAttribute(obj, *test)

  def checkAttributeSeq(self, seq, name, tests):
    for obj, test in zip(seq, tests):
      if test is None:
        self.checkAttribute(obj, name)

      elif isinstance(test, tuple):
        self.checkAttribute(obj, name, *test)

      else:
        self.checkAttribute(obj, name, test)