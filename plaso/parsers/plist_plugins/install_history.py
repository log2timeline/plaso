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
"""This file contains the install history plist plugin in Plaso."""

from plaso.events import plist_event
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class InstallHistoryPlugin(interface.PlistPlugin):
  """Plist plugin that extracts the installation history."""

  NAME = 'plist_install_history'

  PLIST_PATH = 'InstallHistory.plist'
  PLIST_KEYS = frozenset([
      'date', 'displayName', 'displayVersion',
      'processName', 'packageIdentifiers'])

  def GetEntries(self, parser_context, top_level=None, **unused_kwargs):
    """Extracts relevant install history entries.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      top_level: Optional plist in dictionary form. The default is None.
    """
    for entry in top_level:
      packages = []
      for package in entry.get('packageIdentifiers'):
        packages.append(package)
      description = (
          u'Installation of [{0:s} {1:s}] using [{2:s}]. '
          u'Packages: {3:s}.').format(
              entry.get('displayName'), entry.get('displayVersion'),
              entry.get('processName'), u', '.join(packages))
      event_object = plist_event.PlistEvent(
          u'/item', u'', entry.get('date'), description)
      parser_context.ProduceEvent(event_object, plugin_name=self.NAME)


plist.PlistParser.RegisterPlugin(InstallHistoryPlugin)
