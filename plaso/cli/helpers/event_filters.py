# -*- coding: utf-8 -*-
"""The event filters CLI arguments helper."""

from __future__ import unicode_literals

from plaso.cli import time_slices
from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.filters import manager as filters_manager
from plaso.lib import errors
from plaso.lib import timelib

import pytz  # pylint: disable=wrong-import-order


class EventFiltersArgumentsHelper(interface.ArgumentsHelper):
  """Event filters CLI arguments helper."""

  NAME = 'event_filters'
  DESCRIPTION = 'Event filters command line arguments.'

  _DOCUMENTATION_URL = (
      'https://plaso.readthedocs.io/en/latest/sources/user/Event-filters.html')

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
        '--slice', metavar='DATE', dest='slice', type=str,
        default='', action='store', help=(
            'Create a time slice around a certain date. This parameter, if '
            'defined will display all events that happened X minutes before '
            'and after the defined date. X is controlled by the parameter '
            '--slice_size but defaults to 5 minutes.'))

    argument_group.add_argument(
        '--slice_size', '--slice-size', dest='slice_size', type=int,
        default=5, action='store', help=(
            'Defines the slice size. In the case of a regular time slice it '
            'defines the number of minutes the slice size should be. In the '
            'case of the --slicer it determines the number of events before '
            'and after a filter match has been made that will be included in '
            'the result set. The default value is 5. See --slice or --slicer '
            'for more details about this option.'))

    argument_group.add_argument(
        '--slicer', dest='slicer', action='store_true', default=False, help=(
            'Create a time slice around every filter match. This parameter, '
            'if defined will save all X events before and after a filter '
            'match has been made. X is defined by the --slice_size '
            'parameter.'))

    argument_group.add_argument(
        'filter', nargs='?', action='store', metavar='FILTER', default=None,
        type=str, help=(
            'A filter that can be used to filter the dataset before it '
            'is written into storage. More information about the filters '
            'and how to use them can be found here: {0:s}').format(
                cls._DOCUMENTATION_URL))

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
      BadConfigOption: when a configuration parameter fails validation.
    """
    if not isinstance(configuration_object, tools.CLITool):
      raise errors.BadConfigObject(
          'Configuration object is not an instance of CLITool')

    filter_expression = cls._ParseStringOption(options, 'filter')

    event_filter = None
    if filter_expression:
      event_filter = filters_manager.FiltersManager.GetFilterObject(
          filter_expression)
      if not event_filter:
        raise errors.BadConfigOption('Invalid filter expression: {0:s}'.format(
            filter_expression))

    time_slice_event_time_string = getattr(options, 'slice', None)
    time_slice_duration = getattr(options, 'slice_size', 5)
    use_time_slicer = getattr(options, 'slicer', False)

    # The slice and slicer cannot be set at the same time.
    if time_slice_event_time_string and use_time_slicer:
      raise errors.BadConfigOption(
          'Time slice and slicer cannot be used at the same time.')

    time_slice_event_timestamp = None
    if time_slice_event_time_string:
      # Note self._preferred_time_zone is None when not set but represents UTC.
      preferred_time_zone = getattr(
          configuration_object, '_preferred_time_zone', None) or 'UTC'
      timezone = pytz.timezone(preferred_time_zone)
      time_slice_event_timestamp = timelib.Timestamp.FromTimeString(
          time_slice_event_time_string, timezone=timezone)
      if time_slice_event_timestamp is None:
        raise errors.BadConfigOption(
            'Unsupported time slice event date and time: {0:s}'.format(
                time_slice_event_time_string))

    setattr(configuration_object, '_event_filter_expression', filter_expression)

    if event_filter:
      setattr(configuration_object, '_event_filter', event_filter)

    setattr(configuration_object, '_use_time_slicer', use_time_slicer)

    if time_slice_event_timestamp is not None or use_time_slicer:
      # Note that time slicer uses the time slice to determine the duration.
      # TODO: refactor TimeSlice to filters.
      time_slice = time_slices.TimeSlice(
          time_slice_event_timestamp, duration=time_slice_duration)
      setattr(configuration_object, '_time_slice', time_slice)


manager.ArgumentHelperManager.RegisterHelper(EventFiltersArgumentsHelper)
