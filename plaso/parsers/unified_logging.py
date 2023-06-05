# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) file parser."""

import abc
import base64
import collections
import os
import re
import uuid

import lz4.block

from dfdatetime import posix_time as dfdatetime_posix_time

from dfvfs.path import factory as path_spec_factory

from dtfabric.runtime import data_maps as dtfabric_data_maps

from plaso.containers import events
from plaso.helpers.macos import darwin
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class UnifiedLoggingEventData(events.EventData):
  """Apple Unified Logging (AUL) event data.

  Attributes:
    activity_identifier (int): activity identifier.
    boot_identifier (str): boot identifier.
    category (str): event category.
    euid (int): effective user identifier (UID)
    event_message (str): event message.
    event_type (str): event type.
    message_type (str): message type.
    pid (int): process identifier (PID).
    process_image_identifier (str): process image identifier.
    process_image_identifier (str): process image identifier, contains an UUID.
    recorded_time (dfdatetime.DateTimeValues): date and time the log entry was
        recorded.
    sender_image_identifier (str): (sender) image identifier, contains an UUID.
    sender_image_path (str): path of the (sender) image.
    signpost_identifier (int): signpost identifier.
    signpost_name (str): signpost name.
    subsystem (str): subsystem that produced the logging event.
    thread_identifier (int): thread identifier.
    ttl (int): log time to live (TTL).
  """
  DATA_TYPE = 'macos:unified_logging:event'

  def __init__(self):
    """Initialise event data."""
    super(UnifiedLoggingEventData, self).__init__(data_type=self.DATA_TYPE)
    self.activity_identifier = None
    self.boot_identifier = None
    self.category = None
    self.euid = None
    self.event_message = None
    self.event_type = None
    self.message_type = None
    self.pid = None
    self.process_image_identifier = None
    self.process_image_path = None
    self.recorded_time = None
    self.sender_image_identifier = None
    self.sender_image_path = None
    self.signpost_identifier = None
    self.signpost_name = None
    self.subsystem = None
    self.thread_identifier = None
    self.ttl = None


class DSCRange(object):
  """Shared-Cache Strings (dsc) range.

  Attributes:
    data_offset (int): offset of the string data.
    image_identifier (uuid.UUID): the image identifier.
    image_path (str): the image path.
    range_offset (int): the offset of the range.
    range_sizes (int): the size of the range.
    text_offset (int): the offset of the text.
    text_size (int): the size of the text.
    uuid_index (int): index of the dsc UUID.
  """

  def __init__(self):
    """Initializes a Shared-Cache Strings (dsc) range."""
    super(DSCRange, self).__init__()
    self.data_offset = None
    self.image_identifier = None
    self.image_path = None
    self.range_offset = None
    self.range_size = None
    self.text_offset = None
    self.text_size = None
    self.uuid_index = None


class DSCUUID(object):
  """Shared-Cache Strings (dsc) UUID.

  Attributes:
    image_identifier (uuid.UUID): the image identifier.
    image_path (str): the image path.
    text_offset (int): the offset of the text.
    text_size (int): the size of the text.
  """

  def __init__(self):
    """Initializes a Shared-Cache Strings (dsc) UUID."""
    super(DSCUUID, self).__init__()
    self.image_identifier = None
    self.image_path = None
    self.text_offset = None
    self.text_size = None


class BacktraceFrame(object):
  """Backtrace frame.

  Attributes:
    image_identifier (str): image identifier, contains an UUID.
    image_offset (int): image offset.
  """

  def __init__(self):
    """Initializes a backtrace frame."""
    super(BacktraceFrame, self).__init__()
    self.image_identifier = None
    self.image_offset = None


class LogEntry(object):
  """Log entry.

  Attributes:
    activity_identifier (int): activity identifier.
    backtrace_frames (list[BacktraceFrame]): backtrace frames.
    boot_identifier (uuid.UUID): boot identifier.
    category (str): (sub system) category.
    creator_activity_identifier (int): creator activity identifier.
    event_message (str): event message.
    event_type (str): event type.
    format_string (str): format string.
    mach_timestamp (int): Mach timestamp.
    message_type (str): message type.
    parent_activity_identifier (int): parent activity identifier.
    process_identifier (int): process identifier (PID).
    process_image_identifier (uuid.UUID): process image identifier.
    process_image_path (str): path of the process image.
    sender_image_identifier (uuid.UUID): (sender) image identifier.
    sender_image_path (str): path of the (sender) image.
    sender_program_counter (int): (sender) program counter.
    signpost_identifier (int): signpost identifier.
    signpost_name (str): signpost name.
    signpost_scope (str): signpost scope.
    signpost_type (str): signpost type.
    sub_system (str): sub system.
    thread_identifier (int): thread identifier.
    timestamp (int): number of nanoseconds since January 1, 1970
        00:00:00.000000000.
    time_zone_name (str): name of the time zone.
    trace_identifier (int): trace identifier.
    ttl (int): Time to live (TTL) value.
  """

  def __init__(self):
    """Initializes a log entry."""
    super(LogEntry, self).__init__()
    self.activity_identifier = None
    self.backtrace_frames = None
    self.boot_identifier = None
    self.category = None
    self.creator_activity_identifier = None
    self.event_message = None
    self.event_type = None
    self.format_string = None
    self.mach_timestamp = None
    self.message_type = None
    self.parent_activity_identifier = None
    self.process_identifier = None
    self.process_image_identifier = None
    self.process_image_path = None
    self.sender_image_identifier = None
    self.sender_image_path = None
    self.sender_program_counter = None
    self.signpost_identifier = None
    self.signpost_name = None
    self.signpost_scope = None
    self.signpost_type = None
    self.sub_system = None
    self.thread_identifier = None
    self.timestamp = None
    self.time_zone_name = None
    self.trace_identifier = None
    self.ttl = None


class StringFormatter(object):
  """String formatter."""

  _DECODERS_TO_IGNORE = (
      '',
      'private',
      'public',
      'sensitive',
      'xcode:size-in-bytes')

  _ESCAPE_REGEX = re.compile(r'([{}])')

  _OPERATOR_REGEX = re.compile(
      r'(%'
      r'(?:\{([^\}]{1,128})\})?'         # Optional value type decoder.
      r'([-+0 #]{0,5})'                  # Optional flags.
      r'([0-9]+|[*])?'                   # Optional width.
      r'(\.(?:|[0-9]+|[*]))?'            # Optional precision.
      r'(?:h|hh|j|l|ll|L|t|q|z)?'        # Optional length modifier.
      r'([@aAcCdDeEfFgGimnoOpPsSuUxX])'  # Conversion specifier.
      r'|%%)')

  _PYTHON_SPECIFIERS = {
      '@': 's',
      'D': 'd',
      'i': 'd',
      'm': 'd',
      'O': 'o',
      'p': 'x',
      'P': 's',
      'u': 'd',
      'U': 'd'}

  _TYPE_HINTS = {
      'a': 'floating-point',
      'A': 'floating-point',
      'd': 'signed',
      'D': 'signed',
      'e': 'floating-point',
      'E': 'floating-point',
      'f': 'floating-point',
      'F': 'floating-point',
      'g': 'floating-point',
      'G': 'floating-point',
      'i': 'signed',
      'm': 'signed',
      'o': 'unsigned',
      'O': 'unsigned',
      'p': 'unsigned',
      'u': 'unsigned',
      'U': 'unsigned',
      'x': 'unsigned',
      'X': 'unsigned'}

  def __init__(self):
    """Initializes a string formatter."""
    super(StringFormatter, self).__init__()
    self._decoders = []
    self._format_string = None
    self._type_hints = []
    self._value_formatters = []

  @property
  def number_of_formatters(self):
    """int: number of value formatters."""
    return len(self._value_formatters)

  def FormatString(self, values):
    """Formats the string.

    Args:
      values (list[str]): values.

    Returns:
      str: formatted string.
    """
    # Add place holders for missing values.
    while len(values) < len(self._value_formatters):
      values.append('<decode: missing data>')

    if self._format_string is None:
      formatted_string = ''
    elif self._value_formatters:
      formatted_string = self._format_string.format(*values)
    else:
      formatted_string = self._format_string

    return formatted_string

  def GetDecoderNamesByIndex(self, value_index):
    """Retrieves the decoder names of a specific value.

    Args:
      value_index (int): value index.

    Returns:
      list[str]: decoder names.
    """
    try:
      return self._decoders[value_index]
    except IndexError:
      return []

  def GetTypeHintByIndex(self, value_index):
    """Retrieves the specific type of a specific value..

    Args:
      value_index (int): value index.

    Returns:
      list[str]: type hint or None if not available.
    """
    try:
      return self._type_hints[value_index]
    except IndexError:
      return None

  def GetValueFormatter(self, value_index, precision=None):
    """Retrieves a value formatter.

    Args:
      value_index (int): value index.
      precision (int): precision.

    Returns:
      str: value formatter or None if not available.
    """
    try:
      value_formatter = self._value_formatters[value_index]
    except IndexError:
      return None

    # TODO: add precision support.
    _ = precision
    return value_formatter

  def ParseFormatString(self, format_string):
    """Parses an Unified Logging format string.

    Args:
      format_string (str): Unified Logging format string.
    """
    self._decoders = []
    self._format_string = None
    self._type_hints = []
    self._value_formatters = []

    if not format_string:
      return

    specifier_index = 0
    last_match_end = 0
    segments = []

    for match in self._OPERATOR_REGEX.finditer(format_string):
      literal, decoder, flags, width, precision, specifier = match.groups()

      match_start, match_end = match.span()
      if match_start > last_match_end:
        string_segment = self._ESCAPE_REGEX.sub(
            r'\1\1', format_string[last_match_end:match_start])
        segments.append(string_segment)

      if literal == '%%':
        literal = '%'
      elif specifier:
        flags = flags.replace('-', '>')

        decoder = decoder or ''
        decoder_names = [value.strip() for value in decoder.split(',')]

        # Remove private, public and sensitive value type decoders.
        decoder_names = [value for value in decoder_names if (
            value not in self._DECODERS_TO_IGNORE and value[:5] != 'name=')]

        if specifier == 'm':
          decoder_names.append('internal:m')

        width = width or ''

        python_specifier = self._PYTHON_SPECIFIERS.get(specifier, specifier)

        # Ignore the precision of specifier "P" since it refers to the binary
        # data not the resulting string.

        # Prevent: "Precision not allowed in integer format specifier",
        # "Format specifier missing precision" and ".0" formatting as an empty
        # string.
        if (specifier == 'P' or python_specifier in ('d', 'o', 'x', 'X') or
            precision in ('.', '.*') or (
                python_specifier == 's' and precision == '.0')):
          precision = ''
        else:
          precision = precision or ''

        # TODO: add support for "a" and "A"

        if specifier == 'p':
          value_formatter = (
              f'0x{{0:{flags:s}{precision:s}{width:s}{python_specifier:s}}}')
        else:
          value_formatter = (
              f'{{0:{flags:s}{precision:s}{width:s}{python_specifier:s}}}')

        type_hint = self._TYPE_HINTS.get(specifier, None)

        self._decoders.append(decoder_names)
        self._type_hints.append(type_hint)
        self._value_formatters.append(value_formatter)

        literal = f'{{{specifier_index:d}:s}}'
        specifier_index += 1

      last_match_end = match_end

      segments.append(literal)

    string_size = len(format_string)
    if string_size > last_match_end:
      string_segment = self._ESCAPE_REGEX.sub(
          r'\1\1', format_string[last_match_end:string_size])
      segments.append(string_segment)

    self._format_string = ''.join(segments)

    if not self._value_formatters:
      self._format_string = self._format_string.replace('{{', '{')
      self._format_string = self._format_string.replace('}}', '}')


class BaseFormatStringDecoder(object):
  """Format string decoder interface."""

  # True if the value should be bytes.
  VALUE_IN_BYTES = True

  @abc.abstractmethod
  def FormatValue(self, value, value_formatter=None):
    """Formats a value.

    Args:
      value (object): value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted value.
    """


class BooleanFormatStringDecoder(BaseFormatStringDecoder):
  """Boolean value format string decoder."""

  VALUE_IN_BYTES = False

  def __init__(self, false_value='false', true_value='true'):
    """Initializes a boolean value format string decoder.

    Args:
      number (Optional[int]): Signpost telemetry number.
    """
    super(BooleanFormatStringDecoder, self).__init__()
    self._false_value = false_value
    self._true_value = true_value

  def FormatValue(self, value, value_formatter=None):
    """Formats a boolean value.

    Args:
      value (int): boolean value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted boolean value.
    """
    if value:
      return self._true_value

    return self._false_value


class DateTimeInSecondsFormatStringDecoder(BaseFormatStringDecoder):
  """Date and time value in seconds format string decoder."""

  VALUE_IN_BYTES = False

  def FormatValue(self, value, value_formatter=None):
    """Formats a date and time value in seconds.

    Args:
      value (int): timestamp that contains the number of seconds since
          1970-01-01 00:00:00.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted date and time value in seconds.
    """
    date_time = dfdatetime_posix_time.PosixTime(timestamp=value)
    return date_time.CopyToDateTimeString()


class ErrorCodeFormatStringDecoder(BaseFormatStringDecoder):
  """Error code format string decoder."""

  VALUE_IN_BYTES = False

  def FormatValue(self, value, value_formatter=None):
    """Formats an error code value.

    Args:
      value (int): error code.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted error code value.
    """
    # TODO: determine what the MacOS log tool shows when an error message is
    # not defined.
    return darwin.DarwinSystemErrorHelper.GetDescription(value)


class ExtendedErrorCodeFormatStringDecoder(BaseFormatStringDecoder):
  """Extended error code format string decoder."""

  VALUE_IN_BYTES = False

  def FormatValue(self, value, value_formatter=None):
    """Formats an error code value.

    Args:
      value (int): error code.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted error code value.
    """
    # TODO: determine what the MacOS log tool shows when an error message is
    # not defined.
    error_message = darwin.DarwinSystemErrorHelper.GetDescription(value)

    return f'[{value:d}: {error_message:s}]'


class FileModeFormatStringDecoder(BaseFormatStringDecoder):
  """File mode format string decoder."""

  VALUE_IN_BYTES = False

  _FILE_TYPES = {
      0x1000: 'p',
      0x2000: 'c',
      0x4000: 'd',
      0x6000: 'b',
      0xa000: 'l',
      0xc000: 's'}

  def FormatValue(self, value, value_formatter=None):
    """Formats a file mode value.

    Args:
      value (int): file mode.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted file mode value.
    """
    string_parts = 10 * ['-']

    if value & 0x0001:
      string_parts[9] = 'x'
    if value & 0x0002:
      string_parts[8] = 'w'
    if value & 0x0004:
      string_parts[7] = 'r'

    if value & 0x0008:
      string_parts[6] = 'x'
    if value & 0x0010:
      string_parts[5] = 'w'
    if value & 0x0020:
      string_parts[4] = 'r'

    if value & 0x0040:
      string_parts[3] = 'x'
    if value & 0x0080:
      string_parts[2] = 'w'
    if value & 0x0100:
      string_parts[1] = 'r'

    string_parts[0] = self._FILE_TYPES.get(value & 0xf000, '-')

    return ''.join(string_parts)


