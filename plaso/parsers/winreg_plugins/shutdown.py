# -*- coding: utf-8 -*-

import construct

from plaso.containers import windows_events
from plaso.lib import eventdata
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class ShutdownPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing the last shutdown time of a system."""

  NAME = u'windows_shutdown'
  DESCRIPTION = u'Parser for ShutdownTime Registry value.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\Windows')])

  _UINT64_STRUCT = construct.ULInt64(u'value')

  _SOURCE_APPEND = u'Shutdown Entry'

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Collect ShutdownTime value under Windows and produce an event object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
    shutdown_value = registry_key.GetValueByName(u'ShutdownTime')
    if not shutdown_value:
      return

    value_integer = shutdown_value.GetDataAsObject()
    try:
      filetime = self._UINT64_STRUCT.parse(value_integer)
    except construct.FieldError as exception:
      parser_mediator.ProduceParseError((
          u'Unable to extract shutdown timestamp: {0:d} with error: '
          u'{1:s}').format(value_integer, exception))
      return

    values_dict = {u'Description': shutdown_value.name}

    event_object = windows_events.WindowsRegistryEvent(
        filetime, registry_key.path, values_dict,
        offset=registry_key.offset, source_append=self._SOURCE_APPEND,
        usage=eventdata.EventTimestamp.LAST_SHUTDOWN)
    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(ShutdownPlugin)
