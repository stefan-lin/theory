# -*- coding: utf-8 -*-
##### System wide lib #####
import imp
import os
import sys
import tempfile
import unittest

##### Theory lib #####
from theory.db.loading import load_app
from theory.utils.importlib import import_module

##### Theory third-party lib #####

##### Local app #####

##### Theory app #####

##### Misc #####


RUNTESTS_DIR = "/opt/crystal/venv/panel/src/theory/tests"
#RUNTESTS_DIR = os.path.realpath(__file__)
#RUNTESTS_DIR = os.path.dirname(__file__)

# ====================================================================
# All test type dir should be declare in here
UNIT_TESTS_DIR_NAME = 'unitTest'

UNIT_TEST_DIR = os.path.join(RUNTESTS_DIR, UNIT_TESTS_DIR_NAME)
print "eee->", RUNTESTS_DIR, UNIT_TESTS_DIR_NAME, UNIT_TEST_DIR

# ====================================================================
TEMP_DIR = tempfile.mkdtemp(prefix='theory_')
os.environ['THEORY_TEST_TEMP_DIR'] = TEMP_DIR

def getTestModuleAbsPaths():
  modules = []
  for loc, dirpath in (
    (UNIT_TESTS_DIR_NAME, UNIT_TEST_DIR),):
    print "what", loc, dirpath
    for f in os.listdir(dirpath):
      if (f.startswith('__init__') or
          f.startswith('.')):
        continue
      modules.append((loc, f))
  return modules

def registerTestApp():
  sys.path.append(RUNTESTS_DIR)

  testModuleAbsPaths = getTestModuleAbsPaths()
  from theory.conf import settings
  for testModuleDirPath, testModuleFileName in testModuleAbsPaths:
    moduleLabel = ".".join([testModuleDirPath, testModuleFileName])
    #mod = load_app(moduleLabel, True)
    mod = import_module(moduleLabel)
    if(mod and moduleLabel not in settings.INSTALLED_APPS):
      settings.INSTALLED_APPS.append(moduleLabel)