class IPv4FormatStringDecoder(BaseFormatStringDecoder):
  """IPv4 value format string decoder."""

  def FormatValue(self, value, value_formatter=None):
    """Formats an IPv4 value.

    Args:
      value (bytes): IPv4 value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted IPv4 value.
    """
    if len(value) == 4:
      return '.'.join([f'{octet:d}' for octet in value])

    # TODO: determine what the MacOS log tool shows.
    return 'ERROR: unsupported value'


class IPv6FormatStringDecoder(BaseFormatStringDecoder):
  """IPv6 value format string decoder."""

  def FormatValue(self, value, value_formatter=None):
    """Formats an IPv6 value.

    Args:
      value (bytes): IPv6 value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted IPv6 value.
    """
    if len(value) == 16:
      # Note that socket.inet_ntop() is not supported on Windows.
      octet_pairs = zip(value[0::2], value[1::2])
      octet_pairs = [octet1 << 8 | octet2 for octet1, octet2 in octet_pairs]
      # TODO: determine if ":0000" should be omitted from the string.
      return ':'.join([f'{octet_pair:04x}' for octet_pair in octet_pairs])

    # TODO: determine what the MacOS log tool shows.
    return 'ERROR: unsupported value'


class BaseLocationStructureFormatStringDecoder(
    BaseFormatStringDecoder, dtfabric_helper.DtFabricHelper):
  """Shared functionality for location structure format string decoders."""

  # pylint: disable=abstract-method

  def _FormatStructure(self, structure, value_mappings):
    """Formats a structure.

    Args:
      structure (object): structure object to format.
      value_mappings (tuple[str, str]): mappings of output values to structure
          values.

    Return:
      str: formatted structure.
    """
    values = []

    for name, attribute_name in value_mappings:
      attribute_value = getattr(structure, attribute_name, None)
      if attribute_value is None:
        continue

      if isinstance(attribute_value, bool):
        if attribute_value:
          attribute_value = 'true'
        else:
          attribute_value = 'false'

      elif isinstance(attribute_value, int):
        attribute_value = f'{attribute_value:d}'

      elif isinstance(attribute_value, float):
        attribute_value = f'{attribute_value:.0f}'

      values.append(f'"{name:s}":{attribute_value:s}')

    values_string = ','.join(values)

    return f'{{{values_string:s}}}'


class LocationClientManagerStateFormatStringDecoder(
    BaseLocationStructureFormatStringDecoder):
  """Location client manager state format string decoder."""

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'macos_core_location.yaml')

  _VALUE_MAPPINGS = [
      ('locationRestricted', 'location_restricted'),
      ('locationServicesEnabledStatus', 'location_enabled_status')]

  def FormatValue(self, value, value_formatter=None):
    """Formats a location client manager state value.

    Args:
      value (bytes): location client manager state value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted location client manager state value.
    """
    if len(value) != 8:
      # TODO: determine what the MacOS log tool shows.
      return 'ERROR: unsupported value'

    data_type_map = self._GetDataTypeMap('client_manager_state_tracker_state')

    tracker_state = self._ReadStructureFromByteStream(value, 0, data_type_map)

    return self._FormatStructure(tracker_state, self._VALUE_MAPPINGS)


class LocationLocationManagerStateFormatStringDecoder(
    BaseLocationStructureFormatStringDecoder):
  """Location location manager state format string decoder."""

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'macos_core_location.yaml')

  _VALUE_MAPPINGS = [
      ('previousAuthorizationStatusValid',
       'previous_authorization_status_valid'),
      ('paused', 'paused'),
      ('requestingLocation', 'requesting_location'),
      ('updatingVehicleSpeed', 'updating_vehicle_speed'),
      ('desiredAccuracy', 'desired_accuracy'),
      ('allowsBackgroundLocationUpdates', 'allows_background_location_updates'),
      ('dynamicAccuracyReductionEnabled', 'dynamic_accuracy_reduction_enabled'),
      ('distanceFilter', 'distance_filter'),
      ('allowsLocationPrompts', 'allows_location_prompts'),
      ('activityType', 'activity_type'),
      ('groundAltitudeEnabled', 'ground_altitude_enabled'),
      ('pausesLocationUpdatesAutomatially',
       'pauses_location_updates_automatially'),
      ('fusionInfoEnabled', 'fusion_information_enabled'),
      ('isAuthorizedForWidgetUpdates', 'is_authorized_for_widget_updates'),
      ('updatingVehicleHeading', 'updating_vehicle_heading'),
      ('batchingLocation', 'batching_location'),
      ('showsBackgroundLocationIndicator',
       'shows_background_location_indicator'),
      ('updatingLocation', 'updating_location'),
      ('requestingRanging', 'requesting_ranging'),
      ('updatingHeading', 'updating_heading'),
      ('previousAuthorizationStatus', 'previous_authorization_status'),
      ('allowsMapCorrection', 'allows_map_correction'),
      ('matchInfoEnabled', 'match_information_enabled'),
      ('allowsAlteredAccessoryLoctions', 'allows_altered_accessory_location'),
      ('updatingRanging', 'updating_ranging'),
      ('limitsPrecision', 'limits_precision'),
      ('courtesyPromptNeeded', 'courtesy_prompt_needed'),
      ('headingFilter', 'heading_filter')]

  def FormatValue(self, value, value_formatter=None):
    """Formats a location location manager state value.

    Args:
      value (bytes): location location manager state value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted location location manager state value.
    """
    value_size = len(value)
    if value_size == 64:
      data_type_name = 'location_manager_state_tracker_state_v1'
    elif value_size == 72:
      data_type_name = 'location_manager_state_tracker_state_v2'
    else:
      # TODO: determine what the MacOS log tool shows.
      return 'ERROR: unsupported value'

    data_type_map = self._GetDataTypeMap(data_type_name)

    tracker_state = self._ReadStructureFromByteStream(value, 0, data_type_map)

    return self._FormatStructure(tracker_state, self._VALUE_MAPPINGS)


class LocationEscapeOnlyFormatStringDecoder(BaseFormatStringDecoder):
  """Location escape only format string decoder."""

  VALUE_IN_BYTES = False

  def FormatValue(self, value, value_formatter=None):
    """Formats a location value.

    Args:
      value (str): location value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted location value.
    """
    value = value or ''
    value = value.replace('/', '\\/')
    return ''.join(['"', value, '"'])


class LocationSQLiteResultFormatStringDecoder(BaseFormatStringDecoder):
  """Location SQLite result format string decoder."""

  _SQLITE_RESULTS = {
      0: 'SQLITE_OK',
      1: 'SQLITE_ERROR',
      2: 'SQLITE_INTERNAL',
      3: 'SQLITE_PERM',
      4: 'SQLITE_ABORT',
      5: 'SQLITE_BUSY',
      6: 'SQLITE_LOCKED',
      7: 'SQLITE_NOMEM',
      8: 'SQLITE_READONLY',
      9: 'SQLITE_INTERRUPT',
      10: 'SQLITE_IOERR',
      11: 'SQLITE_CORRUPT',
      12: 'SQLITE_NOTFOUND',
      13: 'SQLITE_FULL',
      14: 'SQLITE_CANTOPEN',
      15: 'SQLITE_PROTOCOL',
      16: 'SQLITE_EMPTY',
      17: 'SQLITE_SCHEMA',
      18: 'SQLITE_TOOBIG',
      19: 'SQLITE_CONSTRAINT',
      20: 'SQLITE_MISMATCH',
      21: 'SQLITE_MISUSE',
      22: 'SQLITE_NOLFS',
      23: 'SQLITE_AUTH',
      24: 'SQLITE_FORMAT',
      25: 'SQLITE_RANGE',
      26: 'SQLITE_NOTADB',
      27: 'SQLITE_NOTICE',
      28: 'SQLITE_WARNING',
      100: 'SQLITE_ROW',
      101: 'SQLITE_DONE',
      266: 'SQLITE IO ERR READ'}

  def FormatValue(self, value, value_formatter=None):
    """Formats a SQLite result value.

    Args:
      value (bytes): SQLite result.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted SQLite result value.
    """
    if len(value) != 4:
      # TODO: determine what the MacOS log tool shows.
      return 'ERROR: unsupported value'

    integer_value = int.from_bytes(value, 'little', signed=False)
    string_value = self._SQLITE_RESULTS.get(
        integer_value, 'SQLITE UNKNOWN: {0:d}'.format(integer_value))

    # TODO: determine what the MacOS log tool shows when an SQLite result is
    # not defined.
    return f'"{string_value:s}"'


class MaskHashFormatStringDecoder(BaseFormatStringDecoder):
  """Mask hash format string decoder."""

  def FormatValue(self, value, value_formatter=None):
    """Formats a value as a mask hash.

    Args:
      value (bytes): value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted value as a mask hash.
    """
    if not value:
      value_string = '(null)'
    else:
      base64_string = base64.b64encode(value).decode('ascii')
      value_string = f'\'{base64_string:s}\''

    return f'<mask.hash: {value_string:s}>'


class BaseMDNSDNSStructureFormatStringDecoder(
    BaseFormatStringDecoder, dtfabric_helper.DtFabricHelper):
  """Shared functionality for mDNS DNS structure format string decoders."""

  # pylint: disable=abstract-method

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'macos_mdns.yaml')

  # Note that the flag names have a specific formatting order.
  _FLAG_NAMES = [
      (0x0400, 'AA'),  # Authoritative Answer
      (0x0200, 'TC'),  # Truncated Response
      (0x0100, 'RD'),  # Recursion Desired
      (0x0080, 'RA'),  # Recursion Available
      (0x0020, 'AD'),  # Authentic Data
      (0x0010, 'CD')]  # Checking Disabled

  _OPERATION_BITMASK = 0x7800

  _OPERATION_NAMES = {
      0: 'Query',
      1: 'IQuery',
      2: 'Status',
      3: 'Unassigned',
      4: 'Notify',
      5: 'Update',
      6: 'DSO'}

  _RESPONSE_CODE_BITMASK = 0x000f

  _RESPONSE_CODES = {
      0: 'NoError',
      1: 'FormErr',
      2: 'ServFail',
      3: 'NXDomain',
      4: 'NotImp',
      5: 'Refused',
      6: 'YXDomain',
      7: 'YXRRSet',
      8: 'NXRRSet',
      9: 'NotAuth',
      10: 'NotZone',
      11: 'DSOTypeNI'}

  _RESPONSE_OR_QUERY_BITMASK = 0x8000

  def _FormatFlags(self, flags):
    """Formats the flags value.

    Args:
      flags (int): flags

    Returns:
      str: formatted flags value.
    """
    reponse_code = flags & self._RESPONSE_CODE_BITMASK
    reponse_code = self._RESPONSE_CODES.get(reponse_code, '?')

    flag_names = []

    for bitmask, name in self._FLAG_NAMES:
      if flags & bitmask:
        flag_names.append(name)

    flag_names = ', '.join(flag_names)

    operation = (flags & self._OPERATION_BITMASK) >> 11
    operation_name = self._OPERATION_NAMES.get(operation, '?')

    query_or_response = (
        'R' if flags & self._RESPONSE_OR_QUERY_BITMASK else 'Q')

    return (f'{query_or_response:s}/{operation_name:s}, {flag_names:s}, '
            f'{reponse_code:s}')


class MDNSDNSCountersFormatStringDecoder(
    BaseMDNSDNSStructureFormatStringDecoder):
  """mDNS DNS counters format string decoder."""

  def FormatValue(self, value, value_formatter=None):
    """Formats a mDNS DNS counters value.

    Args:
      value (bytes): mDNS DNS counters value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted mDNS DNS counters value.
    """
    if len(value) != 8:
      # TODO: determine what the MacOS log tool shows.
      return 'ERROR: unsupported value'

    data_type_map = self._GetDataTypeMap('mdsn_dns_counters')

    dns_counters = self._ReadStructureFromByteStream(value, 0, data_type_map)

    return (f'{dns_counters.number_of_questions:d}/'
            f'{dns_counters.number_of_answers:d}/'
            f'{dns_counters.number_of_authority_records:d}/'
            f'{dns_counters.number_of_additional_records:d}')


class MDNSDNSHeaderFormatStringDecoder(BaseMDNSDNSStructureFormatStringDecoder):
  """mDNS DNS header format string decoder."""

  def FormatValue(self, value, value_formatter=None):
    """Formats a mDNS DNS header value.

    Args:
      value (bytes): mDNS DNS header value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted mDNS DNS header value.
    """
    if len(value) != 12:
      # TODO: determine what the MacOS log tool shows.
      return 'ERROR: unsupported value'

    data_type_map = self._GetDataTypeMap('mdsn_dns_header')

    dns_header = self._ReadStructureFromByteStream(value, 0, data_type_map)

    formatted_flags = self._FormatFlags(dns_header.flags)

    return (f'id: 0x{dns_header.identifier:04X} '
            f'({dns_header.identifier:d}), '
            f'flags: 0x{dns_header.flags:04X} '
            f'({formatted_flags:s}), counts: '
            f'{dns_header.number_of_questions:d}/'
            f'{dns_header.number_of_answers:d}/'
            f'{dns_header.number_of_authority_records:d}/'
            f'{dns_header.number_of_additional_records:d}')


class MDNSDNSIdentifierAndFlagsFormatStringDecoder(
    BaseMDNSDNSStructureFormatStringDecoder):
  """mDNS DNS identifier and flags string decoder."""

  def FormatValue(self, value, value_formatter=None):
    """Formats a mDNS DNS identifier and flags value.

    Args:
      value (bytes): mDNS DNS identifier and flags value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted mDNS DNS identifier and flags value.
    """
    if len(value) != 8:
      # TODO: determine what the MacOS log tool shows.
      return 'ERROR: unsupported value'

    data_type_map = self._GetDataTypeMap('mdsn_dns_identifier_and_flags')

    dns_identifier_and_flags = self._ReadStructureFromByteStream(
        value, 0, data_type_map)

    formatted_flags = self._FormatFlags(dns_identifier_and_flags.flags)

    return (f'id: 0x{dns_identifier_and_flags.identifier:04X} '
            f'({dns_identifier_and_flags.identifier:d}), '
            f'flags: 0x{dns_identifier_and_flags.flags:04X} '
            f'({formatted_flags:s})')


class MDNSProtocolFormatStringDecoder(BaseFormatStringDecoder):
  """mDNS protocol format string decoder."""

  VALUE_IN_BYTES = False

  _PROTOCOLS = {
      1: 'UDP',
      2: 'TCP',
      4: 'HTTPS'}

  def FormatValue(self, value, value_formatter=None):
    """Formats a mDNS protocol value.

    Args:
      value (int): mDNS protocol value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted mDNS protocol value.
    """
    return self._PROTOCOLS.get(value, 'UNKNOWN: {0:d}'.format(value))


