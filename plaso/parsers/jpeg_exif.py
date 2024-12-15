# -*- coding: utf-8 -*-
"""Parser for JPG exif data."""

from plaso.parsers import interface
from plaso.parsers import manager
from plaso.containers import events

from datetime import datetime
from dfdatetime import posix_time as dfdatetime_posix_time

import struct # for inline exif parser

# Mapping of Exif tag IDs to human-readable names


class JpegExifEventData(events.EventData):
  """JPEG EXIF event data.

  Attributes:
    exif_datetime (dfdatetime.DateTimeValues): exif datetime
    image_width: image width
    image_height: image height
    software: software
    xres: X resolution
    yres: Y resolution
    manufacturer: Manufacturer/Make
    model: Model
    latitude: Latitude
    longitude: Longitude
    bodyserialnumber: Body serial number
  """
  
  DATA_TYPE = 'jpeg:exif'
  
  def __init__(self):
    """Initializes a JpegExif event data."""
    super(JpegExifEventData, self).__init__(data_type=self.DATA_TYPE)
    self.exif_datetime = None
    self.width = None
    self.height = None
    self.software = None
    self.xres = None
    self.yres = None
    self.manufacturer = None
    self.model = None
    self.latitude = None
    self.longitude = None
    self.bodyserialnumber = None

    
