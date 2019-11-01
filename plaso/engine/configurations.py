# -*- coding: utf-8 -*-
"""Processing configuration classes."""

from __future__ import unicode_literals

from plaso.containers import interface


class CredentialConfiguration(interface.AttributeContainer):
  """Configuration settings for a credential.

  Attributes:
    credential_data (bytes): credential data.
    credential_type (str): credential type.
    path_spec (dfvfs.PathSpec): path specification.
  """
  CONTAINER_TYPE = 'credential_configuration'

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
  CONTAINER_TYPE = 'event_extraction_configuration'

  def __init__(self):
    """Initializes an event extraction configuration object."""
    super(EventExtractionConfiguration, self).__init__()
    self.filter_object = None
    self.text_prepend = None


class ExtractionConfiguration(interface.AttributeContainer):
  """Configuration settings for extraction.

  These settings are primarily used by the extraction worker.

  Attributes:
    hasher_file_size_limit (int): maximum file size that hashers
        should process, where 0 or None represents unlimited.
    hasher_names_string (str): comma separated string of names
        of hashers to use during processing.
    process_archives (bool): True if archive files should be
        scanned for file entries.
    process_compressed_streams (bool): True if file content in
        compressed streams should be processed.
    yara_rules_string (str): Yara rule definitions.
  """
  CONTAINER_TYPE = 'extraction_configuration'

  def __init__(self):
    """Initializes an extraction configuration object."""
    super(ExtractionConfiguration, self).__init__()
    self.hasher_file_size_limit = None
    self.hasher_names_string = None
    self.process_archives = False
    self.process_compressed_streams = True
    self.yara_rules_string = None


class InputSourceConfiguration(interface.AttributeContainer):
  """Configuration settings of an input source.

  Attributes:
    mount_path (str): path of a "mounted" directory input source.
  """
  CONTAINER_TYPE = 'input_source'

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

        * 'memory', which profiles memory usage;
        * 'parsers', which profiles CPU time consumed by individual parsers;
        * 'processing', which profiles CPU time consumed by different parts of
          processing;
        * 'serializers', which profiles CPU time consumed by individual
          serializers.
        * 'storage', which profiles storage reads and writes.
    sample_rate (int): the profiling sample rate. Contains the number of event
        sources processed.
  """
  CONTAINER_TYPE = 'profiling_configuration'

  def __init__(self):
    """Initializes a profiling configuration object."""
    super(ProfilingConfiguration, self).__init__()
    self.directory = None
    self.profilers = set()
    self.sample_rate = 1000

  def HaveProfileMemory(self):
    """Determines if memory profiling is configured.

    Returns:
      bool: True if memory profiling is configured.
    """
    return 'memory' in self.profilers

  def HaveProfileParsers(self):
    """Determines if parsers profiling is configured.

    Returns:
      bool: True if parsers profiling is configured.
    """
    return 'parsers' in self.profilers

  def HaveProfileProcessing(self):
    """Determines if processing profiling is configured.

    Returns:
      bool: True if processing profiling is configured.
    """
    return 'processing' in self.profilers

  def HaveProfileSerializers(self):
    """Determines if serializers profiling is configured.

    Returns:
      bool: True if serializers profiling is configured.
    """
    return 'serializers' in self.profilers

  def HaveProfileStorage(self):
    """Determines if storage profiling is configured.

    Returns:
      bool: True if storage profiling is configured.
    """
    return 'storage' in self.profilers

  def HaveProfileTaskQueue(self):
    """Determines if task queue profiling is configured.

    Returns:
      bool: True if task queue profiling is configured.
    """
    return 'task_queue' in self.profilers

  def HaveProfileTasks(self):
    """Determines if tasks profiling is configured.

    Returns:
      bool: True if task queue profiling is configured.
    """
    return 'tasks' in self.profilers


class ProcessingConfiguration(interface.AttributeContainer):
  """Configuration settings for processing.

  Attributes:
    artifact_filters (Optional list[str]): names of artifact
          definitions that are used for filtering file system and Windows
          Registry key paths.
    credentials (list[CredentialConfiguration]): credential configurations.
    data_location (str): path to the data files.
    debug_output (bool): True if debug output should be enabled.
    event_extraction (EventExtractionConfiguration): event extraction
        configuration.
    extraction (ExtractionConfiguration): extraction configuration.
    filter_file (str): path to a file with find specifications.
    input_source (InputSourceConfiguration): input source configuration.
    log_filename (str): name of the log file.
    parser_filter_expression (str): parser filter expression,
        where None represents all parsers and plugins.
    preferred_year (int): preferred initial year value for year-less date and
        time values.
    profiling (ProfilingConfiguration): profiling configuration.
    task_storage_format (str): format to use for storing task results.
    temporary_directory (str): path of the directory for temporary files.
  """
  CONTAINER_TYPE = 'processing_configuration'

  def __init__(self):
    """Initializes a process configuration object."""
    super(ProcessingConfiguration, self).__init__()
    self.artifact_filters = None
    self.credentials = []
    self.data_location = None
    self.debug_output = False
    self.event_extraction = EventExtractionConfiguration()
    self.extraction = ExtractionConfiguration()
    self.filter_file = None
    self.input_source = InputSourceConfiguration()
    self.log_filename = None
    self.parser_filter_expression = None
    self.preferred_year = None
    self.profiling = ProfilingConfiguration()
    self.task_storage_format = None
    self.temporary_directory = None
