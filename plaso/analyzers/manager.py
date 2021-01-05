# -*- coding: utf-8 -*-
"""This file contains a class for managing digest analyzers for Plaso."""


class AnalyzersManager(object):
  """Class that implements the analyzers manager."""

  _analyzer_classes = {}

  @classmethod
  def DeregisterAnalyzer(cls, analyzer_class):
    """Deregisters a analyzer class.

    The analyzer classes are identified based on their lower case name.

    Args:
      analyzer_class (type): class object of the analyzer.

    Raises:
      KeyError: if analyzer class is not set for the corresponding name.
    """
    analyzer_name = analyzer_class.NAME.lower()
    if analyzer_name not in cls._analyzer_classes:
      raise KeyError('analyzer class not set for name: {0:s}'.format(
          analyzer_class.NAME))

    del cls._analyzer_classes[analyzer_name]

  @classmethod
  def GetAnalyzersInformation(cls):
    """Retrieves the analyzers information.

    Returns:
      list[tuple]: containing:

        str: analyzer name.
        str: analyzer description.
    """
    analyzer_information = []
    for _, analyzer_class in cls.GetAnalyzers():
      description = getattr(analyzer_class, 'DESCRIPTION', '')
      analyzer_information.append((analyzer_class.NAME, description))

    return analyzer_information

  @classmethod
  def GetAnalyzerInstance(cls, analyzer_name):
    """Retrieves an instance of a specific analyzer.

    Args:
      analyzer_name (str): name of the analyzer to retrieve.

    Returns:
      BaseAnalyzer: analyzer instance.

    Raises:
      KeyError: if analyzer class is not set for the corresponding name.
    """
    analyzer_name = analyzer_name.lower()
    if analyzer_name not in cls._analyzer_classes:
      raise KeyError(
          'analyzer class not set for name: {0:s}.'.format(analyzer_name))

    analyzer_class = cls._analyzer_classes[analyzer_name]
    return analyzer_class()

  @classmethod
  def GetAnalyzerInstances(cls, analyzer_names):
    """Retrieves instances for all the specified analyzers.

    Args:
      analyzer_names (list[str]): names of the analyzers to retrieve.

    Returns:
      list[BaseAnalyzer]: analyzer instances.
    """
    analyzer_instances = []
    for analyzer_name, analyzer_class in cls.GetAnalyzers():
      if analyzer_name in analyzer_names:
        analyzer_instances.append(analyzer_class())

    return analyzer_instances

  @classmethod
  def GetAnalyzerNames(cls):
    """Retrieves the names of all loaded analyzers.

    Returns:
      list[str]: of analyzer names.
    """
    return cls._analyzer_classes.keys()

  @classmethod
  def GetAnalyzers(cls):
    """Retrieves the registered analyzers.

    Yields:
      tuple: containing:

        str: the uniquely identifying name of the analyzer
        type: the analyzer class.
    """
    for analyzer_name, analyzer_class in cls._analyzer_classes.items():
      yield analyzer_name, analyzer_class

  @classmethod
  def RegisterAnalyzer(cls, analyzer_class):
    """Registers a analyzer class.

    The analyzer classes are identified by their lower case name.

    Args:
      analyzer_class (type): the analyzer class to register.

    Raises:
      KeyError: if analyzer class is already set for the corresponding name.
    """
    analyzer_name = analyzer_class.NAME.lower()
    if analyzer_name in cls._analyzer_classes:
      raise KeyError('analyzer class already set for name: {0:s}.'.format(
          analyzer_class.NAME))

    cls._analyzer_classes[analyzer_name] = analyzer_class
