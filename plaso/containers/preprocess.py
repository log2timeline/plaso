# -*- coding: utf-8 -*-
"""Preprocess related attribute container object definitions."""

from plaso.containers import interface
from plaso.containers import manager


class PreprocessObject(interface.AttributeContainer):
  """Object used to store all information gained from preprocessing.

  Attributes:
    hosts (dict[str,str]): hostnames, for example {'hostname': 'myhost'}.
    time_zone_str (str): time zone, formatted as a string supported by
        pytz.timezone().
    list[dict[str,str]]: users, for example [{'name': 'me', 'sid': 'S-1',
        'uid': '1'}]
    zone (str): time zone, formatted as a string supported by pytz.timezone().
  """
  CONTAINER_TYPE = u'preprocess'

  def __init__(self):
    """Initializes a preprocess object."""
    super(PreprocessObject, self).__init__()
    self.hosts = {}
    self.time_zone_str = u'UTC'
    self.users = {}
    self.zone = u'UTC'


manager.AttributeContainersManager.RegisterAttributeContainer(PreprocessObject)
