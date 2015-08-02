# -*- coding: utf-8 -*-

import construct

from plaso.events import windows_events
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class ShutdownPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing the last shutdown time of a system."""

  NAME = u'windows_shutdown'
  DESCRIPTION = u'Parser for ShutdownTime Registry value.'

  REG_KEYS = [u'\\{current_control_set}\\Control\\Windows']
  REG_TYPE = u'SYSTEM'
  FILETIME_STRUCT = construct.ULInt64(u'filetime_timestamp')

  def GetEntries(
      self, parser_mediator, key=None, registry_type=None, codepage=u'cp1252',
      **unused_kwargs):
    """Collect ShutdownTime value under Windows and produce an event object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of winreg.WinRegKey).
          The default is None.
      registry_type: Optional Registry type string. The default is None.
    """
    shutdown_value = key.GetValue(u'ShutdownTime')
    if not shutdown_value:
      return
    text_dict = {}
    text_dict[u'Description'] = shutdown_value.name
    try:
      filetime = self.FILETIME_STRUCT.parse(shutdown_value.data)
    except construct.FieldError as exception:
      parser_mediator.ProduceParseError(
          u'Unable to extract shutdown timestamp with error: {0:s}'.format(
              exception))
      return
    timestamp = timelib.Timestamp.FromFiletime(filetime)

    event_object = windows_events.WindowsRegistryEvent(
        timestamp, key.path, text_dict,
        usage=eventdata.EventTimestamp.LAST_SHUTDOWN, offset=key.offset,
        registry_type=registry_type,
        source_append=u'Shutdown Entry')
    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(ShutdownPlugin)
