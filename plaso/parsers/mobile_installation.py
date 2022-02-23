# -*- coding: utf-8 -*-
"""Parser for iOS mobile installation logs files obtained from iOS device.
Based on the research from Alex Brignoni."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import text_parser


class MobileInstallationEventData(events.EventData):
    """Mobile Installation log event data
    Attributes:
        number (str):
        severity (str):
        id (str):
        originator (str): process that created the entry
        body (str): body of the event line
    """

    DATA_TYPE = 'mobile_installation:line'

    def __init__(self):
        """Initializes event data."""
        super(MobileInstallationEventData, self).__init__(data_type=self.DATA_TYPE)
        self.number = None
        self.severity = None
        self.id = None
        self.originator = None
        self.body = None


class MobileInstallationParser(text_parser.PyparsingMultiLineTextParser):
    """Parser for iOS Mobile Installation logs."""

    NAME = 'mobile_installation.log'
    DATA_FORMAT = 'iOS mobile installation logs'

    MONTHS = {'Jan': 1,
              'Feb': 2,
              'Mar': 3,
              'Apr': 4,
              'May': 5,
              'Jun': 6,
              'Jul': 7,
              'Aug': 8,
              'Sep': 9,
              'Oct': 10,
              'Nov': 11,
              'Dec': 12}

    ONE_OR_TWO_DIGITS = text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS
    FOUR_DIGITS = text_parser.PyparsingConstants.FOUR_DIGITS
    THREE_LETTERS = text_parser.PyparsingConstants.THREE_LETTERS
    TIME_ELEMENTS = text_parser.PyparsingConstants.TIME_ELEMENTS

    _TIMESTAMP = (THREE_LETTERS.suppress() + THREE_LETTERS('month') + ONE_OR_TWO_DIGITS('day') +
                  TIME_ELEMENTS + FOUR_DIGITS('year'))

    _ELEMENT_NUMBER = pyparsing.Suppress('[') + pyparsing.Word(pyparsing.nums)('number') + pyparsing.Suppress(']')

    _ELEMENT_SEVERITY = pyparsing.Suppress('<') + pyparsing.Word(pyparsing.alphanums)('severity') + \
        pyparsing.Suppress('>')

    _ELEMENT_ID = pyparsing.Suppress('(') + pyparsing.Word(pyparsing.alphanums)('id') + pyparsing.Suppress(')')

    _ELEMENT_ORIGINATOR = (pyparsing.Suppress('+[') | pyparsing.Suppress('-[')) \
        + pyparsing.SkipTo(pyparsing.Literal(']'))('originator') \
        + pyparsing.Suppress(']: ')

    _BODY_END = pyparsing.StringEnd() | _TIMESTAMP

    _ELEMENT_BODY = pyparsing.SkipTo(_BODY_END)('body')

    _LINE_GRAMMAR = _TIMESTAMP + _ELEMENT_NUMBER + _ELEMENT_SEVERITY + _ELEMENT_ID + _ELEMENT_ORIGINATOR + \
        _ELEMENT_BODY + pyparsing.ZeroOrMore(pyparsing.lineEnd())

    LINE_STRUCTURES = [('log_entry', _LINE_GRAMMAR)]

    def ParseRecord(self, parser_mediator, key, structure):
        """Parses a log record structure and produces events.

        This function takes as an input a parsed pyparsing structure
        and produces an EventObject if possible from that structure.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfvfs.
          key (str): name of the parsed structure.
          structure (pyparsing.ParseResults): tokens from a parsed log line.
        """

        if key != 'log_entry':
            raise errors.ParseError(
                'Unable to parse record, unknown structure: {0:s}'.format(key))

        year = self._GetValueFromStructure(structure, 'year')
        month = self.MONTHS.get(self._GetValueFromStructure(structure, 'month'))
        day = self._GetValueFromStructure(structure, 'day')
        hours = self._GetValueFromStructure(structure, 'hours')
        minutes = self._GetValueFromStructure(structure, 'minutes')
        seconds = self._GetValueFromStructure(structure, 'seconds')

        event_data = MobileInstallationEventData()
        event_data.number = self._GetValueFromStructure(structure, 'number')
        event_data.severity = self._GetValueFromStructure(structure, 'severity')
        event_data.id = self._GetValueFromStructure(structure, 'id')
        event_data.originator = self._GetValueFromStructure(structure, 'originator')
        event_data.body = self._GetValueFromStructure(structure, 'body')

        try:
            date_time = dfdatetime_time_elements.TimeElements(time_elements_tuple=(
                year, month, day, hours, minutes, seconds))
        except (TypeError, ValueError):
            parser_mediator.ProduceExtractionWarning('invalid date time value')
            return

        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_MODIFICATION)

        parser_mediator.ProduceEventWithEventData(event, event_data)

    def VerifyStructure(self, parser_mediator, lines):
        """Verifies that this is a mobile installation log file.

        Args:
          parser_mediator (ParserMediator): mediates interactions between
              parsers and other components, such as storage and dfvfs.
          lines (str): one or more lines from the text file.

        Returns:
          bool: True if this is the correct parser, False otherwise.
        """

        match_generator = self._LINE_GRAMMAR.scanString(lines, maxMatches=1)
        return bool(list(match_generator))


manager.ParsersManager.RegisterParser(MobileInstallationParser)
