"""Parser for Exchangeable Image File Format (EXIF) data in JPEG files."""

import struct

from datetime import datetime

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.parsers import interface
from plaso.parsers import manager
from plaso.containers import events
from plaso.lib import errors


class JpegExifEventData(events.EventData):
  """JPEG EXIF event data.

  Attributes:
    bodyserialnumber (TODO): Body serial number.
    exif_datetime (dfdatetime.DateTimeValues): exif datetime.
    image_height (TODO): image height.
    image_width (TODO): image width.
    latitude (TODO): Latitude.
    longitude (TODO): Longitude.
    makeandmodel (TODO): Make and model.
    manufacturer (TODO): Manufacturer/Make.
    model (TODO): Model.
    software (TODO): software.
    xres (float): X resolution.
    yres (float): Y resolution.
  """

  DATA_TYPE = 'jpeg:exif'

  def __init__(self):
    """Initializes event data."""
    super().__init__(data_type=self.DATA_TYPE)
    self.bodyserialnumber = None
    self.exif_datetime = None
    self.height = None
    self.latitude = None
    self.longitude = None
    self.makeandmodel = None
    self.manufacturer = None
    self.model = None
    self.software = None
    self.width = None
    self.xres = None
    self.yres = None


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

  def _ExtractInlineData(self, value_offset, tag_type, endian):
    """TODO.

    Args:
      value_offset (TODO): TODO.
      tag_type (TODO): TODO.
      endian (TODO): TODO.

    Returns:
      TODO: TODO.
    """
    if tag_type == 3:  # SHORT
      return struct.unpack(
          endian + 'H', struct.pack(endian + 'I', value_offset)[:2])[0]

    if tag_type == 4:  # LONG
      return struct.unpack(
          endian + 'I', struct.pack(endian + 'I', value_offset))[0]

    if tag_type == 1:  # BYTE
      return value_offset & 0xFF

    if tag_type == 2:  # ASCII
      return chr(value_offset & 0xFF)  # Interpret a single byte as ASCII

    return value_offset

  def _ExtractValue(self, data, offset, tag_type, count, endian):
    """TODO.

    Args:
      data (TODO): TODO.
      offset (TODO): TODO.
      tag_type (TODO): TODO.
      count (TODO): TODO.
      endian (TODO): TODO.

    Returns:
      TODO: TODO.
    """
    if tag_type == 1:  # BYTE
      return data[offset:offset+count]

    if tag_type == 2:  # ASCII
      return data[offset:offset+count].rstrip(b'\x00').decode('utf-8')

    if tag_type == 3:  # SHORT (2 bytes)
      return struct.unpack(endian + f'{count}H', data[offset:offset+count*2])

    if tag_type == 4:  # LONG (4 bytes)
      return struct.unpack(endian + f'{count}I', data[offset:offset+count*4])

    if tag_type == 5:  # RATIONAL (two LONGs: numerator/denominator)
      # Extract all LONGs (numerator/denominator pairs)
      raw_values = struct.unpack(
          endian + f'{count * 2}I', data[offset:offset + count * 8])
      # Convert to floats (numerator/denominator)
      return (
          [raw_values[i] / raw_values[i + 1]
          if raw_values[i + 1] != 0 else None
          for i in range(0, len(raw_values), 2)])

    return None

  # TODO: not used, remove?
  def _FormatValue(self, value, tag_type):
    """TODO.

    Args:
      value (TODO): TODO.
      tag_type (TODO): TODO.

    Returns:
      TODO: TODO.
    """
    if tag_type == 2:  # ASCII
      return value if isinstance(value, str) else ''.join(map(chr, value))

    if tag_type in (3, 4):  # SHORT or LONG
      return value# if count > 1 else value[0]

    if tag_type == 5:  # RATIONAL
      return [f'{num}/{den}' for num, den in value]

    return value

  def _ParseExif(self, file_object):
    """TODO.

    Args:
      file_object (dfvfs.FileIO): a file-like object.

    Returns:
      TODO: TODO.
    """
    data = file_object.read()

    # Verify JPEG SOI marker
    if data[:2] != b'\xFF\xD8':
      raise ValueError('Not a valid JPEG file')

    # Look for APP1 (Exif) marker
    offset = 2
    while offset < len(data):
      marker, length = struct.unpack('>2sH', data[offset:offset+4])
      if marker == b'\xFF\xE1':  # APP1 marker
        exif_data = data[offset+4:offset+4+length-2]  # Skip the marker length
        if exif_data[:6] == b'Exif\x00\x00':
          return self._ParseTiff(exif_data[6:])
      offset += length + 2

    raise ValueError('Exif data not found')

  def _ParseIfd(self, data, offset, endian, base_offset):
    """TODO.

    Args:
      data (TODO): TODO.
      offset (TODO): TODO.
      endian (TODO): TODO.
      base_offset (TODO): TODO.

    Returns:
      TODO: TODO.
    """
    # Number of directory entries
    num_entries = struct.unpack(endian + 'H', data[offset:offset+2])[0]
    entries = {}
    for i in range(num_entries):
      entry_offset = offset + 2 + i * 12
      tag, tag_type, count, value_offset = struct.unpack(
          endian + 'HHII', data[entry_offset:entry_offset+12])

      # Interpret the value based on the tag type
      absolute_offset = base_offset + value_offset
      # short strings! they are inline after the entry offset values
      if tag_type == 2 and count * self._GetSizeOfType(tag_type) <= 4:
        value_data = data[entry_offset+8:entry_offset+8+count]
        value = value_data.rstrip(b'\x00').decode('ascii','ignore')

      elif count * self._GetSizeOfType(tag_type) <= 4:  # other inline data
        value = self._ExtractInlineData(value_offset, tag_type, endian)

      else:  # Normal data at offset
        value = self._ExtractValue(
            data, absolute_offset, tag_type, count, endian)
        if tag in (0x0002, 0x0004):
          # gps latlon, convert from deg/min/sec to decimal degrees
          value = value[0] + value[1] / 60.0 + value[2] / 3600.0
        elif count==1:
          value=value[0]

      # Check for subdirectories (ExifIFDPointer, GPSInfo)
      if tag in (0x8769, 0x8825):  # Subdirectory pointers
        sub_ifd = self._ParseIfd(
            data, base_offset + value_offset, endian, base_offset)
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
      endian = '<'
    elif endianness == b'MM':  # Big endian
      endian = '>'
    else:
      raise ValueError('Invalid TIFF header')

    # Verify TIFF magic number
    magic_number = struct.unpack(endian + 'H', data[2:4])[0]
    if magic_number != 0x002A:
      raise ValueError('Invalid TIFF magic number')

    # Get offset to first IFD (Image File Directory)
    ifd_offset = struct.unpack(endian + 'I', data[4:8])[0]

    # Parse IFD
    return self._ParseIfd(data, ifd_offset, endian, base_offset=0)

  def _GetSizeOfType(self, tag_type):
    """TODO.

    Args:
      tag_type (TODO): TODO.

    Returns:
      TODO: TODO.
    """
    # BYTE, ASCII, SHORT, LONG, RATIONAL
    sizes = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8}
    return sizes.get(tag_type, 0)

  def _ExtractExifMetadata(self, file_object):
    """Extracts EXIF metadata.

    Args:
      file_object (dfvfs.FileIO): a file-like object.

    Returns:
      TODO: TODO
    """
    return self._GetAnnotatedExif(self._ParseExif(file_object))

  def _BuildEventData(self, annotated_exif):
    """TODO.

    Args:
      annotated_exif (TODO): TODO.

    Returns:
      JpegExifEventData: event data.
    """
    event_data = JpegExifEventData()

    key = 'Date and Time'
    if key in annotated_exif.keys():
      ts = str(annotated_exif.get(key))
      dt = datetime.strptime(ts, '%Y:%m:%d %H:%M:%S')
      posix_timestamp = int(dt.timestamp())
      event_data.exif_datetime = dfdatetime_posix_time.PosixTime(
          timestamp=posix_timestamp)

    event_data.bodyserialnumber = annotated_exif.get('Body Serial Number')
    event_data.height = annotated_exif.get('Image Height')
    event_data.makeandmodel = annotated_exif.get('Make and Model')
    event_data.manufacturer = annotated_exif.get('Manufacturer')
    event_data.model = annotated_exif.get('Model')
    event_data.software = annotated_exif.get('Software')
    event_data.width = annotated_exif.get('Image Width')
    event_data.xres = annotated_exif.get('X-Resolution')
    event_data.yres = annotated_exif.get('Y-Resolution')

    latitude = annotated_exif.get('Latitude', 0.0)
    latitude_reference = annotated_exif.get('Latitude Reference', '')
    longitude = annotated_exif.get('Longitude', 0.0)
    longitude_reference = annotated_exif.get('Longitude Reference', '')

    event_data.latitude = f'{latitude:2.5f}{latitude_reference:s}'
    event_data.longitude = f'{longitude:2.5f}{longitude_reference:s}'

    return event_data

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a JPEG file for EXIF data.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    try:
      parsed_jpeg_exif = self._ExtractExifMetadata(file_object)
    except ValueError as exception:
      raise errors.WrongParser(
          f'Unable to parse a JPEG file with error: {exception!s}')

    event_data = self._BuildEventData(parsed_jpeg_exif)
    parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(JpegExifParser)