class JpegExifParser(interface.FileObjectParser):
  """Parser for JPEG EXIF data"""

  NAME='jpeg_exif'
  DATA_FORMAT = 'JPEG file'

  def _ExtractExifMetadata(self, file_object):
    """Parses EXIF metadata embedded in a JPEG file. Returns a dictionary of the values found."""
    exiftags = {
      0x0100: "Image Width",
      0x0101: "Image Height",
      0x0102: "Bits per Sample",
      0x0103: "Compression",
      0x0106: "Photometric Interpre",
      0x010f: "Manufacturer",
      0x0110: "Model",
      0x0112: "Orientation",
      0x0115: "Samples per Pixel",
      0x011a: "X-Resolution",
      0x011b: "Y-Resolution",
      0x011c: "Planar Configuration",
      0x0128: "Resolution Unit",
      0x0131: "Software",
      0x0132: "Date and Time",
      0x014a: "SubIFD Offsets",
      0x02bc: "XML Packet",
      0x829a: "Exposure Time",
      0x829d: "F-Number",
      0x8822: "Exposure Program",
      0x8827: "ISO Speed Ratings",
      0x9000: "Exif Version",
      0x9003: "Date and Time",
      0x9004: "Date and Time (modified)",
      0x9204: "Exposure Bias",
      0x9205: "Maximum Aperture Val",
      0x9207: "Metering Mode",
      0x9208: "Light Source",
      0x9209: "Flash",
      0x920a: "Focal Length",
      0xa300: "File Source",
      0xa301: "Scene Type",
      0xa402: "Exposure Mode",
      0xa403: "White Balance",
      0xa404: "Digital Zoom Ratio",
      0xa405: "Focal Length in 35mm",
      0xa406: "Scene Capture Type",
      0xa407: "Gain Control",
      0xa408: "Contrast",
      0xa409: "Saturation",
      0xa40a: "Sharpness",
      0xa431: "Body Serial Number",
      0xa432: "Lens Specification",
      0xa000: "FlashPixVersion",
      0xa001: "Color Space",
      0x0000: "GPS Tag Version",
      0x0001: "Latitude Reference",
      0x0002: "Latitude",
      0x0003: "Longitude Reference",
      0x0004: "Longitude",
      0x0005: "Altitude Reference",
      0x0006: "Altitude",
      0x0009: "GPS Receiver Status",
      0x0012: "Geodetic Survey Data",
      0xc62f: "Body Serial Number",
      0xc614: "Make and Model"
    }

    def parse_exif(file_object):
      data = file_object.read()

      # Verify JPEG SOI marker
      if data[:2] != b'\xFF\xD8':
        raise ValueError("Not a valid JPEG file")

      # Look for APP1 (Exif) marker
      offset = 2
      while offset < len(data):
        marker, length = struct.unpack(">2sH", data[offset:offset+4])
        if marker == b'\xFF\xE1':  # APP1 marker
          exif_data = data[offset+4:offset+4+length-2]  # Skip the marker length
          if exif_data[:6] == b'Exif\x00\x00':
            return parse_tiff(exif_data[6:])
        offset += length + 2

      raise ValueError("Exif data not found")

    def parse_tiff(data):
      # Verify TIFF header
      endianness = data[:2]
      if endianness == b'II':  # Little endian
        endian = "<"
      elif endianness == b'MM':  # Big endian
        endian = ">"
      else:
        raise ValueError("Invalid TIFF header")

      # Verify TIFF magic number
      magic_number = struct.unpack(endian + "H", data[2:4])[0]
      if magic_number != 0x002A:
        raise ValueError("Invalid TIFF magic number")

      # Get offset to first IFD (Image File Directory)
      ifd_offset = struct.unpack(endian + "I", data[4:8])[0]

      # Parse IFD
      return parse_ifd(data, ifd_offset, endian, base_offset=0)

    def parse_ifd(data, offset, endian, base_offset):
      # Number of directory entries
      num_entries = struct.unpack(endian + "H", data[offset:offset+2])[0]
      entries = {}
      for i in range(num_entries):
        entry_offset = offset + 2 + i * 12
        tag, tag_type, count, value_offset = struct.unpack(endian + "HHII", data[entry_offset:entry_offset+12])

        # Interpret the value based on the tag type
        absolute_offset = base_offset + value_offset
        # short strings! they are inline after the entry offset values
        if tag_type == 2 and count * size_of_type(tag_type) <= 4:
          value = data[entry_offset+8:entry_offset+8+count].rstrip(b'\x00').decode('ascii','ignore')
        elif count * size_of_type(tag_type) <= 4:  # other inline data
          value = extract_inline_data(value_offset, tag_type, endian)
        else:  # Normal data at offset
          value = extract_value(data, absolute_offset, tag_type, count, endian)
          if tag == 0x0002 or tag == 0x0004 : #gps latlon, convert from deg/min/sec to decimal degrees
            value = value[0] + value[1] / 60.0 + value[2] / 3600.0
          elif count==1:
            value=value[0]

        # Check for subdirectories (ExifIFDPointer, GPSInfo)
        if tag == 0x8769 or tag == 0x8825:  # Subdirectory pointers
          sub_ifd = parse_ifd(data, base_offset + value_offset, endian, base_offset)
          entries.update(sub_ifd)
        else:
          entries[tag] = value

      return entries

    def size_of_type(tag_type):
      sizes = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8}  # BYTE, ASCII, SHORT, LONG, RATIONAL
      return sizes.get(tag_type, 0)

    def extract_inline_data(value_offset, tag_type, endian):
      if tag_type == 3:  # SHORT
        return struct.unpack(endian + "H", struct.pack(endian + "I", value_offset)[:2])[0]
      elif tag_type == 4:  # LONG
        return struct.unpack(endian + "I", struct.pack(endian + "I", value_offset))[0]
      elif tag_type == 1:  # BYTE
        return value_offset & 0xFF
      elif tag_type == 2:  # ASCII
        return chr(value_offset & 0xFF)  # Interpret a single byte as ASCII
      return value_offset

    def format_value(tag, value, tag_type, count, endian):
      if tag_type == 2:  # ASCII
        return value if isinstance(value, str) else "".join(map(chr, value))
      elif tag_type == 3 or tag_type == 4:  # SHORT or LONG
        return value# if count > 1 else value[0]
      elif tag_type == 5:  # RATIONAL
        return [f"{num}/{den}" for num, den in value]
      return value

    def extract_value(data, offset, tag_type, count, endian):
      if tag_type == 1:  # BYTE
        return data[offset:offset+count]
      elif tag_type == 2:  # ASCII
        return data[offset:offset+count].rstrip(b'\x00').decode('utf-8')
      elif tag_type == 3:  # SHORT (2 bytes)
        return struct.unpack(endian + f"{count}H", data[offset:offset+count*2])
      elif tag_type == 4:  # LONG (4 bytes)
        return struct.unpack(endian + f"{count}I", data[offset:offset+count*4])
      elif tag_type == 5:  # RATIONAL (two LONGs: numerator/denominator)
        # Extract all LONGs (numerator/denominator pairs)
        raw_values = struct.unpack(endian + f"{count * 2}I", data[offset:offset + count * 8])
        # Convert to floats (numerator/denominator)
        return [raw_values[i] / raw_values[i + 1] if raw_values[i + 1] != 0 else None for i in range(0, len(raw_values), 2)]
      return None

    def annotated_exif(values):
      r = {}
      for tag, value in values.items():
        tag_name = exiftags.get(tag, f"Unknown tag ({hex(tag)})")
        if tag_name == 'XML Packet':continue
        r[tag_name] = value
      return r

    return annotated_exif(parse_exif(file_object))

  def _BuildEventData(self, annotated_exif):
    event_data = JpegExifEventData()
    
    key = 'Date and Time'
    if key in annotated_exif.keys():
      ts = str(annotated_exif.get(key))
      dt = datetime.strptime(ts, "%Y:%m:%d %H:%M:%S")
      posix_timestamp = int(dt.timestamp())
      event_data.exif_datetime = dfdatetime_posix_time.PosixTime(timestamp=posix_timestamp)
    event_data.makeandmodel = annotated_exif.get('Make and Model', 'Unknown')
    event_data.manufacturer = annotated_exif.get('Manufacturer', 'Unknown')
    event_data.model = str(annotated_exif.get('Model'))
    event_data.xres = str(annotated_exif.get('X-Resolution'))
    event_data.yres = str(annotated_exif.get('Y-Resolution'))
    event_data.width = annotated_exif.get('Image Width')
    event_data.height = annotated_exif.get('Image Height')
    event_data.software = str(annotated_exif.get('Software'))
    event_data.bodyserialnumber = str(annotated_exif.get('Body Serial Number'))
    event_data.latitude = "%2.5f%s"%(annotated_exif.get('Latitude', 0.0),
                                     annotated_exif.get('Latitude Reference',''))
    event_data.longitude = "%2.5f%s"%(annotated_exif.get('Longitude', 0.0),
                                      annotated_exif.get('Longitude Reference', ''))
    return event_data
  
  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a JPEG file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_object (dfvfx.FileIO): file-like object to be parsed.

    Raises:
      WrongParser: ...
    """

    parsed_jpeg_exif = self._ExtractExifMetadata(file_object)
    event_data = self._BuildEventData(parsed_jpeg_exif)
    parser_mediator.ProduceEventData(event_data)

manager.ParsersManager.RegisterParser(JpegExifParser)

