# -*- coding: utf-8 -*-
#!/usr/bin/env python
##### System wide lib #####
from __future__ import with_statement

from bson.objectid import ObjectId
import json
import os
import warnings

##### Theory lib #####
from theory.conf import settings, UserSettingsHolder
# TODO: enable it
#from theory.test.signals import setting_changed
from theory.test.theoryTestEncoder import TheoryTestEncoder
from theory.utils.translation import deactivate
from theory.utils.functional import wraps

##### Theory third-party lib #####

##### Local app #####

##### Theory app #####

##### Misc #####

__all__ = (
  'Approximate', 'ContextList',  'get_runner', 'override_settings',
  'setup_test_environment', 'teardown_test_environment', 'ObjectComparator',
)

class Approximate(object):
  def __init__(self, val, places=7):
    self.val = val
    self.places = places

  def __repr__(self):
    return repr(self.val)

  def __eq__(self, other):
    if self.val == other:
      return True
    return round(abs(self.val-other), self.places) == 0


class ContextList(list):
  """A wrapper that provides direct key access to context items contained
  in a list of context objects.
  """
  def __getitem__(self, key):
    if isinstance(key, basestring):
      for subcontext in self:
        if key in subcontext:
          return subcontext[key]
      raise KeyError(key)
    else:
      return super(ContextList, self).__getitem__(key)

  def __contains__(self, key):
    try:
      value = self[key]
    except KeyError:
      return False
    return True


def setup_test_environment():
  """Perform any global pre-test setup. This involves:

    - Installing the instrumented test renderer
    - Set the email backend to the locmem email backend.
    - Setting the active locale to match the LANGUAGE_CODE setting.
  """

  deactivate()


def teardown_test_environment():
  """Perform any global post-test teardown. This involves:

    - Restoring the original test renderer
    - Restoring the email sending functions

  """
  pass


def get_warnings_state():
  """
  Returns an object containing the state of the warnings module
  """
  # There is no public interface for doing this, but this implementation of
  # get_warnings_state and restore_warnings_state appears to work on Python
  # 2.4 to 2.7.
  return warnings.filters[:]


def restore_warnings_state(state):
  """
  Restores the state of the warnings module when passed an object that was
  returned by get_warnings_state()
  """
  warnings.filters = state[:]


def get_runner(settings, test_runner_class=None):
  if not test_runner_class:
    test_runner_class = settings.TEST_RUNNER

  test_path = test_runner_class.split('.')
  # Allow for Python 2.5 relative paths
  if len(test_path) > 1:
    test_module_name = '.'.join(test_path[:-1])
  else:
    test_module_name = '.'
  test_module = __import__(test_module_name, {}, {}, test_path[-1])
  test_runner = getattr(test_module, test_path[-1])
  return test_runner

class override_settings(object):
  """
  Acts as either a decorator, or a context manager. If it's a decorator it
  takes a function and returns a wrapped function. If it's a contextmanager
  it's used with the ``with`` statement. In either event entering/exiting
  are called before and after, respectively, the function/block is executed.
  """
  def __init__(self, **kwargs):
    self.options = kwargs
    self.wrapped = settings._wrapped

  def __enter__(self):
    self.enable()

  def __exit__(self, exc_type, exc_value, traceback):
    self.disable()

  def __call__(self, test_func):
    @wraps(test_func)
    def inner(*args, **kwargs):
      with self:
        return test_func(*args, **kwargs)
    return inner

  def enable(self):
    override = UserSettingsHolder(settings._wrapped)
    for key, new_value in self.options.items():
      setattr(override, key, new_value)
    settings._wrapped = override
    for key, new_value in self.options.items():
      setting_changed.send(sender=settings._wrapped.__class__,
                 setting=key, value=new_value)

  def disable(self):
    settings._wrapped = self.wrapped
    for key in self.options:
      new_value = getattr(settings, key, None)
      setting_changed.send(sender=settings._wrapped.__class__,
                 setting=key, value=new_value)

class ObjectDumper(object):
  def __init__(self, includeTermLst=[], excludeTermLst=[], absorbTermLst=[]):
    self.includeTermLst = includeTermLst
    self.excludeTermLst = excludeTermLst
    self.absorbTermSet = set(absorbTermLst)
    if(len(self.includeTermLst)==0):
      self._filterFxn = self._filterByExcludeTerm
    else:
      self._filterFxn = self._filterByIncludeTerm

  def _filterFxn(self, key):
    pass

  def _filterByIncludeTerm(self, key):
    return key in self.includeTermLst

  def _filterByExcludeTerm(self, key):
    return key not in self.excludeTermLst

  def filterNestedDict(self, node):
    if isinstance(node, list):
      r = []
      for i in node:
        r.append(self.filterNestedDict(i))
      return r
    elif isinstance(node, dict):
      r = {}
      nodeKeySet = set((node.keys()))
      intersetAbsorbTermSet = nodeKeySet.intersection(self.absorbTermSet)
      if(
          len(nodeKeySet)==1
          and len(self.absorbTermSet)>0
          and self.absorbTermSet.issubset(nodeKeySet)
          ):
        loopFxn = node[intersetAbsorbTermSet.pop()].iteritems
      else:
        loopFxn = node.iteritems
      for key, val in loopFxn():
        if(self._filterFxn(key)):
          cur_node = self.filterNestedDict(val)
          if cur_node is not None:
            r[key] = cur_node
      return r or None
    else:
      return node

  def jsonifyObjToStr(self, obj):
    """Return a str in JSON format from a given object. Feel free to override
    this fxn if necessary."""
    TheoryTestEncoder.includeTermLst = self.includeTermLst
    TheoryTestEncoder.excludeTermLst = self.excludeTermLst
    return json.dumps(
        obj,
        cls=TheoryTestEncoder,
        indent=2,
        )

  def cleanupJsonifyObj(self, obj):
    return self.filterNestedDict(
        obj,
        )

