# -*- coding: utf-8 -*-
"""Parser For DJI Mavic Drone Log Files."""
import re
import struct

from dfdatetime import time_elements as dfdatetime_time_elements


from plaso.parsers import interface
from plaso.parsers import manager
from plaso.containers import events
from plaso.lib import errors


class DJIDroneLogEventData(events.EventData):
  """DJI Drone Log Event Data"""

  DATA_TYPE = 'drone:dji:mavic'

  def __init__(self):
    """Initializes the DJI drone log event data container.

    This container is used to store parsed data fields from each GPS log record.
    """
    super(DJIDroneLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.timestamp = None
    self.longitude = None
    self.latitude = None
    self.height = None
    self.x_velocity = None
    self.y_velocity = None
    self.z_velocity = None


class DJIDroneLogParser(interface.FileObjectParser):
  """Parser for DJI Drone Dat Files."""
  NAME = 'dji_logfile'
  DATA_FORMAT = 'DJI Mavic log file'

  def __init__(self):
    """Initializes the DJI drone log file parser.

    Sets up default values for parsing data and record start position.
    """
    super(DJIDroneLogParser, self).__init__()
    self.data = None
    self.record_start_pos = None
  # Polinomial 0x1021
  crc_table = [0x0000, 0x1189, 0x2312, 0x329B, 0x4624, 0x57AD, 0x6536, 0x74BF,
               0x8C48, 0x9DC1, 0xAF5A, 0xBED3, 0xCA6C, 0xDBE5, 0xE97E, 0xF8F7,
               0x1081, 0x0108, 0x3393, 0x221A, 0x56A5, 0x472C, 0x75B7, 0x643E,
               0x9CC9, 0x8D40, 0xBFDB, 0xAE52, 0xDAED, 0xCB64, 0xF9FF, 0xE876,
               0x2102, 0x308B, 0x0210, 0x1399, 0x6726, 0x76AF, 0x4434, 0x55BD,
               0xAD4A, 0xBCC3, 0x8E58, 0x9FD1, 0xEB6E, 0xFAE7, 0xC87C, 0xD9F5,
               0x3183, 0x200A, 0x1291, 0x0318, 0x77A7, 0x662E, 0x54B5, 0x453C,
               0xBDCB, 0xAC42, 0x9ED9, 0x8F50, 0xFBEF, 0xEA66, 0xD8FD, 0xC974,
               0x4204, 0x538D, 0x6116, 0x709F, 0x0420, 0x15A9, 0x2732, 0x36BB,
               0xCE4C, 0xDFC5, 0xED5E, 0xFCD7, 0x8868, 0x99E1, 0xAB7A, 0xBAF3,
               0x5285, 0x430C, 0x7197, 0x601E, 0x14A1, 0x0528, 0x37B3, 0x263A,
               0xDECD, 0xCF44, 0xFDDF, 0xEC56, 0x98E9, 0x8960, 0xBBFB, 0xAA72,
               0x6306, 0x728F, 0x4014, 0x519D, 0x2522, 0x34AB, 0x0630, 0x17B9,
               0xEF4E, 0xFEC7, 0xCC5C, 0xDDD5, 0xA96A, 0xB8E3, 0x8A78, 0x9BF1,
               0x7387, 0x620E, 0x5095, 0x411C, 0x35A3, 0x242A, 0x16B1, 0x0738,
               0xFFCF, 0xEE46, 0xDCDD, 0xCD54, 0xB9EB, 0xA862, 0x9AF9, 0x8B70,
               0x8408, 0x9581, 0xA71A, 0xB693, 0xC22C, 0xD3A5, 0xE13E, 0xF0B7,
               0x0840, 0x19C9, 0x2B52, 0x3ADB, 0x4E64, 0x5FED, 0x6D76, 0x7CFF,
               0x9489, 0x8500, 0xB79B, 0xA612, 0xD2AD, 0xC324, 0xF1BF, 0xE036,
               0x18C1, 0x0948, 0x3BD3, 0x2A5A, 0x5EE5, 0x4F6C, 0x7DF7, 0x6C7E,
               0xA50A, 0xB483, 0x8618, 0x9791, 0xE32E, 0xF2A7, 0xC03C, 0xD1B5,
               0x2942, 0x38CB, 0x0A50, 0x1BD9, 0x6F66, 0x7EEF, 0x4C74, 0x5DFD,
               0xB58B, 0xA402, 0x9699, 0x8710, 0xF3AF, 0xE226, 0xD0BD, 0xC134,
               0x39C3, 0x284A, 0x1AD1, 0x0B58, 0x7FE7, 0x6E6E, 0x5CF5, 0x4D7C,
               0xC60C, 0xD785, 0xE51E, 0xF497, 0x8028, 0x91A1, 0xA33A, 0xB2B3,
               0x4A44, 0x5BCD, 0x6956, 0x78DF, 0x0C60, 0x1DE9, 0x2F72, 0x3EFB,
               0xD68D, 0xC704, 0xF59F, 0xE416, 0x90A9, 0x8120, 0xB3BB, 0xA232,
               0x5AC5, 0x4B4C, 0x79D7, 0x685E, 0x1CE1, 0x0D68, 0x3FF3, 0x2E7A,
               0xE70E, 0xF687, 0xC41C, 0xD595, 0xA12A, 0xB0A3, 0x8238, 0x93B1,
               0x6B46, 0x7ACF, 0x4854, 0x59DD, 0x2D62, 0x3CEB, 0x0E70, 0x1FF9,
               0xF78F, 0xE606, 0xD49D, 0xC514, 0xB1AB, 0xA022, 0x92B9, 0x8330,
               0x7BC7, 0x6A4E, 0x58D5, 0x495C, 0x3DE3, 0x2C6A, 0x1EF1, 0x0F78]

  def CheckSum(self, data):
    """Calculates CRC checksum using a predefined CRC-CCITT table.

    Args:
      data (bytes): the data block for which CRC is calculated.

    Returns:
      int: the 16-bit CRC checksum.
    """

    v = 13970
    for i in data:
      v = (v >> 8) ^ DJIDroneLogParser.crc_table[(i ^ v) & 0xFF]
    return v

  def FindNext(self, start):
    """Finds the next possible record start (byte 0x55) in the binary log.

    Args:
      start (int): the start position to begin searching.

    Returns:
      int: the position of the next record start, or -1 if not found.
    """

    pos = self.data[start:].index(0x55) if 0x55 in self.data[start:] else -1
    return start + pos if pos != -1 else -1

  def ParseRecords(self):
    """Parses all valid records from the binary log data.

    Returns:
      list[list]: A list of records. Each record is a list containing:
        - start position
        - length
        - ticket number
        - record type
    """

    record_list = []

    cur_pos = self.record_start_pos
    while True:
      if cur_pos >= len(self.data):
        break

      if self.data[cur_pos] != 0x55:
        cur_pos += 1
        cur_pos = self.FindNext(cur_pos)
        if cur_pos == -1:
          break
        continue

      record_len = self.data[cur_pos + 1]

      if record_len < 10 or cur_pos + record_len > len(self.data):
        cur_pos += 2
        cur_pos = self.FindNext(cur_pos)
        if cur_pos == -1:
          break
        continue

      crc = self.CheckSum(self.data[cur_pos:cur_pos
                                    + record_len - 2])

      if crc & 0xFF != self.data[cur_pos + record_len - 2] or crc >> 8 \
              != self.data[cur_pos + record_len - 1]:
        cur_pos += record_len
        cur_pos = self.FindNext(cur_pos)
        if cur_pos == -1:
          break
        continue

      record_list.append([cur_pos,  # Current Position
                          record_len,  # Record Length
                          struct.unpack("<I", self.data
                                        [cur_pos + 6:cur_pos + 10])
                          [0],  # Ticket Number
                          (self.data[cur_pos + 5] << 8)
                          + self.data[cur_pos + 4]])  # Type

      cur_pos = cur_pos + record_len

    return record_list

  def ParseGPS(self, value):
    """Parses GPS records (record type 2096) from the log data.

    Applies XOR decryption based on the ticket number to extract payload values
    and computes timestamp, coordinates, altitude, and velocity components.

    Args:
      value (bytes): the full binary content of the log file.

    Returns:
      list[list]: A list of parsed GPS records with values:
        [year, month, day, hour, minute, second,
        longitude, latitude, height,
        x_velocity, y_velocity, z_velocity]
    """
    gps_records = []
    self.data = value

    def GetPayload(cur_pos, record_len, ticket_no):
      """Decrypts the payload data from a given record.

      Performs XOR decryption using the ticket number and extracts the actual
      payload from the log entry.

      Args:
        cur_pos (int): start position of the record.
        record_len (int): length of the record.
        ticket_no (int): ticket number used for XOR key.

      Returns:
        bytes: decrypted payload bytes.
      """

      payload = self.data[cur_pos + 10:cur_pos + record_len - 2]
      payload = bytes(map(lambda x: x ^ (ticket_no % 256), payload))
      return payload

    records = self.ParseRecords()
    for x in records:
      if x[3] == 2096:
        payload = struct.unpack("<IIiiifff", GetPayload(x[0], x[1],
                                                        x[2])[:32])
        date = payload[0]
        time = payload[1]
        longitude_raw = payload[2]
        latitude_raw = payload[3]
        height_raw = payload[4]
        x_offset_raw = payload[5]
        y_offset_raw = payload[6]
        z_offset_raw = payload[7]

        year = int(date / 10000)
        month = int(date / 100) % 100
        day = date % 100

        hour = int(time / 10000)
        minute = int(time / 100) % 100
        second = time % 100

        longitude = longitude_raw / (10 ** 7)
        latitude = latitude_raw / (10 ** 7)
        height = height_raw / (10**3)
        x_offset = x_offset_raw / (10**2)
        y_offset = y_offset_raw / (10**2)
        z_offset = z_offset_raw / (10**2)

        gps_records.append([year, month, day, hour, minute, second,
                            longitude, latitude, height, x_offset,
                            y_offset, z_offset])

    return gps_records

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a DJI drone binary log file from a file-like object.

    Validates the filename format and DAT version. Extracts GPS records and 
    sends parsed event data to Plaso's parser mediator.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object containing the DJI log file.

    Raises:
      WrongParser: if the filename does not match expected DJI FLYxxx.DAT 
      format.
    """
    name_pattern = re.compile(r'.*FLY\d{3}\.DAT')
    filename = parser_mediator.GetFilename()

    if not name_pattern.match(filename):
      raise errors.WrongParser('Not a DJI Log Files')

    path = file_object.read()

    self.data = path
    if self.data[242:252] == b'DJI_LOG_V3':
      # DAT File V3
      self.record_start_pos = 256
    else:
      # DAT File V1
      self.record_start_pos = 128

    records = self.ParseGPS(path)

    for record in records:
      if all(v == 0 for v in record[:6]):
        timestamp = dfdatetime_time_elements.TimeElements(None)
      else:
        # Make YYYY-MM-DD HH:MM:SS time structure
        time_structure = (
            f"{record[0]:04d}-{record[1]:02d}-{record[2]:02d} "
            f"{record[3]:02d}:{record[4]:02d}:{record[5]:02d}"
        )
        timestamp = dfdatetime_time_elements.TimeElements()
        timestamp.CopyFromDateTimeString(time_structure)
        timestamp.is_local_time = False
        timestamp.time_zone_offset = None

      event_data = DJIDroneLogEventData()

      event_data.timestamp = timestamp
      event_data.longitude = record[6]
      event_data.latitude = record[7]
      event_data.height = record[8]
      event_data.x_velocity = record[9]
      event_data.y_velocity = record[10]
      event_data.z_velocity = record[11]

      parser_mediator.ProduceEventData(event_data)


# Register the parser in Plaso's manager
manager.ParsersManager.RegisterParser(DJIDroneLogParser)
