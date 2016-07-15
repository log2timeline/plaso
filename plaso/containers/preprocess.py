# -*- coding: utf-8 -*-
"""The attribute container object definitions."""

from plaso.containers import interface
from plaso.containers import manager


class PreprocessObject(interface.AttributeContainer):
  """Object used to store all information gained from preprocessing.

  Attributes:
    collection_information (dict[str, object]): collection information.
    zone (str): time zone.
  """
  CONTAINER_TYPE = u'preprocess'

  def __init__(self):
    """Initializes the preprocess object."""
    super(PreprocessObject, self).__init__()
    self._user_mappings = None
    self.collection_information = {}
    self.zone = u'UTC'

  def GetPathAttributes(self):
    """Retrieves the path attributes.

    Returns:
      dict[str, str]]: path attributes e.g. {'SystemRoot': 'C:\\Windows'}
    """
    # TODO: improve this only return known enviroment variables.
    return self.__dict__

  def GetUserMappings(self):
    """Retrieves mappings of user identifiers to usernames.

    Returns:
      dict[str, str]: mapping of SIDs or UIDs to usernames
    """
    if self._user_mappings is None:
      self._user_mappings = {}

    if self._user_mappings:
      return self._user_mappings

    for user in getattr(self, u'users', []):
      if u'sid' in user:
        user_id = user.get(u'sid', u'')
      elif u'uid' in user:
        user_id = user.get(u'uid', u'')
      else:
        user_id = u''

      if user_id:
        self._user_mappings[user_id] = user.get(u'name', user_id)

    return self._user_mappings

  def GetUsernameById(self, user_identifier):
    """Returns a username for a specific user identifier.

    Args:
      user_identifier (str): user identifier, either a SID or UID.

    Returns:
      str: user name if available, otherwise '-'.
    """
    user_mappings = self.GetUserMappings()

    return user_mappings.get(user_identifier, u'-')


manager.AttributeContainersManager.RegisterAttributeContainer(PreprocessObject)
