# -*- coding: utf-8 -*-
"""Windows preprocessor plugins."""

import os

from plaso.containers import artifacts
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.helpers.windows import languages
from plaso.preprocessors import interface
from plaso.preprocessors import manager


class WindowsEnvironmentVariableArtifactPreprocessorPlugin(
    interface.WindowsRegistryValueArtifactPreprocessorPlugin):
  """Windows environment variable artifact preprocessor plugin."""

  _NAME = None

  def _ParseValueData(self, mediator, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      value_data (object): Windows Registry value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not isinstance(value_data, str):
      raise errors.PreProcessFail(
          'Unsupported Windows Registry value type: {0!s} for '
          'artifact: {1:s}.'.format(
              type(value_data), self.ARTIFACT_DEFINITION_NAME))

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=self._NAME, value=value_data)

    try:
      mediator.AddEnvironmentVariable(environment_variable)
    except KeyError:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME,
          'Unable to set environment variable: {0:s}.'.format(self._NAME))


class WindowsProfilePathEnvironmentVariableArtifactPreprocessorPlugin(
    interface.WindowsRegistryKeyArtifactPreprocessorPlugin):
  """Windows profile path environment variable artifact preprocessor plugin."""

  _NAME = None

  def _ParseKey(self, mediator, registry_key, value_name):
    """Parses a Windows Registry key for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      value_name (str): name of the Windows Registry value or None if not
          specified.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    try:
      registry_value = registry_key.GetValueByName('ProfilesDirectory')
    except IOError as exception:
      raise errors.PreProcessFail((
          'Unable to retrieve Windows Registry key: {0:s} value: '
          'ProfilesDirectory with error: {1!s}').format(
              registry_key.path, exception))

    profiles_directory = ''
    if registry_value:
      value_data = registry_value.GetDataAsObject()
      if isinstance(value_data, str):
        profiles_directory = value_data

    try:
      registry_value = registry_key.GetValueByName(value_name)
    except IOError as exception:
      raise errors.PreProcessFail((
          'Unable to retrieve Windows Registry key: {0:s} value: {1:s} '
          'with error: {2!s}').format(
              registry_key.path, value_name, exception))

    if not registry_value:
      return

    value_data = registry_value.GetDataAsObject()
    if not isinstance(value_data, str):
      raise errors.PreProcessFail(
          'Unsupported Windows Registry value type: {0!s} for '
          'artifact: {1:s}.'.format(
              type(value_data), self.ARTIFACT_DEFINITION_NAME))

    first_path_segment = value_data.split('\\')[0]

    # If the first path segment does not starts with an environment variable or
    # is absolute, consider it to be a relative path and prefix it with the
    # ProfilesDirectory value.
    if first_path_segment[0] == '%' and first_path_segment[-1] == '%':
      profile_path = value_data
    elif not first_path_segment or first_path_segment[1:2] == ':\\':
      profile_path = value_data
    else:
      profile_path = '\\'.join([profiles_directory.rstrip('\\'), value_data])

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=self._NAME, value=profile_path)

    try:
      mediator.AddEnvironmentVariable(environment_variable)
    except KeyError:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME,
          'Unable to set environment variable: {0:s}.'.format(self._NAME))


class WindowsPathEnvironmentVariableArtifactPreprocessorPlugin(
    interface.FileSystemArtifactPreprocessorPlugin):
  """Windows path environment variable plugin interface."""

  _NAME = None

  def _ParsePathSpecification(
      self, mediator, searcher, file_system, path_specification,
      path_separator):
    """Parses artifact file system data for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      searcher (dfvfs.FileSystemSearcher): file system searcher to preprocess
          the file system.
      file_system (dfvfs.FileSystem): file system to be preprocessed.
      path_specification (dfvfs.PathSpec): path specification that contains
          the artifact value data.
      path_separator (str): path segment separator.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    relative_path = searcher.GetRelativePath(path_specification)
    if not relative_path:
      raise errors.PreProcessFail(
          'Unable to read: {0:s} with error: missing relative path'.format(
              self.ARTIFACT_DEFINITION_NAME))

    if path_separator != file_system.PATH_SEPARATOR:
      relative_path_segments = file_system.SplitPath(relative_path)
      relative_path = '{0:s}{1:s}'.format(
          path_separator, path_separator.join(relative_path_segments))

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=self._NAME, value=relative_path)

    try:
      mediator.AddEnvironmentVariable(environment_variable)
    except KeyError:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME,
          'Unable to set environment variable: {0:s}.'.format(self._NAME))


