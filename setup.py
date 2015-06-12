#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2014-2015 Jakub M. Kowalski (Laboratory of                 #
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


try:
  from setuptools import setup, Extension
  # XXX a fix for https://bugs.python.org/issue23246 bug

except ImportError:
  from distutils.core import setup, Extension
  print "The setuptools module is not found - 'Unable to find vcvarsall.bat' error"
  print "(and many others) might occur."
  print
  setuptoolsPresent = False

else:
  setuptoolsPresent = True

cPymice = Extension('pymice._C', sources = ['pymice.cpp'])
setup(name = 'pymice',
      version = '0.1.1b',
      description = 'pymice',
      ext_modules = [cPymice],
      packages = ['pymice'])
