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
"""This file contains a Apple Account plist plugin in Plaso."""

from plaso.events import plist_event
from plaso.lib import errors
from plaso.lib import timelib
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class AppleAccountPlugin(interface.PlistPlugin):
  """Basic plugin to extract the apple account information."""

  NAME = 'plist_appleaccount'

  PLIST_PATH = u'com.apple.coreservices.appleidauthenticationinfo'
  PLIST_KEYS = frozenset(['AuthCertificates', 'AccessorVersions', 'Accounts'])

  def Process(self, plist_name=None, top_level=None, **kwargs):
    """Check if it is a valid Apple account plist file name.

    Args:
      plist_name: name of the plist file.
      top_level: dictionary with the plist file parsed.

    Returns:
      A generator, self.GetEntries(), if the correct plugin, otherwise None.
    """
    if not plist_name.startswith(self.PLIST_PATH):
      raise errors.WrongPlistPlugin(self.plugin_name, plist_name)
    return super(AppleAccountPlugin, self).Process(
        plist_name=self.PLIST_PATH, top_level=top_level, **kwargs)

  # Yield Events
  # Accounts: account name.
  # FirstName: first name associated with the account.
  # LastName: family name associate with the account.
  # CreationDate: timestamp when the account was configured in the system.
  # LastSuccessfulConnect: last time when the account was connected.
  # ValidationDate: last time when the account was validated.

  def GetEntries(self, unused_cache=None):
    """Extracts relevant Apple Account entries.

    Yields:
      EventObject objects extracted from the plist.
    """
    root = '/Accounts'

    for name_account, account in self.match['Accounts'].iteritems():
      general_description = u'{} ({} {})'.format(
          name_account, account['FirstName'], account['LastName'])
      key = name_account
      description = u'Configured Apple account {}'.format(general_description)
      time = timelib.Timestamp.FromPythonDatetime(
          account['CreationDate'])
      yield plist_event.PlistEvent(root, key, time, description)
      description = u'Connected Apple account {}'.format(general_description)
      time = timelib.Timestamp.FromPythonDatetime(
          account['LastSuccessfulConnect'])
      yield plist_event.PlistEvent(root, key, time, description)
      description = u'Last validation Apple account {}'.format(
          general_description)
      time = timelib.Timestamp.FromPythonDatetime(
          account['ValidationDate'])
      yield plist_event.PlistEvent(root, key, time, description)

