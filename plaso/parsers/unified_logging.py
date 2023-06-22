# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) file parser."""

import abc
import base64
import collections
import os
import re
import struct
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
    event_message (str): event message.
    event_type (str): event type.
    message_type (str): message type.
    process_identifier (int): process identifier (PID).
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
    self.event_message = None
    self.event_type = None
    self.message_type = None
    self.process_identifier = None
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


class ImageValues(object):
  """Image values.

  Attributes:
    identifier (uuid.UUID): the identifier.
    path (str): the path.
    string (str): the string.
    text_offset (int): the offset of the text.
  """

  def __init__(
      self, identifier=None, path=None, string=None, text_offset=None):
    """Initializes image values.

    Args:
      identifier (Optional[uuid.UUID]): the identifier.
      path (Optional[str]): the path.
      string (Optional[str]): the string.
      text_offset (Optional[int]): the offset of the text.
    """
    super(ImageValues, self).__init__()
    self._string_formatter = None
    self.identifier = identifier
    self.path = path
    self.string = string
    self.text_offset = text_offset

  def GetStringFormatter(self):
    """Retrieves a string formatter.

    Returns:
      StringFormatter: string formatter.
    """
    if not self._string_formatter:
      self._string_formatter = StringFormatter()
      self._string_formatter.ParseFormatString(self.string)

    return self._string_formatter


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
    loss_count (int): number of message lost.
    loss_end_mach_timestamp (int): Mach timestamp of the end of the message
        loss.
    loss_end_timestamp (int): timestamp of the end of the message loss, in
        number of nanoseconds since January 1, 1970 00:00:00.000000000
    loss_start_mach_timestamp (int): Mach timestamp of the start of the message
        loss.
    loss_start_timestamp (int): timestamp of the start of the message loss, in
        number of nanoseconds since January 1, 1970 00:00:00.000000000
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
    self.loss_count = None
    self.loss_end_mach_timestamp = None
    self.loss_end_timestamp = None
    self.loss_start_mach_timestamp = None
    self.loss_start_timestamp = None
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


class FormatStringOperator(object):
  """Format string operator.

  Attributes:
    flags (str): flags.
    precision (str): precision.
    specifier (str): conversion specifier.
    width (str): width.
  """

  _PYTHON_SPECIFIERS = {
      '@': 's',
      'a': 'f',
      'A': 'f',
      'C': 'c',
      'D': 'd',
      'i': 'd',
      'm': 'd',
      'O': 'o',
      'p': 'x',
      'P': 's',
      'S': 's',
      'u': 'd',
      'U': 'd'}

  def __init__(self, flags=None, precision=None, specifier=None, width=None):
    """Initializes a format string operator.

    Args:
      flags (Optional[str]): flags.
      precision (Optional[str]): precision.
      specifier (Optional[str]): conversion specifier.
      width (Optional[str]): width.
    """
    super(FormatStringOperator, self).__init__()
    self._format_string = None
    self.flags = flags
    self.precision = precision
    self.specifier = specifier
    self.width = width

  def GetPythonFormatString(self):
    """Retrieves the Python format string.

    Returns:
      str: Python format string.
    """
    if self._format_string is None:
      flags = self.flags or ''
      precision = self.precision or ''
      width = self.width or ''

      python_specifier = self._PYTHON_SPECIFIERS.get(
          self.specifier, self.specifier)

      # Format "%3.3d" with 0 padding.
      if self.specifier == 'd' and width and precision:
        flags = '0'

      # Ignore the precision of specifier "P" since it refers to the binary
      # data not the resulting string.
      if self.specifier == 'P':
        precision = ''

      # Prevent: "ValueError: Format specifier missing precision"
      elif precision == '.':
        precision = '.0'

      elif precision == '.*':
        precision = ''

      if python_specifier in ('d', 'o', 'x', 'X'):
        flags = flags.replace('-', '<')

        # Prevent: "ValueError: Precision not allowed in integer format
        # specifier"
        precision = ''

      elif python_specifier == 's':
        if width and not flags:
          flags = '>'
        else:
          flags = flags.replace('-', '<')

        # Prevent: "%.0s" formatting as an empty string.
        if precision == '.0':
          precision = ''

      if self.specifier == 'p':
        self._format_string = (
            f'0x{{0:{flags:s}{precision:s}{width:s}{python_specifier:s}}}')
      else:
        self._format_string = (
            f'{{0:{flags:s}{precision:s}{width:s}{python_specifier:s}}}')

    return self._format_string


class StringFormatter(object):
  """String formatter."""

  _DECODERS_TO_IGNORE = (
      '',
      'bluetooth:OI_STATUS',
      'private',
      'public',
      'sensitive',
      'xcode:size-in-bytes')

  _ESCAPE_REGEX = re.compile(r'([{}])')

  _INTERNAL_DECODERS = {
      '@': 'internal:s',
      'a': 'internal:f',
      'A': 'internal:f',
      'c': 'internal:u',
      'd': 'internal:i',
      'D': 'internal:i',
      'e': 'internal:f',
      'E': 'internal:f',
      'f': 'internal:f',
      'F': 'internal:f',
      'g': 'internal:f',
      'G': 'internal:f',
      'i': 'internal:i',
      'm': 'internal:m',
      'o': 'internal:u',
      'O': 'internal:u',
      'p': 'internal:u',
      'P': 'internal:s',
      's': 'internal:s',
      'u': 'internal:u',
      'U': 'internal:u',
      'x': 'internal:u',
      'X': 'internal:u'}

  _OPERATOR_REGEX = re.compile(
      r'(%'
      r'(?:\{([^\}]{1,128})\})?'         # Optional value type decoder.
      r'([-+0 #]{0,5})'                  # Optional flags.
      r'([0-9]+|[*])?'                   # Optional width.
      r'(\.(?:|[0-9]+|[*]))?'            # Optional precision.
      r'(?:h|hh|j|l|ll|L|t|q|z)?'        # Optional length modifier.
      r'([@aAcCdDeEfFgGimnoOpPsSuUxX])'  # Conversion specifier.
      r'|%%)')

  def __init__(self):
    """Initializes a string formatter."""
    super(StringFormatter, self).__init__()
    self._decoders = []
    self._format_string = None
    self._operators = []

  def FormatString(self, values):
    """Formats the string.

    Args:
      values (list[str]): values.

    Returns:
      str: formatted string.
    """
    # Add place holders for missing values.
    while len(values) < len(self._operators):
      values.append('<decode: missing data>')

    if self._format_string is None:
      formatted_string = ''
    elif self._operators:
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

  def GetFormatStringOperator(self, value_index):
    """Retrieves the format string operator of a specific value.

    Args:
      value_index (int): value index.

    Returns:
      FormatStringOperator: format string operator or None if not available.
    """
    try:
      return self._operators[value_index]
    except IndexError:
      return None

  def ParseFormatString(self, format_string):
    """Parses an Unified Logging format string.

    Args:
      format_string (str): Unified Logging format string.
    """
    self._decoders = []
    self._format_string = None
    self._operators = []

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
        decoder = decoder or ''
        decoder_names = [value.strip() for value in decoder.split(',')]

        # Remove private, public and sensitive value type decoders.
        decoder_names = [value for value in decoder_names if (
            value not in self._DECODERS_TO_IGNORE and value[:5] != 'name=')]

        if not decoder_names:
          internal_decoder = self._INTERNAL_DECODERS.get(specifier, None)
          if internal_decoder:
            decoder_names = [internal_decoder]

        format_string_operator = FormatStringOperator(
            flags=flags or None, precision=precision, specifier=specifier,
            width=width)

        self._decoders.append(decoder_names)
        self._operators.append(format_string_operator)

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

    if not self._operators:
      self._format_string = self._format_string.replace('{{', '{')
      self._format_string = self._format_string.replace('}}', '}')


class BaseFormatStringDecoder(object):
  """Format string decoder interface."""

  @abc.abstractmethod
  def FormatValue(self, value, format_string_operator=None):
    """Formats a value.

    Args:
      value (bytes): value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted value.
    """


class BooleanFormatStringDecoder(BaseFormatStringDecoder):
  """Boolean value format string decoder."""

  def __init__(self, false_value='false', true_value='true'):
    """Initializes a boolean value format string decoder.

    Args:
      false_value (Optional[str]): value that represents False.
      true_value (Optional[str]): value that represents True.
    """
    super(BooleanFormatStringDecoder, self).__init__()
    self._false_value = false_value
    self._true_value = true_value

  def FormatValue(self, value, format_string_operator=None):
    """Formats a boolean value.

    Args:
      value (bytes): boolean value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted boolean value.
    """
    integer_value = int.from_bytes(value, 'little', signed=False)

    if integer_value:
      return self._true_value

    return self._false_value


