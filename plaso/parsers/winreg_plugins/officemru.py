# -*- coding: utf-8 -*-
"""This file contains a parser for MS Office MRUs for Plaso."""

import logging
import re

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class OfficeMRUPlugin(interface.WindowsRegistryPlugin):
  """Plugin that parses Microsoft Office MRU keys."""

  NAME = u'microsoft_office_mru'
  DESCRIPTION = u'Parser for Microsoft Office MRU Registry data.'

  REG_TYPE = u'NTUSER'

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

  _SOURCE_APPEND = u': Microsoft Office MRU'

  def GetEntries(
      self, parser_mediator, registry_key, registry_file_type=None, **kwargs):
    """Collect Values under Office 2010 MRUs and return events for each one.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
    """
    # TODO: Test other Office versions to make sure this plugin is applicable.
    for value in registry_key.GetValues():
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
        logging.warning(u'Unable to convert filetime string to an integer.')
        filetime = 0

      # TODO: why this behavior? Only the first Item is stored with its
      # timestamp. Shouldn't this be: Store all the Item # values with
      # their timestamp and store the entire MRU as one event with the
      # registry key last written time?
      if value.name != u'Item 1':
        filetime = 0

      text_dict = {}
      text_dict[value.name] = value.data

      # TODO: change into a seperate event object.
      event_object = windows_events.WindowsRegistryEvent(
          filetime, registry_key.path, text_dict, offset=registry_key.offset,
          registry_file_type=registry_file_type,
          source_append=self._SOURCE_APPEND)
      parser_mediator.ProduceEvent(event_object)

    # TODO: generate a single event for the whole MRU.


winreg.WinRegistryParser.RegisterPlugin(OfficeMRUPlugin)