class WindowsAllUsersAppDataKnowledgeBasePlugin(
    interface.KnowledgeBasePreprocessorPlugin):
  """The allusersdata knowledge base value plugin.

  The allusersdata value is needed for the expansion of
  %%environ_allusersappdata%% in artifact definitions.
  """

  def Collect(self, mediator):
    """Collects values from the knowledge base.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.

    Raises:
      PreProcessFail: if the preprocessing fails.
    """
    environment_variable = mediator.GetEnvironmentVariable('programdata')
    allusersappdata = getattr(environment_variable, 'value', None)

    if not allusersappdata:
      environment_variable = mediator.GetEnvironmentVariable('allusersprofile')
      allusersdata = getattr(environment_variable, 'value', None)

      if allusersdata:
        allusersappdata = '\\'.join([allusersdata, 'Application Data'])

    if allusersappdata:
      environment_variable = artifacts.EnvironmentVariableArtifact(
          case_sensitive=False, name='allusersappdata', value=allusersappdata)

      try:
        mediator.AddEnvironmentVariable(environment_variable)
      except KeyError:
        mediator.ProducePreprocessingWarning(
            self.__class__.__name__,
            'Unable to set environment variable: %AllUsersAppData% in.')


class WindowsAllUsersProfileEnvironmentVariablePlugin(
    WindowsProfilePathEnvironmentVariableArtifactPreprocessorPlugin):
  """The Windows %AllUsersProfile% environment variable plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsEnvironmentVariableAllUsersProfile'

  _NAME = 'allusersprofile'


class WindowsAllUsersAppProfileKnowledgeBasePlugin(
    interface.KnowledgeBasePreprocessorPlugin):
  """The allusersprofile knowledge base value plugin.

  The allusersprofile value is needed for the expansion of
  %%environ_allusersappprofile%% in artifact definitions.

  It is derived from %ProgramData% for versions of Windows, Vista and later,
  that do not define %AllUsersProfile%.
  """

  def Collect(self, mediator):
    """Collects values from the knowledge base.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.

    Raises:
      PreProcessFail: if the preprocessing fails.
    """
    environment_variable = mediator.GetEnvironmentVariable('allusersprofile')
    allusersprofile = getattr(environment_variable, 'value', None)

    if not allusersprofile:
      environment_variable = mediator.GetEnvironmentVariable('programdata')
      allusersprofile = getattr(environment_variable, 'value', None)

      if allusersprofile:
        environment_variable = artifacts.EnvironmentVariableArtifact(
            case_sensitive=False, name='allusersprofile', value=allusersprofile)

        try:
          mediator.AddEnvironmentVariable(environment_variable)
        except KeyError:
          mediator.ProducePreprocessingWarning(
              self.__class__.__name__,
              'Unable to set environment variable: %AllUsersProfile% in.')


class WindowsAvailableTimeZonesPlugin(
    interface.WindowsRegistryKeyArtifactPreprocessorPlugin,
    dtfabric_helper.DtFabricHelper):
  """The Windows available time zones plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsAvailableTimeZones'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'time_zone_information.yaml')

  def _ParseKey(self, mediator, registry_key, value_name):
    """Parses a Windows Registry key for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      value_name (str): name of the Windows Registry value or None if not
          specified.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    std_value = registry_key.GetValueByName('Std')
    if std_value:
      localized_name = std_value.GetDataAsObject()
    else:
      localized_name = registry_key.name

    mui_std_value = registry_key.GetValueByName('MUI_Std')
    if mui_std_value:
      mui_form = mui_std_value.GetDataAsObject()
    else:
      mui_form = None

    tzi_value = registry_key.GetValueByName('TZI')
    if not tzi_value:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME,
          'TZI value missing from Windows Registry key: {0:s}'.format(
              registry_key.key_path))
      return

    time_zone_artifact = artifacts.TimeZoneArtifact(
        localized_name=localized_name, mui_form=mui_form,
        name=registry_key.name)

    try:
      self._ParseTZIValue(tzi_value.data, time_zone_artifact)

    except (ValueError, errors.ParseError) as exception:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME,
          'Unable to parse TZI record value in Windows Registry key: {0:s} '
          'with error: {2!s}'.format(
              registry_key.key_path, exception))
      return

    try:
      mediator.AddTimeZoneInformation(time_zone_artifact)
    except KeyError:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME,
          ('Unable to add time zone information: {0:s} to knowledge '
           'base.').format(registry_key.name))

  def _ParseTZIValue(self, value_data, time_zone_artifact):
    """Parses the time zone information (TZI) value data.

    Args:
      value_data (bytes): time zone information (TZI) value data.
      time_zone_artifact (TimeZoneArtifact): time zone artifact.

    Raises:
      ParseError: if the value data could not be parsed.
    """
    data_type_map = self._GetDataTypeMap('tzi_record')

    tzi_record = self._ReadStructureFromByteStream(
        value_data, 0, data_type_map)

    if tzi_record.standard_bias:
      time_zone_artifact.offset = tzi_record.standard_bias
    else:
      time_zone_artifact.offset = tzi_record.bias


class WindowsCodePagePlugin(
    interface.WindowsRegistryValueArtifactPreprocessorPlugin):
  """The Windows code page plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsCodePage'

  def _ParseValueData(self, mediator, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      value_data (object): Windows Registry value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not isinstance(value_data, str):
      raise errors.PreProcessFail(
          'Unsupported Windows Registry value type: {0!s} for '
          'artifact: {1:s}.'.format(
              type(value_data), self.ARTIFACT_DEFINITION_NAME))

    # Map the Windows code page name to a Python equivalent name.
    code_page = 'cp{0:s}'.format(value_data)

    try:
      mediator.SetCodePage(code_page)
    except ValueError:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME, 'Unable to set code page.')