class MDNSResourceRecordTypeFormatStringDecoder(BaseFormatStringDecoder):
  """mDNS resource record type format string decoder."""

  VALUE_IN_BYTES = False

  _RECORD_TYPES = {
      1: 'A',
      2: 'NS',
      5: 'CNAME',
      6: 'SOA',
      12: 'PTR',
      13: 'HINFO',
      15: 'MX',
      16: 'TXT',
      17: 'RP',
      18: 'AFSDB',
      24: 'SIG',
      25: 'KEY',
      28: 'AAAA',
      29: 'LOC',
      33: 'SRV',
      35: 'NAPTR',
      36: 'KX',
      37: 'CERT',
      39: 'DNAME',
      42: 'APL',
      43: 'DS',
      44: 'SSHFP',
      45: 'IPSECKEY',
      46: 'RRSIG',
      47: 'NSEC',
      48: 'DNSKEY',
      49: 'DHCID',
      50: 'NSEC3',
      51: 'NSEC3PARAM',
      52: 'TLSA',
      53: 'SMIMEA',
      55: 'HIP',
      59: 'CDS',
      60: 'CDNSKEY',
      61: 'OPENPGPKEY',
      62: 'CSYNC',
      63: 'ZONEMD',
      64: 'SVCB',
      65: 'HTTPS',
      108: 'EUI48',
      109: 'EUI64',
      249: 'TKEY',
      250: 'TSIG',
      256: 'URI',
      257: 'CAA',
      32768: 'TA',
      32769: 'DLV'}

  def FormatValue(self, value, value_formatter=None):
    """Formats a mDNS resource record type value.

    Args:
      value (int): mDNS resource record type value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted mDNS resource record type value.
    """
    return self._RECORD_TYPES.get(value, 'UNKNOWN: {0:d}'.format(value))


class OpenDirectoryErrorFormatStringDecoder(BaseFormatStringDecoder):
  """Open Directory error format string decoder."""

  VALUE_IN_BYTES = False

  _ERROR_CODES = {
      0: 'ODNoError',
      2: 'Not Found',
      1000: 'ODErrorSessionLocalOnlyDaemonInUse',
      1001: 'ODErrorSessionNormalDaemonInUse',
      1002: 'ODErrorSessionDaemonNotRunning',
      1003: 'ODErrorSessionDaemonRefused',
      1100: 'ODErrorSessionProxyCommunicationError',
      1101: 'ODErrorSessionProxyVersionMismatch',
      1102: 'ODErrorSessionProxyIPUnreachable',
      1103: 'ODErrorSessionProxyUnknownHost',
      2000: 'ODErrorNodeUnknownName',
      2001: 'ODErrorNodeUnknownType',
      2002: 'ODErrorNodeDisabled',
      2100: 'ODErrorNodeConnectionFailed',
      2200: 'ODErrorNodeUnknownHost',
      3000: 'ODErrorQuerySynchronize',
      3100: 'ODErrorQueryInvalidMatchType',
      3101: 'ODErrorQueryUnsupportedMatchType',
      3102: 'ODErrorQueryTimeout',
      4000: 'ODErrorRecordReadOnlyNode',
      4001: 'ODErrorRecordPermissionError',
      4100: 'ODErrorRecordParameterError',
      4101: 'ODErrorRecordInvalidType',
      4102: 'ODErrorRecordAlreadyExists',
      4103: 'ODErrorRecordTypeDisabled',
      4104: 'ODErrorRecordNoLongerExists',
      4200: 'ODErrorRecordAttributeUnknownType',
      4201: 'ODErrorRecordAttributeNotFound',
      4202: 'ODErrorRecordAttributeValueSchemaError',
      4203: 'ODErrorRecordAttributeValueNotFound',
      5000: 'ODErrorCredentialsInvalid',
      5001: 'ODErrorCredentialsInvalidComputer',
      5100: 'ODErrorCredentialsMethodNotSupported',
      5101: 'ODErrorCredentialsNotAuthorized',
      5102: 'ODErrorCredentialsParameterError',
      5103: 'ODErrorCredentialsOperationFailed',
      5200: 'ODErrorCredentialsServerUnreachable',
      5201: 'ODErrorCredentialsServerNotFound',
      5202: 'ODErrorCredentialsServerError',
      5203: 'ODErrorCredentialsServerTimeout',
      5204: 'ODErrorCredentialsContactPrimary',
      5205: 'ODErrorCredentialsServerCommunicationError',
      5300: 'ODErrorCredentialsAccountNotFound',
      5301: 'ODErrorCredentialsAccountDisabled',
      5302: 'ODErrorCredentialsAccountExpired',
      5303: 'ODErrorCredentialsAccountInactive',
      5304: 'ODErrorCredentialsAccountTemporarilyLocked',
      5305: 'ODErrorCredentialsAccountLocked',
      5400: 'ODErrorCredentialsPasswordExpired',
      5401: 'ODErrorCredentialsPasswordChangeRequired',
      5402: 'ODErrorCredentialsPasswordQualityFailed',
      5403: 'ODErrorCredentialsPasswordTooShort',
      5404: 'ODErrorCredentialsPasswordTooLong',
      5405: 'ODErrorCredentialsPasswordNeedsLetter',
      5406: 'ODErrorCredentialsPasswordNeedsDigit',
      5407: 'ODErrorCredentialsPasswordChangeTooSoon',
      5408: 'ODErrorCredentialsPasswordUnrecoverable',
      5500: 'ODErrorCredentialsInvalidLogonHours',
      6000: 'ODErrorPolicyUnsupported',
      6001: 'ODErrorPolicyOutOfRange',
      10000: 'ODErrorPluginOperationNotSupported',
      10001: 'ODErrorPluginError',
      10002: 'ODErrorDaemonError',
      10003: 'ODErrorPluginOperationTimeout'}

  def FormatValue(self, value, value_formatter=None):
    """Formats an Open Directory error value.

    Args:
      value (int): Open Directory error value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted Open Directory error value.
    """
    return self._ERROR_CODES.get(value, 'UNKNOWN: {0:d}'.format(value))


class OpenDirectoryMembershipDetailsFormatStringDecoder(
    BaseFormatStringDecoder, dtfabric_helper.DtFabricHelper):
  """Open Directory membership details format string decoder."""

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'macos_open_directory.yaml')

  _TYPES = {
      0x23: ('user', 'membership_details_with_identifier'),
      0x24: ('user', 'membership_details_with_name'),
      0x44: ('group', 'membership_details_with_name'),
      0xa0: ('user', 'membership_details_with_name'),
      0xa3: ('user', 'membership_details_with_identifier'),
      0xa4: ('user', 'membership_details_with_name'),
      0xc3: ('group', 'membership_details_with_identifier')}

  def FormatValue(self, value, value_formatter=None):
    """Formats an Open Directory membership details value.

    Args:
      value (bytes): Open Directory membership details value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted Open Directory membership details value.
    """
    if len(value) < 1:
      # TODO: determine what the MacOS log tool shows.
      return 'ERROR: unsupported value'

    type_indicator = value[0]
    type_name, data_type_map_name = self._TYPES.get(
        type_indicator, (None, None))
    if not data_type_map_name:
      return f'ERROR: unsupported type: 0x{type_indicator:02x}'

    data_type_map = self._GetDataTypeMap(data_type_map_name)

    membership_details = self._ReadStructureFromByteStream(
        value[1:], 1, data_type_map)

    if data_type_map_name == 'membership_details_with_name':
      return (f'{type_name:s}: {membership_details.name:s}@'
              f'{membership_details.domain:s}')

    return (f'{type_name:s}: {membership_details.identifier:d}@'
            f'{membership_details.domain:s}')


class OpenDirectoryMembershipTypeFormatStringDecoder(BaseFormatStringDecoder):
  """Open Directory membership type format string decoder."""

  VALUE_IN_BYTES = False

  _TYPES = {
      0: 'UID',
      1: 'GID',
      3: 'SID',
      4: 'Username',
      5: 'GROUPNAME',
      6: 'UUID',
      7: 'GROUP NFS',
      8: 'USER NFS',
      10: 'GSS EXPORT NAME',
      11: 'X509 DN',
      12: 'KERBEROS'}

  def FormatValue(self, value, value_formatter=None):
    """Formats an Open Directory membership type value.

    Args:
      value (int): Open Directory membership type value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted Open Directory membership type value.
    """
    return self._TYPES.get(value, 'UNKNOWN: {0:d}'.format(value))


class SignpostDescriptionAttributeFormatStringDecoder(BaseFormatStringDecoder):
  """Signpost description attribute value format string decoder."""

  VALUE_IN_BYTES = False

  def FormatValue(self, value, value_formatter=None):
    """Formats a Signpost description attribute value.

    Args:
      value (object): Signpost description attribute value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted Signpost description attribute value.
    """
    if value is None:
      value = ''
    elif not isinstance(value, str):
      value = value_formatter.format(value)

    return f'__##__signpost.description#____#attribute#_##_#{value:s}##__##'


class SignpostDescriptionBeginTimeFormatStringDecoder(BaseFormatStringDecoder):
  """Signpost description begin time value format string decoder."""

  VALUE_IN_BYTES = False

  def FormatValue(self, value, value_formatter=None):
    """Formats a Signpost description begin time value.

    Args:
      value (int): Signpost description begin time value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted Signpost description begin time value.
    """
    return f'__##__signpost.description#____#begin_time#_##_#{value:d}##__##'


class SignpostDescriptionEndTimeFormatStringDecoder(BaseFormatStringDecoder):
  """Signpost description end time value format string decoder."""

  VALUE_IN_BYTES = False

  def FormatValue(self, value, value_formatter=None):
    """Formats a Signpost description end time value.

    Args:
      value (int): Signpost description end time value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted Signpost description end time value.
    """
    return f'__##__signpost.description#____#end_time#_##_#{value:d}##__##'


class SignpostTelemetryNumberFormatStringDecoder(BaseFormatStringDecoder):
  """Signpost telemetry number value format string decoder."""

  VALUE_IN_BYTES = False

  def __init__(self, number=1):
    """Initializes a Signpost telemetry number value format string decoder.

    Args:
      number (Optional[int]): Signpost telemetry number.
    """
    super(SignpostTelemetryNumberFormatStringDecoder, self).__init__()
    self._number = number

  def FormatValue(self, value, value_formatter=None):
    """Formats a Signpost telemetry number value.

    Args:
      value (object): Signpost telemetry number value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted Signpost telemetry number value.
    """
    if isinstance(value, float):
      value_formatter = '{0:.9g}'

    if value is None:
      value = ''
    elif not isinstance(value, str):
      value = value_formatter.format(value)

    return (f'__##__signpost.telemetry#____#number{self._number}'
            f'#_##_#{value:s}##__##')


class SignpostTelemetryStringFormatStringDecoder(BaseFormatStringDecoder):
  """Signpost telemetry string value format string decoder."""

  VALUE_IN_BYTES = False

  def __init__(self, number=1):
    """Initializes a Signpost telemetry string value format string decoder.

    Args:
      number (Optional[int]): Signpost telemetry number.
    """
    super(SignpostTelemetryStringFormatStringDecoder, self).__init__()
    self._number = number

  def FormatValue(self, value, value_formatter=None):
    """Formats a Signpost telemetry string value.

    Args:
      value (str): Signpost telemetry string value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted Signpost telemetry string value.
    """
    return (f'__##__signpost.telemetry#____#string{self._number}'
            f'#_##_#{value:s}##__##')


class SocketAdressFormatStringDecoder(BaseFormatStringDecoder):
  """Socker address value format string decoder."""

  def FormatValue(self, value, value_formatter=None):
    """Formats a socket address value.

    Args:
      value (bytes): socket address value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted socket address value.
    """
    value_size = len(value)
    if value_size >= 2:
      address_family = value[1]
      if address_family == 2 and value_size == 16:
        ipv4_address = value[4:8]
        return '.'.join([f'{octet:d}' for octet in ipv4_address])

      if address_family == 30 and value_size == 28:
        ipv6_address = value[8:24]
        # Note that socket.inet_ntop() is not supported on Windows.
        octet_pairs = zip(ipv6_address[0::2], ipv6_address[1::2])
        octet_pairs = [octet1 << 8 | octet2 for octet1, octet2 in octet_pairs]
        # TODO: determine if ":0000" should be omitted from the string.
        return ':'.join([f'{octet_pair:04x}' for octet_pair in octet_pairs])

    # TODO: determine what the MacOS log tool shows.
    return 'ERROR: unsupported value'


class UUIDFormatStringDecoder(BaseFormatStringDecoder):
  """UUID value format string decoder."""

  VALUE_IN_BYTES = False

  def FormatValue(self, value, value_formatter=None):
    """Formats an UUID value.

    Args:
      value (bytes): UUID value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted UUID value.
    """
    uuid_value = uuid.UUID(bytes=value)
    return f'{uuid_value!s}'.upper()


class WindowsNTSecurityIdentifierFormatStringDecoder(
    BaseFormatStringDecoder, dtfabric_helper.DtFabricHelper):
  """Windows NT security identifier (SID) format string decoder."""

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'windows_nt.yaml')

  def FormatValue(self, value, value_formatter=None):
    """Formats a Windows NT security identifier (SID) value.

    Args:
      value (bytes): Windows NT security identifier (SID) value.
      value_formatter (Optional[str]): value formatter.

    Returns:
      str: formatted Windows NT security identifier (SID) value.
    """
    if len(value) < 8:
      # TODO: determine what the MacOS log tool shows.
      return 'ERROR: unsupported value'

    data_type_map = self._GetDataTypeMap('windows_nt_security_identifier')

    security_identifier = self._ReadStructureFromByteStream(
        value, 0, data_type_map)

    authority = security_identifier.authority_lower | (
        security_identifier.authority_upper << 32)
    sub_authorities = '-'.join([
        f'{sub_authority:d}'
        for sub_authority in security_identifier.sub_authorities])

    return (f'S-{security_identifier.revision_number}-'
            f'{authority:d}-{sub_authorities:s}')


class BaseUnifiedLoggingFile(dtfabric_helper.DtFabricHelper):
  """Shared functionality for Apple Unified Logging (AUL) files."""

  def __init__(self):
    """Initializes a Apple Unified Logging (AUL) file."""
    super(BaseUnifiedLoggingFile, self).__init__()
    self._file_entry = None
    self._file_object = None

  def Close(self):
    """Closes an Apple Unified Logging (AUL) data file.

    Raises:
      IOError: if the file is not opened.
      OSError: if the file is not opened.
    """
    if not self._file_object:
      raise IOError('File not opened')

    self._file_object = None
    self._file_entry = None

  def Open(self, file_entry):
    """Opens an Apple Unified Logging (AUL) data file.

    Args:
      file_entry (dfvfs.FileEntry): a file entry.

    Raises:
      IOError: if the file is already opened.
      OSError: if the file is already opened.
    """
    if self._file_object:
      raise IOError('File already opened')

    self._file_entry = file_entry

    file_object = file_entry.GetFileObject()

    self.ReadFileObject(file_object)

    self._file_object = file_object

  @abc.abstractmethod
  def ReadFileObject(self, file_object):
    """Reads an Apple Unified Logging (AUL) file-like object.

    Args:
      file_object (file): file-like object.
    """


