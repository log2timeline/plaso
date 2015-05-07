# -*- coding: utf-8 -*-
"""The arguments helper interface."""


class ArgumentsHelper(object):
  """The CLI arguments helper class."""

  NAME = u'baseline'
  # Category further divides the registered helpers down after function,
  # this can be something like: analysis, output, storage, etc.
  CATEGORY = u''
  DESCRIPTION = u''

  @classmethod
  def AddArguments(cls, argument_group):
    """Add command line arguments the helper supports to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group: the argparse group (instance of argparse._ArgumentGroup or
                      or argparse.ArgumentParser).
    """

  @classmethod
  def ParseOptions(cls, options, config_object):
    """Parses and validates options.

    Args:
      options: the parser option object (instance of argparse.Namespace).
      config_object: an object that is configured by this helper.

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
      BadConfigOption: when a configuration parameter fails validation.
    """
