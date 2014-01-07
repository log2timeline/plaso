#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains an interface for browser cookie plugins."""

from plaso.lib import errors
from plaso.lib import plugin


def GetPlugins(pre_obj, data_type):
  """Returns a list of all cookie plugins."""
  plugins = []
  for plugin_cls in CookiePlugin.classes.itervalues():
    parent_name = getattr(plugin_cls, 'parent_class', 'NOTHERE')

    if parent_name != 'cookie':
      continue

    plugins.append(plugin_cls(pre_obj, data_type))

  return plugins


# We do not want to implement the GetEntries function here, that should be
# done by child plugins, thus we suppress the pylint message.
# pylint: disable-msg=abstract-method


class CookiePlugin(plugin.BasePlugin):
  """A browser cookie plugin for Plaso.

  This is a generic cookie parsing interface that can handle parsing
  cookies from all browsers. It just needs the cookie name and the
  cookie data to be able to evaluate and parse the cookie content and
  yield back event objects.
  """

  __abstract = True

  NAME = 'cookie'

  # The name of the cookie value that this plugin is designed to parse.
  # This value is used to evaluate whether the plugin is the correct one
  # to parse the browser cookie.
  COOKIE_NAME = u''

  def __init__(self, pre_obj, data_type=None):
    """Initialize the browser cookie plugin."""
    super(CookiePlugin, self).__init__(pre_obj)

    if data_type:
      self._data_type = data_type
    else:
      self._data_type = 'cookie:generic'
    self.cookie_data = ''

  def Process(self, cookie_name=None, cookie_data=None, **kwargs):
    """Determine if this is the right plugin for this cookie.

    Args:
      cookie_name: The name of the cookie value.
      cookie_data: The cookie data, as a byte string.

    Returns:
      A generator that yields event objects.

    Raises:
      errors.WrongPlugin: If the cookie name differs from the one
      supplied in COOKIE_NAME.
      ValueError: If cookie_name or cookie_data are not set.
    """
    if cookie_name is None or cookie_data is None:
      raise ValueError(u'Cookie name or data are not set.')

    if cookie_name != self.COOKIE_NAME:
      raise errors.WrongPlugin(
          u'Not the correct cookie plugin for: {} [{}]'.format(
              cookie_name, self.plugin_name))

    super(CookiePlugin, self).Process(**kwargs)
    self.cookie_data = cookie_data
    return self.GetEntries()
