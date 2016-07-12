# -*- coding: utf-8 -*-
"""This file contains a class for managing digest analyzers for Plaso."""

import os


class AnalyzersManager(object):
  """Class that implements the analyzers manager."""

  _analyzer_classes = {}


  @classmethod
  def AnalyzeFileObject(cls, mediator, file_object, analyzers):
    """Processes a file-like object with the provided analyzers.

    Args:
      mediator (ParserMediator): encapsulates interactions between
          parsers and other components (storage, abort signalling, etc.).
      file_object (dfvfs.FileIO): file-like object to process.
      analyzers (list[analyzer]): analyzers to use on the file object.

    Returns:
      list(AnalyzerResult): results of the analyzers.
    """
    if not analyzers:
      return

    file_object.seek(0, os.SEEK_SET)

    maximum_file_size = max([analyzer.SIZE_LIMIT for analyzer in analyzers])

    results = []
    if file_object.get_size() <= maximum_file_size:
      data = file_object.read()
      for analyzer in analyzers:
        if mediator.abort:
          break
        if len(data) <= analyzer.SIZE_LIMIT:
          analyzer.Analyze(data)
    else:
      data = file_object.read(maximum_file_size)
      while data:
        for analyzer in analyzers:
          if mediator.abort:
            break
          if analyzer.SUPPORTS_INCREMENTAL_UPDATE:
            analyzer.Update(data)
        if mediator.abort:
          break
        data = file_object.read(maximum_file_size)

    for analyzer in analyzers:
      if mediator.abort:
        break
      results.extend(analyzer.GetResults())
      analyzer.Reset()
    return results

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
      raise KeyError(u'analyzer class not set for name: {0:s}'.format(
          analyzer_class.NAME))

    del cls._analyzer_classes[analyzer_name]

  @classmethod
  def GetAnalyzerNames(cls):
    """Retrieves the names of all loaded analyzers.

    Returns:
      list[str]: of analyzer names.
    """
    return cls._analyzer_classes.keys()

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
      description = getattr(analyzer_class, u'DESCRIPTION', u'')
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
          u'analyzer class not set for name: {0:s}.'.format(analyzer_name))

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
    for analyzer_name, analyzer_class in iter(cls.GetAnalyzers()):
      if analyzer_name in analyzer_names:
        analyzer_instances.append(analyzer_class())

    return analyzer_instances

  @classmethod
  def GetAnalyzers(cls):
    """Retrieves the registered analyzers.

    Yields:
      tuple: containing:

        str: the uniquely identifying name of the analyzer
        type: the analyzer class.
    """
    for analyzer_name, analyzer_class in iter(cls._analyzer_classes.items()):
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
      raise KeyError(u'analyzer class already set for name: {0:s}.'.format(
          analyzer_class.NAME))

    cls._analyzer_classes[analyzer_name] = analyzer_class
