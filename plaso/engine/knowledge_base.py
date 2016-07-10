# -*- coding: utf-8 -*-
"""The artifact knowledge base object.

The knowledge base is filled by user provided input and the pre-processing
phase. It is intended to provide successive phases, like the parsing and
analysis phases, with essential information like e.g. the timezone and
codepage of the source data.
"""

from plaso.lib import event
from plaso.lib import py2to3

import pytz  # pylint: disable=wrong-import-order


class KnowledgeBase(object):
  """Class that implements the artifact knowledge base."""

  def __init__(self, pre_obj=None):
    """Initialize the knowledge base object.

    Args:
        pre_obj: Optional preprocess object (instance of PreprocessObject.).
                 The default is None, which indicates the KnowledgeBase should
                 create a new PreprocessObject.
    """
    super(KnowledgeBase, self).__init__()

    # TODO: the first versions of the knowledge base will wrap the pre-process
    # object, but this should be replaced by an artifact style knowledge base
    # or artifact cache.
    if pre_obj:
      self._pre_obj = pre_obj
    else:
      self._pre_obj = event.PreprocessObject()

    self._default_codepage = u'cp1252'
    self._default_timezone = pytz.timezone(u'UTC')
    self._hostnames = {}
    self._preprocess_objects = {}

  @property
  def pre_obj(self):
    """The pre-process object."""
    return self._pre_obj

  @property
  def codepage(self):
    """The codepage."""
    return getattr(self._pre_obj, u'codepage', self._default_codepage)

  @property
  def hostname(self):
    """The hostname."""
    return getattr(self._pre_obj, u'hostname', u'')

  @property
  def platform(self):
    """The platform."""
    return getattr(self._pre_obj, u'guessed_os', u'')

  @platform.setter
  def platform(self, value):
    """The platform."""
    setattr(self._pre_obj, u'guessed_os', value)

  @property
  def timezone(self):
    """The timezone object."""
    return getattr(self._pre_obj, u'zone', self._default_timezone)

  @property
  def users(self):
    """The list of users."""
    return getattr(self._pre_obj, u'users', [])

  @property
  def year(self):
    """The year."""
    return getattr(self._pre_obj, u'year', 0)

  def GetPathAttributes(self):
    """Retrieves the path attributes.

    Returns:
      dict[str, str]: path attributes, typically environment variables
                      that are expanded e.g. $HOME or %SystemRoot%.
    """
    # TODO: improve this only return known enviroment variables.
    return self.pre_obj.__dict__

  def GetUsernameByIdentifier(self, identifier):
    """Retrieves the username based on an identifier.

    Args:
      identifier: the identifier, either a UID or SID.

    Returns:
      The username or - if not available.
    """
    if not identifier:
      return u'-'

    return self._pre_obj.GetUsernameById(identifier)

  def GetValue(self, identifier, default_value=None):
    """Retrieves a value by identifier.

    Args:
      identifier (str): case insensitive unique identifier for the value.
      default_value (object): default value.

    Returns:
      object: value or default value if not available.

    Raises:
      TypeError: if the identifier is not a string type.
    """
    if not isinstance(identifier, py2to3.STRING_TYPES):
      raise TypeError(u'Identifier not a string type.')

    identifier = identifier.lower()
    return getattr(self._pre_obj, identifier, default_value)

  # TODO: refactor.
  def GetHostname(self, store_number, default_hostname=u'-'):
    """Retrieves the hostname related to the event.

    If the hostname is not stored in the event it is determined based
    on the preprocessing information that is stored inside the storage file.

    Args:
      store_number (int): store number.
      default_hostname (Optional[str]): default hostname.

    Returns:
      str: hostname.
    """
    return self._hostnames.get(store_number, default_hostname)

  # TODO: remove this function it is incorrect.
  def GetStoredHostname(self):
    """Retrieves the stored hostname.

    The hostname is determined based on the preprocessing information
    that is stored inside the storage file.

    Returns:
      str: hostname.
    """
    store_number = len(self._hostnames)
    return self._hostnames.get(store_number, None)

  # TODO: refactor.
  def GetUsername(self, user_identifier, store_number, default_username=u'-'):
    """Retrieves the username related to the event.

    Args:
      user_identifier (str): user identifier.
      store_number (int): store number.
      default_username (Optional[str]): default username.

    Returns:
      str: username.
    """
    if not store_number:
      return default_username

    pre_obj = self._preprocess_objects.get(store_number, None)
    if not pre_obj:
      return default_username

    preprocess_username = pre_obj.GetUsernameById(user_identifier)
    if preprocess_username and preprocess_username != u'-':
      return preprocess_username

    if not user_identifier:
      return default_username

    preprocess_username = pre_obj.GetUsernameById(user_identifier)
    if preprocess_username and preprocess_username != u'-':
      return preprocess_username

    return default_username

  # TODO: refactor.
  def InitializeLookupDictionaries(self, storage_file):
    """Initializes the lookup dictionaries.

    Args:
      storage_file (BaseStorage): storage file.

    Builds a dictionary of hostnames and usernames from the preprocess
    objects stored inside the storage file.
    """
    self._hostnames = {}
    self._preprocess_objects = {}

    if not storage_file or not hasattr(storage_file, u'GetStorageInformation'):
      return

    for info in storage_file.GetStorageInformation():
      store_range = getattr(info, u'store_range', None)
      if not store_range:
        continue

      # TODO: should this be store_range[1] + 1 with or without + 1?
      # This is inconsistent in the current version of the codebase.
      for store_number in range(store_range[0], store_range[1]):
        self._preprocess_objects[store_number] = info

        hostname = getattr(info, u'hostname', None)
        if hostname:
          # TODO: A bit wasteful, if the range is large we are wasting keys.
          # Rewrite this logic into a more optimal one.
          self._hostnames[store_number] = hostname

  def SetDefaultCodepage(self, codepage):
    """Sets the default codepage.

    Args:
      codepage: the default codepage.
    """
    # TODO: check if value is sane.
    self._default_codepage = codepage

  def SetDefaultTimezone(self, timezone):
    """Sets the default timezone.

    Args:
      timezone: the default timezone.
    """
    # TODO: check if value is sane.
    self._default_timezone = timezone

  def SetValue(self, identifier, value):
    """Sets a value by identifier.

    Args:
      identifier (str): case insensitive unique identifier for the value.
      value (object): value.

    Raises:
      TypeError: if the identifier is not a string type.
    """
    if not isinstance(identifier, py2to3.STRING_TYPES):
      raise TypeError(u'Identifier not a string type.')

    identifier = identifier.lower()
    setattr(self._pre_obj, identifier, value)
