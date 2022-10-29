# -*- coding: utf-8 -*-
"""Text file parser plugin for Santa log files."""

import re

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements
from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class SantaExecutionEventData(events.EventData):
  """Santa execution event data.

  Attributes:
    action (str): action recorded by Santa.
    certificate_common_name (str): certificate common name.
    certificate_hash (str): SHA256 hash for the certificate associated with the
        executed process.
    decision (str): if the process was allowed or blocked.
    gid (str): group identifier associated with the executed process.
    group (str): group name associated with the executed process.
    long_reason (str): further explanation behind Santa decision to execute
        or block a process.
    mode (str): Santa execution mode, for example Monitor or Lockdown.
    pid (str): process identifier for the process.
    pid_version (str): the process identifier version extracted from the Mach
        audit token. The version can sed to identify process identifier
        rollovers.
    ppid (str): parent process identifier for the executed process.
    process_arguments (str): executed process with its arguments.
    process_hash (str): SHA256 hash for the executed process.
    process_path (str): process file path.
    reason (str): reason behind Santa decision to execute or block a process.
    uid (str): user identifier associated with the executed process.
    user (str): user name associated with the executed process.
  """

  DATA_TYPE = 'santa:execution'

  def __init__(self):
    """Initializes event data."""
    super(SantaExecutionEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action = None
    self.certificate_common_name = None
    self.certificate_hash = None
    self.decision = None
    self.gid = None
    self.group = None
    self.long_reason = None
    self.mode = None
    self.pid = None
    self.pid_version = None
    self.ppid = None
    self.process_arguments = None
    self.process_hash = None
    self.process_path = None
    self.quarantine_url = None
    self.reason = None
    self.uid = None
    self.user = None


class SantaProcessExitEventData(events.EventData):
  """Santa process exit event data.

  Attributes:
    action (str): action recorded by Santa.
    gid (str): group identifier associated with the executed process.
    pid (str): process identifier for the process.
    pid_version (str): the process identifier version extracted from the Mach
        audit token. The version can be used to identify process identifier
        rollovers.
    ppid (str): parent process identifier for the executed process.
    uid (str): user identifier associated with the executed process.
  """

  DATA_TYPE = 'santa:process_exit'

  def __init__(self):
    """Initializes event data."""
    super(SantaProcessExitEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action = None
    self.gid = None
    self.pid = None
    self.pid_version = None
    self.ppid = None
    self.uid = None


class SantaFileSystemEventData(events.EventData):
  """Santa file system event data.

  Attributes:
    action (str): event type recorded by Santa.
    file_new_path (str): new file path and name for RENAME events.
    file_path (str): file path and name for WRITE/DELETE events.
    gid (str): group identifier associated with the executed process.
    group (str): group name associated with the executed process.
    pid (str): process identifier for the process.
    pid_version (str): the process identifier version extracted from the Mach
        audit token. The version can be used to identify process identifier
        rollovers.
    ppid (str): parent process identifier for the executed process.
    process_path (str): process file path.
    process (str): process name.
    uid (str): user identifier associated with the executed process.
    user (str): user name associated with the executed process.
  """

  DATA_TYPE = 'santa:file_system_event'

  def __init__(self):
    """Initializes event data."""
    super(SantaFileSystemEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action = None
    self.file_new_path = None
    self.file_path = None
    self.gid = None
    self.group = None
    self.pid = None
    self.pid_version = None
    self.ppid = None
    self.process = None
    self.process_path = None
    self.uid = None
    self.user = None


class SantaMountEventData(events.EventData):
  """Santa mount event data.

  Attributes:
    action (str): event type recorded by Santa.
    appearance (str): disk appearance date.
    bsd_name (str): disk BSD name.
    bus (str): device protocol.
    dmg_path (str): DMG file path.
    fs (str): disk volume kind.
    model (str): disk model.
    mount (str): disk mount point.
    serial (str): disk serial.
    volume (str): disk volume name.
  """

  DATA_TYPE = 'santa:diskmount'

  def __init__(self):
    """Initializes event data."""
    super(SantaMountEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action = None
    self.appearance = None
    self.bsd_name = None
    self.bus = None
    self.dmg_path = None
    self.fs = None
    self.model = None
    self.mount = None
    self.serial = None
    self.volume = None


class SantaTextPlugin(interface.TextPlugin):
  """Text file parser plugin for Santa log files."""

  NAME = 'santa'
  DATA_FORMAT = 'Santa log (santa.log) file'

  ENCODING = 'utf-8'

  _MAXIMUM_LINE_LENGTH = 3000

  _SEPARATOR = pyparsing.Suppress('|')

  _SKIP_TO_SEPARATOR = pyparsing.SkipTo('|')

  _SKIP_TO_END = pyparsing.SkipTo(pyparsing.lineEnd)

  _DATE_AND_TIME = pyparsing.Combine(
      pyparsing.Suppress('[') + pyparsing.Word(pyparsing.nums, exact=4) +
      pyparsing.Literal('-') + pyparsing.Word(pyparsing.nums, exact=2) +
      pyparsing.Literal('-') + pyparsing.Word(pyparsing.nums, exact=2) +
      pyparsing.Literal('T') + pyparsing.Word(pyparsing.nums, exact=2) +
      pyparsing.Literal(':') + pyparsing.Word(pyparsing.nums, exact=2) +
      pyparsing.Literal(':') + pyparsing.Word(pyparsing.nums, exact=2) +
      pyparsing.Literal('.') + pyparsing.Word(pyparsing.nums, exact=3) +
      pyparsing.Literal('Z') + pyparsing.Suppress(']')).setResultsName(
          'date_time')

  _QUOTA_EXCEEDED_LINE = (_DATE_AND_TIME + pyparsing.Literal((
      '*** LOG MESSAGE QUOTA EXCEEDED - SOME MESSAGES FROM THIS PROCESS '
      'HAVE BEEN DISCARDED ***')))

  _PID = (pyparsing.Suppress('pid=') +
          _SKIP_TO_SEPARATOR.setResultsName('pid') + _SEPARATOR)

  _PID_VERSION = (pyparsing.Suppress('pidversion=') +
                 _SKIP_TO_SEPARATOR.setResultsName('pidversion') + _SEPARATOR)

  _PPID = (pyparsing.Suppress('ppid=') +
           _SKIP_TO_SEPARATOR.setResultsName('ppid') + _SEPARATOR)

  _UID = (pyparsing.Suppress('uid=') +
          _SKIP_TO_SEPARATOR.setResultsName('uid') + _SEPARATOR)

  _USER = (pyparsing.Suppress('user=') +
           _SKIP_TO_SEPARATOR.setResultsName('user') + _SEPARATOR)

  _GID = (pyparsing.Suppress('gid=') +
          (_SKIP_TO_SEPARATOR | _SKIP_TO_END).setResultsName('gid') +
          pyparsing.Optional(_SEPARATOR))

  _GROUP = (pyparsing.Suppress('group=') +
            (_SKIP_TO_SEPARATOR | _SKIP_TO_END).setResultsName('group') +
            pyparsing.Optional(_SEPARATOR))

  _VOLUME = (pyparsing.Suppress('volume=') +
             _SKIP_TO_SEPARATOR.setResultsName('volume') + _SEPARATOR)

  _BSD_NAME = (pyparsing.Suppress('bsdname=') +
               (_SKIP_TO_SEPARATOR | _SKIP_TO_END).setResultsName('bsd_name') +
               pyparsing.Optional(_SEPARATOR))

  _EXIT_ACTION = (pyparsing.Suppress('action=') +
                  pyparsing.Literal('EXIT').setResultsName('action') +
                  _SEPARATOR)

  _SANTAD_PREAMBLE = pyparsing.Suppress('I santad:')

  _PROCESS_EXIT_LINE = (
      _DATE_AND_TIME + _SANTAD_PREAMBLE + _EXIT_ACTION + _PID + _PID_VERSION +
      _PPID + _UID + _GID)

  _EXEC_ACTION = (
      pyparsing.Suppress('action=') +
      pyparsing.Literal('EXEC').setResultsName('action') + _SEPARATOR)

  _DECISION = (
      pyparsing.Suppress('decision=') +
      _SKIP_TO_SEPARATOR.setResultsName('decision') + _SEPARATOR)

  _REASON = (
      pyparsing.Suppress('reason=') +
      _SKIP_TO_SEPARATOR.setResultsName('reason') + _SEPARATOR)

  _EXPLAIN = (
      pyparsing.Suppress('explain=') +
      _SKIP_TO_SEPARATOR.setResultsName('explain') + _SEPARATOR)

  _SHA256 = (
      pyparsing.Suppress('sha256=') +
      _SKIP_TO_SEPARATOR.setResultsName('sha256') + _SEPARATOR)

  _CERT_SHA256 = (
      pyparsing.Suppress('cert_sha256=') +
      _SKIP_TO_SEPARATOR.setResultsName('cert_sha256') + _SEPARATOR)

  _CERT_CN = (
      pyparsing.Suppress('cert_cn=') +
      _SKIP_TO_SEPARATOR.setResultsName('cert_cn') + _SEPARATOR)

  _QUARANTINE_URL = (
      pyparsing.Suppress('quarantine_url=') +
      _SKIP_TO_SEPARATOR.setResultsName('quarantine_url') + _SEPARATOR)

  _MODE = (
      pyparsing.Suppress('mode=') + _SKIP_TO_SEPARATOR.setResultsName('mode') +
      _SEPARATOR)

  _PATH = (
      pyparsing.Suppress('path=') +
      (_SKIP_TO_SEPARATOR | _SKIP_TO_END).setResultsName('path') +
      pyparsing.Optional(_SEPARATOR))

  _ARGS = (pyparsing.Suppress('args=') + _SKIP_TO_END.setResultsName('args'))

  _EXECUTION_LINE = (
      _DATE_AND_TIME + _SANTAD_PREAMBLE + _EXEC_ACTION + _DECISION + _REASON +
      pyparsing.Optional(_EXPLAIN) + _SHA256 +
      pyparsing.Optional(_CERT_SHA256) + pyparsing.Optional(_CERT_CN) +
      pyparsing.Optional(_QUARANTINE_URL) + _PID +
      pyparsing.Optional(_PID_VERSION) + _PPID + _UID + _USER + _GID + _GROUP +
      _MODE + _PATH + pyparsing.Optional(_ARGS))

  _NEW_PATH = (
      pyparsing.Suppress('newpath=') +
      _SKIP_TO_SEPARATOR.setResultsName('newpath') + _SEPARATOR)

  _PROCESS = (
      pyparsing.Suppress('process=') +
      _SKIP_TO_SEPARATOR.setResultsName('process') + _SEPARATOR)

  _PROCESS_PATH = (
      pyparsing.Suppress('processpath=') +
      _SKIP_TO_SEPARATOR.setResultsName('processpath') + _SEPARATOR)

  _FILE_OPERATION_LINE = (
      _DATE_AND_TIME + _SANTAD_PREAMBLE + pyparsing.Suppress('action=') + (
          pyparsing.Literal('WRITE') ^ pyparsing.Literal('RENAME') ^
          pyparsing.Literal('DELETE') ^ pyparsing.Literal('LINK')
      ).setResultsName('action') + _SEPARATOR + _PATH +
      pyparsing.Optional(_NEW_PATH) + _PID + pyparsing.Optional(_PID_VERSION) +
      _PPID + _PROCESS + _PROCESS_PATH + _UID + _USER + _GID + _GROUP)

  _DISKAPPEAR_ACTION = (
      pyparsing.Suppress('action=') +
      pyparsing.Literal('DISKAPPEAR').setResultsName('action') + _SEPARATOR)

  _MOUNT = (pyparsing.Suppress('mount=') +
            _SKIP_TO_SEPARATOR.setResultsName('mount') + _SEPARATOR)

  _FS = (pyparsing.Suppress('fs=') + _SKIP_TO_SEPARATOR.setResultsName('fs') +
         _SEPARATOR)

  _MODEL = (pyparsing.Suppress('model=') +
            _SKIP_TO_SEPARATOR.setResultsName('model') + _SEPARATOR)

  _SERIAL = (pyparsing.Suppress('serial=') +
             _SKIP_TO_SEPARATOR.setResultsName('serial') + _SEPARATOR)

  _BUS = (pyparsing.Suppress('bus=') +
          _SKIP_TO_SEPARATOR.setResultsName('bus') + _SEPARATOR)

  _DMG_PATH = (pyparsing.Suppress('dmgpath=') +
               _SKIP_TO_SEPARATOR.setResultsName('dmg_path') + _SEPARATOR)

  _APPEARANCE = (pyparsing.Suppress('appearance=') +
                 _SKIP_TO_END.setResultsName('appearance'))

  _DISK_MOUNT_LINE = (
      _DATE_AND_TIME + _SANTAD_PREAMBLE + _DISKAPPEAR_ACTION + _MOUNT +
      _VOLUME + _BSD_NAME + _FS + _MODEL + _SERIAL + _BUS + _DMG_PATH +
      _APPEARANCE)

  _DISKDISAPPEAR_ACTION = (
      pyparsing.Suppress('action=') +
      pyparsing.Literal('DISKDISAPPEAR').setResultsName('action') + _SEPARATOR)

  _DISK_UMOUNT_LINE = (
      _DATE_AND_TIME + _SANTAD_PREAMBLE + _DISKDISAPPEAR_ACTION + _MOUNT +
      _VOLUME + _BSD_NAME)

  _LINE_STRUCTURES = [
      ('execution_line', _EXECUTION_LINE),
      ('process_exit_line', _PROCESS_EXIT_LINE),
      ('file_system_event_line', _FILE_OPERATION_LINE),
      ('mount_line', _DISK_MOUNT_LINE),
      ('umount_line', _DISK_UMOUNT_LINE),
      ('quota_exceeded_line', _QUOTA_EXCEEDED_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  _VERIFICATION_REGEX = re.compile(
      r'^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\] [EACWNID] santad:')

  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a pyparsing structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    if key == 'quota_exceeded_line':
      # skip this line
      return

    date_time = dfdatetime_time_elements.TimeElementsInMilliseconds()
    date_time_string = self._GetValueFromStructure(structure, 'date_time')

    try:
      date_time.CopyFromStringISO8601(date_time_string)
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(date_time_string))
      return

    if key == 'execution_line':
      event_data = SantaExecutionEventData()
      event_data.action = self._GetValueFromStructure(structure, 'action')
      event_data.decision = self._GetValueFromStructure(structure, 'decision')
      event_data.long_reason = self._GetValueFromStructure(structure, 'explain')
      event_data.reason = self._GetValueFromStructure(structure, 'reason')
      event_data.process_hash = self._GetValueFromStructure(structure, 'sha256')
      event_data.certificate_hash = self._GetValueFromStructure(
          structure, 'cert_sha256')
      event_data.certificate_common_name = self._GetValueFromStructure(
          structure, 'cert_cn')
      event_data.quarantine_url = self._GetValueFromStructure(
          structure, 'quarantine_url')
      event_data.pid = self._GetValueFromStructure(structure, 'pid')
      event_data.pid_version = self._GetValueFromStructure(
          structure, 'pidversion')
      event_data.ppid = self._GetValueFromStructure(structure, 'ppid')
      event_data.uid = self._GetValueFromStructure(structure, 'uid')
      event_data.user = self._GetValueFromStructure(structure, 'user')
      event_data.gid = self._GetValueFromStructure(structure, 'gid')
      event_data.group = self._GetValueFromStructure(structure, 'group')
      event_data.mode = self._GetValueFromStructure(structure, 'mode')
      event_data.process_path = self._GetValueFromStructure(structure, 'path')
      event_data.process_arguments = self._GetValueFromStructure(
          structure, 'args')

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_LAST_RUN)

    if key == 'process_exit_line':
      event_data = SantaProcessExitEventData()
      event_data.action = self._GetValueFromStructure(structure, 'action')
      event_data.pid = self._GetValueFromStructure(structure, 'pid')
      event_data.pid_version = self._GetValueFromStructure(
          structure, 'pidversion')
      event_data.ppid = self._GetValueFromStructure(structure, 'ppid')
      event_data.uid = self._GetValueFromStructure(structure, 'uid')
      event_data.gid = self._GetValueFromStructure(structure, 'gid')

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_EXIT)

    elif key == 'file_system_event_line':
      event_data = SantaFileSystemEventData()
      event_data.action = self._GetValueFromStructure(structure, 'action')
      event_data.file_path = self._GetValueFromStructure(structure, 'path')
      event_data.file_new_path = self._GetValueFromStructure(
          structure, 'newpath')
      event_data.pid = self._GetValueFromStructure(structure, 'pid')
      event_data.pid_version = self._GetValueFromStructure(
          structure, 'pidversion')
      event_data.ppid = self._GetValueFromStructure(structure, 'ppid')
      event_data.process = self._GetValueFromStructure(structure, 'process')
      event_data.process_path = self._GetValueFromStructure(
          structure, 'processpath')
      event_data.uid = self._GetValueFromStructure(structure, 'uid')
      event_data.user = self._GetValueFromStructure(structure, 'user')
      event_data.gid = self._GetValueFromStructure(structure, 'gid')
      event_data.group = self._GetValueFromStructure(structure, 'group')

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)

    elif key == 'umount_line':
      event_data = SantaMountEventData()
      event_data.action = self._GetValueFromStructure(structure, 'action')
      event_data.mount = self._GetValueFromStructure(structure, 'mount') or None
      event_data.volume = self._GetValueFromStructure(structure, 'volume')
      event_data.bsd_name = self._GetValueFromStructure(structure, 'bsd_name')

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)

    elif key == 'mount_line':
      event_data = SantaMountEventData()
      event_data.action = self._GetValueFromStructure(structure, 'action')
      event_data.mount = self._GetValueFromStructure(structure, 'mount') or None
      event_data.volume = self._GetValueFromStructure(structure, 'volume')
      event_data.bsd_name = self._GetValueFromStructure(structure, 'bsd_name')
      event_data.fs = self._GetValueFromStructure(structure, 'fs')
      event_data.model = self._GetValueFromStructure(structure, 'model')
      event_data.serial = self._GetValueFromStructure(
          structure, 'serial') or None
      event_data.bus = self._GetValueFromStructure(structure, 'bus')
      event_data.dmg_path = self._GetValueFromStructure(structure, 'dmg_path')
      event_data.appearance = self._GetValueFromStructure(
          structure, 'appearance')

      if event_data.appearance:
        new_date_time = dfdatetime_time_elements.TimeElementsInMilliseconds()

        try:
          new_date_time.CopyFromStringISO8601(event_data.appearance)
          new_event = time_events.DateTimeValuesEvent(
              new_date_time, definitions.TIME_DESCRIPTION_FIRST_CONNECTED)
          parser_mediator.ProduceEventWithEventData(new_event, event_data)
        except ValueError:
          parser_mediator.ProduceExtractionWarning(
              'invalid date time value: {0:s}'.format(event_data.appearance))

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)

    parser_mediator.ProduceEventWithEventData(event, event_data)

  def CheckRequiredFormat(self, parser_mediator, text_file_object):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_file_object (dfvfs.TextFile): text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      line = self._ReadLineOfText(text_file_object)
    except UnicodeDecodeError:
      return False

    return bool(self._VERIFICATION_REGEX.match(line))


text_parser.SingleLineTextParser.RegisterPlugin(SantaTextPlugin)