class ObjectComparator(object):
  def __init__(self, objectDumper):
    self.objectDumper = objectDumper

  def _convertObjToJson(self, obj):
    objInStr = self.objectDumper.jsonifyObjToStr(obj)
    return self.objectDumper.cleanupJsonifyObj(json.loads(objInStr))

  def _convertObjToStr(self, obj):
    return json.dumps(self._convertObjToJson(obj), indent=2, sort_keys=True)

  def _getFilePathForTestcase(self, testFilePath, testFxnName):
    path, filename = os.path.split(testFilePath)
    filename = filename.split(".")[0]
    path = os.path.join(
        os.path.dirname(path),
        "files",
        filename,
        )
    if not os.path.exists(path):
      os.makedirs(path)
    return os.path.join(path, testFxnName)

  def compare(self, testFilePath, testFxnName, obj):
    """
    :param testFilePath: The file path of test file, get it from "__file__"
    :type testFilePath: String
    :param testFxnName: The test function name, get it from
                        "self._testMethodName"
    :type testFxnName: String
    :param obj: The object being compared"
    :type obj: Python Object
    """
    sampleFilePath = self._getFilePathForTestcase(testFilePath, testFxnName)
    with open(sampleFilePath, "r") as fd:
      sampledDataInJson = json.loads(fd.read())
    objInJson = self._convertObjToJson(obj)

    diff1 = JsonDiff(sampledDataInJson, objInJson, True).difference
    diff2 = JsonDiff(objInJson, sampledDataInJson, False).difference
    diffs = []
    for type, message in diff1:
      newType = 'CHANGED'
      if type == JsonDiff.PATH:
        newType = 'REMOVED'
      diffs.append({'type': newType, 'message': message})
    for type, message in diff2:
      diffs.append({'type': 'ADDED', 'message': message})
    return diffs

  def serializeSample(self, testFilePath, testFxnName, obj):
    """
    :param testFilePath: The file path of test file, get it from "__file__"
    :type testFilePath: String
    :param testFxnName: The test function name, get it from
                        "self._testMethodName"
    :type testFxnName: String
    :param obj: The object being serialized"
    :type obj: Python Object
    """
    sampleFilePath = self._getFilePathForTestcase(testFilePath, testFxnName)
    with open(sampleFilePath, "w") as fd:
      fd.write(self._convertObjToStr(obj))

class JsonDiff(object):
  # Borrowed from http://djangosnippets.org/snippets/2247/ and
  # https://github.com/monsur/jsoncompare/blob/master/jsoncompare.py
  # with some modifications.
  TYPE = 'TYPE'
  PATH = 'PATH'
  VALUE = 'VALUE'

  def __init__(self, first, second, withValues=False):
    self.difference = []
    self.seen = []
    self.check(first, second, withValues=withValues)

  def check(self, first, second, path='', withValues=False):
    if withValues and second != None:
      if not isinstance(first, type(second)):
        message = '%s - %s, %s' % (
            path,
            type(first).__name__,
            type(second).__name__
            )
        self.saveDiff(message, self.TYPE)

    if isinstance(first, dict):
      for key in first:
        # the first part of path must not have trailing dot.
        if len(path) == 0:
          newPath = key
        else:
          newPath = "%s.%s" % (path, key)

        if isinstance(second, dict):
          if second.has_key(key):
            sec = second[key]
          else:
            #  there are key in the first, that is not presented in the second
            self.saveDiff(newPath, self.PATH)

            # prevent further values checking.
            sec = None

          # recursive call
          if sec != None:
            self.check(first[key], sec, path=newPath, withValues=withValues)
        else:
          # second is not dict. every key from first goes to the difference
          self.saveDiff(newPath, self.PATH)
          self.check(first[key], second, path=newPath, withValues=withValues)

    # if object is list, loop over it and check.
    elif isinstance(first, list):
      for (index, item) in enumerate(first):
        newPath = "%s[%s]" % (path, index)
        # try to get the same index from second
        sec = None
        if second != None:
          try:
            sec = second[index]
          except (IndexError, KeyError):
            # goes to difference
            self.saveDiff('%s - %s' % (
              newPath,
              type(item).__name__),
              self.TYPE
              )

        # recursive call
        self.check(first[index], sec, path=newPath, withValues=withValues)

    # not list, not dict. check for equality (only if withValues is True)
    # and return.
    else:
      if withValues and second != None:
        if first != second:
          self.saveDiff('%s - %s | %s' % (path, first, second), self.VALUE)
      return

  def saveDiff(self, diffMessage, type_):
    if diffMessage not in self.difference:
      self.seen.append(diffMessage)
      self.difference.append((type_, diffMessage))
