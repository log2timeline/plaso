# -*- coding: utf-8 -*-
"""Artifact attribute containers."""

from plaso.containers import interface
from plaso.containers import manager
from plaso.lib import definitions


class ArtifactAttributeContainer(interface.AttributeContainer):
  """Base class to represent an artifact attribute container."""


class EnvironmentVariableArtifact(ArtifactAttributeContainer):
  """Environment variable artifact attribute container.

  Also see:
    https://en.wikipedia.org/wiki/Environment_variable

  Attributes:
    case_sensitive (bool): True if environment variable name is case sensitive.
    name (str): environment variable name such as "SystemRoot" as in
        "%SystemRoot%" or "HOME" as in "$HOME".
    value (str): environment variable value such as "C:\\Windows" or
        "/home/user".
  """
  CONTAINER_TYPE = 'environment_variable'

  def __init__(self, case_sensitive=True, name=None, value=None):
    """Initializes an environment variable artifact.

    Args:
      case_sensitive (Optional[bool]): True if environment variable name
          is case sensitive.
      name (Optional[str]): environment variable name.
      value (Optional[str]): environment variable value.
    """
    super(EnvironmentVariableArtifact, self).__init__()
    self.case_sensitive = case_sensitive
    self.name = name
    self.value = value


class HostnameArtifact(ArtifactAttributeContainer):
  """Hostname artifact attribute container.

  Also see:
    https://en.wikipedia.org/wiki/Hostname
    Cybox / Stix Hostname Object

  Attributes:
    name (str): name of the host according to the naming schema.
    schema (str): naming schema such as "DNS", "NIS", "SMB/NetBIOS".
  """
  CONTAINER_TYPE = 'hostname'

  def __init__(self, name=None, schema='DNS'):
    """Initializes a hostname artifact.

    Args:
      name (Optional[str]): name of the host according to the naming schema.
      schema (Optional[str]): naming schema.
    """
    super(HostnameArtifact, self).__init__()
    self.name = name
    self.schema = schema


