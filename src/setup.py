#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    Argentum Control GUI

    Copyright (C) 2013 Isabella Stevens
    Copyright (C) 2014 Michael Shiel
    Copyright (C) 2015 Trent Waddington

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup
import time

APP = 'gui.py'
NAME = 'Argentum Control'

BASEVERSION = '0.17.1'
BUILDTIME = time.strftime('%Y%m%d')

VERSION = BASEVERSION + '+' + BUILDTIME

CA_CERTS = "./cacerts.pem"

DATA_FILES = []

OPTIONS = {
    "bdist_esky": {
        "freezer_module": "py2app",
        "freezer_options": {
            'includes': [
                'PyQt4', 'PyQt4.QtCore', 'PyQt4.QtGui'
            ],
            'excludes': [
                'PyQt4.QtDesigner', 'PyQt4.QtNetwork', 'PyQt4.QtOpenGL',
                'PyQt4.QtScript', 'PyQt4.QtSql', 'PyQt4.QtTest',
                'PyQt4.QtWebKit', 'PyQt4.QtXml', 'PyQt4.phonon'
            ],

            'argv_emulation': True,
            'emulate-shell-environment': True,
            'iconfile': 'Icon.icns',
            'plist': 'Info.plist'
        }
    }
}
