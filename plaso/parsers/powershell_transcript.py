# -*- coding: utf-8 -*-
"""Parser for powershell transcript files."""

import copy
import os
import re

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import interface
from plaso.parsers import manager


class PowerShellTranscriptEventData(events.EventData):
  """PowerShell transcript event data.

  Attributes:
    build_version (str): Build number of current version.
    clr_version (str): Common Language Runtime version.
    command (str): Command that was executed.
    compatible_versions (str): Compatible PowerShell versions.
    config_name (str): Configuration name.
    edition (str): PowerShell edition
    host_application (str): Application that executed command.
    machine (str): Hostname of machine.
    process_id (str): Process ID.
    remoting_protocol_version (str): PowerShell
      remote management protocol version.
    runas_user (str): User context of execution.
    serialization_version (str): Serialization method version.
    username (str): User that executed command.
    version (str): PowerShell version.
    ws_man_stack_version (str): WS-Management stack version
    username (str): User that executed command.
  """

  DATA_TYPE = 'powershell:transcript:event'

  def __init__(self):
    """Initializes event data."""

    super(PowerShellTranscriptEventData,
      self).__init__(data_type=self.DATA_TYPE)
    self.build_version = None
    self.clr_version = None
    self.command = None
    self.compatible_versions = None
    self.config_name = None
    self.edition = None
    self.host_application = None
    self.machine = None
    self.process_id = None
    self.remoting_protocol_version = None
    self.runas_user = None
    self.serialization_version = None
    self.username = None
    self.version = None
    self.ws_man_stack_version = None


class PowerShellTranscriptParser(interface.FileObjectParser):
  """Parses events from PowerShell transcript files."""

  NAME = 'powershell_transcript'

  DATA_FORMAT = 'PowerShell transcript event'

  _HEADER_READ_SIZE = 25

  # string that separates sections in transcript files
  SEPARATOR = '**********************'

  # dictionary that maps line number to content - we have to use line numbers
  # since different system languages use different 'titles'
  LINE_INFO_DICT = {3:'username',
                    4:'runas_user',
                    5:'config_name',
                    6:'machine',
                    7:'host_application',
                    8:'process_id',
                    9:'version',
                    10:'edition',
                    11:'compatible_versions',
                    12:'build_version',
                    13:'clr_version',
                    14:'ws_man_stack_version',
                    15:'remoting_protocol_version',
                    16:'serialization_version'}

  def CreateEventsFromTranscripts(self, transcripts, parser_mediator,
   header_data):
    """Get commandlines from transcripts

    Args:
      transcripts (list): list of lists containing data for every transcript
          in a file.
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      header_data (PowerShellTranscriptEventData): prefilled
          PowerShellTranscriptEventData object with metainfos.
    """

    for transcript in transcripts:
      # create a copy of the pre-filled event object
      event_data = copy.deepcopy(header_data)
      event = None
      timestamp_pattern = re.compile(r': (\d{14})$')
      # since the system language changes the description of the header fields
      # we have to go for the line numbers and regex match the timestamp
      if timestamp_pattern.search(transcript[2]):
        timestamp_string = timestamp_pattern.search(transcript[2])[1]
        full_headers = True
      elif timestamp_pattern.search(transcript[1]):
        timestamp_string = timestamp_pattern.search(transcript[1])[1]
        full_headers = False
      else:
        parser_mediator.ProduceExtractionWarning('could not find timestamp in '
          'transcript {0!s} - skipping malformed transcript'.format(transcript))
        continue
      # Timestamp format is YYYYMMDDHHmmss
      time_elements_tuple = int(timestamp_string[:4]),\
                            int(timestamp_string[4:6]),\
                            int(timestamp_string[6:8]),\
                            int(timestamp_string[8:10]),\
                            int(timestamp_string[10:12]),\
                            int(timestamp_string[12:])
      try:
        start_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
      except ValueError:
        parser_mediator.ProduceExtractionWarning('timestamp \"{0!s}\" seems '
          'invalid - skipping malformed transcript'.format(time_elements_tuple))
        continue
      start_time.is_local_time = True
      event = time_events.DateTimeValuesEvent(start_time,
        definitions.TIME_DESCRIPTION_START)
      # we don't use line breaks here since they aren't displayed nicely in TS
      if full_headers:
        command = '; '.join(transcript[18:len(transcript)])
      else:
        command = '; '.join(transcript[3:len(transcript)])
      event_data.command = command
      # finally create event if values have been set
      if (event is not None and event_data.command is not None and
            event_data.command != ''):
        parser_mediator.ProduceEventWithEventData(event, event_data)
      else:
        parser_mediator.ProduceExtractionWarning('skipping transcript {0!s} - '
          'since relevant event values could not be set'.format(transcript))


  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an PowerShell transcript file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """

    data = file_object.read(self._HEADER_READ_SIZE)
    if not data == b'\xef\xbb\xbf**********************':
      raise errors.WrongParser('Not a PowerShell transcript file')

    # The current offset of the file-like object needs to point at
    # the start of the file to parse the data correctly.
    file_object.seek(0, os.SEEK_SET)
    file_bytes = file_object.read()

    win_newline = b'\r\n'
    lin_newline = b'\n'
    # If transcript file was opened in editor, line breaks may have been changed
    if win_newline in file_bytes:
      line_bytes = file_bytes.split(win_newline)
    else:
      line_bytes = file_bytes.split(lin_newline)
    lines = [line.decode('utf-8') for line in line_bytes]
    separator_indices = []
    header_data = PowerShellTranscriptEventData()
    for index, line in enumerate(lines):
      if index in self.LINE_INFO_DICT:
        param = self.LINE_INFO_DICT[index]
        splitted = line.split(': ')
        if len(splitted) != 2:
          parser_mediator.ProduceExtractionWarning('line {0!s} seems invalid '
            'or value empty - skipping header info: {1!s}'.format(line,
            self.LINE_INFO_DICT[index]))
          continue
        # pre-fill data for later objects
        setattr(header_data, param, splitted[1])
      if line == self.SEPARATOR:
        separator_indices.append(index)
    # the file always starts with a transcript
    transcript_starts = [0]
    for i, sep_index in enumerate(separator_indices):
      # every second separator marks a new transcript
      if i%2 != 0:
        transcript_starts.append(sep_index)
    transcripts = []
    for i, start in enumerate(transcript_starts):
      # check we are not at the last transcript start
      # and take lines until next start
      if i != len(transcript_starts)-1:
        transcripts.append(lines[start:transcript_starts[i+1]])
      # for the last transcript we take the rest of the file
      else:
        transcripts.append(lines[start:len(lines)])
    self.CreateEventsFromTranscripts(transcripts, parser_mediator, header_data)

manager.ParsersManager.RegisterParser(PowerShellTranscriptParser)
