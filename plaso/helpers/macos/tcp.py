# -*- coding: utf-8 -*-
"""MacOS TCP helper."""

class TCP(object):
  """TCP Helper.

  See https://www.rfc-editor.org/rfc/rfc9293.html
  """

  _TCP_FLAGS = {
    'F': 0x01,
    'S': 0x02,
    'R': 0x04,
    'P': 0x08,
    '.': 0x10,
    'U': 0x20,
    'E': 0x40,
    'W': 0x80
  }

  _TCP_STATE = {
      0: 'CLOSED',
      1: 'LISTEN',
      2: 'SYN_SENT',
      3: 'SYN_RECEIVED',
      4: 'ESTABLISHED',
      5: 'CLOSE_WAIT',
      6: 'FIN_WAIT_1',
      7: 'CLOSING',
      8: 'LAST_ACK',
      9: 'FIN_WAIT_2',
      10: 'TIME_WAIT'}

  @classmethod
  def ParseFlags(cls, flags):
    """Parses the TCP flags

    Args:
      flags (int): TCP flags

    Returns:
      str: formatted flag string.
    """
    enabled_flags = []
    for flag, value in cls._TCP_FLAGS.items():
      if flags & value != 0:
        enabled_flags.append(flag)
    return '[{0:s}]'.format(
      ''.join(enabled_flags))

  @classmethod
  def ParseState(cls, state):
    """Parses the TCP state

    Args:
      state (int): TCP state

    Returns:
      str: formatted state string.
    """
    return cls._TCP_STATE.get(state, 'UNKNOWN')