class WindowsEventLogPublishersPlugin(
    interface.WindowsRegistryKeyArtifactPreprocessorPlugin):
  """The Windows EventLog publishers plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsEventLogPublishers'

  def _ParseKey(self, mediator, registry_key, value_name):
    """Parses a Windows Registry key for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      value_name (str): name of the Windows Registry value or None if not
          specified.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    registry_value = registry_key.GetValueByName('')
    if not registry_value:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME,
          'EventLog source missing for: {0:s}'.format(
              registry_key.name))
      return

    log_source = registry_value.GetDataAsObject()

    event_message_files = None
    registry_value = registry_key.GetValueByName('MessageFileName')
    if registry_value:
      event_message_files = registry_value.GetDataAsObject()
      event_message_files = sorted(filter(None, [
          path.strip().lower() for path in event_message_files.split(';')]))

    provider_identifier = registry_key.name.lower()

    if log_source:
      log_source = log_source.lower()

    windows_event_log_provider = artifacts.WindowsEventLogProviderArtifact(
        event_message_files=event_message_files, identifier=provider_identifier,
        log_source=log_source)

    try:
      mediator.AddWindowsEventLogProvider(windows_event_log_provider)
    except KeyError:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME,
          'Unable to set add Windows EventLog provider: {0:s}.',format(
              log_source))


class WindowsEventLogSourcesPlugin(
    interface.WindowsRegistryKeyArtifactPreprocessorPlugin):
  """The Windows EventLog sources plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsEventLogSources'

  def _ParseKey(self, mediator, registry_key, value_name):
    """Parses a Windows Registry key for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      value_name (str): name of the Windows Registry value or None if not
          specified.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    category_message_files = None
    registry_value = registry_key.GetValueByName('CategoryMessageFile')
    if registry_value:
      category_message_files = registry_value.GetDataAsObject()
      category_message_files = sorted(filter(None, [
          path.strip().lower() for path in category_message_files.split(';')]))

    event_message_files = None
    registry_value = registry_key.GetValueByName('EventMessageFile')
    if registry_value:
      event_message_files = registry_value.GetDataAsObject()
      event_message_files = sorted(filter(None, [
          path.strip().lower() for path in event_message_files.split(';')]))

    parameter_message_files = None
    registry_value = registry_key.GetValueByName('ParameterMessageFile')
    if registry_value:
      parameter_message_files = registry_value.GetDataAsObject()
      parameter_message_files = sorted(filter(None, [
          path.strip().lower() for path in parameter_message_files.split(';')]))

    provider_identifier = None
    registry_value = registry_key.GetValueByName('ProviderGuid')
    if registry_value:
      provider_identifier = registry_value.GetDataAsObject()
      provider_identifier = provider_identifier.lower()

    key_path_segments = registry_key.path.split('\\')

    log_source = key_path_segments[-1]
    if log_source:
      log_source = log_source.lower()

    log_type = key_path_segments[-2]
    if log_type:
      log_type = log_type.lower()

    windows_event_log_provider = artifacts.WindowsEventLogProviderArtifact(
        category_message_files=category_message_files,
        event_message_files=event_message_files, identifier=provider_identifier,
        log_source=log_source, log_type=log_type,
        parameter_message_files=parameter_message_files)

    try:
      mediator.AddWindowsEventLogProvider(windows_event_log_provider)
    except KeyError:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME,
          'Unable to set add Windows EventLog provider: {0:s}/{1:s}.'.format(
              log_type, log_source))


