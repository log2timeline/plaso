#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""This file contains a parser for Plist files."""

import logging

from binplist import binplist

from plaso import plist

from plaso.lib import errors
from plaso.lib import parser
from plaso.lib import plist_interface
from plaso.lib import utils


class PlistParser(parser.PlasoParser):
  """Parse Plist files with applicable plugins and yield events."""

  def __init__(self, pre_obj):
    super(PlistParser, self).__init__(pre_obj)
    self._plugins = plist_interface.GetPlistPlugins()

  def GetTopLevel(self, filehandle):
    """Returns the deserialized content of a plist as a dictionary object.

    Args:
      filehandle: This is a file like object pointing to the plist.

    Returns:
      Dictionary object representing the contents of the plist.
    """
    try:
      bpl = binplist.BinaryPlist(filehandle)
      top_level_object = bpl.Parse()
    except binplist.FormatError as e:
      raise errors.UnableToParseFile(
          u'[PLIST] File is not a plist:{}'.format(utils.GetUnicodeString(e)))
    except OverflowError as e:
      raise errors.UnableToParseFile(
          u'[PLIST] error processing:{} Error:{}'.format(filehandle, e))

    if not bpl:
      raise errors.UnableToParseFile(
          u'[PLIST] File is not a plist:{}'.format(utils.GetUnicodeString(e)))

    if bpl.is_corrupt:
      logging.warning(u'[PLIST] bpl found corruption in: %s', filehandle.name)

    return top_level_object

  def Parse(self, filehandle):
    """Parse and extract values from a plist file.

    Args:
      filehandle: This is a file like object or a PFile object.

    Yields:
      An EventObject containing information extracted from a Plist.
    """
    top_level_object = self.GetTopLevel(filehandle)
    if not top_level_object:
      raise errors.UnableToParseFile(
          u'[PLIST] couldn\'t parse: %s.  Skipping.' % filehandle.name)

    if '\\' in filehandle.name:
      _, _, plist_name = filehandle.name.rpartition('\\')
    else:
      _, _, plist_name = filehandle.name.rpartition('/')

    for plugin in self._plugins:
      try:
        for evt in plugin.Process(plist_name, top_level_object):
          yield evt
      except errors.WrongPlistPlugin as e:
        logging.debug('[PLIST] Wrong Plugin:{} for:{}'.format(e[0], e[1]))
