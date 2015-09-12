# -*- coding: utf-8 -*-
"""File containing a Windows Registry plugin to parse the typed URLs key."""

import re

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class TypedURLsPlugin(interface.WindowsRegistryPlugin):
  """A Windows Registry plugin for typed URLs history."""

  NAME = u'windows_typed_urls'
  DESCRIPTION = u'Parser for Explorer typed URLs Registry data.'

  REG_TYPE = u'NTUSER'
  REG_KEYS = [
      u'\\Software\\Microsoft\\Internet Explorer\\TypedURLs',
      u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\TypedPaths']

  _RE_VALUE_NAME = re.compile(r'^url[0-9]+$', re.I)

  _SOURCE_APPEND = u': Typed URLs'

  def GetEntries(
      self, parser_mediator, registry_key, registry_file_type=None, **kwargs):
    """Collect typed URLs values.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
    """
    values_dict = {}
    for value in registry_key.GetValues():
      # Ignore any value not in the form: 'url[0-9]+'.
      if not value.name or not self._RE_VALUE_NAME.search(value.name):
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not value.data or not value.DataIsString():
        continue

      values_dict[value.name] = value.data

    event_object = windows_events.WindowsRegistryEvent(
        registry_key.last_written_time, registry_key.path, values_dict,
        offset=registry_key.offset, registry_file_type=registry_file_type,
        source_append=self._SOURCE_APPEND)
    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(TypedURLsPlugin)
