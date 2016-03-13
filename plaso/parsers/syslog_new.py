import pyparsing
import re

from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser
from plaso.parsers import syslog

class NewSyslogParser(text_parser.PyparsingMultiLineTextParser):
  NAME = u'new_syslog'

  DESCRIPTION = u'New Syslog Parser'

  VERIFICATION_REGEX = re.compile('^\w{3}\s\d{2}\s\d{2}:\d{2}:\d{2}\s')


  _pyparsing_components = {
    u'month': text_parser.PyparsingConstants.MONTH.setResultsName(u'month'),
    u'day': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(u'day'),
    u'hour': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(u'hour'),
    u'minute': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
        u'minute'),
    u'second': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
        u'second'),
    u'fractional_seconds': pyparsing.Word(pyparsing.nums).setResultsName(
        u'fractional_seconds'),
    u'hostname': pyparsing.Word(pyparsing.printables).setResultsName(
        u'hostname'),
    u'process_name': pyparsing.Word(pyparsing.alphanums + u'.').setResultsName(
        u'process_name'),
    u'pid': text_parser.PyparsingConstants.PID.setResultsName(u'pid'),
    u'message': pyparsing.Regex(
        '.*?(?=($|\n\w{3}\s\d{2}\s\d{2}:\d{2}:\d{2}))', re.DOTALL).
        setResultsName(u'message'),
    u'comment_message': (
        pyparsing.Literal(u'---') +
        pyparsing.SkipTo(u'---\n', include=True)).setResultsName(u'message')
  }
  _pyparsing_components[u'date'] = (
      _pyparsing_components[u'month'] +
      _pyparsing_components[u'day'] +
      _pyparsing_components[u'hour'] + pyparsing.Suppress(u':') +
      _pyparsing_components[u'minute'] + pyparsing.Suppress(u':') +
      _pyparsing_components[u'second'] + pyparsing.Optional(
          pyparsing.Suppress(u'.') +
          _pyparsing_components[u'fractional_seconds']))


  DEFAULT_GRAMMAR = (
      _pyparsing_components[u'date'] +
      _pyparsing_components[u'hostname'] +
      _pyparsing_components[u'process_name'] +
      pyparsing.Optional(
          pyparsing.Suppress(u'[') +
          _pyparsing_components[u'pid'] + pyparsing.Suppress(u']')) +
      pyparsing.Optional(
        pyparsing.Suppress(u'<') +
        pyparsing.Word(pyparsing.alphanums) + pyparsing.Suppress(u'>')) +
      pyparsing.Optional(pyparsing.Suppress(u':')) +
      _pyparsing_components[u'message'] + pyparsing.lineEnd())

  SYSLOG_COMMENT = (_pyparsing_components[u'date'] + pyparsing.Suppress(u':') +
                    _pyparsing_components[u'comment_message'])

  LINE_STRUCTURES = [(u'syslog_line', DEFAULT_GRAMMAR),
                     (u'syslog_comment', SYSLOG_COMMENT)]

  def __init__(self):
    """Initialize the parser."""
    super(NewSyslogParser, self).__init__()
    self._year_use = 0
    self._last_month = 0

  def _UpdateYear(self, parser_mediator, month):
    """Updates the year to use, based on the current month.
    Args:
      month: The month observed by the parser, as a number.
    """
    if not self._year_use:
      self.year_use = parser_mediator.GetEstimatedYear()

    if not self._last_month:
      self._last_month = month
      return


  def VerifyStructure(self, parser_mediator, lines):
    """Verify that this is a syslog file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      lines: A buffer that contains content from the file.

    Returns:
      Returns True if the passed buffer appears to contain syslog content.
    """
    return re.match(self.VERIFICATION_REGEX, lines)

  def ParseRecord(self, parser_mediator, key, structure):
    """Parse a match.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
                 log file.
    """
    # No events for syslog comments.
    if key == u'syslog_comment':
      return

    month = timelib.MONTH_DICT.get(structure.month.lower(), None)
    if not month:
      parser_mediator.ProduceParserError(u'Invalid month value: {0:s}'.format(
        month))
      return
    self._UpdateYear(parser_mediator, month)
    timestamp = timelib.Timestamp.FromTimeParts(
        year= self._year_use, month=month, day=structure.day,
        hour=structure.hour, minutes=structure.minute,
        seconds=structure.second)

    attributes = {u'hostname': structure.hostname,
                  u'reporter': structure.process_name,
                  u'pid': structure.pid,
                  u'body': structure.message}

    event = syslog.SyslogLineEvent(timestamp, 0, attributes)
    parser_mediator.ProduceEvent(event)

manager.ParsersManager.RegisterParser(NewSyslogParser)
