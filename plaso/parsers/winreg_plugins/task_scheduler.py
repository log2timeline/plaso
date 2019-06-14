# -*- coding: utf-8 -*-
"""This file contains the Task Scheduler Registry keys plugins."""

from __future__ import unicode_literals

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import dtfabric_plugin
from plaso.parsers.winreg_plugins import interface


class TaskCacheEventData(events.EventData):
  """Task Cache event data.

  Attributes:
    key_path (str): Windows Registry key path.
    task_name (str): name of the task.
    task_identifier (str): identifier of the task.
  """

  DATA_TYPE = 'task_scheduler:task_cache:entry'

  def __init__(self):
    """Initializes event data."""
    super(TaskCacheEventData, self).__init__(data_type=self.DATA_TYPE)
    self.key_path = None
    self.task_name = None
    self.task_identifier = None


class TaskCacheWindowsRegistryPlugin(
    dtfabric_plugin.DtFabricBaseWindowsRegistryPlugin):
  """Plugin that parses a Task Cache key."""

  NAME = 'windows_task_cache'
  DESCRIPTION = 'Parser for Task Scheduler cache Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\'
          'CurrentVersion\\Schedule\\TaskCache')])

  _DEFINITION_FILE = 'task_scheduler.yaml'

  def _GetIdValue(self, registry_key):
    """Retrieves the Id value from Task Cache Tree key.

    Args:
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.

    Yields:
      tuple: containing:

        dfwinreg.WinRegistryKey: Windows Registry key.
        dfwinreg.WinRegistryValue: Windows Registry value.
    """
    id_value = registry_key.GetValueByName('Id')
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

    tasks_key = registry_key.GetSubkeyByName('Tasks')
    tree_key = registry_key.GetSubkeyByName('Tree')

    if not tasks_key or not tree_key:
      parser_mediator.ProduceExtractionWarning(
          'Task Cache is missing a Tasks or Tree sub key.')
      return

    task_guids = {}
    for sub_key in tree_key.GetSubkeys():
      for value_key, id_value in self._GetIdValue(sub_key):
        # TODO: improve this check to a regex.
        # The GUID is in the form {%GUID%} and stored an UTF-16 little-endian
        # string and should be 78 bytes in size.
        id_value_data_size = len(id_value.data)
        if id_value_data_size != 78:
          parser_mediator.ProduceExtractionWarning(
              'unsupported Id value data size: {0:d}.'.format(
                  id_value_data_size))
          continue

        guid_string = id_value.GetDataAsObject()
        task_guids[guid_string] = value_key.name

    dynamic_info_map = self._GetDataTypeMap('dynamic_info_record')
    dynamic_info2_map = self._GetDataTypeMap('dynamic_info2_record')

    dynamic_info_size = dynamic_info_map.GetByteSize()
    dynamic_info2_size = dynamic_info2_map.GetByteSize()

    for sub_key in tasks_key.GetSubkeys():
      dynamic_info_value = sub_key.GetValueByName('DynamicInfo')
      if not dynamic_info_value:
        continue

      dynamic_info_record_map = None
      dynamic_info_value_data_size = len(dynamic_info_value.data)
      if dynamic_info_value_data_size == dynamic_info_size:
        dynamic_info_record_map = dynamic_info_map
      elif dynamic_info_value_data_size == dynamic_info2_size:
        dynamic_info_record_map = dynamic_info2_map
      else:
        if not dynamic_info_size_error_reported:
          parser_mediator.ProduceExtractionWarning(
              'unsupported DynamicInfo value data size: {0:d}.'.format(
                  dynamic_info_value_data_size))
          dynamic_info_size_error_reported = True
        continue

      try:
        dynamic_info_record = self._ReadStructureFromByteStream(
            dynamic_info_value.data, 0, dynamic_info_record_map)
      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to parse DynamicInfo record with error: {0!s}.'.format(
                exception))

      name = task_guids.get(sub_key.name, sub_key.name)

      event_data = TaskCacheEventData()
      event_data.key_path = registry_key.path
      event_data.task_name = name
      event_data.task_identifier = sub_key.name

      event = time_events.DateTimeValuesEvent(
          registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)

      last_registered_time = dynamic_info_record.last_registered_time
      if last_registered_time:
        # Note this is likely either the last registered time or
        # the update time.
        date_time = dfdatetime_filetime.Filetime(timestamp=last_registered_time)
        event = time_events.DateTimeValuesEvent(
            date_time, 'Last registered time')
        parser_mediator.ProduceEventWithEventData(event, event_data)

      launch_time = dynamic_info_record.launch_time
      if launch_time:
        # Note this is likely the launch time.
        date_time = dfdatetime_filetime.Filetime(timestamp=launch_time)
        event = time_events.DateTimeValuesEvent(
            date_time, 'Launch time')
        parser_mediator.ProduceEventWithEventData(event, event_data)

      unknown_time = getattr(dynamic_info_record, 'unknown_time', None)
      if unknown_time:
        date_time = dfdatetime_filetime.Filetime(timestamp=unknown_time)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_UNKNOWN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

    # TODO: Add support for the Triggers value.


winreg.WinRegistryParser.RegisterPlugin(TaskCacheWindowsRegistryPlugin)
