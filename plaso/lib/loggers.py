# -*- coding: utf-8 -*-
"""Logging related classes and functions."""

import gzip
import logging


class CompressedFileHandler(logging.FileHandler):
  """Compressed file handler for logging."""

  def __init__(self, filename, mode='a', encoding='utf-8'):
    """Initializes a compressed file logging handler.

    Args:
      filename (str): name of the log file.
      mode (Optional[str]): file access mode.
      encoding (Optional[str]): encoding of the log lines.
    """
    if 't' not in mode and encoding:
      mode = '{0:s}t'.format(mode)
    super(CompressedFileHandler, self).__init__(
        filename, mode=mode, encoding=encoding, delay=True)

  def _open(self):
    """Opens the compressed log file.

    Returns
      file: file-like object of the resulting stream.
    """
    return gzip.open(self.baseFilename, mode=self.mode, encoding=self.encoding)


def ConfigureLogging(
    debug_output=False, filename=None, mode='w', quiet_mode=False):
  """Configures the logging root logger.

  Args:
    debug_output (Optional[bool]): True if the logging should include debug
        output.
    filename (Optional[str]): log filename.
    mode (Optional[str]): log file access mode.
    quiet_mode (Optional[bool]): True if the logging should not include
        information output. Note that debug_output takes precedence over
        quiet_mode.
  """
  # Remove all possible log handlers. The log handlers cannot be reconfigured
  # and therefore must be recreated.
  for handler in logging.root.handlers:
    logging.root.removeHandler(handler)

  logger = logging.getLogger()

  if filename and filename.endswith('.gz'):
    handler = CompressedFileHandler(filename, mode=mode)
  elif filename:
    handler = logging.FileHandler(filename, mode=mode)
  else:
    handler = logging.StreamHandler()

  format_string = (
      '%(asctime)s [%(levelname)s] (%(processName)-10s) PID:%(process)d '
      '<%(module)s> %(message)s')

  formatter = logging.Formatter(format_string)
  handler.setFormatter(formatter)

  if debug_output:
    level = logging.DEBUG
  elif quiet_mode:
    level = logging.WARNING
  else:
    level = logging.INFO

  logger.setLevel(level)
  handler.setLevel(level)

  logger.addHandler(handler)
