# -*- coding: utf-8 -*-
"""The CLI arguments helper manager objects."""

from plaso.lib import errors


class ArgumentHelperManager(object):
  """Class that implements the CLI argument helper manager."""

  _helper_classes = {}

  @classmethod
  def AddCommandLineArguments(cls, argument_group, argument_category=None):
    """Adds command line arguments to a configuration object.

    Args:
      argument_group: the argparse group (instance of argparse._ArgumentGroup or
                      or argparse.ArgumentParser).
      argument_category: optional category of helpers to apply to the group,
                         eg: storage, output. Used to add arguments to a select
                         group of registered helpers. Defaults to None, which
                         applies the added arguments to all helpers.
    """
    for helper in cls._helper_classes.itervalues():
      if argument_category and helper.CATEGORY != argument_category:
        continue
      helper.AddArguments(argument_group)

  @classmethod
  def DeregisterHelper(cls, helper_class):
    """Deregisters a helper class.

    The helper classes are identified based on their lower case name.

    Args:
      helper_class: the class object of the helper (instance of ArgumentHelper).

    Raises:
      KeyError: if helper class is not set for the corresponding name.
    """
    helper_name = helper_class.NAME.lower()
    if helper_name not in cls._helper_classes:
      raise KeyError(u'Helper class not set for name: {0:s}.'.format(
          helper_class.NAME))

    del cls._helper_classes[helper_name]

  @classmethod
  def GetHelperNames(cls):
    """Retrieves the helper names.

    Returns:
      A list of helper names.
    """
    return cls._helper_classes.keys()

  @classmethod
  def GetHelperClasses(cls):
    """Retrieves a list of registered helper objects.

    Returns:
      A list of helper objects.
    """
    return cls._helper_classes.values()

  @classmethod
  def ParseOptions(cls, options, config_object):
    """Parses and validates arguments using the appropriate helpers.

    Args:
      options: the parser option object (instance of argparse.Namespace).
      config_object: an object that is configured by this helper.
    """
    for helper in cls._helper_classes.itervalues():
      try:
        helper.ParseOptions(options, config_object)
      except errors.BadConfigObject:
        pass

  @classmethod
  def RegisterHelper(cls, helper_class):
    """Registers a helper class.

    The helper classes are identified based on their lower case name.

    Args:
      helper_class: the class object of the helper (instance of ArgumentHelper).

    Raises:
      KeyError: if helper class is already set for the corresponding name.
    """
    helper_name = helper_class.NAME.lower()
    if helper_name in cls._helper_classes:
      raise KeyError((u'Helper class already set for name: {0:s}.').format(
          helper_class.NAME))

    cls._helper_classes[helper_name] = helper_class

  @classmethod
  def RegisterHelpers(cls, helper_classes):
    """Registers helper classes.

    The helper classes are identified based on their lower case name.

    Args:
      helper_classes: a list of class objects of the helpers.

    Raises:
      KeyError: if helper class is already set for the corresponding name.
    """
    for helper_class in helper_classes:
      cls.RegisterHelper(helper_class)
