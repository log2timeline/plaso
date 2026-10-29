"""The event filter."""

from plaso.filters import expression_parser
from plaso.storage import time_range as storage_time_range


class EventObjectFilter:
    """Event filter."""

    # The range of timestamps that can be stored.
    _TIMESTAMP_MINIMUM = -(1 << 63)
    _TIMESTAMP_MAXIMUM = (1 << 63) - 1

    def __init__(self):
        """Initializes an event filter."""
        super().__init__()
        self._event_filter = None
        self._filter_expression = None

    def CompileFilter(self, filter_expression):
        """Compiles the filter expression.

        The filter expression contains an object filter expression.

        Args:
          filter_expression (str): filter expression.

        Raises:
          ParseError: if the filter expression cannot be parsed.
        """
        parser = expression_parser.EventFilterExpressionParser()
        expression = parser.Parse(filter_expression)

        self._event_filter = expression.Compile()
        self._filter_expression = filter_expression

    def GetTimestampRange(self):
        """Retrieves the range of the timestamps of the events that can match.

        The range is derived from the comparisons of the timestamp attribute,
        such as "date > DATETIME('2020-01-01T00:00:00')", that must match for
        the filter to match. Events outside the range cannot match the filter,
        however events inside the range need to be matched against the filter.

        Returns:
          TimeRange: range of the timestamps of the events that can match the
              filter or None if the filter does not limit the timestamps.
        """
        if not self._event_filter:
            return None

        lower_bound, upper_bound = self._event_filter.GetTimestampBounds()
        if lower_bound is None and upper_bound is None:
            return None

        if lower_bound is None:
            lower_bound = self._TIMESTAMP_MINIMUM

        if upper_bound is None:
            upper_bound = self._TIMESTAMP_MAXIMUM

        # Note that no events can match if the bounds contradict each other.
        upper_bound = max(lower_bound, upper_bound)

        return storage_time_range.TimeRange(lower_bound, upper_bound)

    def Match(self, event, event_data, event_data_stream, event_tag):
        """Determines if an event matches the filter.

        Args:
          event (EventObject): event.
          event_data (EventData): event data.
          event_data_stream (EventDataStream): event data stream.
          event_tag (EventTag): event tag.

        Returns:
          bool: True if the event matches the filter, False otherwise.
        """
        if not self._event_filter:
            return True

        return self._event_filter.Matches(
            event, event_data, event_data_stream, event_tag
        )
