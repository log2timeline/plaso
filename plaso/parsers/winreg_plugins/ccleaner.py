# -*- coding: utf-8 -*-
"""Parser for the CCleaner Registry key."""

from plaso.events import windows_events
from plaso.lib import errors
from plaso.lib import timelib
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Marc Seguin (segumarc@gmail.com)'


class CCleanerPlugin(interface.WindowsRegistryPlugin):
  """Gathers the CCleaner Keys for NTUSER hive."""

  NAME = u'ccleaner'
  DESCRIPTION = u'Parser for CCleaner Registry data.'

  REG_KEYS = [u'\\Software\\Piriform\\CCleaner']
  REG_TYPE = u'NTUSER'

  URLS = [(u'http://cheeky4n6monkey.blogspot.com/2012/02/writing-ccleaner'
           u'-regripper-plugin-part_05.html')]

  def GetEntries(
      self, parser_mediator, key=None, registry_file_type=None,
      codepage=u'cp1252', **unused_kwargs):
    """Extracts event objects from a CCleaner Registry key.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    for value in key.GetValues():
      if not value.name or not value.data:
        continue

      text_dict = {}
      text_dict[value.name] = value.data

      if value.name == u'UpdateKey':
        try:
          timestamp = timelib.Timestamp.FromTimeString(
              value.data, timezone=parser_mediator.timezone)
        except errors.TimestampError:
          parser_mediator.ProduceParseError(
              u'Unable to parse time string: {0:s}'.format(value.data))
          continue

        event_object = windows_events.WindowsRegistryEvent(
            timestamp, key.path, text_dict, offset=key.offset,
            registry_file_type=registry_file_type)

      elif value.name == u'0':
        event_object = windows_events.WindowsRegistryEvent(
            key.timestamp, key.path, text_dict, offset=key.offset,
            registry_file_type=registry_file_type)

      else:
        # TODO: change this event not to set a timestamp of 0.
        event_object = windows_events.WindowsRegistryEvent(
            0, key.path, text_dict, offset=key.offset,
            registry_file_type=registry_file_type)

      event_object.source_append = u': CCleaner Registry key'

      parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(CCleanerPlugin)