class WindowsHostnamePlugin(
    interface.WindowsRegistryValueArtifactPreprocessorPlugin):
  """The Windows hostname plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsComputerName'

  def _ParseValueData(self, mediator, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      value_data (object): Windows Registry value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not isinstance(value_data, str):
      if not hasattr(value_data, '__iter__'):
        raise errors.PreProcessFail(
            'Unsupported Windows Registry value type: {0!s} for '
            'artifact: {1:s}.'.format(
                type(value_data), self.ARTIFACT_DEFINITION_NAME))

      # If the value data is a multi string only use the first string.
      value_data = value_data[0]

    hostname_artifact = artifacts.HostnameArtifact(name=value_data)
    mediator.AddHostname(hostname_artifact)


class WindowsLanguagePlugin(
    interface.WindowsRegistryValueArtifactPreprocessorPlugin):
  """The Windows language plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsLanguage'

  def _ParseValueData(self, mediator, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      value_data (object): Windows Registry value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not isinstance(value_data, str):
      raise errors.PreProcessFail(
          'Unsupported Windows Registry value type: {0!s} for '
          'artifact: {1:s}.'.format(
              type(value_data), self.ARTIFACT_DEFINITION_NAME))

    try:
      lcid = int(value_data, 16)
      language_tag = languages.WindowsLanguageHelper.GetLanguageTagForLCID(lcid)
    except ValueError:
      language_tag = None

    if language_tag:
      mediator.SetLanguage(language_tag)
    else:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME,
          'Unable to determine language tag for LCID: {0:s}.'.format(
              value_data))


class WindowsMountedDevicesPlugin(
    interface.WindowsRegistryKeyArtifactPreprocessorPlugin,
    dtfabric_helper.DtFabricHelper):
  """The Windows mounted devices plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsMountedDevices'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'mounted_devices.yaml')

  def _ParseKey(self, mediator, registry_key, value_name):
    """Parses a Windows Registry key for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      value_name (str): name of the Windows Registry value or None if not
          specified.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    for registry_value in registry_key.GetValues():
      mounted_device_artifact = artifacts.WindowsMountedDeviceArtifact(
          identifier=registry_value.name)

      # TODO: parse registry_value.data
      value_data_size = len(registry_value.data)
      if value_data_size == 12:
        data_type_map = self._GetDataTypeMap('mounted_devices_mbr_partition')

        try:
          partition_values = self._ReadStructureFromByteStream(
              registry_value.data, 0, data_type_map)

          mounted_device_artifact.disk_identity = partition_values.disk_identity
          mounted_device_artifact.partition_offset = (
              partition_values.partition_offset)

        except (ValueError, errors.ParseError) as exception:
          mediator.ProducePreprocessingWarning(
              self.ARTIFACT_DEFINITION_NAME,
              ('Unable to parse mounted devices MBR partition value Windows '
               'Registry value: {0:s} with error: {1!s}').format(
                  registry_value.name, exception))

      elif value_data_size == 24:
        data_type_map = self._GetDataTypeMap('mounted_devices_gpt_partition')

        try:
          partition_values = self._ReadStructureFromByteStream(
              registry_value.data, 0, data_type_map)

          mounted_device_artifact.partition_identifier = str(
              partition_values.partition_identifier)

        except (ValueError, errors.ParseError) as exception:
          mediator.ProducePreprocessingWarning(
              self.ARTIFACT_DEFINITION_NAME,
              ('Unable to parse mounted devices GPT partition value Windows '
               'Registry value: {0:s} with error: {1!s}').format(
                  registry_value.name, exception))

      else:
        try:
          mounted_device_artifact.device = registry_value.data.decode(
              'utf-16-le')
        except UnicodeDecodeError as exception:
          mediator.ProducePreprocessingWarning(
              self.ARTIFACT_DEFINITION_NAME,
              ('Unable to parse mounted devices device string value Windows '
               'Registry value: {0:s} with error: {1!s}').format(
                  registry_value.name, exception))

      try:
        mediator.AddArtifact(mounted_device_artifact)
      except KeyError:
        mediator.ProducePreprocessingWarning(
            self.ARTIFACT_DEFINITION_NAME,
            'Unable to add Windows mounted device: {0:s} artifact.'.format(
                registry_value.name))