class DateTimeInSecondsFormatStringDecoder(BaseFormatStringDecoder):
  """Date and time value in seconds format string decoder."""

  def FormatValue(self, value, format_string_operator=None):
    """Formats a date and time value in seconds.

    Args:
      value (bytes): timestamp that contains the number of seconds since
          1970-01-01 00:00:00.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted date and time value in seconds.
    """
    integer_value = int.from_bytes(value, 'little', signed=False)

    date_time = dfdatetime_posix_time.PosixTime(timestamp=integer_value)
    return date_time.CopyToDateTimeString()


class ErrorCodeFormatStringDecoder(BaseFormatStringDecoder):
  """Error code format string decoder."""

  def FormatValue(self, value, format_string_operator=None):
    """Formats an error code value.

    Args:
      value (bytes): error code value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted error code value.
    """
    if len(value) != 4:
      return '<decode: unsupported value>'

    integer_value = int.from_bytes(value, 'little', signed=False)

    return darwin.DarwinSystemErrorHelper.GetDescription(integer_value)


class ExtendedErrorCodeFormatStringDecoder(BaseFormatStringDecoder):
  """Extended error code format string decoder."""

  def FormatValue(self, value, format_string_operator=None):
    """Formats an error code value.

    Args:
      value (bytes): error code value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted error code value.
    """
    if len(value) != 4:
      return '<decode: unsupported value>'

    integer_value = int.from_bytes(value, 'little', signed=False)

    error_message = darwin.DarwinSystemErrorHelper.GetDescription(integer_value)

    return f'[{integer_value:d}: {error_message:s}]'


class FileModeFormatStringDecoder(BaseFormatStringDecoder):
  """File mode format string decoder."""

  _FILE_TYPES = {
      0x1000: 'p',
      0x2000: 'c',
      0x4000: 'd',
      0x6000: 'b',
      0xa000: 'l',
      0xc000: 's'}

  def FormatValue(self, value, format_string_operator=None):
    """Formats a file mode value.

    Args:
      value (bytes): file mode value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted file mode value.
    """
    integer_value = int.from_bytes(value, 'little', signed=False)

    string_parts = 10 * ['-']

    if integer_value & 0x0001:
      string_parts[9] = 'x'
    if integer_value & 0x0002:
      string_parts[8] = 'w'
    if integer_value & 0x0004:
      string_parts[7] = 'r'

    if integer_value & 0x0008:
      string_parts[6] = 'x'
    if integer_value & 0x0010:
      string_parts[5] = 'w'
    if integer_value & 0x0020:
      string_parts[4] = 'r'

    if integer_value & 0x0040:
      string_parts[3] = 'x'
    if integer_value & 0x0080:
      string_parts[2] = 'w'
    if integer_value & 0x0100:
      string_parts[1] = 'r'

    string_parts[0] = self._FILE_TYPES.get(integer_value & 0xf000, '-')

    return ''.join(string_parts)


class FloatingPointFormatStringDecoder(BaseFormatStringDecoder):
  """Floating-point value format string decoder."""

  def FormatValue(self, value, format_string_operator=None):
    """Formats a floating-point value.

    Args:
      value (bytes): floating-point value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted floating-point value.
    """
    value_size = len(value)
    if value_size not in (4, 8):
      return '<decode: unsupported value>'

    if value_size == 4:
      float_value = struct.unpack('<f', value)
    else:
      float_value = struct.unpack('<d', value)

    # TODO: add support for "a" and "A"
    if format_string_operator:
      format_string = format_string_operator.GetPythonFormatString()
    else:
      format_string = '{0:f}'

    return format_string.format(float_value[0])


class IPv4FormatStringDecoder(BaseFormatStringDecoder):
  """IPv4 value format string decoder."""

  def FormatValue(self, value, format_string_operator=None):
    """Formats an IPv4 value.

    Args:
      value (bytes): IPv4 value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted IPv4 value.
    """
    if len(value) == 4:
      return '.'.join([f'{octet:d}' for octet in value])

    return '<decode: unsupported value>'


class IPv6FormatStringDecoder(BaseFormatStringDecoder):
  """IPv6 value format string decoder."""

  def FormatValue(self, value, format_string_operator=None):
    """Formats an IPv6 value.

    Args:
      value (bytes): IPv6 value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted IPv6 value.
    """
    if len(value) == 16:
      # Note that socket.inet_ntop() is not supported on Windows.
      octet_pairs = zip(value[0::2], value[1::2])
      octet_pairs = [octet1 << 8 | octet2 for octet1, octet2 in octet_pairs]
      # TODO: determine if ":0000" should be omitted from the string.
      return ':'.join([f'{octet_pair:04x}' for octet_pair in octet_pairs])

    return '<decode: unsupported value>'


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

  def FormatValue(self, value, format_string_operator=None):
    """Formats a location client manager state value.

    Args:
      value (bytes): location client manager state value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted location client manager state value.
    """
    if len(value) != 8:
      return '<decode: unsupported value>'

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

  def FormatValue(self, value, format_string_operator=None):
    """Formats a location location manager state value.

    Args:
      value (bytes): location location manager state value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted location location manager state value.
    """
    value_size = len(value)
    if value_size == 64:
      data_type_name = 'location_manager_state_tracker_state_v1'
    elif value_size == 72:
      data_type_name = 'location_manager_state_tracker_state_v2'
    else:
      return '<decode: unsupported value>'

    data_type_map = self._GetDataTypeMap(data_type_name)

    tracker_state = self._ReadStructureFromByteStream(value, 0, data_type_map)

    return self._FormatStructure(tracker_state, self._VALUE_MAPPINGS)


class LocationClientAuthorizationStatusFormatStringDecoder(
    BaseFormatStringDecoder):
  """Location client authorization status format string decoder."""

  _VALUES = {
      0: 'Not Determined',
      1: 'Restricted',
      2: 'Denied',
      3: 'Authorized Always',
      4: 'Authorized When In Use'}

  def FormatValue(self, value, format_string_operator=None):
    """Formats a client authorization status value.

    Args:
      value (bytes): client authorization status value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted client authorization status value.
    """
    integer_value = int.from_bytes(value, 'little', signed=False)

    string_value = self._VALUES.get(
        integer_value, f'<decode: unknown value: {integer_value:d}>')

    return f'"{string_value:s}"'


class LocationEscapeOnlyFormatStringDecoder(BaseFormatStringDecoder):
  """Location escape only format string decoder."""

  def FormatValue(self, value, format_string_operator=None):
    """Formats a location value.

    Args:
      value (bytes): location value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted location value.
    """
    # Note that the string data does not necessarily include an end-of-string
    # character.

    try:
      string_value = value.decode('utf-8').rstrip('\x00')
    except UnicodeDecodeError:
      return '<decode: unsupported value>'

    string_value = string_value.replace('/', '\\/')
    return f'"{string_value:s}"'


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

  def FormatValue(self, value, format_string_operator=None):
    """Formats a SQLite result value.

    Args:
      value (bytes): SQLite result.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted SQLite result value.
    """
    if len(value) != 4:
      return '<decode: unsupported value>'

    integer_value = int.from_bytes(value, 'little', signed=False)
    string_value = self._SQLITE_RESULTS.get(
        integer_value, f'<decode: unknown value: {integer_value:d}>')

    return f'"{string_value:s}"'


