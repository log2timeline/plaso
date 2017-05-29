# -*- coding: utf-8 -*-
"""Artifact attribute containers."""

from plaso.containers import interface
from plaso.containers import manager


class ArtifactAttributeContainer(interface.AttributeContainer):
  """Base class to represent an artifact attribute container."""


class EnvironmentVariableArtifact(ArtifactAttributeContainer):
  """Environment variable artifact attribute container.

  Also see:
    https://en.wikipedia.org/wiki/Environment_variable

  Attributes:
    case_sensitive (bool): True if environment variable name is case sensitive.
    name (str): environment variable name e.g. 'SystemRoot' as in
        '%SystemRoot%' or 'HOME' in '$HOME'.
    value (str): environment variable value e.g. 'C:\\Windows' or '/home/user'.
  """
  CONTAINER_TYPE = u'environment_variable'

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
    http://cybox.mitre.org/language/version2.1/xsddocs/objects/
    Hostname_Object.html

  Attributes:
    name (str): name of the host according to the naming schema.
    schema (str): naming schema e.g. DNS, NIS, SMB/NetBIOS.
  """
  CONTAINER_TYPE = u'hostname'

  def __init__(self, name=None, schema=u'DNS'):
    """Initializes a hostname artifact.

    Args:
      name (Optional[str]): name of the host according to the naming schema.
      schema (Optional[str]): naming schema.
    """
    super(HostnameArtifact, self).__init__()
    self.name = name
    self.schema = schema


class SystemConfigurationArtifact(ArtifactAttributeContainer):
  """System configuration artifact attribute container.

  The system configuration contains the configuration data of a specific
  system installation e.g. Windows or Linux.

  Attributes:
    code_page (str): system code page.
    hostname (HostnameArtifact): hostname.
    keyboard_layout (str): keyboard layout.
    operating_system (str): operating system for example "Mac OS X" or
        "Windows".
    operating_system_product (str): operating system product for example
        "Windows XP".
    operating_system_version (str): operating system version for example
        "10.9.2" or "8.1".
    time_zone (str): system time zone.
    user_accounts (list[UserAccountArtifact]): user accounts.
  """
  CONTAINER_TYPE = u'system_configuration'

  def __init__(self, code_page=None, time_zone=None):
    """Initializes a system configuration artifact.

    Args:
      code page (Optional[str]): system code page.
      time_zone (Optional[str]): system time zone.
    """
    super(SystemConfigurationArtifact, self).__init__()
    self.code_page = code_page
    self.hostname = None
    self.keyboard_layout = None
    self.operating_system = None
    self.operating_system_product = None
    self.operating_system_version = None
    self.time_zone = time_zone
    self.user_accounts = []


class UserAccountArtifact(ArtifactAttributeContainer):
  """User account artifact attribute container.

  Also see:
    http://cybox.mitre.org/language/version2.1/xsddocs/objects/
    User_Account_Object.html

  Attributes:
    full_name (str): name describing the user e.g. full name.
    group_identifier (str): identifier of the primary group the user is part of.
    identifier (str): user identifier.
    user_directory (str): path of the user (or home or profile) directory.
    username (str): name uniquely identifying the user.
  """
  CONTAINER_TYPE = u'user_account'

  def __init__(
      self, full_name=None, group_identifier=None, identifier=None,
      user_directory=None, username=None):
    """Initializes an user artifact.

    Args:
      full_name (Optional[str]): name describing the user e.g. full name.
      group_identifier (Optional[str]): identifier of the primary group
          the user is part of.
      identifier (Optional[str]): user identifier.
      user_directory (Optional[str]): path of the user (or home or profile)
          directory.
      username (Optional[str]): name uniquely identifying the user.
    """
    super(UserAccountArtifact, self).__init__()
    self.full_name = full_name
    self.group_identifier = group_identifier
    self.identifier = identifier
    # TODO: add shell.
    self.user_directory = user_directory
    self.username = username


manager.AttributeContainersManager.RegisterAttributeContainers([
    EnvironmentVariableArtifact, HostnameArtifact, SystemConfigurationArtifact,
    UserAccountArtifact])
