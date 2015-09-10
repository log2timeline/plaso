# -*- coding: utf-8 -*-

import construct

from plaso.events import windows_events
from plaso.lib import eventdata
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

  _SOURCE_APPEND = u'Shutdown Entry'

  def GetEntries(
      self, parser_mediator, registry_key, registry_file_type=None, **kwargs):
    """Collect ShutdownTime value under Windows and produce an event object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
    """
    shutdown_value = registry_key.GetValueByName(u'ShutdownTime')
    if not shutdown_value:
      return

    try:
      filetime = self.FILETIME_STRUCT.parse(shutdown_value.data)
    except construct.FieldError as exception:
      parser_mediator.ProduceParseError(
          u'Unable to extract shutdown timestamp with error: {0:s}'.format(
              exception))
      return

    text_dict = {u'Description': shutdown_value.name}

    event_object = windows_events.WindowsRegistryEvent(
        filetime, registry_key.path, text_dict, offset=registry_key.offset,
        usage=eventdata.EventTimestamp.LAST_SHUTDOWN,
        registry_file_type=registry_file_type,
        source_append=self._SOURCE_APPEND)
    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(ShutdownPlugin)
