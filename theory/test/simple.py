import unittest as real_unittest

from theory.conf import settings
from theory.core.exceptions import ImproperlyConfigured
from theory.db.loading import get_app
from theory.test.utils import setup_test_environment, teardown_test_environment
from theory.test.testcases import TestCase
from theory.utils import unittest
from theory.utils.importlib import import_module
from theory.utils.module_loading import module_has_submodule

__all__ = ('TheoryTestRunner', 'TheoryTestSuiteRunner')

# The module name for tests outside models.py
TEST_MODULE = 'tests'

class TheoryTestRunner(unittest.TextTestRunner):
  def __init__(self, *args, **kwargs):
    import warnings
    warnings.warn(
      "TheoryTestRunner is deprecated; it's functionality is "
      "indistinguishable from TextTestRunner",
      DeprecationWarning
    )
    super(TheoryTestRunner, self).__init__(*args, **kwargs)


def get_tests(app_module):
  try:
    return import_module('.'.join([app_module.__name__] + [TEST_MODULE]))
  except ImportError:
    return None

def build_suite(app_module):
  """
  Create a complete Theory test suite for the provided application module.
  """
  suite = unittest.TestSuite()

  # Load unit and doctests in the models.py module. If module has
  # a suite() method, use it. Otherwise build the test suite ourselves.
  if hasattr(app_module, 'suite'):
    suite.addTest(app_module.suite())
  else:
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(
      app_module))

  # Check to see if a separate 'tests' module exists parallel to the
  # models module
  test_module = get_tests(app_module)
  if test_module:
    # Load unit and doctests in the tests.py module. If module has
    # a suite() method, use it. Otherwise build the test suite ourselves.
    if hasattr(test_module, 'suite'):
      suite.addTest(test_module.suite())
    else:
      suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(
        test_module))
  return suite


def build_test(label):
  """
  Construct a test case with the specified label. Label should be of the
  form model.TestClass or model.TestClass.test_method. Returns an
  instantiated test or test suite corresponding to the label provided.

  """
  parts = label.split('.')
  if len(parts) < 2 or len(parts) > 3:
    raise ValueError("Test label '%s' should be of the form app.TestCase "
             "or app.TestCase.test_method" % label)

  #
  # First, look for TestCase instances with a name that matches
  #
  app_module = get_app(parts[0])
  test_module = get_tests(app_module)
  TestClass = getattr(app_module, parts[1], None)

  # Couldn't find the test class in models.py; look in tests.py
  if TestClass is None:
    if test_module:
      TestClass = getattr(test_module, parts[1], None)

  try:
    if issubclass(TestClass, (unittest.TestCase, real_unittest.TestCase)):
      if len(parts) == 2: # label is app.TestClass
        try:
          return unittest.TestLoader().loadTestsFromTestCase(
            TestClass)
        except TypeError:
          raise ValueError(
            "Test label '%s' does not refer to a test class"
            % label)
      else: # label is app.TestClass.test_method
        return TestClass(parts[2])
  except TypeError:
    # TestClass isn't a TestClass - it must be a method or normal class
    pass

  # If no tests were found, then we were given a bad test label.
  raise ValueError("Test label '%s' does not refer to a test" % label)

def partition_suite(suite, classes, bins):
  """
  Partitions a test suite by test type.

  classes is a sequence of types
  bins is a sequence of TestSuites, one more than classes

  Tests of type classes[i] are added to bins[i],
  tests with no match found in classes are place in bins[-1]
  """
  for test in suite:
    if isinstance(test, unittest.TestSuite):
      partition_suite(test, classes, bins)
    else:
      for i in range(len(classes)):
        if isinstance(test, classes[i]):
          bins[i].addTest(test)
          break
      else:
        bins[-1].addTest(test)


def reorder_suite(suite, classes):
  """
  Reorders a test suite by test type.

  `classes` is a sequence of types

  All tests of type classes[0] are placed first, then tests of type
  classes[1], etc. Tests with no match in classes are placed last.
  """
  class_count = len(classes)
  bins = [unittest.TestSuite() for i in range(class_count+1)]
  partition_suite(suite, classes, bins)
  for i in range(class_count):
    bins[0].addTests(bins[i+1])
  return bins[0]


def dependency_ordered(test_databases, dependencies):
  """Reorder test_databases into an order that honors the dependencies
  described in TEST_DEPENDENCIES.
  """
  ordered_test_databases = []
  resolved_databases = set()
  while test_databases:
    changed = False
    deferred = []

    while test_databases:
      signature, (db_name, aliases) = test_databases.pop()
      dependencies_satisfied = True
      for alias in aliases:
        if alias in dependencies:
          if all(a in resolved_databases
              for a in dependencies[alias]):
            # all dependencies for this alias are satisfied
            dependencies.pop(alias)
            resolved_databases.add(alias)
          else:
            dependencies_satisfied = False
        else:
          resolved_databases.add(alias)

      if dependencies_satisfied:
        ordered_test_databases.append((signature, (db_name, aliases)))
        changed = True
      else:
        deferred.append((signature, (db_name, aliases)))

    if not changed:
      raise ImproperlyConfigured(
        "Circular dependency in TEST_DEPENDENCIES")
    test_databases = deferred
  return ordered_test_databases


