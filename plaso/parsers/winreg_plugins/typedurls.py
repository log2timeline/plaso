# -*- coding: utf-8 -*-

import re

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class TypedURLsPlugin(interface.KeyPlugin):
  """A Windows Registry plugin for typed URLs history."""

  NAME = 'winreg_typed_urls'
  DESCRIPTION = u'Parser for Internet Explorer typed URLs Registry data.'

  REG_TYPE = 'NTUSER'
  REG_KEYS = [
      u'\\Software\\Microsoft\\Internet Explorer\\TypedURLs',
      u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\TypedPaths']

  _RE_VALUE_NAME = re.compile(r'^url[0-9]+$', re.I)

  def GetEntries(
      self, parser_mediator, key=None, registry_type=None, codepage='cp1252',
      **kwargs):
    """Collect typed URLs values.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      registry_type: Optional Registry type string. The default is None.
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
      if value.name == 'url1':
        timestamp = key.last_written_timestamp
      else:
        timestamp = 0

      text_dict = {}
      text_dict[value.name] = value.data

      event_object = windows_events.WindowsRegistryEvent(
          timestamp, key.path, text_dict, offset=key.offset,
          registry_type=registry_type,
          source_append=u': Typed URLs')
      parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(TypedURLsPlugin)
