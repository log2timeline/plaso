# -*- coding: utf-8 -*-
"""The filters shared test library."""

from __future__ import unicode_literals

from plaso.filters import interface

from tests import test_lib as shared_test_lib


class DummyObject(object):
  """Object for testing purposes."""

  def __init__(self, key, value):
    """Initializes an object for testing purposes.

    Args:
      key (str): name of test attribute.
      value (object): value of test attribute.
    """
    super(DummyObject, self).__init__()
    setattr(self, key, value)


class HashObject(object):
  """Object for testing purposes."""

  # pylint: disable=missing-docstring

  def __init__(self, hash_value=None):
    """Initializes an object for testing purposes.

    Args:
      hash_value (Optional[str]): hash value.
    """
    super(HashObject, self).__init__()
    self.value = hash_value

  def __eq__(self, y):
    return self.value == y

  def __lt__(self, y):
    return self.value < y

  @property
  def md5(self):
    return self.value


class Dll(object):
  """Object for testing purposes."""

  # pylint: disable=missing-docstring

  def __init__(self, name, imported_functions=None, exported_functions=None):
    """Initializes an object for testing purposes."""
    super(Dll, self).__init__()
    self._imported_functions = imported_functions or []
    self.exported_functions = exported_functions or []
    self.name = name
    self.num_exported_functions = len(self.exported_functions)
    self.num_imported_functions = len(self._imported_functions)

  @property
  def imported_functions(self):
    for fn in self._imported_functions:
      yield fn


class DummyFile(object):
  """Object for testing purposes."""

  # pylint: disable=missing-docstring

  non_callable_leaf = 'yoda'

  def __init__(self):
    """Initializes an object for testing purposes."""
    super(DummyFile, self).__init__()
    self.non_callable = HashObject('123abc')
    self.non_callable_repeated = [
        DummyObject('desmond', ['brotha', 'brotha']),
        DummyObject('desmond', ['brotha', 'sista'])]
    self.imported_dll1 = Dll('a.dll', ['FindWindow', 'CreateFileA'])
    self.imported_dll2 = Dll('b.dll', ['RegQueryValueEx'])

  @property
  def attributes(self):
    """list[str]: attributes."""
    return ['Backup', 'Archive']

  @property
  def name(self):
    """str: name."""
    return 'boot.ini'

  @property
  def hash(self):
    return [HashObject('123abc'), HashObject('456def')]

  @property
  def size(self):
    return 10

  @property
  def deferred_values(self):
    for v in ['a', 'b']:
      yield v

  @property
  def novalues(self):
    return []

  def Callable(self):
    raise RuntimeError('This can not be called.')

  @property
  def float(self):
    return 123.9823


class TestEventFilter(interface.FilterObject):
  """Test event filter."""

  def CompileFilter(self, filter_expression):
    """Compiles the filter expression.

    Args:
      filter_expression (str): filter expression.

    Raises:
      WrongPlugin: if the filter could not be compiled.
    """
    return


class FilterTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for an event filter."""
