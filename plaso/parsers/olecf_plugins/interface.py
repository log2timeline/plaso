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
"""This file contains the necessary interface for OLECF plugins."""

import abc
import logging

from plaso.lib import errors
from plaso.parsers import plugins


class OlecfPlugin(plugins.BasePlugin):
  """An OLECF plugin for Plaso."""

  __abstract = True

  NAME = 'olecf'

  # List of tables that should be present in the database, for verification.
  REQUIRED_ITEMS = frozenset([])

  def GetTimestamps(self, olecf_item):
    """Takes an OLECF object and returns extracted timestamps.

    Args:
      olecf_item: A OLECF item (instance of pyolecf.item).

    Returns:
      A tuple of two timestamps: created and modified.
    """
    if not olecf_item:
      return None, None

    try:
      creation_time = olecf_item.get_creation_time_as_integer()
    except OverflowError as exception:
      logging.warning(
          u'Unable to read the creaton time with error: {0:s}'.format(
              exception))
      creation_time = 0

    try:
      modification_time = olecf_item.get_modification_time_as_integer()
    except OverflowError as exception:
      logging.warning(
          u'Unable to read the modification time with error: {0:s}'.format(
              exception))
      modification_time = 0

    # If no useful events, return early.
    if not creation_time and not modification_time:
      return None, None

    # Office template documents sometimes contain a creation time
    # of -1 (0xffffffffffffffff).
    if creation_time == 0xffffffffffffffffL:
      creation_time = 0

    return creation_time, modification_time

  @abc.abstractmethod
  def ParseItems(
      self, parser_context, file_entry=None, root_item=None, items=None,
      **kwargs):
    """Parses OLECF items.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      root_item: Optional root item of the OLECF file. The default is None.
      item_names: Optional list of all items discovered in the root.
                  The default is None.
    """

  def Process(
      self, parser_context, file_entry=None, root_item=None, item_names=None,
      **kwargs):
    """Determine if this is the right plugin for this OLECF file.

    This function takes a list of sub items found in the root of a
    OLECF file and compares that to a list of required items defined
    in this plugin.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      root_item: Optional root item of the OLECF file. The default is None.
      item_names: Optional list of all items discovered in the root.
                  The default is None.

    Raises:
      errors.WrongPlugin: If the set of required items is not a subset
                          of the available items.
      ValueError: If the root_item or items are not set.
    """
    if root_item is None or item_names is None:
      raise ValueError(u'Root item or items are not set.')

    if not frozenset(item_names) >= self.REQUIRED_ITEMS:
      raise errors.WrongPlugin(
          u'Not the correct items for: {0:s}'.format(self.plugin_name))

    # This will raise if unhandled keyword arguments are passed.
    super(OlecfPlugin, self).Process(parser_context, **kwargs)

    items = []
    for item_string in self.REQUIRED_ITEMS:
      item = root_item.get_sub_item_by_name(item_string)

      if item:
        items.append(item)

    return self.ParseItems(
        parser_context, file_entry=file_entry, root_item=root_item, items=items)


class OleDefinitions(object):
  """Convenience class for OLE definitions."""

  VT_I2 = 0x0002
  VT_I4 = 0x0003
  VT_BOOL = 0x000b
  VT_LPSTR = 0x001e
  VT_LPWSTR = 0x001e
  VT_FILETIME = 0x0040
  VT_CF = 0x0047
