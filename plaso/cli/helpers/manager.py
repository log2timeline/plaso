# -*- coding: utf-8 -*-
"""The CLI arguments helper manager objects."""

from plaso.lib import errors


class ArgumentHelperManager(object):
  """Class that implements the CLI argument helper manager."""

  _helper_classes = {}

  @classmethod
  def AddCommandLineArguments(
      cls, argument_group, argument_category=None, module_list=None):
    """Adds command line arguments to a configuration object.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
          argparse group.
      argument_category (Optional[str]): category of helpers to apply to
          the group, such as storage, output, where None will apply the
          arguments to all helpers. The category can be used to add arguments
          to a specific group of registered helpers.
      module_list (Optional[list[str]]): names of argument helpers to apply,
          where None will apply the arguments to all helpers.
    """
    # Process the helper classes in alphabetical order this is needed to
    # keep the argument order consistent.
    for _, helper in sorted(cls._helper_classes.items()):
      if argument_category and helper.CATEGORY != argument_category:
        continue

      if module_list and helper.NAME not in module_list:
        continue

      helper.AddArguments(argument_group)

  @classmethod
  def DeregisterHelper(cls, helper_class):
    """Deregisters a helper class.

    The helper classes are identified based on their lower case name.

    Args:
      helper_class (type): class object of the argument helper.

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
    """Retrieves the registered argument helper names.

    Returns:
      list[str]: sorted argument helper names.
    """
    return sorted(cls._helper_classes.keys())

  @classmethod
  def ParseOptions(cls, options, config_object):
    """Parses and validates arguments using the appropriate helpers.

    Args:
      options (argparse.Namespace): parser options.
      config_object (object): object to be configured by an argument helper.
    """
    for helper in iter(cls._helper_classes.values()):
      try:
        helper.ParseOptions(options, config_object)
      except errors.BadConfigObject:
        pass

  @classmethod
  def RegisterHelper(cls, helper_class):
    """Registers a helper class.

    The helper classes are identified based on their lower case name.

    Args:
      helper_class (type): class object of the argument helper.

    Raises:
      KeyError: if helper class is already set for the corresponding name.
    """
    helper_name = helper_class.NAME.lower()
    if helper_name in cls._helper_classes:
      raise KeyError(u'Helper class already set for name: {0:s}.'.format(
          helper_class.NAME))

    cls._helper_classes[helper_name] = helper_class

  @classmethod
  def RegisterHelpers(cls, helper_classes):
    """Registers helper classes.

    The helper classes are identified based on their lower case name.

    Args:
      helper_classes (list[type]): class objects of the argument helpers.

    Raises:
      KeyError: if helper class is already set for the corresponding name.
    """
    for helper_class in helper_classes:
      cls.RegisterHelper(helper_class)
