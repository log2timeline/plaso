# -*- coding: utf-8 -*-
"""File entry filters."""

import abc
import collections
import logging

import pysigscan

from plaso.lib import py2to3
from plaso.lib import timelib


class FileEntryFilter(object):
  """File entry filter interface."""

  @abc.abstractmethod
  def Matches(self, file_entry):
    """Compares the file entry against the filter.

    Args:
      file_entry (dfvfs.FileEntry): file entry to compare.

    Returns:
      bool: True if the file entry matches the filter, False if not or
          None if the filter does not apply.
    """

  @abc.abstractmethod
  def Print(self, output_writer):
    """Prints a human readable version of the filter.

    Args:
      output_writer (CLIOutputWriter): output writer.
    """


class DateTimeFileEntryFilter(FileEntryFilter):
  """Date and time-based file entry filter."""

  _DATE_TIME_RANGE_TUPLE = collections.namedtuple(
      u'date_time_range_tuple', u'time_value start_timestamp end_timestamp')

  _SUPPORTED_TIME_VALUES = frozenset([
      u'atime', u'bkup', u'ctime', u'crtime', u'dtime', u'mtime'])

  def __init__(self):
    """Initializes a date and time-based file entry filter."""
    super(DateTimeFileEntryFilter, self).__init__()
    self._date_time_ranges = []

  def AddDateTimeRange(
      self, time_value, start_time_string=None, end_time_string=None):
    """Adds a date time filter range.

    The time strings are formatted as:
    YYYY-MM-DD hh:mm:ss.######[+-]##:##
    Where # are numeric digits ranging from 0 to 9 and the seconds
    fraction can be either 3 or 6 digits. The time of day, seconds fraction
    and timezone offset are optional. The default timezone is UTC.

    Args:
      time_value (str): time value, such as, atime, ctime, crtime, dtime, bkup
          and mtime.
      start_time_string (str): start date and time value string.
      end_time_string (str): end date and time value string.

    Raises:
      ValueError: If the filter is badly formed.
    """
    if not isinstance(time_value, py2to3.STRING_TYPES):
      raise ValueError(u'Filter type must be a string.')

    if start_time_string is None and end_time_string is None:
      raise ValueError(
          u'Filter must have either a start or an end date time value.')

    time_value_lower = time_value.lower()
    if time_value_lower not in self._SUPPORTED_TIME_VALUES:
      raise ValueError(
          u'Unsupported time value: {0:s}.'.format(time_value))

    if start_time_string:
      start_timestamp = timelib.Timestamp.CopyFromString(start_time_string)
    else:
      start_timestamp = None

    if end_time_string:
      end_timestamp = timelib.Timestamp.CopyFromString(end_time_string)
    else:
      end_timestamp = None

    # Make sure that the end timestamp occurs after the beginning.
    # If not then we need to reverse the time range.
    if (None not in [start_timestamp, end_timestamp] and
        start_timestamp > end_timestamp):
      raise ValueError(
          u'Invalid date time value start must be earlier than end.')

    self._date_time_ranges.append(self._DATE_TIME_RANGE_TUPLE(
        time_value_lower, start_timestamp, end_timestamp))

  def Matches(self, file_entry):
    """Compares the file entry against the filter.

    Args:
      file_entry (dfvfs.FileEntry): file entry to compare.

    Returns:
      bool: True if the file entry matches the filter, False if not or
          None if the filter does not apply.
    """
    if not self._date_time_ranges:
      return

    stat_object = file_entry.GetStat()
    for date_time_range in self._date_time_ranges:
      time_value = date_time_range.time_value
      timestamp = getattr(stat_object, time_value, None)
      if timestamp is None:
        continue

      nano_time_value = u'{0:s}_nano'.format(time_value)
      nano_time_value = getattr(stat_object, nano_time_value, None)

      timestamp = timelib.Timestamp.FromPosixTime(timestamp)
      if nano_time_value is not None:
        # Note that the _nano values are in intervals of 100th nano seconds.
        nano_time_value, _ = divmod(nano_time_value, 10)
        timestamp += nano_time_value

      if (date_time_range.start_timestamp is not None and
          timestamp < date_time_range.start_timestamp):
        return False

      if (date_time_range.end_timestamp is not None and
          timestamp > date_time_range.end_timestamp):
        return False

    return True

  def Print(self, output_writer):
    """Prints a human readable version of the filter.

    Args:
      output_writer (CLIOutputWriter): output writer.
    """
    if self._date_time_ranges:
      for date_time_range in self._date_time_ranges:
        if date_time_range.start_timestamp is None:
          end_time_string = timelib.Timestamp.CopyToIsoFormat(
              date_time_range.end_timestamp)
          output_writer.Write(u'\t{0:s} after {1:s}\n'.format(
              date_time_range.time_value, end_time_string))

        elif date_time_range.end_timestamp is None:
          start_time_string = timelib.Timestamp.CopyToIsoFormat(
              date_time_range.start_timestamp)
          output_writer.Write(u'\t{0:s} before {1:s}\n'.format(
              date_time_range.time_value, start_time_string))

        else:
          start_time_string = timelib.Timestamp.CopyToIsoFormat(
              date_time_range.start_timestamp)
          end_time_string = timelib.Timestamp.CopyToIsoFormat(
              date_time_range.end_timestamp)
          output_writer.Write(u'\t{0:s} between {1:s} and {2:s}\n'.format(
              date_time_range.time_value, start_time_string,
              end_time_string))


