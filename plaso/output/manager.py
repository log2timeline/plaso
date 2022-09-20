# -*- coding: utf-8 -*-
"""Output plugin manager."""


class OutputManager(object):
  """Output module manager."""

  _disabled_output_classes = {}
  _output_classes = {}

  @classmethod
  def DeregisterOutput(cls, output_class):
    """Deregisters an output class.

    The output classes are identified based on their NAME attribute.

    Args:
      output_class (type): output module class.

    Raises:
      KeyError: if output class is not set for the corresponding data type.
    """
    output_class_name = output_class.NAME.lower()

    if output_class_name in cls._disabled_output_classes:
      class_dict = cls._disabled_output_classes
    else:
      class_dict = cls._output_classes

    if output_class_name not in class_dict:
      raise KeyError(
          'Output class not set for name: {0:s}.'.format(
              output_class.NAME))

    del class_dict[output_class_name]

  @classmethod
  def GetDisabledOutputClasses(cls):
    """Retrieves the disabled output classes and its associated name.

    Yields:
      tuple[str, type]: output module name and class.
    """
    for output_class in cls._disabled_output_classes.values():
      yield output_class.NAME, output_class

  @classmethod
  def GetOutputClass(cls, name):
    """Retrieves the output class for a specific name.

    Args:
      name (str): name of the output module.

    Returns:
      type: output module class.

    Raises:
      KeyError: if there is no output class found with the supplied name.
      ValueError: if name is not a string.
    """
    if not isinstance(name, str):
      raise ValueError('Name attribute is not a string.')

    name = name.lower()
    if name not in cls._output_classes:
      raise KeyError(
          'Name: [{0:s}] not registered as an output module.'.format(name))

    return cls._output_classes[name]

  @classmethod
  def GetOutputClasses(cls):
    """Retrieves the available output classes its associated name.

    Yields:
      tuple[str, type]: output class name and type object.
    """
    for output_class in cls._output_classes.values():
      yield output_class.NAME, output_class

  @classmethod
  def HasOutputClass(cls, name):
    """Determines if a specific output class is registered with the manager.

    Args:
      name (str): name of the output module.

    Returns:
      bool: True if the output class is registered.
    """
    if not isinstance(name, str):
      return False

    return name.lower() in cls._output_classes

  @classmethod
  def NewOutputModule(cls, name):
    """Creates a new output module object for the specified output format.

    Args:
      name (str): name of the output module.

    Returns:
      OutputModule: output module.

    Raises:
      KeyError: if there is no output class found with the supplied name.
      ValueError: if name is not a string.
    """
    output_class = cls.GetOutputClass(name)
    return output_class()

  @classmethod
  def RegisterOutput(cls, output_class, disabled=False):
    """Registers an output class.

    The output classes are identified based on their NAME attribute.

    Args:
      output_class (type): output module class.
      disabled (Optional[bool]): True if the output module is disabled due to
          the module not loading correctly or not.

    Raises:
      KeyError: if output class is already set for the corresponding name.
    """
    output_name = output_class.NAME.lower()

    if disabled:
      class_dict = cls._disabled_output_classes
    else:
      class_dict = cls._output_classes

    if output_name in class_dict:
      raise KeyError((
          'Output class already set for name: {0:s}.').format(
              output_class.NAME))

    class_dict[output_name] = output_class

  @classmethod
  def RegisterOutputs(cls, output_classes, disabled=False):
    """Registers output classes.

    The output classes are identified based on their NAME attribute.

    Args:
      output_classes (list[type]): output module classes.
      disabled (Optional[bool]): True if the output module is disabled due to
          the module not loading correctly or not.

    Raises:
      KeyError: if output class is already set for the corresponding name.
    """
    for output_class in output_classes:
      cls.RegisterOutput(output_class, disabled)
