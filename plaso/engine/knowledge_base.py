# -*- coding: utf-8 -*-
"""The artifact knowledge base object.

The knowledge base is filled by user provided input and the pre-processing
phase. It is intended to provide successive phases, like the parsing and
analysis phases, with essential information like e.g. the timezone and
codepage of the source data.
"""

from plaso.lib import event

import pytz


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

    If the identifier is a string it is case insensitive.

    Args:
      identifier: the value identifier.
      default_value: optional default value. The default is None.

    Returns:
      The value or None if not available.
    """
    if isinstance(identifier, basestring):
      identifier = identifier.lower()
    return getattr(self._pre_obj, identifier, default_value)

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

    If the identifier is a string it is case insensitive.

    Args:
      identifier: the value identifier.
      value: the value.
    """
    if isinstance(identifier, basestring):
      identifier = identifier.lower()
    setattr(self._pre_obj, identifier, value)
