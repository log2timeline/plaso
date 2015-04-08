# -*- coding: utf-8 -*-
"""This file contains the output manager class."""


class OutputManager(object):
  """Class that implements the output manager."""

  _output_classes = {}

  @classmethod
  def DeregisterOutput(cls, output_class):
    """Deregisters an output class.

    The output classes are identified based on their NAME attribute.

    Args:
      output_class: the class object of the output module.

    Raises:
      KeyError: if output class is not set for the corresponding data type.
    """
    output_class_name = output_class.NAME.lower()
    if output_class_name not in cls._output_classes:
      raise KeyError(
          u'Output class not set for name: {0:s}.'.format(
              output_class.NAME))

    del cls._output_classes[output_class_name]

  @classmethod
  def GetOutputClass(cls, name):
    """Retrieves the output class for a specific name.

    Args:
      name: The name of the output module.

    Returns:
      The corresponding output class (subclass of OutputModule).

    Raises:
      KeyError: if there is no output class found with the supplied name.
      ValueError: if name is not a string.
    """
    if not isinstance(name, basestring):
      raise ValueError(u'Name attribute is not a string.')

    name = name.lower()
    if name not in cls._output_classes:
      raise KeyError(
          u'Name: [{0:s}] not registered as an output module.'.format(name))

    return cls._output_classes[name]

  @classmethod
  def GetOutputs(cls):
    """Generate a list of all available output classes."""
    for output_class in cls._output_classes.itervalues():
      yield output_class.NAME, output_class.DESCRIPTION

  @classmethod
  def HasOutputClass(cls, name):
    """Determines if a specific output class is registered with the manager.

    Args:
      name: The name of the output module.

    Returns:
      A boolean indicating if the output class is registered.
    """
    if not isinstance(name, basestring):
      return False

    return name.lower() in cls._output_classes

  @classmethod
  def NewOutputModule(cls, name, output_mediator, **kwargs):
    """Creates a new output module object for the specified output format.

    Args:
      name: The name of the output module.
      output_mediator: The output mediator object (instance of OutputMediator).

    Returns:
      An instance of the corresponding output class (instance of OutputModule).

    Raises:
      KeyError: if there is no output class found with the supplied name.
      ValueError: if name is not a string.
    """
    output_class = cls.GetOutputClass(name)
    return output_class(output_mediator, **kwargs)

  @classmethod
  def RegisterOutput(cls, output_class):
    """Registers an output class.

    The output classes are identified based on their NAME attribute.

    Args:
      output_class: the class object of the output (instance of
                    OutputModule).

    Raises:
      KeyError: if output class is already set for the corresponding
                name attribute.
    """
    output_name = output_class.NAME.lower()
    if output_name in cls._output_classes:
      raise KeyError((
          u'Output class already set for name: {0:s}.').format(
              output_class.NAME))

    cls._output_classes[output_name] = output_class

  @classmethod
  def RegisterOutputs(cls, output_classes):
    """Registers output classes.

    The output classes are identified based on their NAME attribute.

    Args:
      output_classes: a list of class objects of the outputs (instance of
                       OutputModule).

    Raises:
      KeyError: if output class is already set for the corresponding name.
    """
    for output_class in output_classes:
      cls.RegisterOutput(output_class)