class MaskHashFormatStringDecoder(BaseFormatStringDecoder):
  """Mask hash format string decoder."""

  def FormatValue(self, value, format_string_operator=None):
    """Formats a value as a mask hash.

    Args:
      value (bytes): value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

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

  _DEFINITION_FILE = os.path.join(os.path.dirname(__file__), 'macos_mdns.yaml')

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

  def FormatValue(self, value, format_string_operator=None):
    """Formats a mDNS DNS counters value.

    Args:
      value (bytes): mDNS DNS counters value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted mDNS DNS counters value.
    """
    if len(value) != 8:
      return '<decode: unsupported value>'

    data_type_map = self._GetDataTypeMap('mdsn_dns_counters')

    dns_counters = self._ReadStructureFromByteStream(value, 0, data_type_map)

    return (f'{dns_counters.number_of_questions:d}/'
            f'{dns_counters.number_of_answers:d}/'
            f'{dns_counters.number_of_authority_records:d}/'
            f'{dns_counters.number_of_additional_records:d}')


class MDNSDNSHeaderFormatStringDecoder(BaseMDNSDNSStructureFormatStringDecoder):
  """mDNS DNS header format string decoder."""

  def FormatValue(self, value, format_string_operator=None):
    """Formats a mDNS DNS header value.

    Args:
      value (bytes): mDNS DNS header value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted mDNS DNS header value.
    """
    if len(value) != 12:
      return '<decode: unsupported value>'

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

  def FormatValue(self, value, format_string_operator=None):
    """Formats a mDNS DNS identifier and flags value.

    Args:
      value (bytes): mDNS DNS identifier and flags value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted mDNS DNS identifier and flags value.
    """
    if len(value) != 8:
      return '<decode: unsupported value>'

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

  _PROTOCOLS = {
      1: 'UDP',
      2: 'TCP',
      4: 'HTTPS'}

  def FormatValue(self, value, format_string_operator=None):
    """Formats a mDNS protocol value.

    Args:
      value (bytes): mDNS protocol value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted mDNS protocol value.
    """
    if len(value) != 4:
      return '<decode: unsupported value>'

    integer_value = int.from_bytes(value, 'little', signed=False)

    return self._PROTOCOLS.get(
        integer_value, f'<decode: unknown value: {integer_value:d}>')


class MDNSReasonFormatStringDecoder(BaseFormatStringDecoder):
  """mDNS reason format string decoder."""

  _REASONS = {
      1: 'no-data',
      2: 'nxdomain',
      3: 'query-suppressed',
      4: 'no-dns-service',
      5: 'server error'}

  def FormatValue(self, value, format_string_operator=None):
    """Formats a mDNS reason value.

    Args:
      value (bytes): mDNS reason value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted mDNS reason value.
    """
    if len(value) != 4:
      return '<decode: unsupported value>'

    integer_value = int.from_bytes(value, 'little', signed=False)

    return self._REASONS.get(
        integer_value, f'<decode: unknown value: {integer_value:d}>')


class MDNSResourceRecordTypeFormatStringDecoder(BaseFormatStringDecoder):
  """mDNS resource record type format string decoder."""

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

  def FormatValue(self, value, format_string_operator=None):
    """Formats a mDNS resource record type value.

    Args:
      value (bytes): mDNS resource record type value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted mDNS resource record type value.
    """
    if len(value) != 4:
      return '<decode: unsupported value>'

    integer_value = int.from_bytes(value, 'little', signed=False)

    return self._RECORD_TYPES.get(
        integer_value, f'<decode: unknown value: {integer_value:d}>')


class OpenDirectoryErrorFormatStringDecoder(BaseFormatStringDecoder):
  """Open Directory error format string decoder."""

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

  def FormatValue(self, value, format_string_operator=None):
    """Formats an Open Directory error value.

    Args:
      value (bytes): Open Directory error value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted Open Directory error value.
    """
    if len(value) != 4:
      return '<decode: unsupported value>'

    integer_value = int.from_bytes(value, 'little', signed=False)

    return self._ERROR_CODES.get(
        integer_value, f'<decode: unknown value: {integer_value:d}>')


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

  def FormatValue(self, value, format_string_operator=None):
    """Formats an Open Directory membership details value.

    Args:
      value (bytes): Open Directory membership details value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted Open Directory membership details value.
    """
    if len(value) < 1:
      return '<decode: unsupported value>'

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

  _TYPES = {
      0: 'UID',
      1: 'GID',
      3: 'SID',
      4: 'Username',
      5: 'Groupname',
      6: 'UUID',
      7: 'GROUP NFS',
      8: 'USER NFS',
      10: 'GSS EXPORT NAME',
      11: 'X509 DN',
      12: 'KERBEROS'}

  def FormatValue(self, value, format_string_operator=None):
    """Formats an Open Directory membership type value.

    Args:
      value (bytes): Open Directory membership type value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted Open Directory membership type value.
    """
    if len(value) != 4:
      return '<decode: unsupported value>'

    integer_value = int.from_bytes(value, 'little', signed=False)

    return self._TYPES.get(
        integer_value, f'<decode: unknown value: {integer_value:d}>')


class SignedIntegerFormatStringDecoder(BaseFormatStringDecoder):
  """Signed integer value format string decoder."""

  def FormatValue(self, value, format_string_operator=None):
    """Formats a signed integer value.

    Args:
      value (bytes): signed integer value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted signed integer value.
    """
    if len(value) not in (1, 2, 4, 8):
      return '<decode: unsupported value>'

    integer_value = int.from_bytes(value, 'little', signed=True)

    if format_string_operator:
      format_string = format_string_operator.GetPythonFormatString()
    else:
      format_string = '{0:d}'

    return format_string.format(integer_value)


class SignpostDescriptionAttributeFormatStringDecoder(BaseFormatStringDecoder):
  """Signpost description attribute value format string decoder."""

  def _GetStringValue(self, value, format_string_operator=None):
    """Retrieves the values as a string.

    Args:
      value (bytes): Signpost value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted Signpost value.
    """
    specifier = getattr(format_string_operator, 'specifier', 's')
    value_size = len(value)

    if not value:
      string_value = ''

    elif specifier in ('a', 'A', 'e', 'E', 'f', 'F', 'g', 'G'):
      if value_size not in (4, 8):
        return '<decode: unsupported value>'

      if value_size == 4:
        float_value = struct.unpack('<f', value)
      else:
        float_value = struct.unpack('<d', value)

      string_value = '{0:.16g}'.format(float_value[0])

    elif specifier in ('c', 'C', 'o', 'O', 'p', 'u', 'U', 'x', 'X'):
      if value_size not in (1, 2, 4, 8):
        return '<decode: unsupported value>'

      integer_value = int.from_bytes(value, 'little', signed=False)

      if format_string_operator:
        format_string = format_string_operator.GetPythonFormatString()
      else:
        format_string = '{0:d}'

      string_value = format_string.format(integer_value)

    elif specifier in ('d', 'D', 'i', 'm'):
      if value_size not in (1, 2, 4, 8):
        return '<decode: unsupported value>'

      integer_value = int.from_bytes(value, 'little', signed=True)

      if format_string_operator:
        format_string = format_string_operator.GetPythonFormatString()
      else:
        format_string = '{0:d}'

      string_value = format_string.format(integer_value)

    elif specifier in ('@', 's', 'S'):
      try:
        string_value = value.decode('utf-8').rstrip('\x00')
      except UnicodeDecodeError:
        return '<decode: unsupported value>'

      if format_string_operator:
        format_string = format_string_operator.GetPythonFormatString()
      else:
        format_string = '{0:s}'

      string_value = format_string.format(string_value)

    else:
      return '<decode: unsupported value>'

    return string_value

  def FormatValue(self, value, format_string_operator=None):
    """Formats a Signpost description attribute value.

    Args:
      value (bytes): Signpost description attribute value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted Signpost description attribute value.
    """
    string_value = self._GetStringValue(
        value, format_string_operator=format_string_operator)

    return (f'__##__signpost.description#____#attribute'
            f'#_##_#{string_value:s}##__##')


class SignpostDescriptionTimeFormatStringDecoder(BaseFormatStringDecoder):
  """Signpost description time value format string decoder."""

  def __init__(self, time='begin'):
    """Initializes a Signpost description time value format string decoder.

    Args:
      time (Optional[str]): Signpost description time.
    """
    super(SignpostDescriptionTimeFormatStringDecoder, self).__init__()
    self._time = time

  def FormatValue(self, value, format_string_operator=None):
    """Formats a Signpost description time value.

    Args:
      value (bytes): Signpost description time value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted Signpost description time value.
    """
    if len(value) != 8:
      return '<decode: unsupported value>'

    integer_value = int.from_bytes(value, 'little', signed=False)

    return (f'__##__signpost.description#____#{self._time:s}_time'
            f'#_##_#{integer_value:d}##__##')


class SignpostTelemetryNumberFormatStringDecoder(BaseFormatStringDecoder):
  """Signpost telemetry number value format string decoder."""

  def __init__(self, number=1):
    """Initializes a Signpost telemetry number value format string decoder.

    Args:
      number (Optional[int]): Signpost telemetry number.
    """
    super(SignpostTelemetryNumberFormatStringDecoder, self).__init__()
    self._number = number

  def _GetStringValue(self, value, format_string_operator=None):
    """Retrieves the values as a string.

    Args:
      value (bytes): Signpost value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted Signpost value.
    """
    specifier = getattr(format_string_operator, 'specifier', 's')
    value_size = len(value)

    if not value:
      string_value = ''

    elif specifier in ('a', 'A', 'e', 'E', 'f', 'F', 'g', 'G'):
      if value_size not in (4, 8):
        return '<decode: unsupported value>'

      if value_size == 4:
        float_value = struct.unpack('<f', value)
      else:
        float_value = struct.unpack('<d', value)

      string_value = '{0:.16g}'.format(float_value[0])

    elif specifier in ('c', 'C', 'o', 'O', 'p', 'u', 'U', 'x', 'X'):
      if value_size not in (1, 2, 4, 8):
        return '<decode: unsupported value>'

      integer_value = int.from_bytes(value, 'little', signed=False)

      if format_string_operator:
        format_string = format_string_operator.GetPythonFormatString()
      else:
        format_string = '{0:d}'

      string_value = format_string.format(integer_value)

    elif specifier in ('d', 'D', 'i', 'm'):
      if value_size not in (1, 2, 4, 8):
        return '<decode: unsupported value>'

      integer_value = int.from_bytes(value, 'little', signed=True)

      if format_string_operator:
        format_string = format_string_operator.GetPythonFormatString()
      else:
        format_string = '{0:d}'

      string_value = format_string.format(integer_value)

    elif specifier in ('@', 's', 'S'):
      try:
        string_value = value.decode('utf-8').rstrip('\x00')
      except UnicodeDecodeError:
        return '<decode: unsupported value>'

      if format_string_operator:
        format_string = format_string_operator.GetPythonFormatString()
      else:
        format_string = '{0:s}'

      string_value = format_string.format(string_value)

    else:
      return '<decode: unsupported value>'

    return string_value

  def FormatValue(self, value, format_string_operator=None):
    """Formats a Signpost telemetry number value.

    Args:
      value (bytes): Signpost telemetry number value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted Signpost telemetry number value.
    """
    string_value = self._GetStringValue(
        value, format_string_operator=format_string_operator)

    return (f'__##__signpost.telemetry#____#number{self._number}'
            f'#_##_#{string_value:s}##__##')


class SignpostTelemetryStringFormatStringDecoder(BaseFormatStringDecoder):
  """Signpost telemetry string value format string decoder."""

  def __init__(self, number=1):
    """Initializes a Signpost telemetry string value format string decoder.

    Args:
      number (Optional[int]): Signpost telemetry number.
    """
    super(SignpostTelemetryStringFormatStringDecoder, self).__init__()
    self._number = number

  def FormatValue(self, value, format_string_operator=None):
    """Formats a Signpost telemetry string value.

    Args:
      value (bytes): Signpost telemetry string value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted Signpost telemetry string value.
    """
    try:
      string_value = value.decode('utf-8').rstrip('\x00')
    except UnicodeDecodeError:
      return '<decode: unsupported value>'

    return (f'__##__signpost.telemetry#____#string{self._number}'
            f'#_##_#{string_value:s}##__##')


class SocketAddressFormatStringDecoder(BaseFormatStringDecoder):
  """Socket address value format string decoder."""

  def FormatValue(self, value, format_string_operator=None):
    """Formats a socket address value.

    Args:
      value (bytes): socket address value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted socket address value.
    """
    value_size = len(value)
    if value_size == 0:
      return '<NULL>'

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
        string_segments = [
            f'{octet_pair:04x}' if octet_pair else ''
            for octet_pair in octet_pairs]
        ip_string = ':'.join(string_segments)
        # TODO: find a more elegant solution.
        if ip_string == ':::::::':
          ip_string = '::'
        return ip_string

    return '<decode: unsupported value>'


class StringFormatStringDecoder(BaseFormatStringDecoder):
  """String value format string decoder."""

  def FormatValue(self, value, format_string_operator=None):
    """Formats a string value.

    Args:
      value (bytes): string value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted string value.
    """
    if not value:
      return '(null)'

    # Note that the string data does not necessarily include an end-of-string
    # character.

    try:
      string_value = value.decode('utf-8').rstrip('\x00')
    except UnicodeDecodeError:
      return '<decode: unsupported value>'

    if format_string_operator:
      format_string = format_string_operator.GetPythonFormatString()
    else:
      format_string = '{0:s}'

    return format_string.format(string_value)


class UnsignedIntegerFormatStringDecoder(BaseFormatStringDecoder):
  """Unsigned integer value format string decoder."""

  def FormatValue(self, value, format_string_operator=None):
    """Formats an unsigned integer value.

    Args:
      value (bytes): unsigned integer value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted unsigned integer value.
    """
    if len(value) not in (1, 2, 4, 8):
      return '<decode: unsupported value>'

    integer_value = int.from_bytes(value, 'little', signed=False)

    if format_string_operator:
      if (integer_value == 0 and format_string_operator.flags == '#' and
          format_string_operator.specifier == 'x'):
        return f'{integer_value:x}'

      format_string = format_string_operator.GetPythonFormatString()
    else:
      format_string = '{0:d}'

    return format_string.format(integer_value)


class UUIDFormatStringDecoder(BaseFormatStringDecoder):
  """UUID value format string decoder."""

  def FormatValue(self, value, format_string_operator=None):
    """Formats an UUID value.

    Args:
      value (bytes): UUID value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted UUID value.
    """
    uuid_value = uuid.UUID(bytes=value)
    return f'{uuid_value!s}'.upper()


class WindowsNTSecurityIdentifierFormatStringDecoder(
    BaseFormatStringDecoder, dtfabric_helper.DtFabricHelper):
  """Windows NT security identifier (SID) format string decoder."""

  _DEFINITION_FILE = os.path.join(os.path.dirname(__file__), 'windows_nt.yaml')

  def FormatValue(self, value, format_string_operator=None):
    """Formats a Windows NT security identifier (SID) value.

    Args:
      value (bytes): Windows NT security identifier (SID) value.
      format_string_operator (Optional[FormatStringOperator]): format string
          operator.

    Returns:
      str: formatted Windows NT security identifier (SID) value.
    """
    if len(value) < 8:
      return '<decode: unsupported value>'

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
    """Closes an Apple Unified Logging (AUL) file.

    Raises:
      IOError: if the file is not opened.
      OSError: if the file is not opened.
    """
    if not self._file_object:
      raise IOError('File not opened')

    self._file_object = None
    self._file_entry = None

  def Open(self, file_entry):
    """Opens an Apple Unified Logging (AUL) file.

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

  _DEFINITION_FILE = os.path.join(os.path.dirname(__file__), 'aul_dsc.yaml')

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

  def GetImageValues(self, string_reference, is_dynamic):
    """Retrieves image values.

    Args:
      string_reference (int): reference of the string.
      is_dynamic (bool): dynamic flag.

    Returns:
      ImageValues: image value or None if not available.

    Raises:
      ParseError: if the image values cannot be read.
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
          string = '%s'
        else:
          file_offset = dsc_range.data_offset + relative_offset
          string = self._ReadString(self._file_object, file_offset)

        return ImageValues(
            identifier=dsc_range.image_identifier, path=dsc_range.image_path,
            string=string, text_offset=dsc_range.text_offset)

    # TODO: if string_reference is invalid use:
    # "<Invalid shared cache format string offset>"

    return None

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

  _DEFINITION_FILE = os.path.join(os.path.dirname(__file__), 'aul_tracev3.yaml')

  _RECORD_TYPE_UNUSED = 0x00
  _RECORD_TYPE_ACTIVITY = 0x02
  _RECORD_TYPE_TRACE = 0x03
  _RECORD_TYPE_LOG = 0x04
  _RECORD_TYPE_SIGNPOST = 0x06
  _RECORD_TYPE_LOSS = 0x07

  _ACTIVITY_EVENT_TYPE_DESCRIPTIONS = {
      0x01: 'activityCreateEvent',
      0x03: 'userActionEvent'}

  _EVENT_TYPE_DESCRIPTIONS = {
      _RECORD_TYPE_LOG: 'logEvent',
      _RECORD_TYPE_LOSS: 'lossEvent',
      _RECORD_TYPE_SIGNPOST: 'signpostEvent',
      _RECORD_TYPE_TRACE: 'traceEvent'}

  _CHUNK_TAG_HEADER = 0x00001000
  _CHUNK_TAG_FIREHOSE = 0x00006001
  _CHUNK_TAG_OVERSIZE = 0x00006002
  _CHUNK_TAG_STATEDUMP = 0x00006003
  _CHUNK_TAG_SIMPLEDUMP = 0x00006004
  _CHUNK_TAG_CATALOG = 0x0000600b
  _CHUNK_TAG_CHUNK_SET = 0x0000600d

  _DATA_ITEM_BINARY_DATA_VALUE_TYPES = (0x30, 0x32, 0xf2)
  _DATA_ITEM_NUMERIC_VALUE_TYPES = (0x00, 0x02)
  _DATA_ITEM_PRECISION_VALUE_TYPES = (0x10, 0x12)
  _DATA_ITEM_PRIVATE_STRING_VALUE_TYPES = (0x21, 0x41)
  _DATA_ITEM_PRIVATE_VALUE_TYPES = (
      0x01, 0x21, 0x25, 0x31, 0x35, 0x41, 0x45)
  _DATA_ITEM_STRING_VALUE_TYPES = (0x20, 0x22, 0x40, 0x42)

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
      'internal:f': FloatingPointFormatStringDecoder(),
      'internal:i': SignedIntegerFormatStringDecoder(),
      'internal:m': ErrorCodeFormatStringDecoder(),
      'internal:s': StringFormatStringDecoder(),
      'internal:u': UnsignedIntegerFormatStringDecoder(),
      'location:_CLClientManagerStateTrackerState': (
          LocationClientManagerStateFormatStringDecoder()),
      'location:_CLLocationManagerStateTrackerState': (
          LocationLocationManagerStateFormatStringDecoder()),
      'location:CLClientAuthorizationStatus': (
          LocationClientAuthorizationStatusFormatStringDecoder()),
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
      'mdns:nreason': MDNSReasonFormatStringDecoder(),
      'mdns:rrtype': MDNSResourceRecordTypeFormatStringDecoder(),
      'mdns:yesno': BooleanFormatStringDecoder(
          false_value='no', true_value='yes'),
      'network:in_addr': IPv4FormatStringDecoder(),
      'network:in6_addr': IPv6FormatStringDecoder(),
      'network:sockaddr': SocketAddressFormatStringDecoder(),
      'mask.hash': MaskHashFormatStringDecoder(),
      'odtypes:mbr_details': (
          OpenDirectoryMembershipDetailsFormatStringDecoder()),
      'odtypes:mbridtype': OpenDirectoryMembershipTypeFormatStringDecoder(),
      'odtypes:nt_sid_t': WindowsNTSecurityIdentifierFormatStringDecoder(),
      'odtypes:ODError': OpenDirectoryErrorFormatStringDecoder(),
      'signpost.description:attribute': (
          SignpostDescriptionAttributeFormatStringDecoder()),
      'signpost.description:begin_time': (
          SignpostDescriptionTimeFormatStringDecoder(time='begin')),
      'signpost.description:end_time': (
          SignpostDescriptionTimeFormatStringDecoder(time='end')),
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
      'sockaddr': SocketAddressFormatStringDecoder(),
      'time_t': DateTimeInSecondsFormatStringDecoder(),
      'uuid_t': UUIDFormatStringDecoder()}

  _FORMAT_STRING_DECODER_NAMES = frozenset(_FORMAT_STRING_DECODERS.keys())

  _MAXIMUM_CACHED_FILES = 64
  _MAXIMUM_CACHED_IMAGE_VALUES = 8192

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
    self._cached_image_values = collections.OrderedDict()
    self._cached_uuidtext_files = collections.OrderedDict()
    self._catalog = None
    self._catalog_process_information_entries = {}
    self._catalog_strings_map = {}
    self._file_system = file_system
    self._header_timebase = 1.0
    self._header_timestamp = 0
    self._sorted_timesync_sync_records = []
    self._timesync_boot_record = None
    self._timesync_path = None
    self._timesync_sync_records = []
    self._timesync_timebase = 1.0
    self._uuidtext_path = None

  def _BuildCatalogProcessInformationEntries(self, catalog):
    """Builds the catalog process information lookup table.

    Args:
      catalog (tracev3_catalog): catalog.

    Raises:
      ParseError: if a process information entry already exists.
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
      if (large_offset_data and
          large_offset_data != calculated_large_offset_data):
        load_address |= large_offset_data << 32
      else:
        load_address |= large_shared_cache_data << 31

    elif large_offset_data:
      load_address |= large_offset_data << 31

    return load_address - image_text_offset

  def _DecodeValue(
      self, string_formatter, value_index, value_data, precision=None):
    """Decodes value data using the string formatter.

    Args:
      string_formatter (StringFormatter): string formatter.
      value_index (int): index of the value in the string formatter.
      value_data (bytes): value data.
      precision (Optional[int]): value format string precision.

    Returns:
      str: decoded value.
    """
    if not string_formatter:
      return '<decode: missing string formatter>'

    decoder_names = string_formatter.GetDecoderNamesByIndex(value_index)
    if not decoder_names:
      return '<decode: missing decoder>'

    decoder_object = self._FORMAT_STRING_DECODERS.get(decoder_names[0], None)
    if not decoder_object:
      return f'<decode: unsupported decoder: {decoder_names[0]:s}>'

    # TODO: add support for precision
    _ = precision

    format_string_operator = string_formatter.GetFormatStringOperator(
        value_index)
    return decoder_object.FormatValue(
        value_data, format_string_operator=format_string_operator)

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

  def _GetDataItemsAndValuesData(
      self, proc_id, tracepoint_data_object, values_data, private_data,
      oversize_chunks):
    """Retrieves the data items and values data.

    Args:
      proc_id (str): firehose tracepoint proc_id value.
      tracepoint_data_object (object): firehose tracepoint data object.
      values_data (bytes): (public) values data.
      private_data (bytes): private data.
      oversize_chunks (dict[str, oversize_chunk]): Oversize chunks per data
          reference.

    Returns:
      tuple[list[tracev3_data_item], bytes, bytes]: data items and values
          data and private data.
    """
    data_reference = getattr(tracepoint_data_object, 'data_reference', None)
    if not data_reference:
      data_items = getattr(tracepoint_data_object, 'data_items', None)
      return data_items, values_data, private_data

    lookup_key = f'{proc_id:s}:{data_reference:04x}'
    oversize_chunk = oversize_chunks.get(lookup_key, None)
    if oversize_chunk:
      return (oversize_chunk.data_items, oversize_chunk.values_data,
              oversize_chunk.private_data)

    # Seen in certain tracev3 files that oversize chunks can be missing.
    # TODO: issue warning.
    return None, values_data, private_data

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

  def _GetImageValues(
      self, process_information_entry, firehose_tracepoint,
      tracepoint_data_object, string_reference, is_dynamic):
    """Retrieves image values.

    Args:
      process_information_entry (tracev3_catalog_process_information_entry):
          process information entry.
      firehose_tracepoint (tracev3_firehose_tracepoint): firehose tracepoint.
      tracepoint_data_object (object): firehose tracepoint data object.
      string_reference (int): string reference.
      is_dynamic (bool): dynamic flag.

    Returns:
      ImageValues: image values.

    Raises:
      ParseError: if the image values cannot be retrieved.
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

      if not strings_file_identifier:
        # ~~> no uuid found for absolute pc
        return None

    elif strings_file_type == 0x000a:
      strings_file_identifier = tracepoint_data_object.uuidtext_file_identifier

    if not strings_file_identifier:
      raise errors.ParseError('Missing strings file identifier.')

    uuid_string = strings_file_identifier.hex.upper()

    lookup_key = f'{uuid_string:s}:0x{string_reference:x}'
    image_values = self._cached_image_values.get(lookup_key, None)
    if not image_values:
      large_offset_data = getattr(
          tracepoint_data_object, 'large_offset_data', None) or 0

      if strings_file_type in self._UUIDTEXT_STRINGS_FILE_TYPES:
        image_values = ImageValues(
            identifier=strings_file_identifier, text_offset=image_text_offset)

        uuidtext_file = self._GetUUIDTextFile(uuid_string)
        if uuidtext_file:
          image_values.path = uuidtext_file.GetImagePath()
          if is_dynamic:
            image_values.string = '%s'
          else:
            image_values.string = uuidtext_file.GetString(string_reference)
            if image_values.string is None:
              # ~~> Invalid bounds INTEGER for UUID
              image_values.text_offset = large_offset_data << 31

      else:
        dsc_file = self._GetDSCFile(uuid_string)
        if dsc_file:
          image_values = dsc_file.GetImageValues(string_reference, is_dynamic)

        if not image_values:
          image_values = ImageValues(
              identifier=strings_file_identifier, text_offset=image_text_offset)

        large_shared_cache_data = getattr(
            tracepoint_data_object, 'large_shared_cache_data', None)

        if large_offset_data and large_shared_cache_data:
          calculated_large_offset_data = large_shared_cache_data >> 1
          if large_offset_data != calculated_large_offset_data:
            # "<Invalid shared cache code pointer offset>"

            image_values.identifier = strings_file_identifier
            image_values.text_offset = 0
            image_values.path = ''

      if len(self._cached_image_values) >= self._MAXIMUM_CACHED_IMAGE_VALUES:
        self._cached_image_values.popitem(last=True)

      self._cached_image_values[lookup_key] = image_values

    self._cached_image_values.move_to_end(lookup_key, last=False)

    return image_values

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

    Returns:
      int: timestamp containing the number of nanoseconds since January 1, 1970
          00:00:00.000000000.
    """
    timesync_record = self._GetTimesyncRecord(continuous_time)
    if timesync_record:
      continuous_time -= timesync_record.kernel_time
      timestamp = timesync_record.timestamp + int(
          continuous_time * self._timesync_timebase)

    elif self._timesync_boot_record:
      timestamp = self._timesync_boot_record.timestamp + int(
          continuous_time * self._timesync_timebase)

    else:
      timestamp = self._header_timestamp + int(
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
    if not self._timesync_path:
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

  def _ReadChunkSet(
        self, file_object, file_offset, chunk_header, oversize_chunks):
    """Reads a chunk set.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the chunk set data relative to the start
          of the file.
      chunk_header (tracev3_chunk_header): the chunk header of the chunk set.
      oversize_chunks (dict[str, oversize_chunk]): Oversize chunks per data
          reference.

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
            chunkset_chunk_data, data_offset, oversize_chunks)

      elif chunkset_chunk_header.chunk_tag == self._CHUNK_TAG_OVERSIZE:
        oversize_chunk = self._ReadOversizeChunkData(
            chunkset_chunk_data, data_offset)

        lookup_key = (f'{oversize_chunk.proc_id_upper:d}@'
                      f'{oversize_chunk.proc_id_lower:d}:'
                      f'{oversize_chunk.data_reference:04x}')
        oversize_chunks[lookup_key] = oversize_chunk

      elif chunkset_chunk_header.chunk_tag == self._CHUNK_TAG_STATEDUMP:
        yield from self._ReadStateDumpChunkData(
            chunkset_chunk_data, data_offset)

      elif chunkset_chunk_header.chunk_tag == self._CHUNK_TAG_SIMPLEDUMP:
        yield from self._ReadSimpleDumpChunkData(
            chunkset_chunk_data, data_offset)

      data_offset = data_end_offset

      _, alignment = divmod(data_offset, 8)
      if alignment > 0:
        alignment = 8 - alignment

      data_offset += alignment

  def _ReadBacktraceData(self, flags, backtrace_data, data_offset):
    """Reads firehose tracepoint backtrace data.

    Args:
      flags (int): firehose tracepoint flags.
      backtrace_data (bytes): firehose tracepoint backtrace data.
      data_offset (int): offset of the firehose tracepoint backtrace data
          relative to the start of the chunk set.

    Returns:
      list[BacktraceFrame]: backtrace frames.

    Raises:
      ParseError: if the backtrace data cannot be read.
    """
    if flags & 0x1000 == 0:
      return []

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

  def _ReadDataItems(
      self, data_items, values_data, private_data, private_data_range_offset,
      string_formatter):
    """Reads data items.

    Args:
      data_items (list[tracev3_data_item]): data items.
      values_data (bytes): (public) values data.
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

      if data_item.value_type in self._DATA_ITEM_NUMERIC_VALUE_TYPES:
        value_data = data_item.data

      elif data_item.value_type in self._DATA_ITEM_PRECISION_VALUE_TYPES:
        value_data = data_item.data

      elif data_item.value_type in self._DATA_ITEM_STRING_VALUE_TYPES:
        value_data_offset = data_item.value_data_offset
        value_data = values_data[
            value_data_offset:value_data_offset + data_item.value_data_size]

      elif data_item.value_type in self._DATA_ITEM_PRIVATE_STRING_VALUE_TYPES:
        value_data_offset = (
            private_data_range_offset + data_item.value_data_offset)
        value_data = private_data[
            value_data_offset:value_data_offset + data_item.value_data_size]

      elif data_item.value_type in self._DATA_ITEM_BINARY_DATA_VALUE_TYPES:
        value_data_offset = data_item.value_data_offset
        value_data = values_data[
            value_data_offset:value_data_offset + data_item.value_data_size]

      if data_item.value_type not in (
          0x00, 0x01, 0x02, 0x10, 0x12, 0x20, 0x21, 0x22, 0x25, 0x30, 0x31,
          0x32, 0x35, 0x40, 0x41, 0x42, 0x45, 0x72, 0xf2):
        raise errors.ParseError((
            f'Unsupported data item value type: '
            f'0x{data_item.value_type:02x}.'))

      if data_item.value_type in self._DATA_ITEM_PRECISION_VALUE_TYPES:
        precision = int.from_bytes(value_data, 'little', signed=False)
        continue

      value = None
      if data_item.value_type in self._DATA_ITEM_PRIVATE_VALUE_TYPES:
        if not value_data:
          value = '<private>'

      if not value:
        value = self._DecodeValue(
            string_formatter, value_index, value_data, precision=precision)

      precision = None

      values.append(value)

      value_index += 1

    return values

  def _ReadFirehoseChunkData(self, chunk_data, data_offset, oversize_chunks):
    """Reads firehose chunk data.

    Args:
      chunk_data (bytes): firehose chunk data.
      data_offset (int): offset of the firehose chunk relative to the start
          of the chunk set.
      oversize_chunks (dict[str, oversize_chunk]): Oversize chunks per data
          reference.

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

    chunk_data_offset = 32
    while chunk_data_offset < firehose_header.public_data_size:
      firehose_tracepoint, bytes_read = self._ReadFirehoseTracepointData(
          chunk_data[chunk_data_offset:], data_offset + chunk_data_offset)

      record_type = firehose_tracepoint.record_type
      if record_type not in (
          self._RECORD_TYPE_UNUSED, self._RECORD_TYPE_ACTIVITY,
          self._RECORD_TYPE_TRACE, self._RECORD_TYPE_LOG,
          self._RECORD_TYPE_SIGNPOST, self._RECORD_TYPE_LOSS):
        raise errors.ParseError(
            f'Unsupported record type: 0x{record_type:02x}.')

      if record_type == self._RECORD_TYPE_UNUSED:
        chunk_data_offset += bytes_read
        continue

      chunk_data_offset += 24

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

      continuous_time = firehose_tracepoint.continuous_time_lower | (
          firehose_tracepoint.continuous_time_upper << 32)
      continuous_time += firehose_header.base_continuous_time

      process_image_identifier, process_image_path = (
          self._GetProcessImageValues(process_information_entry))

      log_entry = LogEntry()
      log_entry.boot_identifier = self._boot_identifier
      log_entry.mach_timestamp = continuous_time
      log_entry.process_image_identifier = process_image_identifier
      log_entry.thread_identifier = firehose_tracepoint.thread_identifier
      log_entry.timestamp = self._GetTimestamp(continuous_time)
      log_entry.trace_identifier = self._GetTraceIdentifier(firehose_tracepoint)

      if record_type == self._RECORD_TYPE_ACTIVITY:
        log_entry.event_type = self._ACTIVITY_EVENT_TYPE_DESCRIPTIONS.get(
            firehose_tracepoint.log_type, None)
      else:
        log_entry.event_type = self._EVENT_TYPE_DESCRIPTIONS.get(
            firehose_tracepoint.record_type, None)

      if record_type == self._RECORD_TYPE_LOSS:
        loss_count = tracepoint_data_object.number_of_messages or 0
        loss_start_time = tracepoint_data_object.start_time or 0
        loss_end_time = tracepoint_data_object.end_time or 0

        log_entry.event_message = (
            f'lost >={loss_count:d} unreliable messages from '
            f'{loss_start_time:d}-{loss_end_time:d} (Mach continuous exact '
            f'start-approx. end)')
        log_entry.loss_count = loss_count
        log_entry.loss_end_mach_timestamp = loss_end_time
        log_entry.loss_end_timestamp = self._GetTimestamp(loss_end_time)
        log_entry.loss_start_mach_timestamp = loss_start_time
        log_entry.loss_start_timestamp = self._GetTimestamp(loss_start_time)

        # TODO: add support for lossCountSaturated

      else:
        values_data_offset = bytes_read
        values_data = firehose_tracepoint.data[values_data_offset:]

        string_reference, is_dynamic = self._CalculateFormatStringReference(
            tracepoint_data_object, firehose_tracepoint.format_string_reference)

        image_values = self._GetImageValues(
            process_information_entry, firehose_tracepoint,
            tracepoint_data_object, string_reference, is_dynamic)

        if image_values:
          string_formatter = image_values.GetStringFormatter()
        else:
          string_formatter = None

        backtrace_frames = []
        values = []

        if record_type == self._RECORD_TYPE_TRACE:
          values = self._ReadFirehoseTracepointTraceValuesData(
              tracepoint_data_object, values_data, string_formatter)

        else:
          private_data_virtual_offset = (
              firehose_header.private_data_virtual_offset & 0x0fff)
          if not private_data_virtual_offset:
            private_data = b''
          else:
            private_data_size = 4096 - private_data_virtual_offset
            private_data = chunk_data[-private_data_size:]

          data_items, values_data, private_data = (
              self._GetDataItemsAndValuesData(
                  proc_id, tracepoint_data_object, values_data, private_data,
                  oversize_chunks))

          backtrace_frames = self._ReadBacktraceData(
              firehose_tracepoint.flags, values_data,
              tracepoint_data_offset + values_data_offset)

          if data_items:
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
            values = self._ReadDataItems(
                data_items, values_data, private_data, private_data_offset,
                string_formatter)

        sub_system_identifier = getattr(
            tracepoint_data_object, 'sub_system_identifier', None)
        category, sub_system = self._GetSubSystemStrings(
            process_information_entry, sub_system_identifier)

        text_offset = getattr(image_values, 'text_offset', None) or 0
        program_counter = self._CalculateProgramCounter(
            tracepoint_data_object, text_offset)

        if not backtrace_frames and image_values:
          backtrace_frame = BacktraceFrame()
          backtrace_frame.image_identifier = image_values.identifier
          backtrace_frame.image_offset = program_counter or 0

          backtrace_frames.append(backtrace_frame)

        log_entry.backtrace_frames = backtrace_frames
        log_entry.category = category
        log_entry.format_string = getattr(image_values, 'string', None)
        log_entry.process_identifier = getattr(
            process_information_entry, 'process_identifier', None) or 0
        log_entry.process_image_path = process_image_path
        log_entry.sender_image_identifier = getattr(
            image_values, 'identifier', None)
        log_entry.sender_image_path = getattr(image_values, 'path', None)
        log_entry.sender_program_counter = program_counter or 0
        log_entry.sub_system = sub_system
        log_entry.time_zone_name = None
        log_entry.ttl = getattr(tracepoint_data_object, 'ttl', None) or 0

        if firehose_tracepoint.record_type != self._RECORD_TYPE_SIGNPOST:
          log_entry.message_type = self._LOG_TYPE_DESCRIPTIONS.get(
              firehose_tracepoint.log_type, None)

        if firehose_tracepoint.record_type == self._RECORD_TYPE_ACTIVITY:
          new_activity_identifier = getattr(
              tracepoint_data_object, 'new_activity_identifier', None) or 0
          log_entry.activity_identifier = (
              new_activity_identifier & self.ACTIVITY_IDENTIFIER_BITMASK)

          if firehose_tracepoint.log_type == 0x01:
            current_activity_identifier = getattr(
                tracepoint_data_object, 'current_activity_identifier',
                None) or 0
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
            name_image_values = self._GetImageValues(
                process_information_entry, firehose_tracepoint,
                tracepoint_data_object, name_string_reference, is_dynamic)
            name_string = name_image_values.string

          log_entry.signpost_identifier = getattr(
              tracepoint_data_object, 'signpost_identifier', None)
          log_entry.signpost_name = name_string
          log_entry.signpost_scope = self._SIGNPOST_SCOPE_DESCRIPTIONS.get(
              firehose_tracepoint.log_type >> 4, None)
          log_entry.signpost_type = self._SIGNPOST_TYPE_DESCRIPTIONS.get(
              firehose_tracepoint.log_type & 0x0f, None)

        if string_formatter:
          log_entry.event_message = string_formatter.FormatString(values)
        else:
          log_entry.event_message = (
              '<compose failure [missing precomposed log]>')

      yield log_entry

      chunk_data_offset += firehose_tracepoint.data_size

      _, alignment = divmod(chunk_data_offset, 8)
      if alignment > 0:
        alignment = 8 - alignment

      chunk_data_offset += alignment

  def _ReadFirehoseTracepointData(self, tracepoint_data, data_offset):
    """Reads firehose tracepoint data.

    Args:
      tracepoint_data (bytes): firehose tracepoint data.
      data_offset (int): offset of the firehose tracepoint relative to
          the start of the chunk set.

    Returns:
      tuple[tracev3_firehose_tracepoint, int]: firehose tracepoint and number
          of bytes read.

    Raises:
      ParseError: if the firehose tracepoint cannot be read.
    """
    data_type_map = self._GetDataTypeMap('tracev3_firehose_tracepoint')

    context = dtfabric_data_maps.DataTypeMapContext()

    firehose_tracepoint = self._ReadStructureFromByteStream(
        tracepoint_data, data_offset, data_type_map, context=context)

    return firehose_tracepoint, context.byte_size

  def _ReadFirehoseTracepointActivityData(
      self, log_type, flags, tracepoint_data, data_offset):
    """Reads firehose tracepoint activity data.

    Args:
      log_type (int): firehose tracepoint log type.
      flags (int): firehose tracepoint flags.
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

  def _ReadFirehoseTracepointLogData(self, flags, tracepoint_data, data_offset):
    """Reads firehose tracepoint log data.

    Args:
      flags (int): firehose tracepoint flags.
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
      flags (int): firehose tracepoint flags.
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
      flags (int): firehose tracepoint flags.
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
      flags (int): firehose tracepoint flags.
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

    trace.number_of_values = tracepoint_data[-1]

    return trace, context.byte_size

  def _ReadFirehoseTracepointTraceValuesData(
      self, trace, values_data, string_formatter):
    """Reads firehose tracepoint trace values data.

    Args:
      trace (tracev3_firehose_tracepoint_trace): trace.
      values_data (bytes): (public) values data.
      string_formatter (StringFormatter): string formatter.

    Returns:
      list[str]: values formatted as strings.

    Raises:
      ParseError: if the values cannot be read.
    """
    if not trace.number_of_values:
      return []

    values = []

    value_data_offset = 0
    value_size_offset = -(1 + trace.number_of_values)

    for value_index in range(trace.number_of_values):
      value_data_size = values_data[value_size_offset]

      if value_data_size not in (4, 8):
        raise errors.ParseError(f'Unsupported value size: {value_data_size:d}')

      value_data = values_data[
          value_data_offset:value_data_offset + value_data_size]

      value = self._DecodeValue(string_formatter, value_index, value_data)

      values.append(value)

      value_data_offset += value_data_size
      value_size_offset += 1

    return values

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

    context = dtfabric_data_maps.DataTypeMapContext()

    oversize_chunk = self._ReadStructureFromByteStream(
        chunk_data, data_offset, data_type_map, context=context)

    data_offset = context.byte_size
    data_size = data_offset + oversize_chunk.data_size
    oversize_chunk.values_data = chunk_data[data_offset:data_size]

    data_offset += oversize_chunk.data_size
    data_size = data_offset + oversize_chunk.private_data_size
    oversize_chunk.private_data = chunk_data[data_offset:data_size]

    return oversize_chunk

  def _ReadSimpleDumpChunkData(self, chunk_data, data_offset):
    """Reads SimpleDump chunk data.

    Args:
      chunk_data (bytes): SimpleDump chunk data.
      data_offset (int): offset of the SimpleDump chunk relative to the start
          of the chunk set.

    Yields:
      LogEntry: a log entry.

    Raises:
      ParseError: if the chunk cannot be read.
    """
    data_type_map = self._GetDataTypeMap('tracev3_simpledump_chunk')

    context = dtfabric_data_maps.DataTypeMapContext()

    simpledump_chunk = self._ReadStructureFromByteStream(
        chunk_data, data_offset, data_type_map, context=context)

    proc_id = (f'{simpledump_chunk.proc_id_upper:d}@'
               f'{simpledump_chunk.proc_id_lower:d}')
    process_information_entry = (
        self._catalog_process_information_entries.get(proc_id, None))
    if not process_information_entry:
      raise errors.ParseError((
          f'Unable to retrieve process information entry: {proc_id:s} from '
          f'catalog'))

    backtrace_frame = BacktraceFrame()
    backtrace_frame.image_identifier = simpledump_chunk.sender_image_identifier
    backtrace_frame.image_offset = simpledump_chunk.load_address

    process_image_identifier, process_image_path = (
        self._GetProcessImageValues(process_information_entry))

    log_entry = LogEntry()
    log_entry.backtrace_frames = [backtrace_frame]
    log_entry.boot_identifier = self._boot_identifier
    log_entry.event_message = simpledump_chunk.message_string
    log_entry.event_type = 'logEvent'
    log_entry.mach_timestamp = simpledump_chunk.continuous_time
    log_entry.message_type = self._LOG_TYPE_DESCRIPTIONS.get(
        simpledump_chunk.log_type, None)
    log_entry.process_identifier = getattr(
        process_information_entry, 'process_identifier', None) or 0
    log_entry.process_image_identifier = process_image_identifier
    log_entry.process_image_path = process_image_path
    log_entry.sub_system = simpledump_chunk.sub_system_string
    log_entry.sender_image_identifier = simpledump_chunk.sender_image_identifier
    # TODO: implement
    log_entry.sender_image_path = None
    log_entry.sender_program_counter = simpledump_chunk.load_address
    log_entry.thread_identifier = simpledump_chunk.thread_identifier
    log_entry.timestamp = self._GetTimestamp(simpledump_chunk.continuous_time)
    log_entry.trace_identifier = 0

    yield log_entry

  def _ReadStateDumpChunkData(self, chunk_data, data_offset):
    """Reads StateDump chunk data.

    Args:
      chunk_data (bytes): StateDump chunk data.
      data_offset (int): offset of the StateDump chunk relative to the start
          of the chunk set.

    Yields:
      LogEntry: a log entry.

    Raises:
      ParseError: if the chunk cannot be read.
    """
    data_type_map = self._GetDataTypeMap('tracev3_statedump_chunk')

    context = dtfabric_data_maps.DataTypeMapContext()

    statedump_chunk = self._ReadStructureFromByteStream(
        chunk_data, data_offset, data_type_map, context=context)

    proc_id = (f'{statedump_chunk.proc_id_upper:d}@'
               f'{statedump_chunk.proc_id_lower:d}')
    process_information_entry = (
        self._catalog_process_information_entries.get(proc_id, None))
    if not process_information_entry:
      raise errors.ParseError((
          f'Unable to retrieve process information entry: {proc_id:s} from '
          f'catalog'))

    event_message = ''
    if statedump_chunk.state_data_type == 0x03:
      library_data = statedump_chunk.library.split(b'\x00', maxsplit=1)[0]
      library = library_data.decode('utf8')

      decoder_type_data = statedump_chunk.decoder_type.split(
          b'\x00', maxsplit=1)[0]
      decoder_type = decoder_type_data.decode('utf8')

      decoder_name = f'{library:s}:{decoder_type:s}'
      decoder_class = self._FORMAT_STRING_DECODERS.get(decoder_name, None)
      if not decoder_class:
        value = f'<decode: unsupported decoder: {decoder_name:s}>'
      else:
        value = decoder_class.FormatValue(statedump_chunk.state_data)

      event_message = f'{statedump_chunk.title:s}\n{value:s}'

    activity_identifier = statedump_chunk.activity_identifier or 0

    backtrace_frame = BacktraceFrame()
    backtrace_frame.image_identifier = statedump_chunk.sender_image_identifier
    backtrace_frame.image_offset = 0

    process_image_identifier, process_image_path = (
        self._GetProcessImageValues(process_information_entry))

    log_entry = LogEntry()
    log_entry.activity_identifier = (
        activity_identifier & self.ACTIVITY_IDENTIFIER_BITMASK)
    log_entry.backtrace_frames = [backtrace_frame]
    log_entry.boot_identifier = self._boot_identifier
    log_entry.event_message = event_message
    log_entry.event_type = 'stateEvent'
    log_entry.mach_timestamp = statedump_chunk.continuous_time
    log_entry.process_identifier = getattr(
        process_information_entry, 'process_identifier', None) or 0
    log_entry.process_image_identifier = process_image_identifier
    log_entry.process_image_path = process_image_path
    log_entry.sender_image_identifier = statedump_chunk.sender_image_identifier
    log_entry.timestamp = self._GetTimestamp(statedump_chunk.continuous_time)
    log_entry.trace_identifier = 0

    yield log_entry

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

      lower_name = sub_file_entry.name.lower()
      if not lower_name.endswith('.timesync'):
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
          self._timesync_boot_record.timebase_numerator /
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
      if path_segments:
        lower_last_path_segment = path_segments[-1].lower()

    if not lower_last_path_segment.endswith('.logarchive'):
      path_segments.pop(-1)
      if path_segments:
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
        header_chunk.timebase_numerator / header_chunk.timebase_denominator)

    self._ReadTimesyncRecords(self._boot_identifier)

  def ReadLogEntries(self):
    """Reads log traces.

    Yields:
      LogEntry: a log entry.

    Raises:
      ParseError: if the file cannot be read.
    """
    if self._timesync_boot_record:
      boot_identifier_string = str(self._boot_identifier).upper()

      log_entry = LogEntry()
      log_entry.boot_identifier = self._boot_identifier
      log_entry.event_message = f'=== system boot: {boot_identifier_string:s}'
      log_entry.event_type = 'timesyncEvent'
      log_entry.mach_timestamp = 0
      log_entry.thread_identifier = 0
      log_entry.timestamp = self._timesync_boot_record.timestamp
      log_entry.trace_identifier = 0

      yield log_entry

    # TODO: generate timesyncEvent LogEntry
    # "=== log class: persist begins"
    # "=== log class: in-memory begins"
    # are these determined based on the base continuous time of the first
    # firehose chunk?

    for record in self._timesync_sync_records:
      boot_identifier_string = str(self._boot_identifier).upper()

      log_entry = LogEntry()
      log_entry.boot_identifier = self._boot_identifier
      log_entry.event_message = '=== system wallclock time adjusted'
      log_entry.event_type = 'timesyncEvent'
      log_entry.mach_timestamp = record.kernel_time
      log_entry.parent_activity_identifier = 0
      log_entry.thread_identifier = 0
      log_entry.timestamp = record.timestamp
      log_entry.trace_identifier = 0

      yield log_entry

    file_offset = self._file_object.tell()

    oversize_chunks = {}

    while file_offset < self._file_entry.size:
      chunk_header = self._ReadChunkHeader(self._file_object, file_offset)
      file_offset += 16

      if chunk_header.chunk_tag == self._CHUNK_TAG_CATALOG:
        self._catalog = self._ReadCatalog(self._file_object, file_offset)
        self._BuildCatalogProcessInformationEntries(self._catalog)

      elif chunk_header.chunk_tag == self._CHUNK_TAG_CHUNK_SET:
        yield from self._ReadChunkSet(
            self._file_object, file_offset, chunk_header, oversize_chunks)

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

    # TODO: extract timesync events

    tracev3_file = TraceV3File(file_system=file_system)

    try:
      tracev3_file.Open(file_entry)
    except errors.ParseError as exception:
      raise errors.WrongParser(
          'Unable to open tracev3 file with error: {0!s}'.format(exception))

    try:
      for log_entry in tracev3_file.ReadLogEntries():
        activity_identifier = log_entry.activity_identifier or 0

        event_data = UnifiedLoggingEventData()
        event_data.activity_identifier = (
            activity_identifier & tracev3_file.ACTIVITY_IDENTIFIER_BITMASK)
        event_data.boot_identifier = str(log_entry.boot_identifier).upper()
        event_data.category = log_entry.category
        event_data.event_message = log_entry.event_message
        event_data.event_type = log_entry.event_type
        event_data.message_type = log_entry.message_type
        event_data.process_identifier = log_entry.process_identifier
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
