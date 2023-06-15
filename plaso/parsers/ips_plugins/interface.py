# -*- coding: utf-8 -*-
"""Interface for IPS log file parser plugins."""

import abc
import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.parsers import plugins


class IPSPlugin(plugins.BasePlugin):
  """IPS file parser plugin."""

  NAME = 'ips_plugin'
  DATA_FORMAT = 'ips log file'

  ENCODING = 'utf-8'

  REQUIRED_HEADER_KEYS = []
  REQUIRED_CONTENT_KEYS = []

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _VARYING_DIGITS = pyparsing.Word(pyparsing.nums)

  TIMESTAMP_GRAMMAR = (
      _FOUR_DIGITS.setResultsName('year') + pyparsing.Suppress('-') +
      _TWO_DIGITS.setResultsName('month') + pyparsing.Suppress('-') +
      _TWO_DIGITS.setResultsName('day') +
      _TWO_DIGITS.setResultsName('hours') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('minutes') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('seconds') + pyparsing.Suppress('.') +
      _VARYING_DIGITS.setResultsName('fraction') +
      pyparsing.Word(
          pyparsing.nums + '+' + '-').setResultsName('timezone_delta'))

  def _ParseTimestampValue(self, parser_mediator, timestamp_text):
    """Parses a timestamp string.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      timestamp_text (str): the timestamp to parse.

    Returns:
       dfdatetime.TimeElements: date and time
          or None if not available.
    """
    # dfDateTime takes the time zone offset as number of minutes relative from
    # UTC. So for Easter Standard Time (EST), which is UTC-5:00 the sign needs
    # to be converted, to +300 minutes.

    parsed_timestamp = self.TIMESTAMP_GRAMMAR.parseString(timestamp_text)

    try:
      time_delta_hours = int(parsed_timestamp['timezone_delta'][:3], 10)
      time_delta_minutes = int(parsed_timestamp['timezone_delta'][3:], 10)
    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning(
          'unsupported timezone offset value')
      return None

    time_zone_offset = (time_delta_hours * 60) + time_delta_minutes

    try:
      fraction_float = float(f"0.{parsed_timestamp['fraction']}")
      milliseconds = round(fraction_float * 1000)

      time_element_object = dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=(
              parsed_timestamp['year'], parsed_timestamp['month'],
              parsed_timestamp['day'], parsed_timestamp['hours'],
              parsed_timestamp['minutes'], parsed_timestamp['seconds'],
              milliseconds),
          time_zone_offset=time_zone_offset)

    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning('unsupported date time value')
      return None

    return time_element_object

  def CheckRequiredKeys(self, ips_file):
    """Checks if the ips file's header and content have the keys required by
    the plugin.
    Args:
      ips_file (IPSFile): the file for which the structure is checked.
    Returns:
      bool: True if the file has the required keys defined by the plugin, or
          False if it does not, or if the plugin does not define required
          keys. The header and content can have more keys than the minimum
          required and still return True.
    """
    if not self.REQUIRED_HEADER_KEYS or not self.REQUIRED_CONTENT_KEYS:
      return False

    has_required_keys = True
    for required_header_key in self.REQUIRED_HEADER_KEYS:
      if required_header_key not in ips_file.header.keys():
        has_required_keys = False
        break

    for required_content_key in self.REQUIRED_CONTENT_KEYS:
      if required_content_key not in ips_file.content.keys():
        has_required_keys = False
        break

    return has_required_keys

  # pylint: disable=arguments-differ
  @abc.abstractmethod
  def Process(self, parser_mediator, ips_file=None, **unused_kwargs):
    """Extracts information from an ips log file.
    This is the main method that an ips plugin needs to implement.
    Args:
      parser_mediator (ParserMediator): parser mediator.
      ips_file (Optional[IPSFile]): database.
    Raises:
      ValueError: If the file value is missing.
    """