class TheoryTestSuiteRunner(object):
  def __init__(self, verbosity=1, interactive=True, failfast=True, **kwargs):
    self.verbosity = verbosity
    self.interactive = interactive
    self.failfast = failfast
    try:
      self.suite = kwargs["suite"]
    except KeyError:
      self.suite = None

  def setup_test_environment(self, **kwargs):
    setup_test_environment()
    settings.DEBUG = False
    unittest.installHandler()

  def build_suite(self, test_labels, extra_tests=None, **kwargs):
    if(self.suite==None):
      suite = unittest.TestSuite()
    else:
      suite = self.suite

    if test_labels:
      for label in test_labels:
        if '.' in label:
          suite.addTest(build_test(label))
        else:
          for appName in settings.INSTALLED_APPS:
            app = import_module(appName)
            suite.addTest(build_suite(app))
    else:
      for appName in settings.INSTALLED_APPS:
        app = import_module(appName)
        suite.addTest(build_suite(app))

    if extra_tests:
      for test in extra_tests:
        suite.addTest(test)

    return reorder_suite(suite, (TestCase,))

  def setup_databases(self, **kwargs):
    from theory.db import connections, DEFAULT_DB_ALIAS

    # First pass -- work out which databases actually need to be created,
    # and which ones are test mirrors or duplicate entries in DATABASES
    mirrored_aliases = {}
    test_databases = {}
    dependencies = {}
    for alias in connections:
      connection = connections[alias]
      if connection.settings_dict['TEST_MIRROR']:
        # If the database is marked as a test mirror, save
        # the alias.
        mirrored_aliases[alias] = (
          connection.settings_dict['TEST_MIRROR'])
      else:
        # Store a tuple with DB parameters that uniquely identify it.
        # If we have two aliases with the same values for that tuple,
        # we only need to create the test database once.
        item = test_databases.setdefault(
          connection.creation.testDbSignature(),
          (connection.settings_dict['NAME'], [])
        )
        item[1].append(alias)

        if 'TEST_DEPENDENCIES' in connection.settings_dict:
          dependencies[alias] = (
            connection.settings_dict['TEST_DEPENDENCIES'])
        else:
          if alias != DEFAULT_DB_ALIAS:
            dependencies[alias] = connection.settings_dict.get(
              'TEST_DEPENDENCIES', [DEFAULT_DB_ALIAS])

    # Second pass -- actually create the databases.
    old_names = []
    mirrors = []
    for signature, (db_name, aliases) in dependency_ordered(
      test_databases.items(), dependencies):
      # Actually create the database for the first connection
      connection = connections[aliases[0]]
      old_names.append((connection, db_name, True))
      test_db_name = connection.creation.createTestDb(
        self.verbosity, autoclobber=not self.interactive)
      for alias in aliases[1:]:
        connection = connections[alias]
        if db_name:
          old_names.append((connection, db_name, False))
          connection.settings_dict['NAME'] = test_db_name
        else:
          # If settings_dict['NAME'] isn't defined, we have a backend
          # where the name isn't important -- e.g., SQLite, which
          # uses :memory:. Force create the database instead of
          # assuming it's a duplicate.
          old_names.append((connection, db_name, True))
          connection.creation.createTestDb(
            self.verbosity, autoclobber=not self.interactive)

    for alias, mirror_alias in mirrored_aliases.items():
      mirrors.append((alias, connections[alias].settings_dict['NAME']))
      connections[alias].settings_dict['NAME'] = (
        connections[mirror_alias].settings_dict['NAME'])
      connections[alias].features = connections[mirror_alias].features

    return old_names, mirrors

  def run_suite(self, suite, **kwargs):
    return unittest.TextTestRunner(
      verbosity=self.verbosity, failfast=self.failfast).run(suite)

  def teardown_databases(self, old_config, **kwargs):
    """
    Destroys all the non-mirror databases.
    """
    old_names, mirrors = old_config
    for connection, old_name, destroy in old_names:
      if destroy:
        connection.creation.destroyTestDb(old_name, self.verbosity)

  def teardown_test_environment(self, **kwargs):
    unittest.removeHandler()
    teardown_test_environment()

  def suite_result(self, suite, result, **kwargs):
    return len(result.failures) + len(result.errors)

  def run_tests(self, test_labels, extra_tests=None, **kwargs):
    """
    Run the unit tests for all the test labels in the provided list.
    Labels must be of the form:
     - app.TestClass.test_method
      Run a single specific test method
     - app.TestClass
      Run all the test methods in a given class
     - app
      Search for doctests and unittests in the named application.

    When looking for tests, the test runner will look in the models and
    tests modules for the application.

    A list of 'extra' tests may also be provided; these tests
    will be added to the test suite.

    Returns the number of tests that failed.
    """
    self.setup_test_environment()
    suite = self.build_suite(test_labels, extra_tests)
    old_config = self.setup_databases()
    result = self.run_suite(suite)
    self.teardown_databases(old_config)
    self.teardown_test_environment()
    return self.suite_result(suite, result)