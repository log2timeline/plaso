# -*- coding: utf-8 -*-
"""The event filters CLI arguments helper."""

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

  NAME = u'event_filters'
  DESCRIPTION = u'Event filters command line arguments.'

  _DOCUMENTATION_URL = u'https://github.com/log2timeline/plaso/wiki/Filters'

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
        u'--slice', metavar=u'DATE', dest=u'slice', type=str,
        default=u'', action=u'store', help=(
            u'Create a time slice around a certain date. This parameter, if '
            u'defined will display all events that happened X minutes before '
            u'and after the defined date. X is controlled by the parameter '
            u'--slice_size but defaults to 5 minutes.'))

    argument_group.add_argument(
        u'--slice_size', u'--slice-size', dest=u'slice_size', type=int,
        default=5, action=u'store', help=(
            u'Defines the slice size. In the case of a regular time slice it '
            u'defines the number of minutes the slice size should be. In the '
            u'case of the --slicer it determines the number of events before '
            u'and after a filter match has been made that will be included in '
            u'the result set. The default value is 5]. See --slice or --slicer '
            u'for more details about this option.'))

    argument_group.add_argument(
        u'--slicer', dest=u'slicer', action=u'store_true', default=False, help=(
            u'Create a time slice around every filter match. This parameter, '
            u'if defined will save all X events before and after a filter '
            u'match has been made. X is defined by the --slice_size '
            u'parameter.'))

    argument_group.add_argument(
        u'filter', nargs=u'?', action=u'store', metavar=u'FILTER', default=None,
        type=str, help=(
            u'A filter that can be used to filter the dataset before it '
            u'is written into storage. More information about the filters '
            u'and how to use them can be found here: {0:s}').format(
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
          u'Configuration object is not an instance of CLITool')

    filter_expression = cls._ParseStringOption(options, u'filter')

    event_filter = None
    if filter_expression:
      event_filter = filters_manager.FiltersManager.GetFilterObject(
          filter_expression)
      if not event_filter:
        raise errors.BadConfigOption(u'Invalid filter expression: {0:s}'.format(
            filter_expression))

    time_slice_event_time_string = getattr(options, u'slice', None)
    time_slice_duration = getattr(options, u'slice_size', 5)
    use_time_slicer = getattr(options, u'slicer', False)

    # The slice and slicer cannot be set at the same time.
    if time_slice_event_time_string and use_time_slicer:
      raise errors.BadConfigOption(
          u'Time slice and slicer cannot be used at the same time.')

    time_slice_event_timestamp = None
    if time_slice_event_time_string:
      preferred_time_zone = getattr(
          configuration_object, u'_preferred_time_zone', u'UTC')
      timezone = pytz.timezone(preferred_time_zone)
      time_slice_event_timestamp = timelib.Timestamp.FromTimeString(
          time_slice_event_time_string, timezone=timezone)
      if time_slice_event_timestamp is None:
        raise errors.BadConfigOption(
            u'Unsupported time slice event date and time: {0:s}'.format(
                time_slice_event_time_string))

    setattr(configuration_object, u'_event_filter_expression',
            filter_expression)

    if event_filter:
      setattr(configuration_object, u'_event_filter', event_filter)

    setattr(configuration_object, u'_use_time_slicer', use_time_slicer)

    if time_slice_event_timestamp is not None or use_time_slicer:
      # Note that time slicer uses the time slice to determine the duration.
      # TODO: refactor TimeSlice to filters.
      time_slice = time_slices.TimeSlice(
          time_slice_event_timestamp, duration=time_slice_duration)
      setattr(configuration_object, u'_time_slice', time_slice)


manager.ArgumentHelperManager.RegisterHelper(EventFiltersArgumentsHelper)