class OperatingSystemArtifact(ArtifactAttributeContainer):
  """Operating system artifact attribute container.

  Attributes:
    family (str): operating system family name, such as "Linux", "MacOS"
        or "Windows", defined in definitions.OPERATING_SYSTEM_FAMILIES.
        This value is used to programmatically link a parser preset to an
        operating system and therefore must be one of predefined values.
    name (str): operating system name, such as "macOS Mojave" or "Windows XP".
        This value is used to programmatically link a parser preset to an
        operating system and therefore must be one of predefined values.
    product (str): product information, such as "macOS Mojave" or "Windows
        Professional XP". This value is typically obtained from the source data.
    version (str): version, such as "10.14.1" or "5.1". This value is typically
        obtained from the source data.
  """
  CONTAINER_TYPE = 'operating_system'

  _DEFAULT_FAMILY_AND_VERSION = (
      definitions.OPERATING_SYSTEM_FAMILY_UNKNOWN, (0, 0))

  _FAMILY_AND_VERSION_PER_NAME = {
      'Windows 2000': (definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT, (5, 0)),
      'Windows 2003': (definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT, (5, 2)),
      'Windows 2003 R2': (
          definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT, (5, 2)),
      'Windows 2008': (definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT, (6, 0)),
      'Windows 2008 R2': (
          definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT, (6, 1)),
      'Windows 2012': (definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT, (6, 2)),
      'Windows 2012 R2': (
          definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT, (6, 3)),
      'Windows 2016': (definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT, (10, 0)),
      'Windows 2019': (definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT, (10, 0)),
      'Windows 7': (definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT, (6, 1)),
      'Windows 8': (definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT, (6, 2)),
      'Windows 8.1': (definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT, (6, 3)),
      'Windows 10': (definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT, (10, 0)),
      'Windows Vista': (definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT, (6, 0)),
      'Windows XP': (definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT, (5, 1))}

  def __init__(self, family=None, product=None, version=None):
    """Initializes an operating system artifact.

    Args:
      family (Optional[str]): operating system family name, such as "Linux",
        "MacOS" or "Windows", defined in definitions.OPERATING_SYSTEM_FAMILIES.
        This value is used to programmatically link a parser preset to an
        operating system and therefore must be one of predefined values.
      product (Optional[str]): product information, such as "macOS Mojave" or
          "Windows Professional XP". This value is typically obtained from the
          source data.
      version (Optional[str]): version, such as "10.14.1" or "5.1". This value
          is typically obtained from the source data.
    """
    super(OperatingSystemArtifact, self).__init__()
    self.family = family
    self.name = None
    self.product = product
    self.version = version

    if product:
      self.name = self._GetNameFromProduct()

  @property
  def version_tuple(self):
    """tuple[int]: version tuple or None if version is not set or invalid."""
    try:
      return tuple([int(digit, 10) for digit in self.version.split('.')])
    except (AttributeError, TypeError, ValueError):
      return None

  def _GetNameFromProduct(self):
    """Determines the predefined operating system name from the product.

    Returns:
      str: operating system name, such as "macOS Mojave" or "Windows XP" or
          None if the name cannot be determined. This value is used to
          programmatically link a parser preset to an operating system and
          therefore must be one of predefined values.
    """
    product = self.product or ''
    product = product.split(' ')
    product_lower_case = [segment.lower() for segment in product]
    number_of_segments = len(product)

    if 'windows' in product_lower_case:
      segment_index = product_lower_case.index('windows') + 1
      if product_lower_case[segment_index] in ('(r)', 'server', 'web'):
        segment_index += 1

      # Check if the version has a suffix.
      suffix_segment_index = segment_index + 1
      if (suffix_segment_index < number_of_segments and
          product_lower_case[suffix_segment_index] == 'r2'):
        return 'Windows {0:s} R2'.format(product[segment_index])

      return 'Windows {0:s}'.format(product[segment_index])

    return None

  def IsEquivalent(self, other):
    """Determines if 2 operating system artifacts are equivalent.

    This function compares the operating systems based in order of:
    * name derived from product
    * family and version
    * family

    Args:
      other (OperatingSystemArtifact): operating system artifact attribute
          container to compare with.

    Returns:
      bool: True if the operating systems are considered equivalent, False if
          the most specific criteria do no match, or no criteria are available.
    """
    if self.name and other.name:
      return self.name == other.name

    if self.name:
      self_family, self_version_tuple = self._FAMILY_AND_VERSION_PER_NAME.get(
          self.name, self._DEFAULT_FAMILY_AND_VERSION)
      return (
          self_family == other.family and
          self_version_tuple == other.version_tuple)

    if self.family and self.version:
      if other.name:
        other_family, other_version_tuple = (
            self._FAMILY_AND_VERSION_PER_NAME.get(
                other.name, self._DEFAULT_FAMILY_AND_VERSION))
      else:
        other_family = other.family
        other_version_tuple = other.version_tuple

      return (
          self.family == other_family and
          self.version_tuple == other_version_tuple)

    if self.family:
      if other.name:
        other_family, _ = self._FAMILY_AND_VERSION_PER_NAME.get(
            other.name, self._DEFAULT_FAMILY_AND_VERSION)
      else:
        other_family = other.family

      return self.family == other_family

    return False


