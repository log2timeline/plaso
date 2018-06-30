# -*- coding: utf-8 -*-
"""The arguments helper interface."""

from __future__ import unicode_literals

import locale
import sys

from plaso.lib import errors
from plaso.lib import py2to3


class ArgumentsHelper(object):
  """CLI arguments helper."""

  NAME = 'baseline'
  # Category further divides the registered helpers down after function,
  # this can be something like: analysis, output, storage, etc.
  CATEGORY = ''
  DESCRIPTION = ''

  _PREFERRED_ENCODING = 'UTF-8'

  @classmethod
  def _ParseNumericOption(cls, options, argument_name, default_value=None):
    """Parses a numeric command line argument.

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
    if argument_value is None:
      return default_value

    if not isinstance(argument_value, py2to3.INTEGER_TYPES):
      raise errors.BadConfigOption(
          'Unsupported option: {0:s} integer type required.'.format(
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
    if argument_value is None:
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
            'Unable to convert option: {0:s} to Unicode with error: '
            '{1!s}.').format(argument_name, exception))

    elif not isinstance(argument_value, py2to3.UNICODE_TYPE):
      raise errors.BadConfigOption(
          'Unsupported option: {0:s} string type required.'.format(
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
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (object): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
      BadConfigOption: when a configuration parameter fails validation.
    """
