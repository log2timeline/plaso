import pyparsing

from plaso.parsers import text_parser
from plaso.parsers import syslog

class NewSyslogParser(text_parser.PyparsingMultiLineTextParser):
  NAME = u'new_syslog'

  DESCRIPTION = u'New Syslog Parser'


  _pyparsing_components = {
    u'month': text_parser.PyparsingConstants.MONTH.setResultsName(u'month'),
    u'day': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(u'day'),
    u'time': text_parser.PyparsingConstants.TIME.setResultsName(u'time'),
    u'hostname': pyparsing.Word(pyparsing.printables).setResultsName(
        u'hostname'),
    u'process_name': pyparsing.Word(pyparsing.alphanums).setResultsName(
        u'process'),
    u'pid': text_parser.PyparsingConstants.PID,

  }


  LINE_GRAMMAR = (_pyparsing_components[u'month'] +
                  _pyparsing_components[u'day'] +
                  _pyparsing_components[u'time'] )

  LINE_STRUCTURES = [(u'syslog_line', LINE_GRAMMAR)]

  def __init__(self):
    """Initialize the parser."""
    super(NewSyslogParser, self).__init__()

  def ParseRecord(self, parser_mediator, key, structure):
    """Parse a match."""

    