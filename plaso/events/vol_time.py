#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Collection of EventObject helpers for the timeliner plugin in volatility."""
from plaso.lib import event
from plaso.lib import eventdata


class VolatilityEvent(event.EventObject):
  """A convenience class for an EventObject created from volatility."""

  # TODO: Have each event use a separate data type and move logic partially
  # into the formatters.
  DATA_TYPE = 'memory:volatility:timeliner'

  def __init__(self, timestamp):
    """Initializes a volatility event.

    Args:
      timestamp: The timestamp time value.
    """
    super(VolatilityEvent, self).__init__()

    if type(timestamp) not in (int, long):
      timestamp = int(timestamp)

    self.timestamp = timestamp * int(1e6)
    if self.timestamp < 1:
      self.timestamp = 0

    self.timestamp_desc = eventdata.EventTimestamp.CREATION_TIME


class EprocessEvent(VolatilityEvent):
  """Process Creation Event."""

  def __init__(self, timestamp, eprocess, timezone, event_exit=False):
    """Initialize the event.

    Args:
      timestamp: The timestamp of the entry.
      eprocess: A Eprocess object from the PSScan module.
      timezone: Timezone information about the event.
      event_exit: A boolean indicating if this is an process exit or
      creation event.
    """
    super(EprocessEvent, self).__init__(timestamp)
    # TODO: Remove this once each separate data type has it's own formatter.
    self.source_type = 'Eprocess'
    self.text = (
        u'Process: {}/PID: {}/PPID: {}/POffset:0x{:08x}').format(
            eprocess.ImageFileName, eprocess.UniqueProcessId,
            eprocess.InheritedFromUniqueProcessId, eprocess.obj_offset)

    if event_exit:
      self.timestamp_desc = eventdata.EventTimestamp.EXIT_TIME


class SockEvent(VolatilityEvent):
  """Network socket Event."""

  def __init__(self, timestamp, sock, protocol):
    """Initialize the network socket event.

    Args:
      timestamp: The timestamp of the entry.
      sock: A socket object from the Sockets plugin.
      protocol: String indicating the protocol.
    """
    super(SockEvent, self).__init__(timestamp)

    self.source_type = 'Socket'
    self.text = u'PID: {}/LocalIP: {}:{}/Protocol: {}({})'.format(
        sock.Pid, sock.LocalIpAddress, sock.LocalPort, sock.Protocol, protocol,
        sock.obj_offset)


class EvtEvent(VolatilityEvent):
  """An Windows EventViewer EVT log entry from the evetlogs.EvtLogs plugin."""

  def __init__(self, timestamp, fields):
    """Initialize the EventObject.

    Args:
      timestamp: The timestamp of the entry.
      fields: A list of events as the parser_evt_info function returns.
    """
    super(EvtEvent, self).__init__(timestamp)
    self.timestamp_desc = eventdata.EventTimestamp.WRITTEN_TIME
    self.source_type = 'WinEvt'
    # TODO: Refactor this so the text makes more sense, split each
    # field into a proper attribute and make a formatter.
    self.text = u'{}/{}/{}/{}/{}/{}/{}'.format(
        fields[1], fields[2], fields[3], fields[4],
        fields[5], fields[6], fields[7])


class NetObjectEvent(VolatilityEvent):
  """An event extracted from the Netscan plugin."""

  def __init__(self, timestamp, net_object, src_ip, src_port, dst_ip,
               dst_port, proto, state):
    """Initialize the event.

    Args:
      timestamp: The timestamp of the entry.
      net_object: A netscan._TCP_LISTENER or another class that
      inherits that object, based on the protocol.
      src_ip: IP address of the network source.
      src_port: Port number for the source connection.
      dst_ip: Destination IP address of the network source.
      dst_port: Port number for the destination connection.
      proto: The protocol used, a string, eg: TCP.
      state: The network connection state.
    """
    super(NetObjectEvent, self).__init__(timestamp)
    self.source_type = 'Network Connection'
    self.text = u'{}/{}:{} -> {}:{}/{}/{}/{:<#10x}'.format(
        net_object.Owner.UniqueProcessId, src_ip, src_port, dst_ip, dst_port,
        proto, state, net_object.obj_offset)


