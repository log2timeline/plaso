#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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

  # TODO: the first versions of the knowledge base will wrap the pre-process
  # object, but this should be replaced by an artifact style knowledge base
  # or artifact cache.
  _pre_obj = event.PreprocessObject()

  def __init__(self):
    """Initialize the knowledge base object."""
    super(KnowledgeBase, self).__init__()
    self._default_codepage = u'cp1252'
    self._default_timezone = pytz.timezone('UTC')

  @property
  def pre_obj(self):
    """The pre-process object."""
    return self._pre_obj

  @property
  def codepage(self):
    """The codepage."""
    return getattr(self._pre_obj, 'codepage', self._default_codepage)

  @property
  def hostname(self):
    """The hostname."""
    return getattr(self._pre_obj, 'hostname', u'')

  @property
  def platform(self):
    """The platform."""
    return getattr(self._pre_obj, 'guessed_os', u'')

  @platform.setter
  def platform(self, value):
    """The platform."""
    return setattr(self._pre_obj, 'guessed_os', value)

  @property
  def timezone(self):
    """The timezone object."""
    return getattr(self._pre_obj, 'zone', self._default_timezone)

  @property
  def users(self):
    """The list of users."""
    return getattr(self._pre_obj, 'users', [])

  @property
  def year(self):
    """The year."""
    return getattr(self._pre_obj, 'year', 0)

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
      identifier: the value identifier.
      default_value: optional default value. The default is None.

    Returns:
      The value or None if not available.
    """
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
      codepage: the default timezone.
    """
    # TODO: check if value is sane.
    self._default_timezone = timezone

  def SetValue(self, identifier, value):
    """Sets a value by identifier.

    Args:
      identifier: the value identifier.
      value: the value.
    """
    setattr(self._pre_obj, identifier, value)
