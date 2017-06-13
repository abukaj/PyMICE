#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2017 Jakub M. Dzik a.k.a. Kowalski (Laboratory of          #
#    Neuroinformatics; Nencki Institute of Experimental Biology of Polish     #
#    Academy of Sciences)                                                     #
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
import unittest

from pymice._Bibliography import reference

class TestReference(unittest.TestCase):
    APA_6_PLAIN = {'1.1.1': "Dzik, J. M., Łęski, S., & Puścian, A. (2017, April). PyMICE (v. 1.1.1) [computer software; RRID:nlx_158570]. doi: 10.5281/zenodo.557087",
                   '1.1.0': "Dzik, J. M., Łęski, S., & Puścian, A. (2016, December). PyMICE (v. 1.1.0) [computer software; RRID:nlx_158570]. doi: 10.5281/zenodo.200648",
                   '1.0.0': "Dzik, J. M., Łęski, S., & Puścian, A. (2016, May). PyMICE (v. 1.0.0) [computer software; RRID:nlx_158570]. doi: 10.5281/zenodo.51092",
                   '0.2.5': "Dzik, J. M., Łęski, S., & Puścian, A. (2016, April). PyMICE (v. 0.2.5) [computer software; RRID:nlx_158570]. doi: 10.5281/zenodo.49550",
                   '0.2.4': "Dzik, J. M., Łęski, S., & Puścian, A. (2016, January). PyMICE (v. 0.2.4) [computer software; RRID:nlx_158570]. doi: 10.5281/zenodo.47305",
                   '0.2.3': "Dzik, J. M., Łęski, S., & Puścian, A. (2016, January). PyMICE (v. 0.2.3) [computer software; RRID:nlx_158570]. doi: 10.5281/zenodo.47259",
                   'unknown': "Dzik, J. M., Łęski, S., & Puścian, A. (n.d.). PyMICE (v. unknown) [computer software; RRID:nlx_158570]",
                   }
    def testTxtAPA6(self):
        for version, expected in self.APA_6_PLAIN.items():
            self.assertEqual(expected,
                             reference.software(version, 'apa6', 'txt'))