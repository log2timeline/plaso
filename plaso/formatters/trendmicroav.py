# -*- coding: utf-8 -*-
"""The Trend Micro AV Logs file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


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

  _SCAN_RESULTS = {
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

  _SCAN_TYPES = {
      0: "Manual scan",
      1: "Real-time scan",
      2: "Scheduled scan",
      3: "Scan Now scan",
      4: "DCS scan"
  }

  def __init__(self):
    """Initializes a Trend Micro Virus Log event format helper."""
    super(OfficeScanVirusDetectionLogEventFormatter, self).__init__()
    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='action',
        output_attribute='action', values=self._SCAN_RESULTS)

    self.helpers.append(helper)

    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='scan_type',
        output_attribute='scan_type', values=self._SCAN_TYPES)

    self.helpers.append(helper)


class OfficeScanWebReputationLogEventFormatter(
    interface.ConditionalEventFormatter):
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

  SOURCE_LONG = 'Trend Micro Office Scan Virus Detection Log'
  SOURCE_SHORT = 'LOG'

  _BLOCK_MODES = {
      0: "Internal filter",
      1: "Whitelist only"
  }

  def __init__(self):
    """Initializes a Trend Micro Virus Log event format helper."""
    super(OfficeScanWebReputationLogEventFormatter, self).__init__()
    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='block_mode',
        output_attribute='block_mode', values=self._BLOCK_MODES)

    self.helpers.append(helper)


manager.FormattersManager.RegisterFormatters([
    OfficeScanVirusDetectionLogEventFormatter,
    OfficeScanWebReputationLogEventFormatter])
