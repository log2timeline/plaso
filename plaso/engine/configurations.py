# -*- coding: utf-8 -*-
"""Processing configuration classes."""

from plaso.containers import interface


class CredentialConfiguration(interface.AttributeContainer):
  """Configuration settings for a credential.

  Attributes:
    credential_data (bytes): credential data.
    credential_type (str): credential type.
    path_spec (dfvfs.PathSpec): path specification.
  """
  CONTAINER_TYPE = u'credential_configuration'

  def __init__(
      self, credential_data=None, credential_type=None, path_spec=None):
    """Initializes a credential configuration object.

    Args:
      credential_data (Optional[bytes]): credential data.
      credential_type (Optional[str]): credential type.
      path_spec (Optional[dfvfs.PathSpec]): path specification.
    """
    super(CredentialConfiguration, self).__init__()
    self.credential_data = credential_data
    self.credential_type = credential_type
    self.path_spec = path_spec


class EventExtractionConfiguration(interface.AttributeContainer):
  """Configuration settings for event extraction.

  These settings are primarily used by the parser mediator.

  Attributes:
    filter_object (objectfilter.Filter): filter that specifies which
        events to include.
    text_prepend (str): text to prepend to every event.
  """
  CONTAINER_TYPE = u'event_extraction_configuration'

  def __init__(self):
    """Initializes an event extraction configuration object."""
    super(EventExtractionConfiguration, self).__init__()
    self.filter_object = None
    self.text_prepend = None


class ExtractionConfiguration(interface.AttributeContainer):
  """Configuration settings for extraction.

  These settings are primarily used by the extraction worker.

  Attributes:
    hasher_names_string (str): comma separated string of names
        of hashers to use during processing.
    process_archives (bool): True if archive files should be
        scanned for file entries.
    process_compressed_streams (bool): True if file content in
        compressed streams should be processed.
    yara_rules_string (str): Yara rule definitions.
  """
  CONTAINER_TYPE = u'extraction_configuration'

  def __init__(self):
    """Initializes an extraction configuration object."""
    super(ExtractionConfiguration, self).__init__()
    self.hasher_names_string = None
    self.process_archives = False
    self.process_compressed_streams = True
    self.yara_rules_string = None


class InputSourceConfiguration(interface.AttributeContainer):
  """Configuration settings of an input source.

  Attributes:
    mount_path (str): path of a "mounted" directory input source.
  """
  CONTAINER_TYPE = u'input_source'

  def __init__(self):
    """Initializes an input source configuration object."""
    super(InputSourceConfiguration, self).__init__()
    self.mount_path = None


class ProfilingConfiguration(interface.AttributeContainer):
  """Configuration settings for profiling.

  Attributes:
    directory (str): path to the directory where the profiling sample files
        should be stored.
    profilers (set(str)): names of the profilers to enable.
        Supported profilers are:

        * 'guppy', which profiles memory usage using guppy;
        * 'memory', which profiles memory usage;
        * 'parsers', which profiles CPU time consumed by individual parsers;
        * 'processing', which profiles CPU time consumed by different parts of
          processing;
        * 'serializers', which profiles CPU time consumed by individual
          serializers.
    sample_rate (int): the profiling sample rate. Contains the number of event
        sources processed.
  """
  CONTAINER_TYPE = u'profiling_configuration'

  def __init__(self):
    """Initializes a profiling configuration object."""
    super(ProfilingConfiguration, self).__init__()
    self.directory = None
    self.profilers = set()
    self.sample_rate = 1000

  def HaveProfileMemoryGuppy(self):
    """Determines if memory profiling with guppy is configured.

    Returns:
      bool: True if memory profiling with guppy is configured.
    """
    return u'guppy' in self.profilers

  def HaveProfileMemory(self):
    """Determines if memory profiling is configured.

    Returns:
      bool: True if memory profiling is configured.
    """
    return u'memory' in self.profilers

  def HaveProfileParsers(self):
    """Determines if parsers profiling is configured.

    Returns:
      bool: True if parsers profiling is configured.
    """
    return u'parsers' in self.profilers

  def HaveProfileProcessing(self):
    """Determines if processing profiling is configured.

    Returns:
      bool: True if processing profiling is configured.
    """
    return u'processing' in self.profilers

  def HaveProfileSerializers(self):
    """Determines if serializers profiling is configured.

    Returns:
      bool: True if serializers profiling is configured.
    """
    return u'serializers' in self.profilers


class ProcessingConfiguration(interface.AttributeContainer):
  """Configuration settings for processing.

  Attributes:
    credentials (list[CredentialConfiguration]): credential configurations.
    data_location (str): path to the data files.
    debug_output (bool): True if debug output should be enabled.
    event_extraction (EventExtractionConfiguration): event extraction
        configuration.
    extraction (ExtractionConfiguration): extraction configuration.
    filter_file (str): path to a file with find specifications.
    input_source (InputSourceConfiguration): input source configuration.
    parser_filter_expression (str): parser filter expression,
        where None represents all parsers and plugins.
    preferred_year (int): preferred initial year value for year-less date and
        time values.
    profiling (ProfilingConfiguration): profiling configuration.
    temporary_directory (str): path of the directory for temporary files.
  """
  CONTAINER_TYPE = u'processing_configuration'

  def __init__(self):
    """Initializes a process configuration object."""
    super(ProcessingConfiguration, self).__init__()
    self.credentials = []
    self.data_location = None
    self.debug_output = False
    self.event_extraction = EventExtractionConfiguration()
    self.extraction = ExtractionConfiguration()
    self.filter_file = None
    self.input_source = InputSourceConfiguration()
    self.parser_filter_expression = None
    self.preferred_year = None
    self.profiling = ProfilingConfiguration()
    self.temporary_directory = None
