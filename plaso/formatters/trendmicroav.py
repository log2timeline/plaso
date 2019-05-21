# -*- coding: utf-8 -*-
"""The Trend Micro AV Logs file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


SCAN_RESULTS = {
    0: "Success (clean)",
    1: "Success (move)",
    2: "Success (delete)",
    3: "Success (rename)",
    4: "Pass > Deny access",
    5: "Failure (clean)",
    6: "Failure (move)",
    7: "Failure (delete)",
    8: "Failure (rename)",
    10: "Failure (clean), moved",
    11: "Failure (clean), deleted",
    12: "Failure (clean), renamed",
    13: "Pass > Deny access",
    14: "Failure (clean), move also failed",
    15: "Failure (clean), delete also failed",
    16: "Failure (clean), rename also failed",
    25: "Passed a potential security risk"
}

SCAN_TYPES = {
    0: "Manual scan",
    1: "Real-time scan",
    2: "Scheduled scan",
    3: "Scan Now scan",
    4: "DCS scan"
}

BLOCK_MODES = {
    0: "Internal filter",
    1: "Whitelist only"
}


class OfficeScanVirusDetectionLogEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a Trend Micro Office Scan Virus Detection Log event."""

  DATA_TYPE = 'av:trendmicro:scan'

  FORMAT_STRING_PIECES = [
      'Path: {path}',
      'File name: {filename}',
      '{threat}',
      ': {action}',
      '({scan_type})']

  FORMAT_STRING_SHORT_PIECES = [
      '{path}',
      '{filename}',
      '{action}']

  SOURCE_LONG = 'Trend Micro Office Scan Virus Detection Log'
  SOURCE_SHORT = 'LOG'

  # VALUE_FORMATTERS contains formatting functions for event values that are
  # not ready for human consumption.
  # These functions replace the integer codes for scan types and scan results
  # (a.k.a. actions) with human-readable strings.
  VALUE_FORMATTERS = {
      'scan_type': lambda scan_type: SCAN_TYPES[scan_type],
      'action': lambda action: SCAN_RESULTS[action],
  }

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    If any event values have a matching formatting function in VALUE_FORMATTERS,
    they are run through that function; then the dictionary is passed to the
    superclass's formatting method.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions
          between formatters and other components, such as storage and Windows
          EventLog resources.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter(
          'Unsupported data type: {0:s}.'.format(event_data.data_type))

    event_values = event_data.CopyToDict()
    for formattable_value_name, formatter in self.VALUE_FORMATTERS.items():
      if formattable_value_name in event_values:
        value = event_values[formattable_value_name]
        event_values[formattable_value_name] = formatter(value)

    return self._ConditionalFormatMessages(event_values)


class OfficeScanWebReputationLogEventFormatter(
    OfficeScanVirusDetectionLogEventFormatter):
  """Formatter for a Trend Micro Office Scan Virus Detection Log event."""

  DATA_TYPE = 'av:trendmicro:webrep'

  FORMAT_STRING_PIECES = [
      '{url}',
      '{ip}',
      'Group: {group_name}',
      '{group_code}',
      'Mode: {block_mode}',
      'Policy ID: {policy_identifier}',
      'Credibility rating: {credibility_rating}',
      'Credibility score: {credibility_score}',
      'Threshold value: {threshold}',
      'Accessed by: {application_name}']

  FORMAT_STRING_SHORT_PIECES = [
      '{url}',
      '{group_name}']

  VALUE_FORMATTERS = {
      'block_mode': lambda block_mode: BLOCK_MODES[block_mode]
  }

  SOURCE_LONG = 'Trend Micro Office Scan Virus Detection Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatters([
    OfficeScanVirusDetectionLogEventFormatter,
    OfficeScanWebReputationLogEventFormatter])
