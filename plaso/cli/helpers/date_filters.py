# -*- coding: utf-8 -*-
"""The date filters CLI arguments helper."""

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.filters import file_entry as file_entry_filters
from plaso.lib import errors


class DateFiltersArgumentsHelper(interface.ArgumentsHelper):
  """Date filters CLI arguments helper."""

  NAME = 'date_filters'
  DESCRIPTION = 'Date filters command line arguments.'

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
          argparse group.
    """
    argument_group.add_argument(
        '--date-filter', '--date_filter', action='append', type=str,
        dest='date_filters', metavar='TYPE_START_END', default=[], help=(
            'Filter based on file entry date and time ranges. This parameter '
            'is formatted as "TIME_VALUE,START_DATE_TIME,END_DATE_TIME" where '
            'TIME_VALUE defines which file entry timestamp the filter applies '
            'to e.g. atime, ctime, crtime, bkup, etc. START_DATE_TIME and '
            'END_DATE_TIME define respectively the start and end of the date '
            'time range. A date time range requires at minimum start or end '
            'to time of the boundary and END defines the end time. Both '
            'timestamps be set. The date time values are formatted as: '
            'YYYY-MM-DD hh:mm:ss.######[+-]##:## Where # are numeric digits '
            'ranging from 0 to 9 and the seconds fraction can be either 3 '
            'or 6 digits. The time of day, seconds fraction and time zone '
            'offset are optional. The default time zone is UTC. E.g. "atime, '
            '2013-01-01 23:12:14, 2013-02-23". This parameter can be repeated '
            'as needed to add additional date boundaries, e.g. once for '
            'atime, once for crtime, etc.'))

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
      BadConfigOption: when the date filter is badly formatted.
    """
    if not isinstance(configuration_object, tools.CLITool):
      raise errors.BadConfigObject(
          'Configuration object is not an instance of CLITool')

    filter_collection = getattr(
        configuration_object, '_filter_collection', None)
    if not filter_collection:
      raise errors.BadConfigObject(
          'Filter collection missing from configuration object')

    date_filters = getattr(options, 'date_filters', None)
    if not date_filters:
      return

    file_entry_filter = file_entry_filters.DateTimeFileEntryFilter()

    for date_filter in date_filters:
      date_filter_pieces = date_filter.split(',')
      if len(date_filter_pieces) != 3:
        raise errors.BadConfigOption(
            'Badly formed date filter: {0:s}'.format(date_filter))

      time_value, start_time_string, end_time_string = date_filter_pieces
      time_value = time_value.strip()
      start_time_string = start_time_string.strip()
      end_time_string = end_time_string.strip()

      try:
        file_entry_filter.AddDateTimeRange(
            time_value, start_time_string=start_time_string,
            end_time_string=end_time_string)
      except ValueError:
        raise errors.BadConfigOption(
            'Badly formed date filter: {0:s}'.format(date_filter))

    filter_collection.AddFilter(file_entry_filter)


manager.ArgumentHelperManager.RegisterHelper(DateFiltersArgumentsHelper)
