#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
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
"""This file contains a default plist plugin in Plaso."""

import datetime
import logging

from plaso.events import plist_event
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class DefaultPlugin(interface.PlistPlugin):
  """Basic plugin to extract keys with timestamps as values from plists."""

  NAME = 'plist_default'
  DESCRIPTION = u'Parser for plist files.'

  def GetEntries(self, parser_mediator, top_level=None, **unused_kwargs):
    """Simple method to exact date values from a Plist.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      top_level: Plist in dictionary form.
    """
    for root, key, value in interface.RecurseKey(top_level):
      if isinstance(value, datetime.datetime):
        event_object = plist_event.PlistEvent(root, key, value)
        parser_mediator.ProduceEvent(event_object)

      # TODO: Binplist keeps a list of offsets but not mapped to a key.
      # adjust code when there is a way to map keys to offsets.

  # TODO: move this into the parser as with the olecf plugins.
  def Process(self, parser_mediator, plist_name, top_level, **kwargs):
    """Overwrite the default Process function so it always triggers.

    Process() checks if the current plist being processed is a match for a
    plugin by comparing the PATH and KEY requirements defined by a plugin.  If
    both match processing continues; else raise WrongPlistPlugin.

    The purpose of the default plugin is to always trigger on any given plist
    file, thus it needs to overwrite the default behavior of comparing PATH
    and KEY.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      plist_name: Name of the plist file.
      top_level: Plist in dictionary form.
    """
    logging.debug(u'Plist {0:s} plugin used for: {1:s}'.format(
        self.NAME, plist_name))
    self.GetEntries(parser_mediator, top_level=top_level, **kwargs)


plist.PlistParser.RegisterPlugin(DefaultPlugin)
