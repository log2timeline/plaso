# -*- coding: utf-8 -*-
"""Parser for powershell transcript files."""

import copy
import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import text_parser
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

class PowerShellTranscriptParser(text_parser.PyparsingMultiLineTextParser):
  """Parses events from PowerShell transcript files."""

  NAME = 'powershell_transcript'

  DATA_FORMAT = 'PowerShell transcript event'

  # PowerShell transcript lines can be very long.
  MAX_LINE_LENGTH = 65536

  _ENCODING = 'utf-8-sig'

  _SEPARATOR = '**********************'

  _COLON = pyparsing.Literal(': ').suppress()

  # key always start with an uppercase character
  _METADATA_KEY = (pyparsing.Word(pyparsing.alphas.upper(), ' ' +
                   pyparsing.alphas) + _COLON)
  # negative lookahead needed for correct identification
  _METADATA_VALUE = (~_METADATA_KEY +
                     pyparsing.Word(pyparsing.printables,
                                    ' ' + pyparsing.printables))

  _METADATA_LINE = (
      _METADATA_KEY +
      _COLON +
      pyparsing.Optional(_METADATA_VALUE) +
      pyparsing.LineEnd().suppress()
  )

  _TRANSCRIPT_LINE = (
      ~_METADATA_LINE +
      pyparsing.Word(' ' + '\t' + '\r' +
                     pyparsing.printables + pyparsing.alphas8bit +
                     pyparsing.punc8bit,
                     exclude_chars='**********************') +
      pyparsing.LineEnd().suppress()
  )

  _SEPARATOR_LINE = (
      pyparsing.Literal(_SEPARATOR) +
      pyparsing.LineEnd().suppress()
  )

  LINE_STRUCTURES = [
      ('metadata_line', _METADATA_LINE),
      ('separator_line', _SEPARATOR_LINE),
      ('transcript_line', _TRANSCRIPT_LINE),
  ]

  def __init__(self):
    """Initializes instance attributes needed for processing."""
    super(PowerShellTranscriptParser, self).__init__()
    self.is_first_line = True
    self.is_transcript_start = True
    self.found_first_separator = False
    self.key_structure = []
    self.base_event = None

  def _GetTimestampFromString(self, value):
    """Parse a timestamp string an return a TimeElements event.

    Args:
      value (str): String containing a timestamp.

    Returns:
      dfdatetime_time_elements.TimeElements: TimeElements, if string
          was valid, None otherwise
    """
    if len(value) == 14:
      time_elements_tuple = (
          int(value[:4]),
          int(value[4:6]),
          int(value[6:8]),
          int(value[8:10]),
          int(value[10:12]),
          int(value[12:]),
      )
      try:
        start_time = dfdatetime_time_elements.TimeElements(
            time_elements_tuple=time_elements_tuple)
      except ValueError:
        start_time = None
    else:
      start_time = None
    return start_time

  def _CreateEventFromTranscript(self, parser_mediator):
    """Parse the transcript and return a PowerShell transcript event object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.

    Returns:
      bool: True if event could be created, false otherwise.
    """
    # whenever we reach this point, one full transcript was detected
    # and the next line will be a 'new first line' again
    self.is_transcript_start = True
    # create local key_structure for working
    key_structure = self.key_structure.copy()
    # reset class key_structure for next transcript
    self.key_structure.clear()

    new_event = PowerShellTranscriptEventData()
    transcript_text = ''
    metadata_lines = []
    event_time = None
    for key, structure in key_structure:
      if key == 'transcript_line':
        transcript_text = transcript_text + structure + '; '
      elif key == 'metadata_line':
        metadata_lines.append(structure)
    # transcript has a full header
    # that means we can try to extract all header infos
    if len(metadata_lines) > 1:
      # counter needed for identification of line
      counter = 0
      for metadata in metadata_lines:
        if ': ' in metadata:
          value = metadata.split(': ')[1]
        else:
          value = None
        # timestamp
        if counter == 1:
          start_time = self._GetTimestampFromString(value)
          if start_time is None:
            parser_mediator.ProduceExtractionWarning(
                'timestamp \"{0!s}\" seems invalid - skipping malformed '
                'transcript'.format(value))
            return False
          start_time.is_local_time = True
          event_time = time_events.DateTimeValuesEvent(
              start_time, definitions.TIME_DESCRIPTION_START)
        # username
        elif counter == 2:
          new_event.username = value
        # runas
        elif counter == 3:
          new_event.runas_user = value
        # configuration
        elif counter == 4:
          new_event.config_name = value
        # machine
        elif counter == 5:
          new_event.machine = value
        # host application
        elif counter == 6:
          new_event.host_application = value
        # process id
        elif counter == 7:
          new_event.process_id = value
        # version
        elif counter == 8:
          new_event.version = value
        # edition
        elif counter == 9:
          new_event.edition = value
        # compatible version
        elif counter == 10:
          new_event.compatible_versions = value
        # build version
        elif counter == 11:
          new_event.build_version = value
        # clr version
        elif counter == 12:
          new_event.clr_version = value
        # ws man stack version
        elif counter == 13:
          new_event.ws_man_stack_version = value
        # remoting protocol version
        elif counter == 14:
          new_event.remoting_protocol_version = value
        # serialization version
        elif counter == 15:
          new_event.serialization_version = value
        counter += 1
      # update base event for future use
      self.base_event = copy.deepcopy(new_event)
    # transcript with timestamp header
    elif len(metadata_lines) == 1:
      if self.base_event is None:
        parser_mediator.ProduceExtractionWarning(
            'initial transcript seems to have missing headers'
            ' - can not produce event')
        return False
      # since we don't have the full headers,
      # we just copy the headers from the last full event...
      new_event = copy.deepcopy(self.base_event)
      if ': ' in metadata_lines[0]:
        value = metadata_lines[0].split(': ')[1]
      else:
        value = None
      # ... and overwrite the timestamp
      start_time = self._GetTimestampFromString(value)
      if start_time is None:
        parser_mediator.ProduceExtractionWarning(
            'timestamp \"{0!s}\" seems invalid - skipping malformed '
            'transcript'.format(value))
        return False
      start_time.is_local_time = True
      event_time = time_events.DateTimeValuesEvent(start_time,
        definitions.TIME_DESCRIPTION_START)

    if transcript_text == '':
      parser_mediator.ProduceExtractionWarning(
          'skipping transcript {0!s} - since transcript text could '
          'not be set'.format(key_structure))
      return False
    new_event.command = transcript_text
    # create event if at least the most relevant fields are set
    if (event_time is not None and new_event.command is not None
        and new_event.command != ''):
      parser_mediator.ProduceEventWithEventData(event_time, new_event)
    else:
      parser_mediator.ProduceExtractionWarning(
          'skipping transcript {0!s} - relevant event values could '
          'not be set'.format(key_structure))
      return False
    return True

  def ParseRecord(self, parser_mediator, key, structure):
    """Parse the record and decide when a full transcript has been seen.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    # skip the very first (separator) line since it does not contain any
    # relevant info and will break our logic
    if self.is_first_line:
      self.is_first_line = False
      return
    # the first line of a transcript will always be a metadata line, however
    # pyparsing grammar might misinterpret this since 'start-line' looks like
    # a transcript line
    if self.is_transcript_start and key != 'separator_line':
      key = 'metadata_line'
      self.is_transcript_start = False

    # transcripts will begin/end at every second separator
    # so we need to monitor for them
    elif self.found_first_separator is False and key == 'separator_line':
      self.found_first_separator = True
      self.key_structure.append((key, ' '.join(structure)))
    # if 'second' separator is found, the current transcript
    # is finished and we can create an event from it
    elif self.found_first_separator is True and key == 'separator_line':
      self.found_first_separator = False
      # TODO: if the last transcript is not exited cleanly
      # (i.e. there is no final separator), we miss the final transcript
      # we would somehow need to know which line is the last one
      # and call _CreateEventFromTranscript on it -- however I have not found
      # a way to extract this information as a PyparsingMultiLineTextParser.
      # pyparsing.StringEnd() did not match correctly
      # __del__ will not be called in regular use cases
      # tl;dr I currently have no idea how to fix this
      self._CreateEventFromTranscript(parser_mediator)
    else:
      # overwrite key, since a transcript_line can never be followed directly
      # by a metadata_line (and vice versa) and the pyparsing could be wrong
      # (since a transcript_line can basically contain everything)
      if (key == 'metadata_line' and len(self.key_structure) > 0
          and self.key_structure[-1][0] == 'transcript_line'):
        key = 'transcript_line'
      elif (key == 'transcript_line' and len(self.key_structure) > 0
            and self.key_structure[-1][0] == 'metadata_line'):
        key = 'metadata_line'
    self.key_structure.append((key, ': '.join(structure)))


  def VerifyStructure(self, parser_mediator, lines):
    """Verifies whether content corresponds to an PowerShell transcript file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    if lines[:22] == self._SEPARATOR and 'Windows PowerShell' in lines:
      if 'Windows PowerShell' in lines:
        return True
    return False

manager.ParsersManager.RegisterParser(PowerShellTranscriptParser)
