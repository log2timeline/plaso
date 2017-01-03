# -*- coding: utf-8 -*-
"""Processing configuration classes."""

# TODO: should these be attribute containers?


class EventExtractionConfiguration(object):
  """Configuration settings for event extraction.

  Attributes:
    filter_object (objectfilter.Filter): filter object.
    text_prepend (str): text to prepend to every event.
  """

  def __init__(self):
    """Initializes an event extraction configuration object."""
    super(EventExtractionConfiguration, self).__init__()
    self.filter_object = None
    self.text_prepend = None


class ExtractionConfiguration(object):
  """Configuration settings for extraction.

  Attributes:
    hasher_names_string (str): comma separated string of names
        of hashers to use during processing.
    process_archives (bool): True if archive files should be
        scanned for file entries.
    process_compressed_streams (bool): True if file content in
        compressed streams should be processed.
    yara_rules_string (str): Yara rule definitions.
  """

  def __init__(self):
    """Initializes an extraction configuration object."""
    super(ExtractionConfiguration, self).__init__()
    self.hasher_names_string = None
    self.process_archives = False
    self.process_compressed_streams = True
    self.yara_rules_string = None


class InputSourceConfiguration(object):
  """Configuration settings of an input source.

  Attributes:
    mount_path (str): path of a "mounted" directory input source.
  """

  def __init__(self):
    """Initializes an input source configuration object."""
    super(InputSourceConfiguration, self).__init__()
    self.mount_path = None


class ProfilingConfiguration(object):
  """Configuration settings for profiling.

  Attributes:
    directory (str): path to the directory where the profiling sample files
        should be stored.
    enable (bool): True if profiling should be enabled.
    profiling_type (str): type of profiling.
        Supported types are:

        * 'memory' to profile memory usage;
        * 'parsers' to profile CPU time consumed by individual parsers;
        * 'processing' to profile CPU time consumed by different parts of
          the processing;
        * 'serializers' to profile CPU time consumed by individual
          serializers.
    sample_rate (int): the profiling sample rate. Contains the number of event
        sources processed.
  """

  def __init__(self):
    """Initializes a profiling configuration object."""
    super(ProfilingConfiguration, self).__init__()
    self.directory = None
    self.enable = False
    self.profiling_type = u'all'
    self.sample_rate = 1000

  def HaveProfileMemory(self):
    """Determines if memory profiling is configured.

    Returns:
      bool: True if memory profiling is configured.
    """
    return self.enable and self.profiling_type in (u'all', u'memory')

  def HaveProfileParsers(self):
    """Determines if parsers profiling is configured.

    Returns:
      bool: True if parsers profiling is configured.
    """
    return self.enable and self.profiling_type in (u'all', u'parsers')

  def HaveProfileProcessing(self):
    """Determines if processing profiling is configured.

    Returns:
      bool: True if processing profiling is configured.
    """
    return self.enable and self.profiling_type in (u'all', u'processing')

  def HaveProfileSerializers(self):
    """Determines if serializers profiling is configured.

    Returns:
      bool: True if serializers profiling is configured.
    """
    return self.enable and self.profiling_type in (u'all', u'serializers')


class ProcessingConfiguration(object):
  """Configuration settings for processing.

  Attributes:
    debug_output (bool): True if debug output should be enabled.
    event_extraction (EventExtractionConfiguration): event extraction
        configuration.
    extraction (ExtractionConfiguration): extraction configuration.
    input_source (InputSourceConfiguration): input source configuration.
    parser_filter_expression (str): parser filter expression,
        where None represents all parsers and plugins.
    preferred_year (int): preferred initial year value for year-less date and
        time values.
    profiling (ProfilingConfiguration): profiling configuration.
    temporary_directory (str): path of the directory for temporary files.
  """

  def __init__(self):
    """Initializes a process configuration object."""
    super(ProcessingConfiguration, self).__init__()
    self.debug_output = False
    self.event_extraction = EventExtractionConfiguration()
    self.extraction = ExtractionConfiguration()
    self.input_source = InputSourceConfiguration()
    self.parser_filter_expression = None
    self.preferred_year = None
    self.profiling = ProfilingConfiguration()
    self.temporary_directory = None
