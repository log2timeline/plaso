"""Parser for Exchangeable Image File Format (EXIF) data in JPEG files."""

import struct
import os

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class JpegExifEventData(events.EventData):
  """JPEG EXIF event data.

  Attributes:
    body_serial_number (str): Body serial number.
    exif_datetime (dfdatetime.DateTimeValues): exif datetime.
    height (int): image height.
    latitude (str): Latitude.
    longitude (str): Longitude.
    make_and_model (str): Make and model.
    manufacturer (str): Manufacturer/Make.
    model (str): Model.
    software (str): software.
    width (int): image width.
    x_resolution (float): X resolution.
    y_resolution (float): Y resolution.
  """

  DATA_TYPE = 'jpeg:exif'

  def __init__(self):
    """Initializes event data."""
    super().__init__(data_type=self.DATA_TYPE)
    self.body_serial_number = None
    self.exif_datetime = None
    self.height = None
    self.latitude = None
    self.longitude = None
    self.make_and_model = None
    self.manufacturer = None
    self.model = None
    self.software = None
    self.width = None
    self.x_resolution = None
    self.y_resolution = None


class JpegExifParser(interface.FileObjectParser):
  """Parser for JPEG EXIF data"""

  NAME='jpeg_exif'
  DATA_FORMAT = 'JPEG file'

  _EXIF_TAGS = {
      0x0000: 'GPS Tag Version',
      0x0001: 'Latitude Reference',
      0x0002: 'Latitude',
      0x0003: 'Longitude Reference',
      0x0004: 'Longitude',
      0x0005: 'Altitude Reference',
      0x0006: 'Altitude',
      0x0009: 'GPS Receiver Status',
      0x0012: 'Geodetic Survey Data',
      0x0100: 'Image Width',
      0x0101: 'Image Height',
      0x0102: 'Bits per Sample',
      0x0103: 'Compression',
      0x0106: 'Photometric Interpre',
      0x010f: 'Manufacturer',
      0x0110: 'Model',
      0x0112: 'Orientation',
      0x0115: 'Samples per Pixel',
      0x011a: 'X-Resolution',
      0x011b: 'Y-Resolution',
      0x011c: 'Planar Configuration',
      0x0128: 'Resolution Unit',
      0x0131: 'Software',
      0x0132: 'Date and Time',
      0x014a: 'SubIFD Offsets',
      0x02bc: 'XML Packet',
      0x829a: 'Exposure Time',
      0x829d: 'F-Number',
      0x8822: 'Exposure Program',
      0x8827: 'ISO Speed Ratings',
      0x9000: 'Exif Version',
      0x9003: 'Date and Time',
      0x9004: 'Date and Time (modified)',
      0x9204: 'Exposure Bias',
      0x9205: 'Maximum Aperture Val',
      0x9207: 'Metering Mode',
      0x9208: 'Light Source',
      0x9209: 'Flash',
      0x920a: 'Focal Length',
      0xa000: 'FlashPixVersion',
      0xa001: 'Color Space',
      0xa300: 'File Source',
      0xa301: 'Scene Type',
      0xa402: 'Exposure Mode',
      0xa403: 'White Balance',
      0xa404: 'Digital Zoom Ratio',
      0xa405: 'Focal Length in 35mm',
      0xa406: 'Scene Capture Type',
      0xa407: 'Gain Control',
      0xa408: 'Contrast',
      0xa409: 'Saturation',
      0xa40a: 'Sharpness',
      0xa431: 'Body Serial Number',
      0xa432: 'Lens Specification',
      0xc614: 'Make and Model',
      0xc62f: 'Body Serial Number'}

  _TAG_TYPE_BYTE = 1
  _TAG_TYPE_ASCII = 2
  _TAG_TYPE_SHORT = 3
  _TAG_TYPE_LONG = 4
  _TAG_TYPE_RATIONAL = 5

  _BYTE_SIZE_PER_TAG_TYPE = {
      _TAG_TYPE_BYTE: 1,
      _TAG_TYPE_ASCII: 1,
      _TAG_TYPE_SHORT: 2,
      _TAG_TYPE_LONG: 4,
      _TAG_TYPE_RATIONAL: 8}

  def _GetAnnotatedExif(self, values):
    """TODO.

    Args:
      values (TODO): TODO.

    Returns:
      TODO: TODO.
    """
    r = {}
    for tag, value in values.items():
      tag_name = self._EXIF_TAGS.get(tag, f'Unknown tag ({hex(tag)})')
      if tag_name == 'XML Packet':
        continue
      r[tag_name] = value
    return r

  def _ExtractInlineData(self, value_offset, tag_type, byte_order):
    """Extracts inline data.

    Args:
      value_offset (TODO): TODO.
      tag_type (int): tag type.
      byte_order (str): struct byte-order indicator.

    Returns:
      int: value.
    """
    if tag_type == self._TAG_TYPE_SHORT:
      value_data = struct.pack(f'{byte_order:s}I', value_offset)
      return struct.unpack(f'{byte_order:s}H', value_data[:2])[0]

    if tag_type == self._TAG_TYPE_LONG:
      value_data = struct.pack(f'{byte_order:s}I', value_offset)
      return struct.unpack(f'{byte_order:s}I', value_data)[0]

    if tag_type == self._TAG_TYPE_BYTE:
      return value_offset & 0xFF

    if tag_type == self._TAG_TYPE_ASCII:
      return chr(value_offset & 0xFF)  # Interpret a single byte as ASCII

    return value_offset

  def _ExtractValue(self, data, offset, tag_type, count, byte_order):
    """TODO.

    Args:
      data (TODO): TODO.
      offset (TODO): TODO.
      tag_type (TODO): TODO.
      count (int): number of values.
      byte_order (str): struct byte-order indicator.

    Returns:
      TODO: TODO.
    """
    if tag_type == self._TAG_TYPE_BYTE:
      return data[offset:offset+count]

    if tag_type == self._TAG_TYPE_ASCII:
      end_offset = offset + count
      # TODO: catch UnicodeDecodeError
      return data[offset:end_offset].rstrip(b'\x00').decode('utf-8')

    if tag_type == self._TAG_TYPE_SHORT:
      end_offset = offset + (count * 2)
      return struct.unpack(f'{byte_order:s}{count:d}H', data[offset:end_offset])

    if tag_type == self._TAG_TYPE_LONG:
      end_offset = offset + (count * 4)
      return struct.unpack(f'{byte_order:s}{count:d}I', data[offset:end_offset])

    if tag_type == self._TAG_TYPE_RATIONAL:
      # A rational consist of 2 LONG values: numerator and denominator
      # Extract all LONGs (numerator/denominator pairs)
      end_offset = offset + (count * 8)
      raw_values = struct.unpack(
          f'{byte_order:s}{count * 2}I', data[offset:end_offset])

      # Convert to floats (numerator/denominator)
      return [
          raw_values[i] / raw_values[i + 1]
          if raw_values[i + 1] != 0 else None
          for i in range(0, len(raw_values), 2)]

    return None

  def _ParseExif(self, file_object):
    """Extracts EXIF data.

    Args:
      file_object (dfvfs.FileIO): a file-like object.

    Returns:
      TODO: TODO.

    Raises:
      ValueError: if the EXIF data could not be extracted.
    """
    # TODO: this can fill the memory if the file is too large.
    data = file_object.read()
    data_size = len(data)

    # Look for APP1 (Exif) marker
    offset = 2
    while offset < data_size:
      end_offset = offset + 4
      marker, length = struct.unpack('>2sH', data[offset:end_offset])

      if marker == b'\xFF\xE1':  # APP1 marker
        exif_data = data[offset+4:offset+4+length-2]  # Skip the marker length
        if exif_data[:6] == b'Exif\x00\x00':
          return self._ParseTiff(exif_data[6:])

      offset += length + 2

    raise ValueError('Exif data not found')

  def _ParseIfd(self, data, offset, byte_order, base_offset):
    """TODO.

    Args:
      data (TODO): TODO.
      offset (TODO): TODO.
      byte_order (str): struct byte-order indicator.
      base_offset (TODO): TODO.

    Returns:
      TODO: TODO.
    """
    # Number of directory entries
    end_offset = offset + 2
    num_entries = struct.unpack(f'{byte_order:s}H', data[offset:end_offset])[0]
    entries = {}
    for i in range(num_entries):
      entry_offset = offset + 2 + i * 12
      end_offset = entry_offset + 12
      tag, tag_type, count, value_offset = struct.unpack(
          f'{byte_order:s}HHII', data[entry_offset:end_offset])

      # Interpret the value based on the tag type
      absolute_offset = base_offset + value_offset
      # short strings! they are inline after the entry offset values

      # TODO: tracker parser warning if tag type not supported.
      byte_size = self._BYTE_SIZE_PER_TAG_TYPE.get(tag_type, 0)

      if tag_type == 2 and count * byte_size <= 4:
        value_data = data[entry_offset+8:entry_offset+8+count]
        value = value_data.rstrip(b'\x00').decode('ascii','ignore')

      elif count * byte_size <= 4:  # other inline data
        value = self._ExtractInlineData(value_offset, tag_type, byte_order)

      else:  # Normal data at offset
        value = self._ExtractValue(
            data, absolute_offset, tag_type, count, byte_order)
        if tag in (0x0002, 0x0004):
          # gps latlon, convert from deg/min/sec to decimal degrees
          value = value[0] + value[1] / 60.0 + value[2] / 3600.0
        elif count==1:
          value=value[0]

      # Check for subdirectories (ExifIFDPointer, GPSInfo)
      if tag in (0x8769, 0x8825):  # Subdirectory pointers
        sub_ifd = self._ParseIfd(
            data, base_offset + value_offset, byte_order, base_offset)
        entries.update(sub_ifd)
      else:
        entries[tag] = value

    return entries

  def _ParseTiff(self, data):
    """TODO.

    Args:
      data (TODO): TODO.

    Returns:
      TODO: TODO.
    """
    # Verify TIFF header
    endianness = data[:2]
    if endianness == b'II':  # Little endian
      byte_order = '<'
    elif endianness == b'MM':  # Big endian
      byte_order = '>'
    else:
      raise ValueError('Invalid TIFF header')

    # Verify TIFF magic number
    magic_number = struct.unpack(f'{byte_order:s}H', data[2:4])[0]
    if magic_number != 0x002A:
      raise ValueError('Invalid TIFF magic number')

    # Get offset to first IFD (Image File Directory)
    ifd_offset = struct.unpack(f'{byte_order:s}I', data[4:8])[0]

    return self._ParseIfd(data, ifd_offset, byte_order, 0)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a JPEG file for EXIF data.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    if file_object.read(2) != b'\xff\xd8':
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser(
          f'[{self.NAME!s}] {display_name!s} is not a JPEG file.')

    file_object.seek(0, os.SEEK_SET)

    try:
      exif_data = self._ParseExif(file_object)
    except ValueError as exception:
      raise errors.WrongParser(
          f'Unable to parse a JPEG file with error: {exception!s}')

    annotated_exif = self._GetAnnotatedExif(exif_data)

    event_data = JpegExifEventData()

    latitude = annotated_exif.get('Latitude', 0.0)
    latitude_reference = annotated_exif.get('Latitude Reference', '')
    longitude = annotated_exif.get('Longitude', 0.0)
    longitude_reference = annotated_exif.get('Longitude Reference', '')

    event_data.body_serial_number = annotated_exif.get('Body Serial Number')
    event_data.height = annotated_exif.get('Image Height')
    event_data.latitude = f'{latitude:2.5f}{latitude_reference:s}'
    event_data.longitude = f'{longitude:2.5f}{longitude_reference:s}'
    event_data.make_and_model = annotated_exif.get('Make and Model')
    event_data.manufacturer = annotated_exif.get('Manufacturer')
    event_data.model = annotated_exif.get('Model')
    event_data.software = annotated_exif.get('Software')
    event_data.width = annotated_exif.get('Image Width')
    event_data.x_resolution = annotated_exif.get('X-Resolution')
    event_data.y_resolution = annotated_exif.get('Y-Resolution')

    time_string = annotated_exif.get('Date and Time')
    if time_string:
      date, time = time_string.split(' ')
      year, month, day_of_month = [int(value, 10) for value in date.split(':')]
      hours, minutes, seconds = [int(value, 10) for value in time.split(':')]

      try:
        date_time = dfdatetime_time_elements.TimeElements(time_elements_tuple=(
            year, month, day_of_month, hours, minutes, seconds))
        event_data.exif_datetime = date_time
      except (TypeError, ValueError) as exception:
        error_string = (
            f'Unable to parse date time value with error: {exception!s}')
        parser_mediator.ProduceExtractionWarning(error_string)

    parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(JpegExifParser)
