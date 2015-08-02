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

  REG_TYPE = u'SOFTWARE'
  REG_KEYS = [
      u'\\Microsoft\\Windows NT\\CurrentVersion\\Schedule\\TaskCache']

  URL = [
      u'https://code.google.com/p/winreg-kb/wiki/TaskSchedulerKeys']

  _DYNAMIC_INFO_STRUCT = construct.Struct(
      u'dynamic_info_record',
      construct.ULInt32(u'version'),
      construct.ULInt64(u'last_registered_time'),
      construct.ULInt64(u'launch_time'),
      construct.Padding(8))

  _DYNAMIC_INFO_STRUCT_SIZE = _DYNAMIC_INFO_STRUCT.sizeof()

  def _GetIdValue(self, key):
    """Retrieves the Id value from Task Cache Tree key.

    Args:
      key: A Windows Registry key (instance of WinRegKey).

    Yields:
      A tuple containing a Windows Registry Key (instance of WinRegKey) and
      a Windows Registry value (instance of WinRegValue).
    """
    id_value = key.GetValue(u'Id')
    if id_value:
      yield key, id_value

    for sub_key in key.GetSubkeys():
      for value_key, id_value in self._GetIdValue(sub_key):
        yield value_key, id_value

  def GetEntries(
      self, parser_mediator, key=None, registry_type=None, codepage=u'cp1252',
      **unused_kwargs):
    """Parses a Task Cache Registry key.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
    """
    tasks_key = key.GetSubkey(u'Tasks')
    tree_key = key.GetSubkey(u'Tree')

    if not tasks_key or not tree_key:
      parser_mediator.ProduceParseError(
          u'Task Cache is missing a Tasks or Tree sub key.')
      return

    task_guids = {}
    for sub_key in tree_key.GetSubkeys():
      for value_key, id_value in self._GetIdValue(sub_key):
        # The GUID is in the form {%GUID%} and stored an UTF-16 little-endian
        # string and should be 78 bytes in size.
        if len(id_value.raw_data) != 78:
          parser_mediator.ProduceParseError(u'Unsupported Id value data size.')
          continue
        task_guids[id_value.data] = value_key.name

    for sub_key in tasks_key.GetSubkeys():
      dynamic_info_value = sub_key.GetValue(u'DynamicInfo')
      if not dynamic_info_value:
        continue

      if len(dynamic_info_value.raw_data) != self._DYNAMIC_INFO_STRUCT_SIZE:
        parser_mediator.ProduceParseError(
            u'Unsupported DynamicInfo value data size.')
        continue

      dynamic_info = self._DYNAMIC_INFO_STRUCT.parse(
          dynamic_info_value.raw_data)

      name = task_guids.get(sub_key.name, sub_key.name)

      text_dict = {}
      text_dict[u'Task: {0:s}'.format(name)] = u'[ID: {0:s}]'.format(
          sub_key.name)
      event_object = windows_events.WindowsRegistryEvent(
          key.last_written_timestamp, key.path, text_dict, offset=key.offset,
          registry_type=registry_type)
      parser_mediator.ProduceEvent(event_object)

      if dynamic_info.last_registered_time:
        # Note this is likely either the last registered time or
        # the update time.
        event_object = TaskCacheEvent(
            dynamic_info.last_registered_time, u'Last registered time', name,
            sub_key.name)
        parser_mediator.ProduceEvent(event_object)

      if dynamic_info.launch_time:
        # Note this is likely the launch time.
        event_object = TaskCacheEvent(
            dynamic_info.launch_time, u'Launch time', name, sub_key.name)
        parser_mediator.ProduceEvent(event_object)

    # TODO: Add support for the Triggers value.


winreg.WinRegistryParser.RegisterPlugin(TaskCachePlugin)
