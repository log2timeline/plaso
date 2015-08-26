# -*- coding: utf-8 -*-
"""File containing a Windows Registry plugin to parse the typed URLs key."""

import re

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class TypedURLsPlugin(interface.KeyPlugin):
  """A Windows Registry plugin for typed URLs history."""

  NAME = u'windows_typed_urls'
  DESCRIPTION = u'Parser for Explorer typed URLs Registry data.'

  REG_TYPE = u'NTUSER'
  REG_KEYS = [
      u'\\Software\\Microsoft\\Internet Explorer\\TypedURLs',
      u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\TypedPaths']

  _RE_VALUE_NAME = re.compile(r'^url[0-9]+$', re.I)

  def GetEntries(
      self, parser_mediator, key=None, registry_file_type=None,
      codepage=u'cp1252', **kwargs):
    """Collect typed URLs values.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    for value in key.GetValues():
      # Ignore any value not in the form: 'url[0-9]+'.
      if not value.name or not self._RE_VALUE_NAME.search(value.name):
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not value.data or not value.DataIsString():
        continue

      # TODO: shouldn't this behavior be, put all the typed urls
      # into a single event object with the last written time of the key?
      if value.name == u'url1':
        timestamp = key.last_written_timestamp
      else:
        timestamp = 0

      text_dict = {}
      text_dict[value.name] = value.data

      event_object = windows_events.WindowsRegistryEvent(
          timestamp, key.path, text_dict, offset=key.offset,
          registry_file_type=registry_file_type,
          source_append=u': Typed URLs')
      parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(TypedURLsPlugin)