class ThreadEvent(VolatilityEvent):
  """Event created from the modscan.ThrdScan module."""

  def __init__(self, timestamp, image, thread, thread_exit=False):
    """Initialize the event.

    Args:
      timestamp: The timestamp of the entry.
      thread exit or creation.
      image: The name of the executable.
      thread: The modscan._ETHREAD object of the process.
      thread_exit: Indication if this is a process exit.
    """
    super(ThreadEvent, self).__init__(timestamp)
    self.source_type = 'Thread'
    self.text = u'File: {}/PID: {}/TID: {}'.format(
        image, thread.Cid.UniqueProcess, thread.Cid.UniqueThread)

    if thread_exit:
      self.timestamp_desc = eventdata.EventTimestamp.EXIT_TIME


class ProcExeDumpEvent(VolatilityEvent):
  """Event created from the procdump.ProcExeDump."""

  def __init__(self, timestamp, mod_name, mod_base):
    """Initialize the event.

    Args:
      timestamp: The timestamp of the entry.
      mod_name: The name of the DLL.
      mod_base: The base of the DLL.
    """
    super(ProcExeDumpEvent, self).__init__(timestamp)
    self.source_type = 'ProcExe Dump'
    self.text = u'File: {}/Base: {:#010x}'.format(
        mod_name, mod_base)


class PoOffsetEvent(VolatilityEvent):
  """Event created from offsets found in the filescan.PSScan plugin."""

  def __init__(self, timestamp, task, offset):
    """Initialize the event.

    Args:
      timestamp: The timestamp of the entry.
      task: A process object.
      offset: The offset.
    """
    super(PoOffsetEvent, self).__init__(timestamp)
    self.source_type = 'PE Timestamp Exe'
    self.text = (
        u'File: {}/PID: {}/PPID: {}/Command: {}/'
        'POffset:0x{:08x}').format(
            task.ImageFileName, task.UniqueProcessId,
            task.InheritedFromUniqueProcessId,
            task.Peb.ProcessParameters.CommandLine, offset)


class DLLEvent(VolatilityEvent):
  """Event created from the dlldump.DLLDump plugin."""

  def __init__(self, timestamp, task, basename, offset, base):
    """Initialize the event.

    Args:
      timestamp: The timestamp of the entry.
      task: A process object.
      basename: The name of the base DLL (BaseDllName).
      offset: The offset.
      base: The base of the DLL (DllBase).
    """
    super(DLLEvent, self).__init__(timestamp)
    self.source_type = 'PE DLL'
    self.text = (
        u'File: {}/Process: {}/PID: {}/PPID: {}/Process POffset:'
        '0x{:08x}/DLL Base: 0x{:8x}').format(
            task.ImageFileName, task.UniqueProcessId,
            task.InheritedFromUniqueProcessId, basename, offset, base)


class UserAssistEvent(VolatilityEvent):
  """Event created from the userassist.UserAssist plugin."""

  def __init__(self, timestamp, reg, subname, reg_id, count, focus_count,
               time_focused):
    """Initialize the event.

    Args:
      timestamp: The timestamp of the entry.
      reg: The registry key path.
      subname: The name of the application executed.
      reg_id: ID value of the UA record.
      count: The counter of times the application being executed.
      focus_count: The time the application has had focused.
    """
    super(UserAssistEvent, self).__init__(timestamp)
    self.timestamp_desc = 'Last Written'
    self.source_type = 'User Assist'
    self.text = (
        u'{}/Value: {}/ID: {}/Count: {}/FocusCount:{}/TimeFocused:'
        '{}').format(
            reg, subname, reg_id, count, focus_count, time_focused)


class ShimCacheEvent(VolatilityEvent):
  """Event created from the shimcache.ShimCache plugin."""

  def __init__(self, timestamp, path, update=False):
    """Initialize the event.

    Args:
      timestamp: The timestamp of the entry.
      path: The path to the file.
      update: Boolean indicating whether or not this is a new record
      or last written time (updated).
    """
    super(ShimCacheEvent, self).__init__(timestamp)
    self.source_type = 'ShimCache'
    self.text = unicode(path)
    if update:
      self.timestamp_desc = eventdata.EventTimestamp.WRITTEN_TIME


class RegistryEvent(VolatilityEvent):
  """Event created from the registryapi.RegistryApi plugin."""

  def __init__(self, timestamp, reg_key, reg_value):
    """Initialize the event.

    Args:
      timestamp: The timestamp of the entry.
      reg_key: The registry key path of the extracted registry key.
      reg_value: The extracted registry value.
    """
    super(RegistryEvent, self).__init__(timestamp)
    self.source_type = 'Registry'
    self.text = u'{}/{}'.format(reg_key, reg_value)