class WindowsProgramDataEnvironmentVariablePlugin(
    WindowsProfilePathEnvironmentVariableArtifactPreprocessorPlugin):
  """The Windows %ProgramData% environment variable plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsEnvironmentVariableProgramData'

  _NAME = 'programdata'


class WindowsProgramDataKnowledgeBasePlugin(
    interface.KnowledgeBasePreprocessorPlugin):
  """The programdata knowledge base value plugin.

  The programdata value is needed for the expansion of %%environ_programdata%%
  in artifact definitions.

  It is derived from %AllUsersProfile% for versions of Windows prior to Vista
  that do not define %ProgramData%.
  """

  def Collect(self, mediator):
    """Collects values from the knowledge base.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.

    Raises:
      PreProcessFail: if the preprocessing fails.
    """
    environment_variable = mediator.GetEnvironmentVariable('programdata')
    allusersprofile = getattr(environment_variable, 'value', None)

    if not allusersprofile:
      environment_variable = mediator.GetEnvironmentVariable('allusersprofile')
      allusersprofile = getattr(environment_variable, 'value', None)

      if allusersprofile:
        environment_variable = artifacts.EnvironmentVariableArtifact(
            case_sensitive=False, name='programdata', value=allusersprofile)

        try:
          mediator.AddEnvironmentVariable(environment_variable)
        except KeyError:
          mediator.ProducePreprocessingWarning(
              self.__class__.__name__,
              'Unable to set environment variable: %ProgramData%.')


class WindowsProgramFilesEnvironmentVariablePlugin(
    WindowsEnvironmentVariableArtifactPreprocessorPlugin):
  """The Windows %ProgramFiles% environment variable plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsEnvironmentVariableProgramFiles'

  _NAME = 'programfiles'