class ExtensionsFileEntryFilter(FileEntryFilter):
  """Extensions-based file entry filter."""

  def __init__(self, extensions):
    """Initializes an extensions-based file entry filter.

    An extension is defined as "pdf" as in "document.pdf".

    Args:
      extensions (list[str]): a list of extension strings.
    """
    super(ExtensionsFileEntryFilter, self).__init__()
    self._extensions = extensions

  def Matches(self, file_entry):
    """Compares the file entry against the filter.

    Args:
      file_entry (dfvfs.FileEntry): file entry to compare.

    Returns:
      bool: True if the file entry matches the filter, False if not or
          None if the filter does not apply.
    """
    location = getattr(file_entry.path_spec, u'location', None)
    if not location:
      return

    if u'.' not in location:
      return False

    _, _, extension = location.rpartition(u'.')
    return extension.lower() in self._extensions

  def Print(self, output_writer):
    """Prints a human readable version of the filter.

    Args:
      output_writer (CLIOutputWriter): output writer.
    """
    if self._extensions:
      output_writer.Write(u'\textensions: {0:s}\n'.format(
          u', '.join(self._extensions)))


class NamesFileEntryFilter(FileEntryFilter):
  """Names-based file entry filter."""

  def __init__(self, names):
    """Initializes a names-based file entry filter.

    Args:
      names (list[str]): names.
    """
    super(NamesFileEntryFilter, self).__init__()
    self._names = names

  def Matches(self, file_entry):
    """Compares the file entry against the filter.

    Args:
      file_entry (dfvfs.FileEntry): file entry to compare.

    Returns:
      bool: True if the file entry matches the filter.
    """
    if not self._names or not file_entry.IsFile():
      return

    return file_entry.name.lower() in self._names

  def Print(self, output_writer):
    """Prints a human readable version of the filter.

    Args:
      output_writer (CLIOutputWriter): output writer.
    """
    if self._names:
      output_writer.Write(u'\tnames: {0:s}\n'.format(
          u', '.join(self._names)))