class PathArtifact(ArtifactAttributeContainer):
  """Path artifact attribute container.

  Attributes:
    data_stream (str): name of a data stream.
    path_segment_separator (str): path segment separator.
    path_segments (list[str]): path segments.
  """
  CONTAINER_TYPE = 'path'

  def __init__(self, data_stream=None, path=None, path_segment_separator='/'):
    """Initializes a path artifact.

    Args:
      data_stream (Optional[str]): name of a data stream.
      path (Optional[str]): a path.
      path_segment_separator (Optional[str]): path segment separator.
    """
    super(PathArtifact, self).__init__()
    self.data_stream = data_stream
    self.path_segment_separator = path_segment_separator
    self.path_segments = self._SplitPath(path, path_segment_separator)

  def __eq__(self, other):
    """Determines if the path is equal to other.

    Args:
      other (str): path to compare against.

    Returns:
      bool: True if the path are equal to other.
    """
    if not isinstance(other, str):
      return False

    other_path_segments = self._SplitPath(other, self.path_segment_separator)
    return self.path_segments == other_path_segments

  def __ge__(self, other):
    """Determines if the path are greater than or equal to other.

    Args:
      other (str): path to compare against.

    Returns:
      bool: True if the path are greater than or equal to other.

    Raises:
      ValueError: if other is not an instance of string.
    """
    if not isinstance(other, str):
      raise ValueError('Other not an instance of string.')

    other_path_segments = self._SplitPath(other, self.path_segment_separator)
    return self.path_segments >= other_path_segments

  def __gt__(self, other):
    """Determines if the path are greater than other.

    Args:
      other (str): path to compare against.

    Returns:
      bool: True if the path are greater than other.

    Raises:
      ValueError: if other is not an instance of string.
    """
    if not isinstance(other, str):
      raise ValueError('Other not an instance of string.')

    other_path_segments = self._SplitPath(other, self.path_segment_separator)
    return self.path_segments > other_path_segments

  def __le__(self, other):
    """Determines if the path are greater than or equal to other.

    Args:
      other (str): path to compare against.

    Returns:
      bool: True if the path are greater than or equal to other.

    Raises:
      ValueError: if other is not an instance of string.
    """
    if not isinstance(other, str):
      raise ValueError('Other not an instance of string.')

    other_path_segments = self._SplitPath(other, self.path_segment_separator)
    return self.path_segments <= other_path_segments

  def __lt__(self, other):
    """Determines if the path are less than other.

    Args:
      other (str): path to compare against.

    Returns:
      bool: True if the path are less than other.

    Raises:
      ValueError: if other is not an instance of string.
    """
    if not isinstance(other, str):
      raise ValueError('Other not an instance of string.')

    other_path_segments = self._SplitPath(other, self.path_segment_separator)
    return self.path_segments < other_path_segments

  def __ne__(self, other):
    """Determines if the path are not equal to other.

    Args:
      other (str): path to compare against.

    Returns:
      bool: True if the path are not equal to other.
    """
    if not isinstance(other, str):
      return False

    other_path_segments = self._SplitPath(other, self.path_segment_separator)
    return self.path_segments != other_path_segments

  def _SplitPath(self, path, path_segment_separator):
    """Splits a path.

    Args:
      path (str): a path.
      path_segment_separator (str): path segment separator.

    Returns:
      list[str]: path segments.
    """
    path = path or ''
    split_path = path.split(path_segment_separator)

    path_segments = [split_path[0]]
    path_segments.extend(list(filter(None, split_path[1:])))

    return path_segments

  def ContainedIn(self, other):
    """Determines if the path are contained in other.

    Args:
      other (str): path to compare against.

    Returns:
      bool: True if the path is contained in other.
    """
    if isinstance(other, str):
      number_of_path_segments = len(self.path_segments)
      other_path_segments = self._SplitPath(other, self.path_segment_separator)
      number_of_other_path_segments = len(other_path_segments)
      if number_of_path_segments < number_of_other_path_segments:
        maximum_compare_length = (
            number_of_other_path_segments - number_of_path_segments + 1)

        for compare_start_index in range(0, maximum_compare_length):
          compare_end_index = compare_start_index + number_of_path_segments
          compare_path_segments = other_path_segments[
              compare_start_index:compare_end_index]
          if self.path_segments == compare_path_segments:
            return True

    return False


class SourceConfigurationArtifact(ArtifactAttributeContainer):
  """Source configuration artifact attribute container.

  The source configuration contains the configuration data of a source
  that is (or going to be) processed such as volume in a storage media
  image or a mounted directory.

  Attributes:
    mount_path (str): path of a "mounted" directory input source.
    path_spec (dfvfs.PathSpec): path specification of the source that is
        processed.
    system_configuration (SystemConfigurationArtifact): system configuration of
        a specific system installation, such as Windows or Linux, detected by
        the pre-processing on the source.
  """
  CONTAINER_TYPE = 'source_configuration'

  def __init__(self, path_spec=None):
    """Initializes a source configuration artifact.

    Args:
      path_spec (Optional[dfvfs.PathSpec]): path specification of the source
          that is processed.
    """
    super(SourceConfigurationArtifact, self).__init__()
    self.mount_path = None
    self.path_spec = path_spec
    self.system_configuration = None


