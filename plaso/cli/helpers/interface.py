# -*- coding: utf-8 -*-
"""The arguments helper interface."""

import locale
import sys

from plaso.lib import errors
from plaso.lib import py2to3


class ArgumentsHelper(object):
  """CLI arguments helper."""

  NAME = u'baseline'
  # Category further divides the registered helpers down after function,
  # this can be something like: analysis, output, storage, etc.
  CATEGORY = u''
  DESCRIPTION = u''

  _PREFERRED_ENCODING = u'UTF-8'

  @classmethod
  def _ParseIntegerOption(cls, options, argument_name, default_value=None):
    """Parses an integer command line argument.

    Args:
      options (argparse.Namespace): parser options.
      argument_name (str): name of the command line argument.
      default_value (Optional[int]): default value of the command line argument.

    Returns:
      int: command line argument value or the default value if the command line
          argument is not set

    Raises:
      BadConfigOption: if the command line argument value cannot be converted
                       to a Unicode string.
    """
    argument_value = getattr(options, argument_name, None)
    if not argument_value:
      return default_value

    if not isinstance(argument_value, py2to3.INTEGER_TYPES):
      raise errors.BadConfigOption(
          u'Unsupported option: {0:s} integer type required.'.format(
              argument_name))

    return argument_value

  @classmethod
  def _ParseStringOption(cls, options, argument_name, default_value=None):
    """Parses a string command line argument.

    Args:
      options (argparse.Namespace): parser options.
      argument_name (str): name of the command line argument.
      default_value (Optional[str]): default value of the command line argument.

    Returns:
      str: command line argument value or the default value if the command line
          argument is not set

    Raises:
      BadConfigOption: if the command line argument value cannot be converted
                       to a Unicode string.
    """
    argument_value = getattr(options, argument_name, None)
    if not argument_value:
      return default_value

    if isinstance(argument_value, py2to3.BYTES_TYPE):
      encoding = sys.stdin.encoding

      # Note that sys.stdin.encoding can be None.
      if not encoding:
        encoding = locale.getpreferredencoding()
      if not encoding:
        encoding = cls._PREFERRED_ENCODING

      try:
        argument_value = argument_value.decode(encoding)
      except UnicodeDecodeError as exception:
        raise errors.BadConfigOption((
            u'Unable to convert option: {0:s} to Unicode with error: '
            u'{1:s}.').format(argument_name, exception))

    elif not isinstance(argument_value, py2to3.UNICODE_TYPE):
      raise errors.BadConfigOption(
          u'Unsupported option: {0:s} string type required.'.format(
              argument_name))

    return argument_value

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
          argparse group.
    """

  @classmethod
  def ParseOptions(cls, options, config_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      config_object (object): object to be configured by an argument helper.

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
      BadConfigOption: when a configuration parameter fails validation.
    """
