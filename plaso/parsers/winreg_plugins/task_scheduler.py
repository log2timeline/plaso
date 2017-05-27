# -*- coding: utf-8 -*-
"""This file contains the Task Scheduler Registry keys plugins."""

import construct

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.containers import windows_events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class TaskCacheEventData(events.EventData):
  """Task Cache event data.

  Attributes:
    task_name (str): name of the task.
    task_identifier (str): identifier of the task.
  """

  DATA_TYPE = u'task_scheduler:task_cache:entry'

  def __init__(self):
    """Initializes event data."""
    super(TaskCacheEventData, self).__init__(data_type=self.DATA_TYPE)
    self.task_name = None
    self.task_identifier = None


class TaskCachePlugin(interface.WindowsRegistryPlugin):
  """Plugin that parses a Task Cache key."""

  NAME = u'windows_task_cache'
  DESCRIPTION = u'Parser for Task Scheduler cache Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\'
          u'CurrentVersion\\Schedule\\TaskCache')])

  URLS = [(
      u'https://github.com/libyal/winreg-kb/blob/master/documentation/'
      u'Task%20Scheduler%20Keys.asciidoc')]

  _DYNAMIC_INFO_STRUCT = construct.Struct(
      u'dynamic_info_record',
      construct.ULInt32(u'unknown1'),
      construct.ULInt64(u'last_registered_time'),
      construct.ULInt64(u'launch_time'),
      construct.ULInt32(u'unknown2'),
      construct.ULInt32(u'unknown3'))

  _DYNAMIC_INFO_STRUCT_SIZE = _DYNAMIC_INFO_STRUCT.sizeof()

  _DYNAMIC_INFO2_STRUCT = construct.Struct(
      u'dynamic_info2_record',
      construct.ULInt32(u'unknown1'),
      construct.ULInt64(u'last_registered_time'),
      construct.ULInt64(u'launch_time'),
      construct.ULInt32(u'unknown2'),
      construct.ULInt32(u'unknown3'),
      construct.ULInt64(u'unknown_time'))

  _DYNAMIC_INFO2_STRUCT_SIZE = _DYNAMIC_INFO2_STRUCT.sizeof()

  def _GetIdValue(self, registry_key):
    """Retrieves the Id value from Task Cache Tree key.

    Args:
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.

    Yields:
      tuple: contains:

        dfwinreg.WinRegistryKey: Windows Registry key.
        dfwinreg.WinRegistryValue: Windows Registry value.
    """
    id_value = registry_key.GetValueByName(u'Id')
    if id_value:
      yield registry_key, id_value

    for sub_key in registry_key.GetSubkeys():
      for value_key, id_value in self._GetIdValue(sub_key):
        yield value_key, id_value

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    dynamic_info_size_error_reported = False

    tasks_key = registry_key.GetSubkeyByName(u'Tasks')
    tree_key = registry_key.GetSubkeyByName(u'Tree')

    if not tasks_key or not tree_key:
      parser_mediator.ProduceExtractionError(
          u'Task Cache is missing a Tasks or Tree sub key.')
      return

    task_guids = {}
    for sub_key in tree_key.GetSubkeys():
      for value_key, id_value in self._GetIdValue(sub_key):
        # TODO: improve this check to a regex.
        # The GUID is in the form {%GUID%} and stored an UTF-16 little-endian
        # string and should be 78 bytes in size.
        id_value_data_size = len(id_value.data)
        if id_value_data_size != 78:
          parser_mediator.ProduceExtractionError(
              u'unsupported Id value data size: {0:d}.'.format(
                  id_value_data_size))
          continue

        guid_string = id_value.GetDataAsObject()
        task_guids[guid_string] = value_key.name

    for sub_key in tasks_key.GetSubkeys():
      dynamic_info_value = sub_key.GetValueByName(u'DynamicInfo')
      if not dynamic_info_value:
        continue

      dynamic_info_value_data_size = len(dynamic_info_value.data)
      if dynamic_info_value_data_size == self._DYNAMIC_INFO_STRUCT_SIZE:
        dynamic_info_struct = self._DYNAMIC_INFO_STRUCT.parse(
            dynamic_info_value.data)

      elif dynamic_info_value_data_size == self._DYNAMIC_INFO2_STRUCT_SIZE:
        dynamic_info_struct = self._DYNAMIC_INFO_STRUCT.parse(
            dynamic_info_value.data)

      else:
        if not dynamic_info_size_error_reported:
          parser_mediator.ProduceExtractionError(
              u'unsupported DynamicInfo value data size: {0:d}.'.format(
                  dynamic_info_value_data_size))
          dynamic_info_size_error_reported = True
        continue

      name = task_guids.get(sub_key.name, sub_key.name)

      values_dict = {}
      values_dict[u'Task: {0:s}'.format(name)] = u'[ID: {0:s}]'.format(
          sub_key.name)

      event_data = windows_events.WindowsRegistryEventData()
      event_data.key_path = registry_key.path
      event_data.offset = registry_key.offset
      event_data.regvalue = values_dict

      event = time_events.DateTimeValuesEvent(
          registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)

      event_data = TaskCacheEventData()
      event_data.task_name = name
      event_data.task_identifier = sub_key.name

      last_registered_time = dynamic_info_struct.get(u'last_registered_time')
      if last_registered_time:
        # Note this is likely either the last registered time or
        # the update time.
        date_time = dfdatetime_filetime.Filetime(timestamp=last_registered_time)
        event = time_events.DateTimeValuesEvent(
            date_time, u'Last registered time')
        parser_mediator.ProduceEventWithEventData(event, event_data)

      launch_time = dynamic_info_struct.get(u'launch_time')
      if launch_time:
        # Note this is likely the launch time.
        date_time = dfdatetime_filetime.Filetime(timestamp=launch_time)
        event = time_events.DateTimeValuesEvent(
            date_time, u'Launch time')
        parser_mediator.ProduceEventWithEventData(event, event_data)

      unknown_time = dynamic_info_struct.get(u'unknown_time')
      if unknown_time:
        date_time = dfdatetime_filetime.Filetime(timestamp=unknown_time)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_UNKNOWN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

    # TODO: Add support for the Triggers value.


winreg.WinRegistryParser.RegisterPlugin(TaskCachePlugin)
