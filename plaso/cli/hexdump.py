# -*- coding: utf-8 -*-
"""Class to represent binary data as hexadecimal."""


class Hexdump(object):
  """Class that defines a hexadecimal representation formatter (hexdump)."""

  @classmethod
  def _FormatDataLine(cls, data, data_offset, data_size):
    """Formats binary data in a single line of hexadecimal representation.

    Args:
      data: String containing the binary data.
      data_offset: Offset of the data.
      data_size: Size of the data.

    Returns:
      A Unicode string containing a hexadecimal representation of
      the binary data.

    Raises:
      ValueError: if the data offset is out of bounds.
    """
    if data_offset < 0 or data_offset >= data_size:
      raise ValueError(u'Data offset value out of bounds.')

    if data_size - data_offset > 16:
      data_size = data_offset + 16

    word_values = []
    for byte_offset in range(data_offset, data_size, 2):
      word_value = u'{0:02x}{1:02x}'.format(
          ord(data[byte_offset]), ord(data[byte_offset + 1]))
      word_values.append(word_value)

    byte_values = []
    for byte_offset in range(data_offset, data_size):
      byte_value = ord(data[byte_offset])
      if byte_value > 31 and byte_value < 127:
        byte_value = data[byte_offset]
      else:
        byte_value = u'.'

      byte_values.append(byte_value)

    return u'{0:07x}: {1:s}  {2:s}'.format(
        data_offset, u' '.join(word_values), u''.join(byte_values))

  @classmethod
  def FormatData(cls, data, data_offset=0, maximum_data_size=None):
    """Formats binary data in hexadecimal representation.

    All ASCII characters in the hexadecimal representation (hexdump) are
    translated back to their character representation.

    Args:
      data: String containing the binary data.
      data_offset: Optional offset within the data to start formatting.
      maximum_data_size: Optional maximum size of the data to format.
                         The default is None which represents all of
                         the binary data.

    Returns:
      A Unicode string containing a hexadecimal representation of
      the binary data.
    """
    data_size = len(data)
    if maximum_data_size is not None and maximum_data_size < data_size:
      data_size = maximum_data_size

    output_strings = []
    for line_offset in range(data_offset, data_size, 16):
      hexdump_line = cls._FormatDataLine(data, line_offset, data_size)
      output_strings.append(hexdump_line)

    return u'\n'.join(output_strings)
