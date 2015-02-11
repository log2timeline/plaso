# -*- coding: utf-8 -*-
"""This file contains a parser for MS Office MRUs for Plaso."""

import logging
import re

from plaso.events import windows_events
from plaso.lib import timelib
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class OfficeMRUPlugin(interface.KeyPlugin):
  """Plugin that parses Microsoft Office MRU keys."""

  NAME = 'winreg_office_mru'
  DESCRIPTION = u'Parser for Microsoft Office MRU Registry data.'

  REG_TYPE = 'NTUSER'

  REG_KEYS = [
      u'\\Software\\Microsoft\\Office\\14.0\\Word\\Place MRU',
      u'\\Software\\Microsoft\\Office\\14.0\\Access\\File MRU',
      u'\\Software\\Microsoft\\Office\\14.0\\Access\\Place MRU',
      u'\\Software\\Microsoft\\Office\\14.0\\PowerPoint\\File MRU',
      u'\\Software\\Microsoft\\Office\\14.0\\PowerPoint\\Place MRU',
      u'\\Software\\Microsoft\\Office\\14.0\\Excel\\File MRU',
      u'\\Software\\Microsoft\\Office\\14.0\\Excel\\Place MRU',
      u'\\Software\\Microsoft\\Office\\14.0\\Word\\File MRU']

  _RE_VALUE_NAME = re.compile(r'^Item [0-9]+$', re.I)

  # The Office 12 item MRU is formatted as:
  # [F00000000][T%FILETIME%]*\\%FILENAME%

  # The Office 14 item MRU is formatted as:
  # [F00000000][T%FILETIME%][O00000000]*%FILENAME%
  _RE_VALUE_DATA = re.compile(r'\[F00000000\]\[T([0-9A-Z]+)\].*\*[\\]?(.*)')

  def GetEntries(
      self, parser_mediator, key=None, registry_type=None, codepage='cp1252',
      **unused_kwargs):
    """Collect Values under Office 2010 MRUs and return events for each one.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
            The default is None.
      parser_chain: Optional string containing the parsing chain up to this
              point. The default is None.
    """
    # TODO: Test other Office versions to make sure this plugin is applicable.
    for value in key.GetValues():
      # Ignore any value not in the form: 'Item [0-9]+'.
      if not value.name or not self._RE_VALUE_NAME.search(value.name):
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not value.data or not value.DataIsString():
        continue

      values = self._RE_VALUE_DATA.findall(value.data)

      # Values will contain a list containing a tuple containing 2 values.
      if len(values) != 1 or len(values[0]) != 2:
        continue

      try:
        filetime = int(values[0][0], 16)
      except ValueError:
        logging.warning('Unable to convert filetime string to an integer.')
        filetime = 0

      # TODO: why this behavior? Only the first Item is stored with its
      # timestamp. Shouldn't this be: Store all the Item # values with
      # their timestamp and store the entire MRU as one event with the
      # registry key last written time?
      if value.name == 'Item 1':
        timestamp = timelib.Timestamp.FromFiletime(filetime)
      else:
        timestamp = 0

      text_dict = {}
      text_dict[value.name] = value.data

      event_object = windows_events.WindowsRegistryEvent(
          timestamp, key.path, text_dict, offset=key.offset,
          registry_type=registry_type,
          source_append=': Microsoft Office MRU')
      parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(OfficeMRUPlugin)
