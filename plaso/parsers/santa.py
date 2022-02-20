# -*- coding: utf-8 -*-
"""Santa log (santa.log) parser."""

import re
import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements
from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import text_parser


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
    pid (str): process identifier for the process.
    pid_version (str): the process identifier version extracted from the Mach
        audit token. The version can be used to identify process identifier
        rollovers.
    ppid (str): parent process identifier for the executed process.
    uid (str): user identifier associated with the executed process.
    gid (str): group identifier associated with the executed process.
  """

  DATA_TYPE = 'santa:process_exit'

  def __init__(self):
    """Initializes event data."""
    super(SantaProcessExitEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action = None
    self.pid = None
    self.pid_version = None
    self.ppid = None
    self.uid = None
    self.gid = None


class SantaFileSystemEventData(events.EventData):
  """Santa file system event data.

  Attributes:
    action (str): event type recorded by Santa.
    file_path (str): file path and name for WRITE/DELETE events.
    file_new_path (str): new file path and name for RENAME events.
    pid (str): process identifier for the process.
    pid_version (str): the process identifier version extracted from the Mach
        audit token. The version can be used to identify process identifier
        rollovers.
    ppid (str): parent process identifier for the executed process.
    process (str): process name.
    process_path (str): process file path.
    uid (str): user identifier associated with the executed process.
    user (str): user name associated with the executed process.
    gid (str): group identifier associated with the executed process.
    group (str): group name associated with the executed process.
  """

  DATA_TYPE = 'santa:file_system_event'

  def __init__(self):
    """Initializes event data."""
    super(SantaFileSystemEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action = None
    self.file_path = None
    self.file_new_path = None
    self.pid = None
    self.pid_version = None
    self.ppid = None
    self.process = None
    self.process_path = None
    self.uid = None
    self.user = None
    self.gid = None
    self.group = None


class SantaMountEventData(events.EventData):
  """Santa mount event data.

  Attributes:
    action (str): event type recorded by Santa.
    mount (str): disk mount point.
    volume (str): disk volume name.
    bsd_name (str): disk BSD name.
    fs (str): disk volume kind.
    model (str): disk model.
    serial (str): disk serial.
    bus (str): device protocol.
    dmg_path (str): DMG file path.
    appearance (str): disk appearance date.
  """

  DATA_TYPE = 'santa:diskmount'

  def __init__(self):
    """Initializes event data."""
    super(SantaMountEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action = None
    self.mount = None
    self.volume = None
    self.bsd_name = None
    self.fs = None
    self.model = None
    self.serial = None
    self.bus = None
    self.dmg_path = None
    self.appearance = None


class SantaParser(text_parser.PyparsingSingleLineTextParser):
  """Parses a Santa log file."""

  NAME = 'santa'
  DATA_FORMAT = 'Santa log (santa.log) file'

  _ENCODING = 'utf-8'

  MAX_LINE_LENGTH = 16384

  _SEP_TOKEN = pyparsing.Suppress('|')
  _SKIP_SEP = pyparsing.SkipTo('|')
  _SKIP_END = pyparsing.SkipTo(pyparsing.lineEnd)

  _PYPARSING_COMPONENTS = {
      'action': pyparsing.Suppress('action=') +
                _SKIP_SEP.setResultsName('action') + _SEP_TOKEN,
      'decision': pyparsing.Suppress('decision=') +
                  _SKIP_SEP.setResultsName('decision') + _SEP_TOKEN,
      'reason': pyparsing.Suppress('reason=') +
                _SKIP_SEP.setResultsName('reason') + _SEP_TOKEN,
      'explain': pyparsing.Suppress('explain=') +
                 _SKIP_SEP.setResultsName('explain') + _SEP_TOKEN,
      'process': pyparsing.Suppress('process=') +
                 _SKIP_SEP.setResultsName('process') + _SEP_TOKEN,
      'processpath': pyparsing.Suppress('processpath=') +
                     _SKIP_SEP.setResultsName('processpath') + _SEP_TOKEN,
      'sha256': pyparsing.Suppress('sha256=') +
                _SKIP_SEP.setResultsName('sha256') + _SEP_TOKEN,
      'cert_sha256': pyparsing.Suppress('cert_sha256=') +
                     _SKIP_SEP.setResultsName('cert_sha256') + _SEP_TOKEN,
      'cert_cn': pyparsing.Suppress('cert_cn=') +
                 _SKIP_SEP.setResultsName('cert_cn') + _SEP_TOKEN,
      'quarantine_url': pyparsing.Suppress('quarantine_url=') +
                        _SKIP_SEP.setResultsName('quarantine_url') +
                        _SEP_TOKEN,
      'pid': pyparsing.Suppress('pid=') + _SKIP_SEP.setResultsName('pid') +
             _SEP_TOKEN,
      'pidversion': pyparsing.Suppress('pidversion=') +
                    _SKIP_SEP.setResultsName(
                        'pidversion') + _SEP_TOKEN,
      'ppid': pyparsing.Suppress('ppid=') + _SKIP_SEP.setResultsName('ppid') +
              _SEP_TOKEN,
      'uid': pyparsing.Suppress('uid=') + _SKIP_SEP.setResultsName('uid') +
             _SEP_TOKEN,
      'user': pyparsing.Suppress('user=') + _SKIP_SEP.setResultsName('user') +
              _SEP_TOKEN,
      'gid': pyparsing.Suppress('gid=') +
             (_SKIP_SEP | _SKIP_END).setResultsName('gid') +
             pyparsing.Optional(_SEP_TOKEN),
      'group': pyparsing.Suppress('group=') +
               (_SKIP_SEP | _SKIP_END).setResultsName('group') +
               pyparsing.Optional(_SEP_TOKEN),
      'mode': pyparsing.Suppress('mode=') + _SKIP_SEP.setResultsName('mode') +
              _SEP_TOKEN,
      'newpath': pyparsing.Suppress('newpath=') +
                 _SKIP_SEP.setResultsName('newpath') + _SEP_TOKEN,
      'path': pyparsing.Suppress('path=') +
              (_SKIP_SEP | _SKIP_END).setResultsName('path') +
              pyparsing.Optional(_SEP_TOKEN),
      'args': pyparsing.Suppress('args=') + _SKIP_END.setResultsName('args'),
      'mount': pyparsing.Suppress('mount=') +
               _SKIP_SEP.setResultsName('mount') + _SEP_TOKEN,
      'volume': pyparsing.Suppress('volume=') +
                _SKIP_SEP.setResultsName('volume') + _SEP_TOKEN,
      'bsd_name': pyparsing.Suppress('bsdname=') +
                  (_SKIP_SEP | _SKIP_END).setResultsName('bsd_name') +
                  pyparsing.Optional(_SEP_TOKEN),
      'fs': pyparsing.Suppress('fs=') + _SKIP_SEP.setResultsName('fs') +
            _SEP_TOKEN,
      'model': pyparsing.Suppress('model=') +
               _SKIP_SEP.setResultsName('model') + _SEP_TOKEN,
      'serial': pyparsing.Suppress('serial=') +
                _SKIP_SEP.setResultsName('serial') + _SEP_TOKEN,
      'bus': pyparsing.Suppress('bus=') + _SKIP_SEP.setResultsName('bus') +
             _SEP_TOKEN,
      'dmg_path': pyparsing.Suppress('dmgpath=') +
                  _SKIP_SEP.setResultsName('dmg_path') + _SEP_TOKEN,
      'appearance': pyparsing.Suppress('appearance=') +
                    _SKIP_END.setResultsName('appearance')}

  _PYPARSING_COMPONENTS['date'] = pyparsing.Combine(
      pyparsing.Suppress('[') +
      pyparsing.Word(pyparsing.nums, exact=4) + pyparsing.Literal('-') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('-') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('T') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal(':') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal(':') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('.') +
      pyparsing.Word(pyparsing.nums, exact=3) + pyparsing.Literal('Z') +
      pyparsing.Suppress(']'))

  _VERIFICATION_REGEX = re.compile(
      r'^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\] [EACWNID] santad:')

  _QUOTA_EXCEEDED_LINE = (
      _PYPARSING_COMPONENTS['date'] +
      pyparsing.Literal(
          '*** LOG MESSAGE QUOTA EXCEEDED - SOME MESSAGES FROM THIS PROCESS '
          'HAVE BEEN DISCARDED ***'))

  _PROCESS_EXIT_LINE = (
      _PYPARSING_COMPONENTS['date'].setResultsName('date') +
      pyparsing.Suppress('I santad:') +
      pyparsing.Suppress('action=') +
      pyparsing.Literal('EXIT').setResultsName('action') + _SEP_TOKEN +
      _PYPARSING_COMPONENTS['pid'] +
      _PYPARSING_COMPONENTS['pidversion'] +
      _PYPARSING_COMPONENTS['ppid'] +
      _PYPARSING_COMPONENTS['uid'] +
      _PYPARSING_COMPONENTS['gid'])

  _EXECUTION_LINE = (
      _PYPARSING_COMPONENTS['date'].setResultsName('date') +
      pyparsing.Suppress('I santad:') +
      pyparsing.Suppress('action=') +
      pyparsing.Literal('EXEC').setResultsName('action') + _SEP_TOKEN +
      _PYPARSING_COMPONENTS['decision'] +
      _PYPARSING_COMPONENTS['reason'] +
      pyparsing.Optional(_PYPARSING_COMPONENTS['explain']) +
      _PYPARSING_COMPONENTS['sha256'] +
      pyparsing.Optional(_PYPARSING_COMPONENTS['cert_sha256']) +
      pyparsing.Optional(_PYPARSING_COMPONENTS['cert_cn']) +
      pyparsing.Optional(_PYPARSING_COMPONENTS['quarantine_url']) +
      _PYPARSING_COMPONENTS['pid'] +
      pyparsing.Optional(_PYPARSING_COMPONENTS['pidversion']) +
      _PYPARSING_COMPONENTS['ppid'] +
      _PYPARSING_COMPONENTS['uid'] +
      _PYPARSING_COMPONENTS['user'] +
      _PYPARSING_COMPONENTS['gid'] +
      _PYPARSING_COMPONENTS['group'] +
      _PYPARSING_COMPONENTS['mode'] +
      _PYPARSING_COMPONENTS['path'] +
      pyparsing.Optional(_PYPARSING_COMPONENTS['args']))

  _FILE_OPERATION_LINE = (
      _PYPARSING_COMPONENTS['date'].setResultsName('date') +
      pyparsing.Suppress('I santad:') +
      pyparsing.Suppress('action=') +
      (pyparsing.Literal('WRITE') ^
       pyparsing.Literal('RENAME') ^
       pyparsing.Literal('DELETE') ^
       pyparsing.Literal('LINK')).setResultsName('action') + _SEP_TOKEN +
      _PYPARSING_COMPONENTS['path'] +
      pyparsing.Optional(_PYPARSING_COMPONENTS['newpath']) +
      _PYPARSING_COMPONENTS['pid'] +
      pyparsing.Optional(_PYPARSING_COMPONENTS['pidversion']) +
      _PYPARSING_COMPONENTS['ppid'] +
      _PYPARSING_COMPONENTS['process'] +
      _PYPARSING_COMPONENTS['processpath'] +
      _PYPARSING_COMPONENTS['uid'] +
      _PYPARSING_COMPONENTS['user'] +
      _PYPARSING_COMPONENTS['gid'] +
      _PYPARSING_COMPONENTS['group'])

  _DISK_MOUNT_LINE = (
      _PYPARSING_COMPONENTS['date'].setResultsName('date') +
      pyparsing.Suppress('I santad:') +
      pyparsing.Suppress('action=') +
      pyparsing.Literal('DISKAPPEAR').setResultsName('action') + _SEP_TOKEN +
      _PYPARSING_COMPONENTS['mount'] +
      _PYPARSING_COMPONENTS['volume'] +
      _PYPARSING_COMPONENTS['bsd_name'] +
      _PYPARSING_COMPONENTS['fs'] +
      _PYPARSING_COMPONENTS['model'] +
      _PYPARSING_COMPONENTS['serial'] +
      _PYPARSING_COMPONENTS['bus'] +
      _PYPARSING_COMPONENTS['dmg_path'] +
      _PYPARSING_COMPONENTS['appearance'])

  _DISK_UMOUNT_LINE = (
      _PYPARSING_COMPONENTS['date'].setResultsName('date') +
      pyparsing.Suppress('I santad:') +
      pyparsing.Suppress('action=') +
      pyparsing.Literal('DISKDISAPPEAR').setResultsName('action') + _SEP_TOKEN +
      _PYPARSING_COMPONENTS['mount'] +
      _PYPARSING_COMPONENTS['volume'] +
      _PYPARSING_COMPONENTS['bsd_name'])

  LINE_STRUCTURES = [
      ('execution_line', _EXECUTION_LINE),
      ('process_exit_line', _PROCESS_EXIT_LINE),
      ('file_system_event_line', _FILE_OPERATION_LINE),
      ('mount_line', _DISK_MOUNT_LINE),
      ('umount_line', _DISK_UMOUNT_LINE),
      ('quota_exceeded_line', _QUOTA_EXCEEDED_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a matching entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
        and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): elements parsed from the file.

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
    date_time_string = self._GetValueFromStructure(structure, 'date')

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
      event_data.mount = self._GetValueFromStructure(structure, 'mount')
      event_data.volume = self._GetValueFromStructure(structure, 'volume')
      event_data.bsd_name = self._GetValueFromStructure(structure, 'bsd_name')

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)

    elif key == 'mount_line':
      event_data = SantaMountEventData()
      event_data.action = self._GetValueFromStructure(structure, 'action')
      event_data.mount = self._GetValueFromStructure(structure, 'mount')
      event_data.volume = self._GetValueFromStructure(structure, 'volume')
      event_data.bsd_name = self._GetValueFromStructure(structure, 'bsd_name')
      event_data.fs = self._GetValueFromStructure(structure, 'fs')
      event_data.model = self._GetValueFromStructure(structure, 'model')
      event_data.serial = self._GetValueFromStructure(structure, 'serial')
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

  # pylint: disable=unused-argument
  def VerifyStructure(self, parser_mediator, line):
    """Verifies that this is a santa log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      line (str): line from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    return re.match(self._VERIFICATION_REGEX, line) is not None


manager.ParsersManager.RegisterParser(SantaParser)