class DSCFile(BaseUnifiedLoggingFile):
  """Shared-Cache Strings (dsc) file.

  Attributes:
    ranges (list[DSCRange]): the ranges.
    uuids (list[DSCUUID]): the UUIDs.
  """

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'aul_dsc.yaml')

  _SUPPORTED_FORMAT_VERSIONS = ((1, 0), (2, 0))

  def __init__(self):
    """Initializes a shared-cache strings (dsc) file."""
    super(DSCFile, self).__init__()
    self.ranges = []
    self.uuids = []

  def _ReadFileHeader(self, file_object):
    """Reads a file header.

    Args:
      file_object (file): file-like object.

    Returns:
      dsc_file_header: a file header.

    Raises:
      ParseError: if the file header cannot be read.
    """
    data_type_map = self._GetDataTypeMap('dsc_file_header')

    file_header, _ = self._ReadStructureFromFileObject(
        file_object, 0, data_type_map)

    if file_header.signature != b'hcsd':
      raise errors.ParseError('Unsupported signature.')

    format_version = (
        file_header.major_format_version, file_header.minor_format_version)
    if format_version not in self._SUPPORTED_FORMAT_VERSIONS:
      format_version_string = '.'.join([
          f'{file_header.major_format_version:d}',
          f'{file_header.minor_format_version:d}'])
      raise errors.ParseError(
          f'Unsupported format version: {format_version_string:s}')

    return file_header

  def _ReadString(self, file_object, file_offset):
    """Reads a string.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the string data relative to the start
          of the file.

    Returns:
      str: string.

    Raises:
      ParseError: if the string cannot be read.
    """
    data_type_map = self._GetDataTypeMap('cstring')

    format_string, _ = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

    return format_string

  def _ReadImagePath(self, file_object, file_offset):
    """Reads an image path.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the image path data relative to the start
          of the file.

    Returns:
      str: image path.

    Raises:
      ParseError: if the image path cannot be read.
    """
    data_type_map = self._GetDataTypeMap('cstring')

    image_path, _ = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

    return image_path

  def _ReadRangeDescriptors(
      self, file_object, file_offset, version, number_of_ranges):
    """Reads the range descriptors.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the start of range descriptors data relative
          to the start of the file.
      version (int): major version of the file.
      number_of_ranges (int): the number of range descriptions to retrieve.

    Yields:
      DSCRange: a range.

    Raises:
      ParseError: if the file cannot be read.
    """
    if version not in (1, 2):
      raise errors.ParseError(f'Unsupported format version: {version:d}.')

    if version == 1:
      data_type_map_name = 'dsc_range_descriptor_v1'
    else:
      data_type_map_name = 'dsc_range_descriptor_v2'

    data_type_map = self._GetDataTypeMap(data_type_map_name)

    for _ in range(number_of_ranges):
      range_descriptor, record_size = self._ReadStructureFromFileObject(
          file_object, file_offset, data_type_map)

      file_offset += record_size

      dsc_range = DSCRange()
      dsc_range.data_offset = range_descriptor.data_offset
      dsc_range.range_offset = range_descriptor.range_offset
      dsc_range.range_size = range_descriptor.range_size
      dsc_range.uuid_index = range_descriptor.uuid_descriptor_index
      yield dsc_range

  def _ReadUUIDDescriptors(
      self, file_object, file_offset, version, number_of_uuids):
    """Reads the UUID descriptors.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the start of UUID descriptors data relative
          to the start of the file.
      version (int): major version of the file
      number_of_uuids (int): the number of UUID descriptions to retrieve.

    Yields:
      DSCUUId: an UUID.

    Raises:
      ParseError: if the file cannot be read.
    """
    if version not in (1, 2):
      raise errors.ParseError(f'Unsupported format version: {version:d}.')

    if version == 1:
      data_type_map_name = 'dsc_uuid_descriptor_v1'
    else:
      data_type_map_name = 'dsc_uuid_descriptor_v2'

    data_type_map = self._GetDataTypeMap(data_type_map_name)

    for _ in range(number_of_uuids):
      uuid_descriptor, record_size = self._ReadStructureFromFileObject(
          file_object, file_offset, data_type_map)

      file_offset += record_size

      dsc_uuid = DSCUUID()
      dsc_uuid.image_identifier = uuid_descriptor.image_identifier
      dsc_uuid.text_offset = uuid_descriptor.text_offset
      dsc_uuid.text_size = uuid_descriptor.text_size

      dsc_uuid.image_path = self._ReadImagePath(
          file_object, uuid_descriptor.path_offset)

      yield dsc_uuid

  def GetImageValuesAndString(self, string_reference, is_dynamic):
    """Retrieves image values and string.

    Args:
      string_reference (int): reference of the string.
      is_dynamic (bool): dynamic flag.

    Returns:
      tuple[uuid.UUID, int, str, str]: image identifier, image text offset,
          image path and string or (None, 0, None, None) if not available.

    Raises:
      ParseError: if the string cannot be read.
    """
    for dsc_range in self.ranges:
      if is_dynamic:
        range_offset = dsc_range.text_offset
        range_size = dsc_range.text_size
      else:
        range_offset = dsc_range.range_offset
        range_size = dsc_range.range_size

      if string_reference < range_offset:
        continue

      relative_offset = string_reference - range_offset
      if relative_offset <= range_size:
        if is_dynamic:
          format_string = '%s'
        else:
          file_offset = dsc_range.data_offset + relative_offset
          format_string = self._ReadString(self._file_object, file_offset)

        return (dsc_range.image_identifier, dsc_range.text_offset,
                dsc_range.image_path, format_string)

    # TODO: if string_reference is invalid use:
    # "<Invalid shared cache format string offset>"

    return None, 0, None, None

  def ReadFileObject(self, file_object):
    """Reads a shared-cache strings (dsc) file-like object.

    Args:
      file_object (file): file-like object.

    Raises:
      ParseError: if the file cannot be read.
    """
    file_header = self._ReadFileHeader(file_object)

    file_offset = file_object.tell()

    self.ranges = list(self._ReadRangeDescriptors(
        file_object, file_offset, file_header.major_format_version,
        file_header.number_of_ranges))

    file_offset = file_object.tell()

    self.uuids = list(self._ReadUUIDDescriptors(
        file_object, file_offset, file_header.major_format_version,
        file_header.number_of_uuids))

    for dsc_range in self.ranges:
      dsc_uuid = self.uuids[dsc_range.uuid_index]

      dsc_range.image_identifier = dsc_uuid.image_identifier
      dsc_range.image_path = dsc_uuid.image_path
      dsc_range.text_offset = dsc_uuid.text_offset
      dsc_range.text_size = dsc_uuid.text_size


class TimesyncDatabaseFile(BaseUnifiedLoggingFile):
  """Timesync database file."""

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'aul_timesync.yaml')

  _BOOT_RECORD_SIGNATURE = b'\xb0\xbb'
  _SYNC_RECORD_SIGNATURE = b'Ts'

  def __init__(self):
    """Initializes a timesync database file."""
    super(TimesyncDatabaseFile, self).__init__()
    self._boot_record_data_type_map = self._GetDataTypeMap(
        'timesync_boot_record')
    self._sync_record_data_type_map = self._GetDataTypeMap(
        'timesync_sync_record')

  def _ReadRecord(self, file_object, file_offset):
    """Reads a boot or sync record.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the start of the record relative to the start
          of the file.

    Returns:
      tuple[object, int]: boot or sync record and number of bytes read.

    Raises:
      ParseError: if the file cannot be read.
    """
    signature = file_object.read(2)

    if signature == self._BOOT_RECORD_SIGNATURE:
      data_type_map = self._boot_record_data_type_map

    elif signature == self._SYNC_RECORD_SIGNATURE:
      data_type_map = self._sync_record_data_type_map

    else:
      signature = repr(signature)
      raise errors.ParseError(f'Unsupported signature: {signature:s}.')

    return self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

  def ReadFileObject(self, file_object):
    """Reads a timesync file-like object.

    Args:
      file_object (file): file-like object.

    Raises:
      ParseError: if the file cannot be read.
    """
    return

  def ReadRecords(self):
    """Reads a timesync records.

    Yields:
      object: boot or sync record.

    Raises:
      ParseError: if the file cannot be read.
    """
    file_offset = 0

    while file_offset < self._file_entry.size:
      record, _ = self._ReadRecord(self._file_object, file_offset)
      yield record

      file_offset += record.record_size