class SignaturesFileEntryFilter(FileEntryFilter):
  """Signature-based file entry filter."""

  def __init__(self, specification_store, signature_identifiers):
    """Initializes a signature-based file entry filter.

    Args:
      specification_store (FormatSpecificationStore): a specification store.
      signature_identifiers (list[str]): signature identifiers.
    """
    super(SignaturesFileEntryFilter, self).__init__()
    self._file_scanner = None
    self._signature_identifiers = []

    self._file_scanner = self._GetScanner(
        specification_store, signature_identifiers)

  def _GetScanner(self, specification_store, signature_identifiers):
    """Initializes the scanner form the specification store.

    Args:
      specification_store (FormatSpecificationStore): a specification store.
      signature_identifiers (list[str]): signature identifiers.

    Returns:
      pysigscan.scanner: signature scanner or None.
    """
    if not specification_store:
      return

    scanner_object = pysigscan.scanner()

    for format_specification in specification_store.specifications:
      if format_specification.identifier not in signature_identifiers:
        continue

      for signature in format_specification.signatures:
        pattern_offset = signature.offset
        if pattern_offset is None:
          signature_flags = pysigscan.signature_flags.NO_OFFSET
        elif pattern_offset < 0:
          pattern_offset *= -1
          signature_flags = pysigscan.signature_flags.RELATIVE_FROM_END
        else:
          signature_flags = pysigscan.signature_flags.RELATIVE_FROM_START

        scanner_object.add_signature(
            signature.identifier, pattern_offset, signature.pattern,
            signature_flags)

      self._signature_identifiers.append(format_specification.identifier)

    return scanner_object

  def Matches(self, file_entry):
    """Compares the file entry against the filter.

    Args:
      file_entry (dfvfs.FileEntry): file entry to compare.

    Returns:
      bool: True if the file entry matches the filter, False if not or
          None if the filter does not apply.
    """
    if not self._file_scanner or not file_entry.IsFile():
      return

    file_object = file_entry.GetFileObject()
    if not file_object:
      return False

    try:
      scan_state = pysigscan.scan_state()
      self._file_scanner.scan_file_object(scan_state, file_object)

    except IOError as exception:
      # TODO: replace location by display name.
      location = getattr(file_entry.path_spec, u'location', u'')
      logging.error((
          u'[skipping] unable to scan file: {0:s} for signatures '
          u'with error: {1:s}').format(location, exception))
      return False

    finally:
      file_object.close()

    return scan_state.number_of_scan_results > 0

  def Print(self, output_writer):
    """Prints a human readable version of the filter.

    Args:
      output_writer (CLIOutputWriter): output writer.
    """
    if self._file_scanner:
      output_writer.Write(u'\tsignature identifiers: {0:s}\n'.format(
          u', '.join(self._signature_identifiers)))


class FileEntryFilterCollection(object):
  """Collection of file entry filters."""

  def __init__(self):
    """Initializes a file entry filter collection."""
    super(FileEntryFilterCollection, self).__init__()
    self._filters = []

  def AddFilter(self, file_entry_filter):
    """Adds a file entry filter to the collection.

    Args:
      file_entry_filter (FileEntryFilter): file entry filter.
    """
    self._filters.append(file_entry_filter)

  def HasFilters(self):
    """Determines if filters are defined.

    Returns:
      bool: True if filters are defined.
    """
    return bool(self._filters)

  def Matches(self, file_entry):
    """Compares the file entry against the filter collection.

    Args:
      file_entry (dfvfs.FileEntry): file entry to compare.

    Returns:
      bool: True if the file entry matches one of the filters. If no filters
          are provided or applicable the result will be True.
    """
    if not self._filters:
      return True

    results = []
    for file_entry_filter in self._filters:
      result = file_entry_filter.Matches(file_entry)
      results.append(result)

    return True in results or False not in results

  def Print(self, output_writer):
    """Prints a human readable version of the filter.

    Args:
      output_writer (CLIOutputWriter): output writer.
    """
    if self._filters:
      output_writer.Write(u'Filters:\n')
      for file_entry_filter in self._filters:
        file_entry_filter.Print(output_writer)
