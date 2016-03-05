# -*- coding: utf-8 -*-
"""The Symantec AV log file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


__author__ = 'David Nides (david.nides@gmail.com)'


class SymantecAVFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Symantec AV log file event."""

  DATA_TYPE = u'av:symantec:scanlog'

  EVENT_NAMES = {
      u'1': u'GL_EVENT_IS_ALERT',
      u'2': u'GL_EVENT_SCAN_STOP',
      u'3': u'GL_EVENT_SCAN_START',
      u'4': u'GL_EVENT_PATTERN_UPDATE',
      u'5': u'GL_EVENT_INFECTION',
      u'6': u'GL_EVENT_FILE_NOT_OPEN',
      u'7': u'GL_EVENT_LOAD_PATTERN',
      u'8': u'GL_STD_MESSAGE_INFO',
      u'9': u'GL_STD_MESSAGE_ERROR',
      u'10': u'GL_EVENT_CHECKSUM',
      u'11': u'GL_EVENT_TRAP',
      u'12': u'GL_EVENT_CONFIG_CHANGE',
      u'13': u'GL_EVENT_SHUTDOWN',
      u'14': u'GL_EVENT_STARTUP',
      u'16': u'GL_EVENT_PATTERN_DOWNLOAD',
      u'17': u'GL_EVENT_TOO_MANY_VIRUSES',
      u'18': u'GL_EVENT_FWD_TO_QSERVER',
      u'19': u'GL_EVENT_SCANDLVR',
      u'20': u'GL_EVENT_BACKUP',
      u'21': u'GL_EVENT_SCAN_ABORT',
      u'22': u'GL_EVENT_RTS_LOAD_ERROR',
      u'23': u'GL_EVENT_RTS_LOAD',
      u'24': u'GL_EVENT_RTS_UNLOAD',
      u'25': u'GL_EVENT_REMOVE_CLIENT',
      u'26': u'GL_EVENT_SCAN_DELAYED',
      u'27': u'GL_EVENT_SCAN_RESTART',
      u'28': u'GL_EVENT_ADD_SAVROAMCLIENT_TOSERVER',
      u'29': u'GL_EVENT_REMOVE_SAVROAMCLIENT_FROMSERVER',
      u'30': u'GL_EVENT_LICENSE_WARNING',
      u'31': u'GL_EVENT_LICENSE_ERROR',
      u'32': u'GL_EVENT_LICENSE_GRACE',
      u'33': u'GL_EVENT_UNAUTHORIZED_COMM',
      u'34': u'GL_EVENT_LOG_FWD_THRD_ERR',
      u'35': u'GL_EVENT_LICENSE_INSTALLED',
      u'36': u'GL_EVENT_LICENSE_ALLOCATED',
      u'37': u'GL_EVENT_LICENSE_OK',
      u'38': u'GL_EVENT_LICENSE_DEALLOCATED',
      u'39': u'GL_EVENT_BAD_DEFS_ROLLBACK',
      u'40': u'GL_EVENT_BAD_DEFS_UNPROTECTED',
      u'41': u'GL_EVENT_SAV_PROVIDER_PARSING_ERROR',
      u'42': u'GL_EVENT_RTS_ERROR',
      u'43': u'GL_EVENT_COMPLIANCE_FAIL',
      u'44': u'GL_EVENT_COMPLIANCE_SUCCESS',
      u'45': u'GL_EVENT_SECURITY_SYMPROTECT_POLICYVIOLATION',
      u'46': u'GL_EVENT_ANOMALY_START',
      u'47': u'GL_EVENT_DETECTION_ACTION_TAKEN',
      u'48': u'GL_EVENT_REMEDIATION_ACTION_PENDING',
      u'49': u'GL_EVENT_REMEDIATION_ACTION_FAILED',
      u'50': u'GL_EVENT_REMEDIATION_ACTION_SUCCESSFUL',
      u'51': u'GL_EVENT_ANOMALY_FINISH',
      u'52': u'GL_EVENT_COMMS_LOGIN_FAILED',
      u'53': u'GL_EVENT_COMMS_LOGIN_SUCCESS',
      u'54': u'GL_EVENT_COMMS_UNAUTHORIZED_COMM',
      u'55': u'GL_EVENT_CLIENT_INSTALL_AV',
      u'56': u'GL_EVENT_CLIENT_INSTALL_FW',
      u'57': u'GL_EVENT_CLIENT_UNINSTALL',
      u'58': u'GL_EVENT_CLIENT_UNINSTALL_ROLLBACK',
      u'59': u'GL_EVENT_COMMS_SERVER_GROUP_ROOT_CERT_ISSUE',
      u'60': u'GL_EVENT_COMMS_SERVER_CERT_ISSUE',
      u'61': u'GL_EVENT_COMMS_TRUSTED_ROOT_CHANGE',
      u'62': u'GL_EVENT_COMMS_SERVER_CERT_STARTUP_FAILED',
      u'63': u'GL_EVENT_CLIENT_CHECKIN',
      u'64': u'GL_EVENT_CLIENT_NO_CHECKIN',
      u'65': u'GL_EVENT_SCAN_SUSPENDED',
      u'66': u'GL_EVENT_SCAN_RESUMED',
      u'67': u'GL_EVENT_SCAN_DURATION_INSUFFICIENT',
      u'68': u'GL_EVENT_CLIENT_MOVE',
      u'69': u'GL_EVENT_SCAN_FAILED_ENHANCED',
      u'70': u'GL_EVENT_MAX_event_name',
      u'71': u'GL_EVENT_HEUR_THREAT_NOW_WHITELISTED',
      u'72': u'GL_EVENT_INTERESTING_PROCESS_DETECTED_START',
      u'73': u'GL_EVENT_LOAD_ERROR_COH',
      u'74': u'GL_EVENT_LOAD_ERROR_SYKNAPPS',
      u'75': u'GL_EVENT_INTERESTING_PROCESS_DETECTED_FINISH',
      u'76': u'GL_EVENT_HPP_SCAN_NOT_SUPPORTED_FOR_OS',
      u'77': u'GL_EVENT_HEUR_THREAT_NOW_KNOWN'}

  CATEGORY_NAMES = {
      u'1': u'GL_CAT_INFECTION',
      u'2': u'GL_CAT_SUMMARY',
      u'3': u'GL_CAT_PATTERN',
      u'4': u'GL_CAT_SECURITY'}

  ACTION_1_2_NAMES = {
      u'1': u'Quarantine infected file',
      u'2': u'Rename infected file',
      u'3': u'Delete infected file',
      u'4': u'Leave alone (log only)',
      u'5': u'Clean virus from file',
      u'6': u'Clean or delete macros'}

  ACTION_0_NAMES = {
      u'1': u'Quarantined',
      u'2': u'Renamed',
      u'3': u'Deleted',
      u'4': u'Left alone',
      u'5': u'Cleaned',
      u'6': (u'Cleaned or macros deleted (no longer used as of '
             u'Symantec AntiVirus 9.x)'),
      u'7': u'Saved file as...',
      u'8': u'Sent to Intel (AMS)',
      u'9': u'Moved to backup location',
      u'10': u'Renamed backup file',
      u'11': u'Undo action in Quarantine View',
      u'12': u'Write protected or lack of permissions - Unable to act on file',
      u'13': u'Backed up file'}

  # The identifier for the formatter (a regular expression)
  FORMAT_STRING_SEPARATOR = u'; '
  FORMAT_STRING_PIECES = [
      u'Event Name: {event_map}',
      u'Category Name: {category_map}',
      u'Malware Name: {virus}',
      u'Malware Path: {file}',
      u'Action0: {action0_map}',
      u'Action1: {action1_map}',
      u'Action2: {action2_map}',
      u'Description: {description}',
      u'Scan ID: {scanid}',
      u'Event Data: {event_data}',
      u'Remote Machine: {remote_machine}',
      u'Remote IP: {remote_machine_ip}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{file}',
      u'{virus}',
      u'{action0_map}',
      u'{action1_map}',
      u'{action2_map}']

  SOURCE_LONG = u'Symantec AV Log'
  SOURCE_SHORT = u'LOG'

  def GetMessages(self, unused_formatter_mediator, event_object):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator: the formatter mediator object (instance of
                          FormatterMediator).
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple containing the formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    event_values = event_object.CopyToDict()

    event = event_values.get(u'event', None)
    if event:
      event_values[u'event_map'] = self.EVENT_NAMES.get(event, u'Unknown')

    category = event_values.get(u'cat', None)
    if category:
      event_values[u'category_map'] = self.CATEGORY_NAMES.get(
          category, u'Unknown')

    action = event_values.get(u'action0', None)
    if action:
      event_values[u'action0_map'] = self.ACTION_0_NAMES.get(action, u'Unknown')

    action = event_values.get(u'action1', None)
    if action:
      event_values[u'action1_map'] = self.ACTION_1_2_NAMES.get(
          action, u'Unknown')

    action = event_values.get(u'action2', None)
    if action:
      event_values[u'action2_map'] = self.ACTION_1_2_NAMES.get(
          action, u'Unknown')

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(SymantecAVFormatter)