class TraceV3File(BaseUnifiedLoggingFile):
  """Apple Unified Logging and Activity Tracing (tracev3) file."""

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'aul_tracev3.yaml')

  _RECORD_TYPE_ACTIVITY = 0x02
  _RECORD_TYPE_TRACE = 0x03
  _RECORD_TYPE_LOG = 0x04
  _RECORD_TYPE_SIGNPOST = 0x06
  _RECORD_TYPE_LOSS = 0x07

  _EVENT_TYPE_DESCRIPTIONS = {
      _RECORD_TYPE_ACTIVITY: 'activityCreateEvent',
      _RECORD_TYPE_LOG: 'logEvent',
      _RECORD_TYPE_SIGNPOST: 'signpostEvent'}

  _RECORD_TYPE_DESCRIPTIONS = {
      _RECORD_TYPE_ACTIVITY: 'Activity',
      _RECORD_TYPE_LOG: 'Log',
      _RECORD_TYPE_LOSS: 'Loss',
      _RECORD_TYPE_SIGNPOST: 'Signpost',
      _RECORD_TYPE_TRACE: 'Trace'}

  _STREAM_TYPE_DESCRIPTIONS = {
      0x00: 'persist',
      0x01: 'special handling',
      0x02: 'memory',
      0x04: 'signpost'}

  _CHUNK_TAG_HEADER = 0x00001000
  _CHUNK_TAG_FIREHOSE = 0x00006001
  _CHUNK_TAG_OVERSIZE = 0x00006002
  _CHUNK_TAG_STATEDUMP = 0x00006003
  _CHUNK_TAG_SIMPLEDUMP = 0x00006004
  _CHUNK_TAG_CATALOG = 0x0000600b
  _CHUNK_TAG_CHUNK_SET = 0x0000600d

  _CHUNK_TAG_DESCRIPTIONS = {
      _CHUNK_TAG_HEADER: 'Header',
      _CHUNK_TAG_FIREHOSE: 'Firehose',
      _CHUNK_TAG_OVERSIZE: 'Oversize',
      _CHUNK_TAG_STATEDUMP: 'StateDump',
      _CHUNK_TAG_SIMPLEDUMP: 'SimpleDump',
      _CHUNK_TAG_CATALOG: 'Catalog',
      _CHUNK_TAG_CHUNK_SET: 'ChunkSet'}

  _DATA_ITEM_VALUE_TYPE_DESCRIPTIONS = {}

  _DATA_ITEM_BINARY_DATA_VALUE_TYPES = (0x30, 0x32, 0xf2)
  _DATA_ITEM_NUMERIC_VALUE_TYPES = (0x00, 0x02)
  _DATA_ITEM_PRIVATE_VALUE_TYPES = (
      0x01, 0x21, 0x25, 0x31, 0x35, 0x41, 0x45)
  _DATA_ITEM_STRING_VALUE_TYPES = (0x20, 0x22, 0x40, 0x42)

  _DATA_ITEM_NUMERIC_DATA_MAP_NAMES = {
      'floating-point': {
          4: 'float32le',
          8: 'float64le'},
      'signed': {
          1: 'int8',
          2: 'int16le',
          4: 'int32le',
          8: 'int64le'},
      'unsigned': {
          1: 'uint8',
          2: 'uint16le',
          4: 'uint32le',
          8: 'uint64le'}}

  _FLAG_HAS_ACTIVITY_IDENTIFIER = 0x0001
  _FLAG_HAS_LARGE_OFFSET = 0x0020
  _FLAG_HAS_PRIVATE_STRINGS_RANGE = 0x0100

  _SUPPORTED_STRINGS_FILE_TYPES = (0x0002, 0x0004, 0x0008, 0x000a, 0x000c)
  _UUIDTEXT_STRINGS_FILE_TYPES = (0x0002, 0x0008, 0x000a)

  _LOG_TYPE_DESCRIPTIONS = {
      0x00: 'Default',
      0x01: 'Info',
      0x02: 'Debug',
      0x03: 'Useraction',
      0x10: 'Error',
      0x11: 'Fault',
      0x40: 'Thread Signpost Event',
      0x41: 'Thread Signpost Start',
      0x42: 'Thread Signpost End',
      0x80: 'Process Signpost Event',
      0x81: 'Process Signpost Start',
      0x82: 'Process Signpost End',
      0xc0: 'System Signpost Event',
      0xc1: 'System Signpost Start',
      0xc2: 'System Signpost End'}

  _SIGNPOST_SCOPE_DESCRIPTIONS = {
      0x04: 'thread',
      0x08: 'process',
      0x0c: 'system'}

  _SIGNPOST_TYPE_DESCRIPTIONS = {
      0x00: 'event',
      0x01: 'begin',
      0x02: 'end'}

  _FORMAT_STRING_DECODERS = {
      'bool': BooleanFormatStringDecoder(
          false_value='false', true_value='true'),
      'BOOL': BooleanFormatStringDecoder(
          false_value='NO', true_value='YES'),
      'darwin.errno': ExtendedErrorCodeFormatStringDecoder(),
      'darwin.mode': FileModeFormatStringDecoder(),
      'errno': ExtendedErrorCodeFormatStringDecoder(),
      'in_addr': IPv4FormatStringDecoder(),
      'in6_addr': IPv6FormatStringDecoder(),
      'internal:m': ErrorCodeFormatStringDecoder(),
      'location:_CLClientManagerStateTrackerState': (
          LocationClientManagerStateFormatStringDecoder()),
      'location:_CLLocationManagerStateTrackerState': (
          LocationLocationManagerStateFormatStringDecoder()),
      'location:escape_only': LocationEscapeOnlyFormatStringDecoder(),
      'location:SqliteResult': LocationSQLiteResultFormatStringDecoder(),
      'mdns:acceptable': BooleanFormatStringDecoder(
          false_value='unacceptable', true_value='acceptable'),
      'mdns:addrmv': BooleanFormatStringDecoder(
          false_value='rmv', true_value='add'),
      'mdns:dns.counts': MDNSDNSCountersFormatStringDecoder(),
      'mdns:dns.idflags': MDNSDNSIdentifierAndFlagsFormatStringDecoder(),
      'mdns:dnshdr': MDNSDNSHeaderFormatStringDecoder(),
      'mdns:protocol': MDNSProtocolFormatStringDecoder(),
      'mdns:rrtype': MDNSResourceRecordTypeFormatStringDecoder(),
      'mdns:yesno': BooleanFormatStringDecoder(
          false_value='no', true_value='yes'),
      'network:in_addr': IPv4FormatStringDecoder(),
      'network:in6_addr': IPv6FormatStringDecoder(),
      'network:sockaddr': SocketAdressFormatStringDecoder(),
      'mask.hash': MaskHashFormatStringDecoder(),
      'odtypes:mbr_details': (
          OpenDirectoryMembershipDetailsFormatStringDecoder()),
      'odtypes:mbridtype': OpenDirectoryMembershipTypeFormatStringDecoder(),
      'odtypes:nt_sid_t': WindowsNTSecurityIdentifierFormatStringDecoder(),
      'odtypes:ODError': OpenDirectoryErrorFormatStringDecoder(),
      'signpost.description:attribute': (
          SignpostDescriptionAttributeFormatStringDecoder()),
      'signpost.description:begin_time': (
          SignpostDescriptionBeginTimeFormatStringDecoder()),
      'signpost.description:end_time': (
          SignpostDescriptionEndTimeFormatStringDecoder()),
      'signpost.telemetry:number1': (
          SignpostTelemetryNumberFormatStringDecoder(number=1)),
      'signpost.telemetry:number2': (
          SignpostTelemetryNumberFormatStringDecoder(number=2)),
      'signpost.telemetry:number3': (
          SignpostTelemetryNumberFormatStringDecoder(number=3)),
      'signpost.telemetry:string1': (
          SignpostTelemetryStringFormatStringDecoder(number=1)),
      'signpost.telemetry:string2': (
          SignpostTelemetryStringFormatStringDecoder(number=2)),
      'sockaddr': SocketAdressFormatStringDecoder(),
      'time_t': DateTimeInSecondsFormatStringDecoder(),
      'uuid_t': UUIDFormatStringDecoder()}

  _FORMAT_STRING_DECODER_NAMES = frozenset(_FORMAT_STRING_DECODERS.keys())

  _MAXIMUM_CACHED_FILES = 64
  _MAXIMUM_CACHED_FORMAT_STRINGS = 1024

  _NANOSECONDS_PER_SECOND = 1000000000

  ACTIVITY_IDENTIFIER_BITMASK = (1 << 63) - 1

  def __init__(self, file_system=None):
    """Initializes a tracev3 file.

    Args:
      file_system (Optional[dfvfs.FileSystem]): file system.
    """
    super(TraceV3File, self).__init__()
    self._boot_identifier = None
    self._cached_dsc_files = collections.OrderedDict()
    self._cached_uuidtext_files = collections.OrderedDict()
    self._catalog = None
    self._catalog_process_information_entries = {}
    self._catalog_strings_map = {}
    self._chunk_index = 0
    self._file_system = file_system
    self._header_timebase = 1
    self._header_timestamp = 0
    self._sorted_timesync_sync_records = []
    self._timesync_boot_record = None
    self._timesync_path = None
    self._timesync_sync_records = []
    self._timesync_timebase = 1
    self._uuidtext_path = None

  def _BuildCatalogProcessInformationEntries(self, catalog):
    """Builds the catalog process information lookup table.

    Args:
      catalog (tracev3_catalog): catalog.
    """
    self._catalog_strings_map = self._GetCatalogSubSystemStringMap(catalog)

    self._catalog_process_information_entries = {}

    for process_information_entry in catalog.process_information_entries:
      if process_information_entry.main_uuid_index >= 0:
        process_information_entry.main_uuid = catalog.uuids[
            process_information_entry.main_uuid_index]

      if process_information_entry.dsc_uuid_index >= 0:
        process_information_entry.dsc_uuid = catalog.uuids[
            process_information_entry.dsc_uuid_index]

      proc_id = (f'{process_information_entry.proc_id_upper:d}@'
                 f'{process_information_entry.proc_id_lower:d}')
      if proc_id in self._catalog_process_information_entries:
        raise errors.ParseError(f'proc_id: {proc_id:s} already set')

      self._catalog_process_information_entries[proc_id] = (
          process_information_entry)

  def _CalculateFormatStringReference(
      self, tracepoint_data_object, string_reference):
    """Calculates the format string reference.

    Args:
      tracepoint_data_object (object): firehose tracepoint data object.
      string_reference (int): string reference.

    Returns:
      tuple[int, bool]: string reference and dynamic flag.
    """
    is_dynamic = bool(string_reference & 0x80000000 != 0)
    if is_dynamic:
      string_reference &= 0x7fffffff

    large_offset_data = getattr(
        tracepoint_data_object, 'large_offset_data', None)
    large_shared_cache_data = getattr(
        tracepoint_data_object, 'large_shared_cache_data', None)

    if large_shared_cache_data:
      string_reference |= large_shared_cache_data << 31

    elif large_offset_data:
      string_reference |= large_offset_data << 31

    return string_reference, is_dynamic

  def _CalculateNameStringReference(self, tracepoint_data_object):
    """Calculates the name string reference.

    Args:
      tracepoint_data_object (object): firehose tracepoint data object.

    Returns:
      tuple[int, bool]: string reference and dynamic flag.
    """
    string_reference = getattr(
        tracepoint_data_object, 'name_string_reference_lower', None) or 0
    is_dynamic = bool(string_reference & 0x80000000 != 0)

    if is_dynamic:
      string_reference &= 0x7fffffff

    large_offset_data = getattr(
        tracepoint_data_object, 'name_string_reference_upper', None)

    if large_offset_data:
      string_reference |= large_offset_data << 31

    return string_reference, is_dynamic

  def _CalculateProgramCounter(self, tracepoint_data_object, image_text_offset):
    """Calculates the program counter.

    Args:
      tracepoint_data_object (object): firehose tracepoint data object.
      image_text_offset (int): image text offset.

    Returns:
      int: program counter.
    """
    load_address = getattr(
        tracepoint_data_object, 'load_address_upper', None) or 0
    load_address <<= 32
    load_address |= tracepoint_data_object.load_address_lower

    large_offset_data = getattr(
        tracepoint_data_object, 'large_offset_data', None)
    large_shared_cache_data = getattr(
        tracepoint_data_object, 'large_shared_cache_data', None)

    if large_shared_cache_data:
      calculated_large_offset_data = large_shared_cache_data >> 1
      if large_offset_data != calculated_large_offset_data:
        load_address |= large_offset_data << 32
      else:
        load_address |= large_shared_cache_data << 31

    elif large_offset_data:
      load_address |= large_offset_data << 31

    return load_address - image_text_offset

  def _GetCatalogSubSystemStringMap(self, catalog):
    """Retrieves a map of the catalog sub system strings and offsets.

    Args:
      catalog (tracev3_catalog): catalog.

    Returns:
      dict[int, str]: catalog sub system string per offset.
    """
    strings_map = {}

    map_offset = 0
    for string in catalog.sub_system_strings:
      strings_map[map_offset] = string
      map_offset += len(string) + 1

    return strings_map

  def _GetDSCFile(self, uuid_string):
    """Retrieves a specific shared-cache strings (DSC) file.

    Args:
      uuid_string (str): string representation of the UUID.

    Returns:
      DSCFile: a shared-cache strings (DSC) file or None if not available.
    """
    dsc_file = self._cached_dsc_files.get(uuid_string, None)
    if not dsc_file:
      dsc_file = self._OpenDSCFile(uuid_string)
      if len(self._cached_dsc_files) >= self._MAXIMUM_CACHED_FILES:
        _, cached_dsc_file = self._cached_dsc_files.popitem(last=True)
        if cached_dsc_file:
          cached_dsc_file.Close()

      self._cached_dsc_files[uuid_string] = dsc_file

    self._cached_dsc_files.move_to_end(uuid_string, last=False)

    return dsc_file

  def _GetImageValuesAndString(
      self, process_information_entry, firehose_tracepoint,
      tracepoint_data_object, string_reference, is_dynamic):
    """Retrieves image values and string.

    Args:
      process_information_entry (tracev3_catalog_process_information_entry):
          process information entry.
      firehose_tracepoint (tracev3_firehose_tracepoint): firehose tracepoint.
      tracepoint_data_object (object): firehose tracepoint data object.
      string_reference (int): string reference.
      is_dynamic (bool): dynamic flag.

    Returns:
      tuple[uuid.UUID, int, str, str]: image identifier, image text offset,
          image path and string or (None, None, None, None) if not available.

    Raises:
      ParseError: if the image path or string cannot be retrieved.
    """
    strings_file_type = firehose_tracepoint.flags & 0x000e

    if strings_file_type not in self._SUPPORTED_STRINGS_FILE_TYPES:
      raise errors.ParseError(
          f'Unsupported strings file type: 0x{strings_file_type:04x}')

    strings_file_identifier = None
    image_text_offset = 0

    if strings_file_type == 0x0002:
      strings_file_identifier = process_information_entry.main_uuid

    if strings_file_type in (0x0004, 0x000c):
      strings_file_identifier = process_information_entry.dsc_uuid

    if strings_file_type == 0x0008:
      load_address_upper = tracepoint_data_object.load_address_upper or 0
      load_address_lower = tracepoint_data_object.load_address_lower

      for uuid_entry in process_information_entry.uuid_entries:
        if (load_address_upper != uuid_entry.load_address_upper or
            load_address_lower < uuid_entry.load_address_lower):
          continue

        if load_address_lower <= (
            uuid_entry.load_address_lower + uuid_entry.size):
          strings_file_identifier = self._catalog.uuids[uuid_entry.uuid_index]

          image_text_offset = uuid_entry.load_address_lower | (
              uuid_entry.load_address_upper << 32)
          break

    elif strings_file_type == 0x000a:
      strings_file_identifier = tracepoint_data_object.uuidtext_file_identifier

    if not strings_file_identifier:
      raise errors.ParseError('Missing strings file identifier.')

    uuid_string = strings_file_identifier.hex.upper()

    large_offset_data = getattr(
        tracepoint_data_object, 'large_offset_data', None) or 0

    image_identifier = None
    image_path = None
    string = None

    if strings_file_type in self._UUIDTEXT_STRINGS_FILE_TYPES:
      uuidtext_file = self._GetUUIDTextFile(uuid_string)
      if uuidtext_file:
        image_identifier = strings_file_identifier
        image_path = uuidtext_file.GetImagePath()
        if is_dynamic:
          string = '%s'
        else:
          string = uuidtext_file.GetString(string_reference)
          if string is None:
            # ~~> Invalid bounds INTEGER for UUID
            image_text_offset = large_offset_data << 31

    else:
      dsc_file = self._GetDSCFile(uuid_string)
      if dsc_file:
        image_identifier, image_text_offset, image_path, string = (
            dsc_file.GetImageValuesAndString(string_reference, is_dynamic))

      large_shared_cache_data = getattr(
          tracepoint_data_object, 'large_shared_cache_data', None)

      if large_offset_data and large_shared_cache_data:
        calculated_large_offset_data = large_shared_cache_data >> 1
        if large_offset_data != calculated_large_offset_data:
          image_identifier = strings_file_identifier
          image_text_offset = 0
          image_path = ''

    return image_identifier, image_text_offset, image_path, string

  def _GetProcessImageValues(self, process_information_entry):
    """Retrieves the process image value.

    Args:
      process_information_entry (tracev3_catalog_process_information_entry):
          process information entry.

    Returns:
      tuple[uuid.UUID, str]: process image identifier and path or (None, None)
          if not available.
    """
    image_identifier = None
    image_path = None

    if process_information_entry and process_information_entry.main_uuid:
      uuid_string = process_information_entry.main_uuid.hex.upper()
      uuidtext_file = self._GetUUIDTextFile(uuid_string)
      if uuidtext_file:
        image_identifier = process_information_entry.main_uuid
        image_path = uuidtext_file.GetImagePath()

    return image_identifier, image_path

  def _GetSubSystemStrings(
      self, process_information_entry, sub_system_identifier):
    """Retrieves the sub system strings.

    Args:
      process_information_entry (tracev3_catalog_process_information_entry):
          process information entry.
      sub_system_identifier (int): sub system identifier.

    Returns:
      tuple[str, str]: category and sub system or (None, None) if not available.
    """
    category = None
    sub_system = None

    # TODO: build a look up table of entries per identifier.
    if process_information_entry and sub_system_identifier is not None:
      for sub_system_entry in process_information_entry.sub_system_entries:
        if sub_system_entry.identifier == sub_system_identifier:
          category = self._catalog_strings_map.get(
              sub_system_entry.category_offset, None)
          sub_system = self._catalog_strings_map.get(
               sub_system_entry.sub_system_offset, None)

    return category, sub_system

  def _GetTimestamp(self, continuous_time):
    """Determine the timestamp from a continuous time.

    Args:
      continuous_time (int): continuous time.
      description (Optional[str]): description of the time value.

    Returns:
      int: timestamp containing the number of nanoseconds since January 1, 1970
          00:00:00.000000000.
    """
    timesync_record = self._GetTimesyncRecord(continuous_time)
    if timesync_record:
      continuous_time -= timesync_record.kernel_time
      timestamp = timesync_record.timestamp + (
          continuous_time * self._timesync_timebase)

    elif self._timesync_boot_record:
      timestamp = self._timesync_boot_record.timestamp + (
          continuous_time * self._timesync_timebase)

    else:
      timestamp = self._header_timestamp + (
          continuous_time * self._header_timebase)

    return timestamp

  def _GetTraceIdentifier(self, firehose_tracepoint):
    """Determines a trace identifier.

    Args:
      firehose_tracepoint (tracev3_firehose_tracepoint): firehose tracepoint.

    Returns:
      int: trace identifier.
    """
    trace_identifier = firehose_tracepoint.format_string_reference << 32
    trace_identifier |= firehose_tracepoint.flags << 16
    trace_identifier |= firehose_tracepoint.log_type << 8
    trace_identifier |= firehose_tracepoint.record_type

    return trace_identifier

  def _GetTimesyncRecord(self, continuous_time):
    """Retrieves a timesync record corresponding to the continuous time.

    Args:
      continuous_time (int): continuous time.

    Returns:
      timesync_sync_record: timesync sync record or None if not available.
    """
    for record in self._sorted_timesync_sync_records:
      if continuous_time >= record.kernel_time:
        return record

    return None

  def _GetUUIDTextFile(self, uuid_string):
    """Retrieves a specific uuidtext file.

    Args:
      uuid_string (str): string representation of the UUID.

    Returns:
      UUIDTextFile: an uuidtext file or None if not available.
    """
    uuidtext_file = self._cached_uuidtext_files.get(uuid_string, None)
    if not uuidtext_file:
      uuidtext_file = self._OpenUUIDTextFile(uuid_string)
      if len(self._cached_uuidtext_files) >= self._MAXIMUM_CACHED_FILES:
        _, cached_uuidtext_file = self._cached_uuidtext_files.popitem(last=True)
        if cached_uuidtext_file:
          cached_uuidtext_file.Close()

      self._cached_uuidtext_files[uuid_string] = uuidtext_file

    self._cached_uuidtext_files.move_to_end(uuid_string, last=False)

    return uuidtext_file

  def _OpenDSCFile(self, uuid_string):
    """Opens a specific shared-cache strings (DSC) file.

    Args:
      uuid_string (str): string representation of the UUID.

    Returns:
      DSCFile: a shared-cache strings (DSC) file or None if not available.
    """
    if not self._uuidtext_path:
      return None

    dsc_file_path = self._file_system.JoinPath([
        self._uuidtext_path, 'dsc', uuid_string])

    path_spec = path_spec_factory.Factory.NewPathSpec(
        self._file_entry.type_indicator, location=dsc_file_path,
        parent=self._file_entry.path_spec.parent)
    file_entry = self._file_system.GetFileEntryByPathSpec(path_spec)
    if not file_entry:
      return None

    dsc_file = DSCFile()
    dsc_file.Open(file_entry)

    return dsc_file

  def _OpenTimesyncDatabaseFile(self, file_entry):
    """Opens a specific timesync database file.

    Args:
      file_entry (dfvfs.FileEntry): file entry of the timesync database file.

    Returns:
      TimesyncDatabaseFile: a timesync database file or None if not available.
    """
    if not file_entry:
      return None

    timesync_file = TimesyncDatabaseFile()
    timesync_file.Open(file_entry)

    return timesync_file

  def _OpenUUIDTextFile(self, uuid_string):
    """Opens a specific uuidtext file.

    Args:
      uuid_string (str): string representation of the UUID.

    Returns:
      UUIDTextFile: an uuidtext file or None if not available.
    """
    if not self._uuidtext_path:
      return None

    uuidtext_file_path = self._file_system.JoinPath([
        self._uuidtext_path, uuid_string[0:2], uuid_string[2:]])

    path_spec = path_spec_factory.Factory.NewPathSpec(
        self._file_entry.type_indicator, location=uuidtext_file_path,
        parent=self._file_entry.path_spec.parent)
    file_entry = self._file_system.GetFileEntryByPathSpec(path_spec)
    if not file_entry:
      return None

    uuidtext_file = UUIDTextFile()
    uuidtext_file.Open(file_entry)

    return uuidtext_file

  def _ReadCatalog(self, file_object, file_offset):
    """Reads a catalog.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the catalog data relative to the start
          of the file.

    Returns:
      tracev3_catalog: catalog.

    Raises:
      ParseError: if the chunk header cannot be read.
    """
    data_type_map = self._GetDataTypeMap('tracev3_catalog')

    catalog, bytes_read = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

    file_offset += bytes_read

    data_type_map = self._GetDataTypeMap(
        'tracev3_catalog_process_information_entry')

    catalog.process_information_entries = []
    for _ in range(catalog.number_of_process_information_entries):
      process_information_entry, bytes_read = self._ReadStructureFromFileObject(
          file_object, file_offset, data_type_map)

      file_offset += bytes_read

      catalog.process_information_entries.append(process_information_entry)

    return catalog

  def _ReadChunkHeader(self, file_object, file_offset):
    """Reads a chunk header.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the chunk header relative to the start
          of the file.

    Returns:
      tracev3_chunk_header: a chunk header.

    Raises:
      ParseError: if the chunk header cannot be read.
    """
    data_type_map = self._GetDataTypeMap('tracev3_chunk_header')

    chunk_header, _ = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

    return chunk_header

  def _ReadChunkSet(self, file_object, file_offset, chunk_header):
    """Reads a chunk set.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the chunk set data relative to the start
          of the file.
      chunk_header (tracev3_chunk_header): the chunk header of the chunk set.

    Yields:
      LogEntry: a log entry.

    Raises:
      ParseError: if the chunk header cannot be read.
    """
    chunk_data = file_object.read(chunk_header.chunk_data_size)

    data_type_map = self._GetDataTypeMap('tracev3_lz4_block_header')

    lz4_block_header, _ = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

    if lz4_block_header.signature == b'bv41':
      end_of_data_offset = 12 + lz4_block_header.compressed_data_size
      uncompressed_data = lz4.block.decompress(
          chunk_data[12:end_of_data_offset],
          uncompressed_size=lz4_block_header.uncompressed_data_size)

    elif lz4_block_header.signature == b'bv4-':
      end_of_data_offset = 8 + lz4_block_header.uncompressed_data_size
      uncompressed_data = chunk_data[8:end_of_data_offset]

    else:
      raise errors.ParseError('Unsupported start of LZ4 block marker')

    end_of_lz4_block_marker = chunk_data[
        end_of_data_offset:end_of_data_offset + 4]

    if end_of_lz4_block_marker != b'bv4$':
      raise errors.ParseError('Unsupported end of LZ4 block marker')

    data_type_map = self._GetDataTypeMap('tracev3_chunk_header')

    data_offset = 0
    while data_offset < lz4_block_header.uncompressed_data_size:
      chunkset_chunk_header = self._ReadStructureFromByteStream(
          uncompressed_data[data_offset:], data_offset, data_type_map)
      data_offset += 16

      data_end_offset = data_offset + chunkset_chunk_header.chunk_data_size
      chunkset_chunk_data = uncompressed_data[data_offset:data_end_offset]

      if chunkset_chunk_header.chunk_tag == self._CHUNK_TAG_FIREHOSE:
        yield from self._ReadFirehoseChunkData(
            chunkset_chunk_data, chunkset_chunk_header.chunk_data_size,
            data_offset)

      elif chunkset_chunk_header.chunk_tag == self._CHUNK_TAG_OVERSIZE:
        self._ReadOversizeChunkData(chunkset_chunk_data, data_offset)

      elif chunkset_chunk_header.chunk_tag == self._CHUNK_TAG_STATEDUMP:
        self._ReadStateDumpChunkData(chunkset_chunk_data, data_offset)

      elif chunkset_chunk_header.chunk_tag == self._CHUNK_TAG_SIMPLEDUMP:
        self._ReadSimpleDumpChunkData(chunkset_chunk_data, data_offset)

      data_offset = data_end_offset

      _, alignment = divmod(data_offset, 8)
      if alignment > 0:
        alignment = 8 - alignment

      data_offset += alignment

  def _ReadBacktraceData(self, backtrace_data, data_offset):
    """Reads firehose tracepoint backtrace data.

    Args:
      backtrace_data (bytes): firehose tracepoint backtrace data.
      data_offset (int): offset of the firehose tracepoint backtrace data
          relative to the start of the chunk set.

    Returns:
      list[BacktraceFrame]: backtrace frames.

    Raises:
      ParseError: if the backtrace data cannot be read.
    """
    data_type_map = self._GetDataTypeMap(
        'tracev3_firehose_tracepoint_backtrace_data')

    backtrace_data = self._ReadStructureFromByteStream(
        backtrace_data, data_offset, data_type_map)

    backtrace_frames = []
    for frame_index in range(backtrace_data.number_of_frames):
      identifier_index = backtrace_data.indexes[frame_index]

      backtrace_frame = BacktraceFrame()
      backtrace_frame.image_offset = backtrace_data.offsets[frame_index]

      if identifier_index == 0xff:
        backtrace_frame.image_identifier = uuid.UUID(
            '00000000-0000-0000-0000-000000000000')
      else:
        backtrace_frame.image_identifier = backtrace_data.identifiers[
            identifier_index]

      backtrace_frames.append(backtrace_frame)

    return backtrace_frames

  def _ReadFirehoseChunkData(self, chunk_data, chunk_data_size, data_offset):
    """Reads firehose chunk data.

    Args:
      chunk_data (bytes): firehose chunk data.
      chunk_data_size (int): size of the firehose chunk data.
      data_offset (int): offset of the firehose chunk relative to the start
          of the chunk set.

    Yields:
      LogEntry: a log entry.

    Raises:
      ParseError: if the firehose chunk cannot be read.
    """
    data_type_map = self._GetDataTypeMap('tracev3_firehose_header')

    firehose_header = self._ReadStructureFromByteStream(
        chunk_data, data_offset, data_type_map)

    proc_id = (f'{firehose_header.proc_id_upper:d}@'
               f'{firehose_header.proc_id_lower:d}')
    process_information_entry = (
        self._catalog_process_information_entries.get(proc_id, None))
    if not process_information_entry:
      raise errors.ParseError((
          f'Unable to retrieve process information entry: {proc_id:s} from '
          f'catalog'))

    private_data_virtual_offset = (
        firehose_header.private_data_virtual_offset & 0x0fff)
    if not private_data_virtual_offset:
      private_data_size = 0
      private_data = b''
    else:
      private_data_size = 4096 - private_data_virtual_offset
      private_data = chunk_data[-private_data_size:]

    chunk_data_offset = 32
    while chunk_data_offset < firehose_header.public_data_size:
      firehose_tracepoint = self._ReadFirehoseTracepointData(
          chunk_data[chunk_data_offset:], data_offset + chunk_data_offset)

      chunk_data_offset += 24

      record_type = firehose_tracepoint.record_type
      if record_type not in (
          0x00, self._RECORD_TYPE_ACTIVITY, self._RECORD_TYPE_TRACE,
          self._RECORD_TYPE_LOG, self._RECORD_TYPE_SIGNPOST,
          self._RECORD_TYPE_LOSS):
        raise errors.ParseError(
            f'Unsupported record type: 0x{record_type:02x}.')

      tracepoint_data_offset = data_offset + chunk_data_offset
      tracepoint_data_object = None
      bytes_read = 0

      if record_type == self._RECORD_TYPE_ACTIVITY:
        if firehose_tracepoint.log_type not in (0x01, 0x03):
          raise errors.ParseError(
              f'Unsupported log type: 0x{firehose_tracepoint.log_type:02x}.')

        tracepoint_data_object, bytes_read = (
            self._ReadFirehoseTracepointActivityData(
                firehose_tracepoint.log_type, firehose_tracepoint.flags,
                firehose_tracepoint.data, tracepoint_data_offset))

      elif record_type == self._RECORD_TYPE_TRACE:
        if firehose_tracepoint.log_type not in (0x00, ):
          raise errors.ParseError(
              f'Unsupported log type: 0x{firehose_tracepoint.log_type:02x}.')

        tracepoint_data_object, bytes_read = (
            self._ReadFirehoseTracepointTraceData(
                firehose_tracepoint.flags, firehose_tracepoint.data,
                tracepoint_data_offset))

      elif record_type == self._RECORD_TYPE_LOG:
        if firehose_tracepoint.log_type not in (0x00, 0x01, 0x02, 0x10, 0x11):
          raise errors.ParseError(
              f'Unsupported log type: 0x{firehose_tracepoint.log_type:02x}.')

        tracepoint_data_object, bytes_read = (
            self._ReadFirehoseTracepointLogData(
                firehose_tracepoint.flags, firehose_tracepoint.data,
                tracepoint_data_offset))

      elif record_type == self._RECORD_TYPE_SIGNPOST:
        if firehose_tracepoint.log_type not in (
            0x40, 0x41, 0x42, 0x80, 0x81, 0x82, 0xc0, 0xc1, 0xc2):
          raise errors.ParseError(
              f'Unsupported log type: 0x{firehose_tracepoint.log_type:02x}.')

        tracepoint_data_object, bytes_read = (
            self._ReadFirehoseTracepointSignpostData(
                firehose_tracepoint.flags, firehose_tracepoint.data,
                tracepoint_data_offset))

      elif record_type == self._RECORD_TYPE_LOSS:
        if firehose_tracepoint.log_type not in (0x00, ):
          raise errors.ParseError(
              f'Unsupported log type: 0x{firehose_tracepoint.log_type:02x}.')

        tracepoint_data_object, bytes_read = (
            self._ReadFirehoseTracepointLossData(
                firehose_tracepoint.flags, firehose_tracepoint.data,
                tracepoint_data_offset))

      if tracepoint_data_object:
        values_data_offset = bytes_read

        if firehose_tracepoint.flags & 0x1000 == 0:
          backtrace_frames = []
        else:
          backtrace_frames = self._ReadBacktraceData(
              firehose_tracepoint.data[values_data_offset:],
              tracepoint_data_offset + values_data_offset)

        string_reference, is_dynamic = self._CalculateFormatStringReference(
            tracepoint_data_object, firehose_tracepoint.format_string_reference)

        image_identifier, image_text_offset, image_path, format_string = (
            self._GetImageValuesAndString(
                process_information_entry, firehose_tracepoint,
                tracepoint_data_object, string_reference, is_dynamic))

        string_formatter = StringFormatter()
        string_formatter.ParseFormatString(format_string)

        data_items = getattr(tracepoint_data_object, 'data_items', None)
        if data_items is None:
          values = []
        else:
          private_data_range = getattr(
              tracepoint_data_object, 'private_data_range', None)
          if private_data_range is None:
            private_data_offset = 0
          else:
            # TODO: error if private_data_virtual_offset >
            # private_data_range.offset
            private_data_offset = (
                private_data_range.offset - private_data_virtual_offset)

          # TODO: calculate item data offset for debugging purposes.
          values = self._ReadFirehoseTracepointDataItems(
              firehose_tracepoint.data, data_offset + chunk_data_offset,
              data_items, values_data_offset, private_data,
              private_data_offset, string_formatter)

        continuous_time = firehose_tracepoint.continuous_time_lower | (
            firehose_tracepoint.continuous_time_upper << 32)
        continuous_time += firehose_header.base_continuous_time

        sub_system_identifier = getattr(
            tracepoint_data_object, 'sub_system_identifier', None)
        category, sub_system = self._GetSubSystemStrings(
            process_information_entry, sub_system_identifier)

        process_image_identifier, process_image_path = (
            self._GetProcessImageValues(process_information_entry))

        program_counter = self._CalculateProgramCounter(
            tracepoint_data_object, image_text_offset)

        if not backtrace_frames:
          backtrace_frame = BacktraceFrame()
          backtrace_frame.image_identifier = image_identifier
          backtrace_frame.image_offset = program_counter or 0

          backtrace_frames.append(backtrace_frame)

        log_entry = LogEntry()
        log_entry.backtrace_frames = backtrace_frames
        log_entry.boot_identifier = self._boot_identifier
        log_entry.category = category
        log_entry.event_message = string_formatter.FormatString(values)
        log_entry.event_type = self._EVENT_TYPE_DESCRIPTIONS.get(
            firehose_tracepoint.record_type, None)
        log_entry.format_string = format_string
        log_entry.mach_timestamp = continuous_time
        log_entry.process_identifier = getattr(
            process_information_entry, 'process_identifier', None) or 0
        log_entry.process_image_identifier = process_image_identifier
        log_entry.process_image_path = process_image_path
        log_entry.sender_image_identifier = image_identifier
        log_entry.sender_image_path = image_path
        log_entry.sender_program_counter = program_counter or 0
        log_entry.sub_system = sub_system
        log_entry.thread_identifier = firehose_tracepoint.thread_identifier
        log_entry.timestamp = self._GetTimestamp(continuous_time)
        log_entry.time_zone_name = None
        log_entry.trace_identifier = self._GetTraceIdentifier(
            firehose_tracepoint)
        log_entry.ttl = getattr(tracepoint_data_object, 'ttl', None) or 0

        if firehose_tracepoint.record_type != self._RECORD_TYPE_SIGNPOST:
          log_entry.message_type = self._LOG_TYPE_DESCRIPTIONS.get(
              firehose_tracepoint.log_type, None)

        if firehose_tracepoint.record_type == self._RECORD_TYPE_ACTIVITY:
          new_activity_identifier = getattr(
              tracepoint_data_object, 'new_activity_identifier', None) or 0
          log_entry.activity_identifier = (
              new_activity_identifier & self.ACTIVITY_IDENTIFIER_BITMASK)

          current_activity_identifier = getattr(
              tracepoint_data_object, 'current_activity_identifier', None) or 0
          # Note that the creator activity identifier is not masked in
          # the output.
          log_entry.creator_activity_identifier = current_activity_identifier

          other_activity_identifier = getattr(
              tracepoint_data_object, 'other_activity_identifier', None) or 0
          log_entry.parent_activity_identifier = (
              other_activity_identifier & self.ACTIVITY_IDENTIFIER_BITMASK)

        else:
          current_activity_identifier = getattr(
              tracepoint_data_object, 'current_activity_identifier', None) or 0
          log_entry.activity_identifier = (
              current_activity_identifier & self.ACTIVITY_IDENTIFIER_BITMASK)

        if firehose_tracepoint.record_type == self._RECORD_TYPE_SIGNPOST:
          name_string_reference, is_dynamic = (
              self._CalculateNameStringReference(tracepoint_data_object))

          if not name_string_reference:
            name_string = None
          else:
            _, _, _, name_string = self._GetImageValuesAndString(
                process_information_entry, firehose_tracepoint,
                tracepoint_data_object, name_string_reference, is_dynamic)

          log_entry.signpost_identifier = getattr(
              tracepoint_data_object, 'signpost_identifier', None)
          log_entry.signpost_name = name_string
          log_entry.signpost_scope = self._SIGNPOST_SCOPE_DESCRIPTIONS.get(
              firehose_tracepoint.log_type >> 4, None)
          log_entry.signpost_type = self._SIGNPOST_TYPE_DESCRIPTIONS.get(
              firehose_tracepoint.log_type & 0x0f, None)

        yield log_entry

      chunk_data_offset += firehose_tracepoint.data_size

      _, alignment = divmod(chunk_data_offset, 8)
      if alignment > 0:
        alignment = 8 - alignment

      chunk_data_offset += alignment

    if private_data_size:
      chunk_data_size -= private_data_size

  def _ReadFirehoseTracepointData(self, tracepoint_data, data_offset):
    """Reads firehose tracepoint data.

    Args:
      tracepoint_data (bytes): firehose tracepoint data.
      data_offset (int): offset of the firehose tracepoint relative to
          the start of the chunk set.

    Returns:
      tracev3_firehose_tracepoint: firehose tracepoint.

    Raises:
      ParseError: if the firehose tracepoint cannot be read.
    """
    data_type_map = self._GetDataTypeMap('tracev3_firehose_tracepoint')

    return self._ReadStructureFromByteStream(
        tracepoint_data, data_offset, data_type_map)

  def _ReadFirehoseTracepointActivityData(
      self, log_type, flags, tracepoint_data, data_offset):
    """Reads firehose tracepoint activity data.

    Args:
      log_type (bytes): firehose tracepoint log type.
      flags (bytes): firehose tracepoint flags.
      tracepoint_data (bytes): firehose tracepoint data.
      data_offset (int): offset of the firehose tracepoint data relative to
          the start of the chunk set.

    Returns:
      tuple[tracev3_firehose_tracepoint_activity, int]: activity and the number
          of bytes read.

    Raises:
      ParseError: if the activity data cannot be read.
    """
    supported_flags = 0x0001 | 0x000e | 0x0010 | 0x0020 | 0x0100 | 0x0200

    if flags & ~supported_flags != 0:
      raise errors.ParseError(f'Unsupported flags: 0x{flags:04x}.')

    data_type_map = self._GetDataTypeMap('tracev3_firehose_tracepoint_activity')

    context = dtfabric_data_maps.DataTypeMapContext(values={
        'tracev3_firehose_tracepoint_flags': flags,
        'tracev3_firehose_tracepoint_log_type': log_type,
        'tracev3_firehose_tracepoint_strings_file_type': flags & 0x000e})

    activity = self._ReadStructureFromByteStream(
        tracepoint_data, data_offset, data_type_map, context=context)

    return activity, context.byte_size

  def _ReadFirehoseTracepointDataItems(
      self, tracepoint_data, data_offset, data_items, values_data_offset,
      private_data, private_data_range_offset, string_formatter):
    """Reads firehose tracepoint data items.

    Args:
      tracepoint_data (bytes): firehose tracepoint data.
      data_offset (int): offset of the firehose tracepoint data relative to
          the start of the chunk set.
      data_items (list[tracev3_firehose_tracepoint_data_item]): data items.
      values_data_offset (int): offset of the values data relative to the start
          of the firehose tracepoint data.
      private_data (bytes): firehose private data.
      private_data_range_offset (int): offset of the private data range
          relative to the start of the private data.
      string_formatter (StringFormatter): string formatter.

    Returns:
      list[str]: values formatted as strings.

    Raises:
      ParseError: if the data items cannot be read.
    """
    values = []

    value_index = 0
    precision = None

    for data_item in data_items:
      value_data = None
      value = None

      if data_item.value_type in self._DATA_ITEM_NUMERIC_VALUE_TYPES:
        type_hint = string_formatter.GetTypeHintByIndex(value_index)
        data_type_map_name = self._DATA_ITEM_NUMERIC_DATA_MAP_NAMES.get(
            type_hint or 'unsigned', {}).get(data_item.data_size, None)

        if data_type_map_name:
          data_type_map = self._GetDataTypeMap(data_type_map_name)

          # TODO: calculate data offset for debugging purposes.
          _ = data_offset

          value_data = data_item.data
          value = self._ReadStructureFromByteStream(
              value_data, 0, data_type_map)

      elif data_item.value_type in self._DATA_ITEM_STRING_VALUE_TYPES:
        if data_item.value_data_size > 0:
          # Note that the string data does not necessarily include
          # an end-of-string character hence the cstring data_type_map is not
          # used here.
          value_data_offset = values_data_offset + data_item.value_data_offset
          value_data = tracepoint_data[
              value_data_offset:value_data_offset + data_item.value_data_size]

          try:
            value = value_data.decode('utf-8').rstrip('\x00')
          except UnicodeDecodeError:
            pass

      elif data_item.value_type == 0x21:
        if data_item.value_data_size > 0:
          # Note that the string data does not necessarily include
          # an end-of-string character hence the cstring data_type_map is not
          # used here.
          value_data_offset = (
              private_data_range_offset + data_item.value_data_offset)
          value_data = private_data[
              value_data_offset:value_data_offset + data_item.value_data_size]

          try:
            value = value_data.decode('utf-8').rstrip('\x00')
          except UnicodeDecodeError:
            pass

      elif data_item.value_type in self._DATA_ITEM_BINARY_DATA_VALUE_TYPES:
        value_data_offset = values_data_offset + data_item.value_data_offset
        value_data = tracepoint_data[
            value_data_offset:value_data_offset + data_item.value_data_size]
        value = value_data

      if data_item.value_type not in (
          0x00, 0x01, 0x02, 0x10, 0x12, 0x20, 0x21, 0x22, 0x25, 0x30, 0x31,
          0x32, 0x35, 0x40, 0x41, 0x42, 0x45, 0x72, 0xf2):
        raise errors.ParseError((
            f'Unsupported data item value type: '
            f'0x{data_item.value_type:02x}.'))

      if data_item.value_type in (0x10, 0x12):
        precision = value
        continue

      value_formatter = string_formatter.GetValueFormatter(
          value_index, precision=precision)

      decoder_names = string_formatter.GetDecoderNamesByIndex(value_index)
      if data_item.value_type in self._DATA_ITEM_PRIVATE_VALUE_TYPES:
        if value is None:
          value = '<private>'

      elif decoder_names:
        decoder_class = self._FORMAT_STRING_DECODERS.get(decoder_names[0], None)
        if not decoder_class:
          value = f'<decode: unsupported decoder: {decoder_names[0]:s}>'
        elif decoder_class.VALUE_IN_BYTES:
          value = decoder_class.FormatValue(
              value_data, value_formatter=value_formatter)
        else:
          value = decoder_class.FormatValue(
              value, value_formatter=value_formatter)

      elif data_item.value_type in self._DATA_ITEM_STRING_VALUE_TYPES:
        if value is None:
          value = '(null)'

      elif isinstance(value, bytes):
        # TODO: determine how binary data is formatted
        value = f'\'{value!s}\''

      elif value_formatter:
        value = value_formatter.format(value)

      else:
        value = '<decode: missing format string>'

      precision = None

      values.append(value)

      value_index += 1

    return values

  def _ReadFirehoseTracepointLogData(self, flags, tracepoint_data, data_offset):
    """Reads firehose tracepoint log data.

    Args:
      flags (bytes): firehose tracepoint flags.
      tracepoint_data (bytes): firehose tracepoint data.
      data_offset (int): offset of the firehose tracepoint data relative to
          the start of the chunk set.

    Returns:
      tuple[tracev3_firehose_tracepoint_log, int]: log and the number of bytes
          read.

    Raises:
      ParseError: if the log data cannot be read.
    """
    supported_flags = (
        0x0001 | 0x000e | 0x0020 | 0x0100 | 0x0200 | 0x0400 | 0x0800 | 0x1000)

    if flags & ~supported_flags != 0:
      raise errors.ParseError(f'Unsupported flags: 0x{flags:04x}.')

    data_type_map = self._GetDataTypeMap('tracev3_firehose_tracepoint_log')

    context = dtfabric_data_maps.DataTypeMapContext(values={
        'tracev3_firehose_tracepoint_flags': flags,
        'tracev3_firehose_tracepoint_strings_file_type': flags & 0x000e})

    log = self._ReadStructureFromByteStream(
        tracepoint_data, data_offset, data_type_map, context=context)

    return log, context.byte_size

  def _ReadFirehoseTracepointLossData(
      self, flags, tracepoint_data, data_offset):
    """Reads firehose tracepoint loss data.

    Args:
      flags (bytes): firehose tracepoint flags.
      tracepoint_data (bytes): firehose tracepoint data.
      data_offset (int): offset of the firehose tracepoint data relative to
          the start of the chunk set.

    Returns:
      tuple[tracev3_firehose_tracepoint_loss, int]: loss and the number of bytes
          read.

    Raises:
      ParseError: if the loss data cannot be read.
    """
    supported_flags = 0x0000

    if flags & ~supported_flags != 0:
      raise errors.ParseError(f'Unsupported flags: 0x{flags:04x}.')

    data_type_map = self._GetDataTypeMap('tracev3_firehose_tracepoint_loss')

    context = dtfabric_data_maps.DataTypeMapContext(values={
        'tracev3_firehose_tracepoint_flags': flags,
        'tracev3_firehose_tracepoint_strings_file_type': flags & 0x000e})

    loss = self._ReadStructureFromByteStream(
        tracepoint_data, data_offset, data_type_map, context=context)

    return loss, context.byte_size

  def _ReadFirehoseTracepointSignpostData(
      self, flags, tracepoint_data, data_offset):
    """Reads firehose tracepoint signpost data.

    Args:
      flags (bytes): firehose tracepoint flags.
      tracepoint_data (bytes): firehose tracepoint data.
      data_offset (int): offset of the firehose tracepoint data relative to
          the start of the chunk set.

    Returns:
      tuple[tracev3_firehose_tracepoint_signpost, int]: signpost and the number
          of bytes read.

    Raises:
      ParseError: if the signpost data cannot be read.
    """
    supported_flags = (
        0x0001 | 0x000e | 0x0020 | 0x0100 | 0x0200 | 0x0400 | 0x0800 | 0x8000)

    if flags & ~supported_flags != 0:
      raise errors.ParseError(f'Unsupported flags: 0x{flags:04x}.')

    data_type_map = self._GetDataTypeMap('tracev3_firehose_tracepoint_signpost')

    context = dtfabric_data_maps.DataTypeMapContext(values={
        'tracev3_firehose_tracepoint_flags': flags,
        'tracev3_firehose_tracepoint_strings_file_type': flags & 0x000e})

    signpost = self._ReadStructureFromByteStream(
        tracepoint_data, data_offset, data_type_map, context=context)

    return signpost, context.byte_size

  def _ReadFirehoseTracepointTraceData(
      self, flags, tracepoint_data, data_offset):
    """Reads firehose tracepoint trace data.

    Args:
      flags (bytes): firehose tracepoint flags.
      tracepoint_data (bytes): firehose tracepoint data.
      data_offset (int): offset of the firehose tracepoint data relative to
          the start of the chunk set.

    Returns:
      tuple[tracev3_firehose_tracepoint_trace, int]: trace and the number of
          bytes read.

    Raises:
      ParseError: if the trace data cannot be read.
    """
    supported_flags = 0x0002

    if flags & ~supported_flags != 0:
      raise errors.ParseError(f'Unsupported flags: 0x{flags:04x}.')

    data_type_map = self._GetDataTypeMap('tracev3_firehose_tracepoint_trace')

    context = dtfabric_data_maps.DataTypeMapContext(values={
        'tracev3_firehose_tracepoint_flags': flags,
        'tracev3_firehose_tracepoint_strings_file_type': flags & 0x000e})

    trace = self._ReadStructureFromByteStream(
        tracepoint_data, data_offset, data_type_map, context=context)

    return trace, context.byte_size

  def _ReadHeaderChunk(self, file_object, file_offset):
    """Reads a header chunk.

    Args:
       file_object (file): file-like object.
       file_offset (int): offset of the chunk relative to the start of the file.

    Returns:
      header_chunk: a header chunk.

    Raises:
      ParseError: if the header chunk cannot be read.
    """
    data_type_map = self._GetDataTypeMap('tracev3_header_chunk')

    header_chunk, _ = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

    if header_chunk.flags & 0x0001 == 0:
      raise errors.ParseError(
          f'Unsupported header chunk flags: 0x{header_chunk.flags:04x}.')

    self._boot_identifier = header_chunk.generation.boot_identifier

    return header_chunk

  def _ReadOversizeChunkData(self, chunk_data, data_offset):
    """Reads Oversize chunk data.

    Args:
      chunk_data (bytes): Oversize chunk data.
      data_offset (int): offset of the Oversize chunk relative to the start
          of the chunk set.

    Returns:
      oversize_chunk: an Oversize chunk.

    Raises:
      ParseError: if the chunk cannot be read.
    """
    data_type_map = self._GetDataTypeMap('tracev3_oversize_chunk')

    return self._ReadStructureFromByteStream(
        chunk_data, data_offset, data_type_map)

  def _ReadSimpleDumpChunkData(self, chunk_data, data_offset):
    """Reads SimpleDump chunk data.

    Args:
      chunk_data (bytes): SimpleDump chunk data.
      data_offset (int): offset of the SimpleDump chunk relative to the start
          of the chunk set.

    Returns:
      simpledump_chunk: a SimpleDump chunk.

    Raises:
      ParseError: if the chunk cannot be read.
    """
    data_type_map = self._GetDataTypeMap('tracev3_simpledump_chunk')

    return self._ReadStructureFromByteStream(
        chunk_data, data_offset, data_type_map)

  def _ReadStateDumpChunkData(self, chunk_data, data_offset):
    """Reads StateDump chunk data.

    Args:
      chunk_data (bytes): StateDump chunk data.
      data_offset (int): offset of the StateDump chunk relative to the start
          of the chunk set.

    Returns:
      statedump_chunk: a StateDump chunk.

    Raises:
      ParseError: if the chunk cannot be read.
    """
    data_type_map = self._GetDataTypeMap('tracev3_statedump_chunk')

    return self._ReadStructureFromByteStream(
        chunk_data, data_offset, data_type_map)

  def _ReadTimesyncRecords(self, boot_identifier):
    """Reads the timesync records corresponding to the boot identifier.

    Args:
      boot_identifier (str): boot identifier (UUID).
    """
    self._timesync_boot_record = None
    self._timesync_sync_records = []

    if not self._timesync_path:
      return

    path_spec = path_spec_factory.Factory.NewPathSpec(
        self._file_entry.type_indicator, location=self._timesync_path,
        parent=self._file_entry.path_spec.parent)
    file_entry = self._file_system.GetFileEntryByPathSpec(path_spec)
    if not file_entry:
      return

    for sub_file_entry in file_entry.sub_file_entries:
      if self._timesync_boot_record:
        break

      if not sub_file_entry.name.endswith('.timesync'):
        continue

      timesync_file = self._OpenTimesyncDatabaseFile(sub_file_entry)

      for record in timesync_file.ReadRecords():
        record_boot_identifier = getattr(record, 'boot_identifier', None)

        if self._timesync_boot_record:
          if record_boot_identifier:
            break

          self._timesync_sync_records.append(record)

        elif record_boot_identifier == boot_identifier:
          self._timesync_boot_record = record

    if self._timesync_boot_record:
      self._timesync_timebase = (
          self._timesync_boot_record.timebase_numerator //
          self._timesync_boot_record.timebase_denominator)

      # Sort the timesync records starting with the largest kernel time.
      self._sorted_timesync_sync_records = sorted(
          self._timesync_sync_records, key=lambda record: record.kernel_time,
          reverse=True)

  def Close(self):
    """Closes a tracev3 file.

    Raises:
      IOError: if the file is not opened.
      OSError: if the file is not opened.
    """
    for dsc_file in self._cached_dsc_files.values():
      if dsc_file:
        dsc_file.Close()

    for uuidtext_file in self._cached_uuidtext_files.values():
      if uuidtext_file:
        uuidtext_file.Close()

    super(TraceV3File, self).Close()

  def ReadFileObject(self, file_object):
    """Reads a tracev3 file-like object.

    Args:
      file_object (file): file-like object.

    Raises:
      ParseError: if the file cannot be read.
    """
    # The uuidtext files can be stored in multiple locations relative from
    # the tracev3 file.
    # * in ../ for *.logarchive/logdata.LiveData.tracev3
    # * in ../../ for .logarchive/*/*.tracev3
    # * in ../../uuidtext/ for /private/var/db/diagnostics/*/*.tracev3
    path_segments = self._file_system.SplitPath(
        self._file_entry.path_spec.location)

    # Remove the filename from the path.
    path_segments.pop(-1)

    lower_last_path_segment = path_segments[-1].lower()
    if not lower_last_path_segment.endswith('.logarchive'):
      path_segments.pop(-1)
      lower_last_path_segment = path_segments[-1].lower()

    if not lower_last_path_segment.endswith('.logarchive'):
      path_segments.pop(-1)
      lower_last_path_segment = path_segments[-1].lower()

    if lower_last_path_segment.endswith('.logarchive'):
      path_segments.append('dsc')
      dsc_path = self._file_system.JoinPath(path_segments)

      path_spec = path_spec_factory.Factory.NewPathSpec(
          self._file_entry.type_indicator, location=dsc_path,
          parent=self._file_entry.path_spec.parent)
      if self._file_system.FileEntryExistsByPathSpec(path_spec):
        path_segments.pop(-1)
        self._uuidtext_path = self._file_system.JoinPath(path_segments)

    else:
      path_segments.append('uuidtext')
      uuidtext_path = self._file_system.JoinPath(path_segments)

      path_spec = path_spec_factory.Factory.NewPathSpec(
          self._file_entry.type_indicator, location=uuidtext_path,
          parent=self._file_entry.path_spec.parent)
      if self._file_system.FileEntryExistsByPathSpec(path_spec):
        self._uuidtext_path = uuidtext_path

      path_segments.pop(-1)

    # The timesync files can be stored in multiple locations relative from
    # the tracev3 file.
    # * in ../timesync/ for *.logarchive/logdata.LiveData.tracev3
    # * in ../../timesync/ for .logarchive/*/*.tracev3
    # * in ../../timesync/ for /private/var/db/diagnostics/*/*.tracev3
    # * in ../timesync/ for /private/var/db/diagnostics/*/*.tracev3
    path_segments.append('timesync')

    timesync_path = self._file_system.JoinPath(path_segments)

    path_spec = path_spec_factory.Factory.NewPathSpec(
        self._file_entry.type_indicator, location=timesync_path,
        parent=self._file_entry.path_spec.parent)
    if not self._file_system.FileEntryExistsByPathSpec(path_spec):
      path_segments.insert(-1, 'diagnostics')

      timesync_path = self._file_system.JoinPath(path_segments)

      path_spec = path_spec_factory.Factory.NewPathSpec(
          self._file_entry.type_indicator, location=timesync_path,
          parent=self._file_entry.path_spec.parent)

    if self._file_system.FileEntryExistsByPathSpec(path_spec):
      self._timesync_path = timesync_path

    file_offset = 0
    self._chunk_index = 1

    chunk_header = self._ReadChunkHeader(file_object, file_offset)
    file_offset += 16

    header_chunk = self._ReadHeaderChunk(file_object, file_offset)
    file_offset += chunk_header.chunk_data_size

    _, alignment = divmod(file_offset, 8)
    if alignment > 0:
      alignment = 8 - alignment

    file_offset += alignment

    file_object.seek(file_offset, os.SEEK_SET)

    self._header_timestamp = (
        header_chunk.timestamp * self._NANOSECONDS_PER_SECOND)
    self._header_timebase = (
        header_chunk.timebase_numerator // header_chunk.timebase_denominator)

    self._ReadTimesyncRecords(self._boot_identifier)

  def ReadLogEntries(self):
    """Reads log traces.

    Yields:
      LogEntry: a log entry.

    Raises:
      ParseError: if the file cannot be read.
    """
    file_offset = self._file_object.tell()

    while file_offset < self._file_entry.size:
      chunk_header = self._ReadChunkHeader(self._file_object, file_offset)
      file_offset += 16

      if chunk_header.chunk_tag == self._CHUNK_TAG_CATALOG:
        self._catalog = self._ReadCatalog(self._file_object, file_offset)
        self._BuildCatalogProcessInformationEntries(self._catalog)

      elif chunk_header.chunk_tag == self._CHUNK_TAG_CHUNK_SET:
        yield from self._ReadChunkSet(
            self._file_object, file_offset, chunk_header)

      else:
        raise errors.ParseError(
            f'Unsupported chunk tag: 0x{chunk_header.chunk_tag:04x}.')

      file_offset += chunk_header.chunk_data_size

      _, alignment = divmod(file_offset, 8)
      if alignment > 0:
        alignment = 8 - alignment

      file_offset += alignment


class UUIDTextFile(BaseUnifiedLoggingFile):
  """Apple Unified Logging and Activity Tracing (uuidtext) file."""

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'aul_uuidtext.yaml')

  def __init__(self):
    """Initializes an uuidtext file."""
    super(UUIDTextFile, self).__init__()
    self._entry_descriptors = []
    self._file_footer = None

  def _ReadFileFooter(self, file_object, file_offset):
    """Reads a file footer.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the file footer relative to the start
          of the file.

    Returns:
      uuidtext_file_footer: a file footer.

    Raises:
      ParseError: if the file footer cannot be read.
    """
    data_type_map = self._GetDataTypeMap('uuidtext_file_footer')

    file_footer, _ = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

    return file_footer

  def _ReadFileHeader(self, file_object):
    """Reads a file header.

    Args:
      file_object (file): file-like object.

    Returns:
      uuidtext_file_header: a file header.

    Raises:
      ParseError: if the file header cannot be read.
    """
    data_type_map = self._GetDataTypeMap('uuidtext_file_header')

    file_header, _ = self._ReadStructureFromFileObject(
        file_object, 0, data_type_map)

    format_version = (
        file_header.major_format_version, file_header.minor_format_version)
    if format_version != (2, 1):
      format_version_string = '.'.join([
          f'{file_header.major_format_version:d}',
          f'{file_header.minor_format_version:d}'])
      raise errors.ParseError(
          f'Unsupported format version: {format_version_string:s}')

    return file_header

  def _ReadString(self, file_object, file_offset):
    """Reads a string.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the string data relative to the start
          of the file.

    Returns:
      str: string.

    Raises:
      ParseError: if the string cannot be read.
    """
    data_type_map = self._GetDataTypeMap('cstring')

    format_string, _ = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

    return format_string

  def GetString(self, string_reference):
    """Retrieves a string.

    Args:
      string_reference (int): reference of the string.

    Returns:
      str: string or None if not available.

    Raises:
      ParseError: if the string cannot be read.
    """
    for file_offset, entry_descriptor in self._entry_descriptors:
      if string_reference < entry_descriptor.offset:
        continue

      relative_offset = string_reference - entry_descriptor.offset
      if relative_offset <= entry_descriptor.data_size:
        file_offset += relative_offset
        return self._ReadString(self._file_object, file_offset)

    return None

  def GetImagePath(self):
    """Retrieves the image path.

    Returns:
      str: image path or None if not available.
    """
    return getattr(self._file_footer, 'image_path', None)

  def ReadFileObject(self, file_object):
    """Reads an uuidtext file-like object.

    Args:
      file_object (file): file-like object.

    Raises:
      ParseError: if the file cannot be read.
    """
    file_header = self._ReadFileHeader(file_object)

    self._entry_descriptors = []

    file_offset = file_object.tell()
    for entry_descriptor in file_header.entry_descriptors:
      self._entry_descriptors.append((file_offset, entry_descriptor))

      file_offset += entry_descriptor.data_size

    self._file_footer = self._ReadFileFooter(file_object, file_offset)