class SystemConfigurationArtifact(ArtifactAttributeContainer):
  """System configuration artifact attribute container.

  The system configuration contains the configuration data of a specific
  system installation such as Windows or Linux.

  Attributes:
    available_time_zones (list[TimeZone]): available time zones.
    code_page (str): system code page.
    hostname (HostnameArtifact): hostname.
    keyboard_layout (str): keyboard layout.
    operating_system (str): operating system for example "MacOS" or "Windows".
    operating_system_product (str): operating system product for example
        "Windows XP".
    operating_system_version (str): operating system version for example
        "10.9.2" or "8.1".
    time_zone (str): system time zone.
    user_accounts (list[UserAccountArtifact]): user accounts.
  """
  CONTAINER_TYPE = 'system_configuration'

  def __init__(self, code_page=None, time_zone=None):
    """Initializes a system configuration artifact.

    Args:
      code_page (Optional[str]): system code page.
      time_zone (Optional[str]): system time zone.
    """
    super(SystemConfigurationArtifact, self).__init__()
    self.available_time_zones = []
    self.code_page = code_page
    self.hostname = None
    self.keyboard_layout = None
    self.operating_system = None
    self.operating_system_product = None
    self.operating_system_version = None
    self.time_zone = time_zone
    self.user_accounts = []


class TimeZoneArtifact(ArtifactAttributeContainer):
  """Time zone artifact attribute container.

  Attributes:
    name (str): name describing the time zone for example Greenwich Standard
        Time.
  """
  CONTAINER_TYPE = 'time_zone'

  def __init__(self, name=None):
    """Initializes a time zone artifact.

    Args:
      name (Optional[str]): name describing the time zone for example Greenwich
          Standard Time.
    """
    super(TimeZoneArtifact, self).__init__()
    self.name = name


class UserAccountArtifact(ArtifactAttributeContainer):
  """User account artifact attribute container.

  Also see:
    Cybox / Stix User Account Object

  Attributes:
    full_name (str): name describing the user.
    group_identifier (str): identifier of the primary group the user is part of.
    identifier (str): user identifier.
    user_directory (str): path of the user (or home or profile) directory.
    username (str): name uniquely identifying the user.
  """
  CONTAINER_TYPE = 'user_account'

  def __init__(
      self, full_name=None, group_identifier=None, identifier=None,
      path_separator='/', user_directory=None, username=None):
    """Initializes a user account artifact.

    Args:
      full_name (Optional[str]): name describing the user.
      group_identifier (Optional[str]): identifier of the primary group
          the user is part of.
      identifier (Optional[str]): user identifier.
      path_separator (Optional[str]): path segment separator.
      user_directory (Optional[str]): path of the user (or home or profile)
          directory.
      username (Optional[str]): name uniquely identifying the user.
    """
    super(UserAccountArtifact, self).__init__()
    self._path_separator = path_separator
    self.full_name = full_name
    self.group_identifier = group_identifier
    self.identifier = identifier
    # TODO: add shell.
    self.user_directory = user_directory
    self.username = username

  def GetUserDirectoryPathSegments(self):
    """Retrieves the path segments of the user directory.

    Returns:
      list[str]: path segments of the user directory or an empty list if no
          user directory is set.
    """
    if not self.user_directory:
      return []
    return self.user_directory.split(self._path_separator)


manager.AttributeContainersManager.RegisterAttributeContainers([
    EnvironmentVariableArtifact, HostnameArtifact, OperatingSystemArtifact,
    PathArtifact, SourceConfigurationArtifact, SystemConfigurationArtifact,
    TimeZoneArtifact, UserAccountArtifact])
