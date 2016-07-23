# -*- coding: utf-8 -*-
"""Windows Registry plugin for parsing the last shutdown time of a system."""

import construct

from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class ShutdownWindowsRegistryEvent(time_events.FiletimeEvent):
  """Convenience class for a shutdown Windows Registry event.

  Attributes:
    key_path: a string containing the Windows Registry key path.
    offset: an integer containing the data offset of the shutdown
            Windows Registry value.
    value_name: a string containing the name of the Registry value.
  """

  DATA_TYPE = u'windows:registry:shutdown'

  def __init__(self, filetime, key_path, offset, value_name):
    """Initializes a shutdown Windows Registry event.

    Args:
      filetime: an integer containing a FILETIME timestamp.
      key_path: a string containing the Windows Registry key path.
      offset: an integer containing the data offset of the shutdown
              Windows Registry value.
      value_name: a string containing the name of the Registry value.
    """
    super(ShutdownWindowsRegistryEvent, self).__init__(
        filetime, eventdata.EventTimestamp.LAST_SHUTDOWN)
    self.key_path = key_path
    self.offset = offset
    self.value_name = value_name


class ShutdownPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing the last shutdown time of a system."""

  NAME = u'windows_shutdown'
  DESCRIPTION = u'Parser for ShutdownTime Registry value.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\Windows')])

  _UINT64_STRUCT = construct.ULInt64(u'value')

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
      parser_mediator.ProduceExtractionError((
          u'Unable to extract shutdown timestamp: {0:d} with error: '
          u'{1:s}').format(value_integer, exception))
      return

    event_object = ShutdownWindowsRegistryEvent(
        filetime, registry_key.path, shutdown_value.offset,
        shutdown_value.name)
    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(ShutdownPlugin)