# TODO: refactor
class AULOversizeData(object):
  """Apple Unified Logging (AUL) oversize data.

  Attributes:
    data_ref_index (str): index of the data reference.
    first_proc_id (str): First process identifier.
    second_proc_id (str): Second process identifier.
    strings (List[str]): oversized strings.
  """

  def __init__(self, first_proc_id, second_proc_id, data_ref_index):
    """Initialises oversized data.

    Args:
      first_proc_id (str): First process identifier.
      second_proc_id (str): Second process identifier.
      data_ref_index (str): index of the data reference.
    """
    super(AULOversizeData, self).__init__()
    self.data_ref_index = data_ref_index
    self.first_proc_id = first_proc_id
    self.second_proc_id = second_proc_id
    self.strings = []


class UnifiedLoggingParser(interface.FileEntryParser):
  """Parses Apple Unified Logging (AUL) tracev3 files."""

  NAME = 'unified_logging'
  DATA_FORMAT = 'Apple Unified Logging (AUL) 64-bit tracev3 file'

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    # A tracev3 file does not have a distinct signature hence we use the first
    # 3 values.
    format_specification.AddNewSignature(
        b'\x00\x10\x00\x00\x11\x00\x00\x00\xd0\x00\x00\x00\x00\x00\x00\x00',
        offset=0)
    return format_specification

  def ParseFileEntry(self, parser_mediator, file_entry):
    """Parses an Apple Unified Logging (AUL) tracev3 file entry:

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_entry (dfvfs.FileEntry): a file entry to parse.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    file_system = file_entry.GetFileSystem()

    # TODO: add oversize chunk support
    # TODO: extract SimpleDump events
    # TODO: extract Loss events

    # TODO: extract timesync events
    # TODO: extract StateDump events
    # TODO: extract Trace events

    tracev3_file = TraceV3File(file_system=file_system)

    try:
      tracev3_file.Open(file_entry)
    except errors.ParseError as exception:
      raise errors.WrongParser(
          'Unable to open tracev3 file with error: {0!s}'.format(exception))

    try:
      for log_entry in tracev3_file.ReadLogEntries():
        event_data = UnifiedLoggingEventData()
        event_data.activity_identifier = (
            log_entry.activity_identifier &
            tracev3_file.ACTIVITY_IDENTIFIER_BITMASK)
        event_data.boot_identifier = str(log_entry.boot_identifier).upper()
        event_data.category = log_entry.category
        event_data.euid = None
        event_data.event_message = log_entry.event_message
        event_data.event_type = log_entry.event_type
        event_data.message_type = log_entry.message_type
        event_data.pid = log_entry.process_identifier
        event_data.process_image_identifier = str(
            log_entry.process_image_identifier).upper()
        event_data.process_image_path = log_entry.process_image_path
        event_data.recorded_time = dfdatetime_posix_time.PosixTimeInNanoseconds(
            timestamp=log_entry.timestamp)
        event_data.signpost_identifier = log_entry.signpost_identifier
        event_data.signpost_name = log_entry.signpost_name
        event_data.sender_image_identifier = str(
            log_entry.sender_image_identifier).upper()
        event_data.sender_image_path = log_entry.sender_image_path
        event_data.subsystem = log_entry.sub_system
        event_data.thread_identifier = log_entry.thread_identifier
        event_data.ttl = log_entry.ttl

        parser_mediator.ProduceEventData(event_data)

    finally:
      tracev3_file.Close()


manager.ParsersManager.RegisterParser(UnifiedLoggingParser)
