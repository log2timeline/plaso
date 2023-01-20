# -*- coding: utf-8 -*-
"""MacOS Core Location services helper."""
import os

from plaso.lib import dtfabric_helper
from plaso.lib import errors


class ClientAuthStatusHelper(object):
  """Core Location Client Authorisation Status helper"""
  _AUTH_STATUS_CODES = {
    0: 'Not Determined',
    1: 'Restricted',
    2: 'Denied',
    3: 'Authorized Always',
    4: 'Authorized When In Use'}

  @classmethod
  def GetCode(cls, code):
    """Retrieves the description for a code.

    Args:
      code (int): status code

    Returns:
      str: name of the status code.
    """
    return cls._AUTH_STATUS_CODES.get(code, 'UNKNOWN: {0:d}'.format(code))


class DaemonStatusHelper(object):
  """Core Location Daemon Status helper"""
  _DAEMON_STATUS_CODES = {
    0: 'Reachability Unavailable',
    1: 'Reachability Small',
    2: 'Reachability Large',
    56: 'Reachability Unachievable'}

  @classmethod
  def GetCode(cls, code):
    """Retrieves the description for a code.

    Args:
      code (int): status code

    Returns:
      str: name of the status code.
    """
    return cls._DAEMON_STATUS_CODES.get(code, 'UNKNOWN: {0:d}'.format(code))


class SubharvesterIDHelper(object):
  """Core Location Subharvester ID helper"""
  _SUBHARVESTER_ID = {
    1: 'Wifi',
    2: 'Tracks',
    3: 'Realtime',
    4: 'App',
    5: 'Pass',
    6: 'Indoor',
    7: 'Pressure',
    8: 'Poi',
    9: 'Trace',
    10: 'Avenger',
    11: 'Altimeter',
    12: 'Ionosphere',
    13: 'Unknown'}

  @classmethod
  def GetCode(cls, subharvester_id):
    """Retrieves the description for an ID.

    Args:
      subharvester_id (int): identifier

    Returns:
      str: name of the ID.
    """
    return cls._SUBHARVESTER_ID.get(
        subharvester_id, 'UNKNOWN: {0:d}'.format(subharvester_id))


class LocationClientStateTrackerParser(dtfabric_helper.DtFabricHelper):
  """LocationClientStateTracker data chunk parser"""

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'location.yaml')

  def Parse(self, data):
    """Parses given data of a given size as a LocationClientStateTracker chunk

    Args:
      data (bytes): Raw data

    Returns:
      Dict: The state tracker data

    Raises:
      ParseError: if the data cannot be parsed.
    """
    return self._ReadStructureFromByteStream(
      data, 0, self._GetDataTypeMap('location_tracker_client_data')).__dict__


class LocationManagerStateTrackerParser(dtfabric_helper.DtFabricHelper):
  """LocationManagerStateTracker data chunk parser"""

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'location.yaml')

  def Parse(self, size, data):
    """Parses given data of a given size as a LocationManagerStateTracker chunk

    Args:
      size (int):  Size of the parsed data
      data (bytes): Raw data

    Returns:
      tuple(Dict, Dict): The state tracker data and an optional extra structure
        if running on Catalina.

    Raises:
      ParseError: if the data cannot be parsed.
    """
    state_tracker_structure = {}
    extra_state_tracker_structure = {}

    if size not in [64, 72]:
      raise errors.ParseError(
        "Possibly corrupted CLLocationManagerStateTracker block")
    state_tracker_structure = self._ReadStructureFromByteStream(
        data, 0, self._GetDataTypeMap(
          'location_manager_state_data')).__dict__
    if len(data) == 72:
      extra_state_tracker_structure = self._ReadStructureFromByteStream(
          data[64:], 64, self._GetDataTypeMap(
            'location_manager_state_data_extra')).__dict__

    return (state_tracker_structure, extra_state_tracker_structure)


class LocationTrackerIOHelper(object):
  """Location Tracker IO Message helper"""
  _IO_MESSAGE = {
    3758097008: 'CanSystemSleep',
    3758097024: 'SystemWillSleep',
    3758097040: 'SystemWillNotSleep',
    3758097184: 'SystemWillPowerOn',
    3758097168: 'SystemWillRestart',
    3758097152: 'SystemHasPoweredOn',
    3758097200: 'CopyClientID',
    3758097216: 'SystemCapabilityChange',
    3758097232: 'DeviceSignaledWakeup',
    3758096400: 'ServiceIsTerminated',
    3758096416: 'ServiceIsSuspended',
    3758096432: 'ServiceIsResumed',
    3758096640: 'ServiceIsRequestingClose',
    3758096641: 'ServiceIsAttemptingOpen',
    3758096656: 'ServiceWasClosed',
    3758096672: 'ServiceBusyStateChange',
    3758096680: 'ConsoleSecurityChange',
    3758096688: 'ServicePropertyChange',
    3758096896: 'CanDevicePowerOff',
    3758096912: 'DeviceWillPowerOff',
    3758096928: 'DeviceWillNotPowerOff',
    3758096944: 'DeviceHasPoweredOn',
    3758096976: 'SystemWillPowerOff',
    3758096981: 'SystemPagingOff'}

  @classmethod
  def GetMessage(cls, message_id):
    """Retrieves the description for a message ID.

    Args:
      message_id (int): identifier

    Returns:
      str: name of the ID.
    """
    return cls._IO_MESSAGE.get(message_id, 'UNKNOWN: {0:d}'.format(message_id))
