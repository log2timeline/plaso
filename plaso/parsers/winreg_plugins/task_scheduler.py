# -*- coding: utf-8 -*-
"""This file contains the Task Scheduler Registry keys plugins."""

import construct

from plaso.events import windows_events
from plaso.events import time_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class TaskCacheEvent(time_events.FiletimeEvent):
  """Convenience class for a Task Cache event."""

  DATA_TYPE = u'task_scheduler:task_cache:entry'

  def __init__(
      self, timestamp, timestamp_description, task_name, task_identifier):
    """Initializes the event.

    Args:
      timestamp: The FILETIME value for the timestamp.
      timestamp_description: The usage string for the timestamp value.
      task_name: String containing the name of the task.
      task_identifier: String containing the identifier of the task.
    """
    super(TaskCacheEvent, self).__init__(timestamp, timestamp_description)

    self.offset = 0
    self.task_name = task_name
    self.task_identifier = task_identifier


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

  def _GetIdValue(self, key):
    """Retrieves the Id value from Task Cache Tree key.

    Args:
      key: A Windows Registry key (instance of dfwinreg.WinRegistryKey).

    Yields:
      A tuple containing a Windows Registry Key (instance of
      dfwinreg.WinRegistryKey) and a Windows Registry value (instance of
      dfwinreg.WinRegistryValue).
    """
    id_value = key.GetValueByName(u'Id')
    if id_value:
      yield key, id_value

    for sub_key in key.GetSubkeys():
      for value_key, id_value in self._GetIdValue(sub_key):
        yield value_key, id_value

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Parses a Task Cache Registry key.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
    dynamic_info_size_error_reported = False

    tasks_key = registry_key.GetSubkeyByName(u'Tasks')
    tree_key = registry_key.GetSubkeyByName(u'Tree')

    if not tasks_key or not tree_key:
      parser_mediator.ProduceParseError(
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
          parser_mediator.ProduceParseError(
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
          parser_mediator.ProduceParseError(
              u'unsupported DynamicInfo value data size: {0:d}.'.format(
                  dynamic_info_value_data_size))
          dynamic_info_size_error_reported = True
        continue

      name = task_guids.get(sub_key.name, sub_key.name)

      values_dict = {}
      values_dict[u'Task: {0:s}'.format(name)] = u'[ID: {0:s}]'.format(
          sub_key.name)
      event_object = windows_events.WindowsRegistryEvent(
          registry_key.last_written_time, registry_key.path, values_dict,
          offset=registry_key.offset)
      parser_mediator.ProduceEvent(event_object)

      last_registered_time = dynamic_info_struct.get(u'last_registered_time')
      if last_registered_time:
        # Note this is likely either the last registered time or
        # the update time.
        event_object = TaskCacheEvent(
            last_registered_time, u'Last registered time', name, sub_key.name)
        parser_mediator.ProduceEvent(event_object)

      launch_time = dynamic_info_struct.get(u'launch_time')
      if launch_time:
        # Note this is likely the launch time.
        event_object = TaskCacheEvent(
            launch_time, u'Launch time', name, sub_key.name)
        parser_mediator.ProduceEvent(event_object)

      unknown_time = dynamic_info_struct.get(u'unknown_time')
      if unknown_time:
        event_object = TaskCacheEvent(
            unknown_time, u'Unknown time', name, sub_key.name)
        parser_mediator.ProduceEvent(event_object)

    # TODO: Add support for the Triggers value.


winreg.WinRegistryParser.RegisterPlugin(TaskCachePlugin)