class WindowsProgramFilesX86EnvironmentVariablePlugin(
    WindowsEnvironmentVariableArtifactPreprocessorPlugin):
  """The Windows %ProgramFilesX86% environment variable plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsEnvironmentVariableProgramFilesX86'

  _NAME = 'programfilesx86'


class WindowsServicesAndDriversPlugin(
    interface.WindowsRegistryKeyArtifactPreprocessorPlugin):
  """The Windows service (and driver) configurations plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsServices'

  def _ParseKey(self, mediator, registry_key, value_name):
    """Parses a Windows Registry key for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      value_name (str): name of the Windows Registry value or None if not
          specified.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    service_type = None
    start_type = None

    registry_value = registry_key.GetValueByName('Type')
    if registry_value:
      service_type = registry_value.GetDataAsObject()

    registry_value = registry_key.GetValueByName('Start')
    if registry_value:
      start_type = registry_value.GetDataAsObject()

    if None in (service_type, start_type):
      return

    service_configuration = artifacts.WindowsServiceConfigurationArtifact(
        name=registry_key.name, service_type=service_type,
        start_type=start_type)

    registry_value = registry_key.GetValueByName('ErrorControl')
    if registry_value:
      service_configuration.error_control = registry_value.GetDataAsObject()

    registry_value = registry_key.GetValueByName('ImagePath')
    if registry_value:
      service_configuration.image_path = registry_value.GetDataAsObject()

    registry_value = registry_key.GetValueByName('ObjectName')
    if registry_value:
      service_configuration.object_name = registry_value.GetDataAsObject()

    sub_registry_key = registry_key.GetSubkeyByName('Parameters')
    if sub_registry_key:
      registry_value = sub_registry_key.GetValueByName('ServiceDll')
      if registry_value:
        service_configuration.service_dll = registry_value.GetDataAsObject()

    try:
      mediator.AddArtifact(service_configuration)
    except KeyError:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME,
          'Unable to add Windows service configuation: {0:s} artifact.'.format(
              registry_value.name))


class WindowsSystemProductPlugin(
    interface.WindowsRegistryValueArtifactPreprocessorPlugin):
  """The Windows system product information plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsProductName'

  def _ParseValueData(self, mediator, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      value_data (object): Windows Registry value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not isinstance(value_data, str):
      raise errors.PreProcessFail(
          'Unsupported Windows Registry value type: {0!s} for '
          'artifact: {1:s}.'.format(
              type(value_data), self.ARTIFACT_DEFINITION_NAME))

    mediator.SetValue('operating_system_product', value_data)


class WindowsSystemRootEnvironmentVariablePlugin(
    WindowsPathEnvironmentVariableArtifactPreprocessorPlugin):
  """The Windows %SystemRoot% environment variable plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsEnvironmentVariableSystemRoot'

  _NAME = 'systemroot'


class WindowsSystemVersionPlugin(
    interface.WindowsRegistryValueArtifactPreprocessorPlugin):
  """The Windows system version information plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsCurrentVersion'

  def _ParseValueData(self, mediator, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      value_data (object): Windows Registry value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not isinstance(value_data, str):
      raise errors.PreProcessFail(
          'Unsupported Windows Registry value type: {0!s} for '
          'artifact: {1:s}.'.format(
              type(value_data), self.ARTIFACT_DEFINITION_NAME))

    mediator.SetValue('operating_system_version', value_data)


class WindowsTimeZonePlugin(
    interface.WindowsRegistryValueArtifactPreprocessorPlugin):
  """The Windows time zone plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsTimezone'

  def _ParseValueData(self, mediator, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      value_data (object): Windows Registry value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not isinstance(value_data, str):
      raise errors.PreProcessFail(
          'Unsupported Windows Registry value type: {0!s} for '
          'artifact: {1:s}.'.format(
              type(value_data), self.ARTIFACT_DEFINITION_NAME))

    try:
      mediator.SetTimeZone(value_data)
    except ValueError as execption:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME,
          'Unable to map: "{0:s}" to time zone with error: {1!s}'.format(
              value_data, execption))


class WindowsUserAccountsPlugin(
    interface.WindowsRegistryKeyArtifactPreprocessorPlugin):
  """The Windows user account plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsRegistryProfiles'

  def _GetUsernameFromProfilePath(self, path):
    """Retrieves the username from a Windows profile path.

    Trailing path path segment are ignored.

    Args:
      path (str): a Windows path with '\\' as path segment separator.

    Returns:
      str: basename which is the last path segment.
    """
    # Strip trailing key separators.
    while path and path[-1] == '\\':
      path = path[:-1]

    if path:
      _, _, path = path.rpartition('\\')
    return path

  def _ParseKey(self, mediator, registry_key, value_name):
    """Parses a Windows Registry key for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      value_name (str): name of the Windows Registry value or None if not
          specified.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    user_account = artifacts.UserAccountArtifact(
        identifier=registry_key.name, path_separator='\\')

    registry_value = registry_key.GetValueByName('ProfileImagePath')
    if registry_value:
      profile_path = registry_value.GetDataAsObject()
      username = self._GetUsernameFromProfilePath(profile_path)

      user_account.user_directory = profile_path or None
      user_account.username = username or None

    try:
      mediator.AddUserAccount(user_account)
    except KeyError:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME,
          ('Unable to add user account: "{0!s}" to knowledge '
           'base').format(username))


class WindowsWinDirEnvironmentVariablePlugin(
    WindowsPathEnvironmentVariableArtifactPreprocessorPlugin):
  """The Windows %WinDir% environment variable plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsEnvironmentVariableWinDir'

  _NAME = 'windir'


manager.PreprocessPluginsManager.RegisterPlugins([
    WindowsAllUsersAppDataKnowledgeBasePlugin,
    WindowsAllUsersProfileEnvironmentVariablePlugin,
    WindowsAllUsersAppProfileKnowledgeBasePlugin,
    WindowsAvailableTimeZonesPlugin,
    WindowsCodePagePlugin, WindowsEventLogPublishersPlugin,
    WindowsEventLogSourcesPlugin, WindowsHostnamePlugin, WindowsLanguagePlugin,
    WindowsMountedDevicesPlugin, WindowsProgramDataEnvironmentVariablePlugin,
    WindowsProgramDataKnowledgeBasePlugin,
    WindowsProgramFilesEnvironmentVariablePlugin,
    WindowsProgramFilesX86EnvironmentVariablePlugin,
    WindowsServicesAndDriversPlugin, WindowsSystemProductPlugin,
    WindowsSystemRootEnvironmentVariablePlugin, WindowsSystemVersionPlugin,
    WindowsTimeZonePlugin, WindowsWinDirEnvironmentVariablePlugin,
    WindowsUserAccountsPlugin])
