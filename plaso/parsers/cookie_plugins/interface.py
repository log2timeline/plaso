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

import abc

from plaso.lib import errors
from plaso.parsers import plugins


# TODO: move this into the parsers and plugins manager.
def GetPlugins():
  """Returns a list of all cookie plugins."""
  plugins_list = []
  for plugin_cls in CookiePlugin.classes.itervalues():
    parent_name = getattr(plugin_cls, 'parent_class_name', 'NOTHERE')
    if parent_name != 'cookie':
      continue

    plugins_list.append(plugin_cls())

  return plugins_list


class CookiePlugin(plugins.BasePlugin):
  """A browser cookie plugin for Plaso.

  This is a generic cookie parsing interface that can handle parsing
  cookies from all browsers.
  """

  __abstract = True

  NAME = 'cookie'

  # The name of the cookie value that this plugin is designed to parse.
  # This value is used to evaluate whether the plugin is the correct one
  # to parse the browser cookie.
  COOKIE_NAME = u''

  def __init__(self):
    """Initialize the browser cookie plugin."""
    super(CookiePlugin, self).__init__()
    self.cookie_data = ''

  @abc.abstractmethod
  def GetEntries(self, parser_context, cookie_data=None, url=None, **kwargs):
    """Extract and return EventObjects from the data structure.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      cookie_data: Optional cookie data, as a byte string.
      url: Optional URL or path where the cookie got set.
    """

  def Process(
      self, parser_context, cookie_name=None, cookie_data=None, url=None,
      **kwargs):
    """Determine if this is the right plugin for this cookie.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      cookie_name: The name of the cookie value.
      cookie_data: The cookie data, as a byte string.
      url: The full URL or path where the cookie got set.

    Raises:
      errors.WrongPlugin: If the cookie name differs from the one
      supplied in COOKIE_NAME.
      ValueError: If cookie_name or cookie_data are not set.
    """
    if cookie_name is None or cookie_data is None:
      raise ValueError(u'Cookie name or data are not set.')

    if cookie_name != self.COOKIE_NAME:
      raise errors.WrongPlugin(
          u'Not the correct cookie plugin for: {0:s} [{1:s}]'.format(
              cookie_name, self.plugin_name))

    # This will raise if unhandled keyword arguments are passed.
    super(CookiePlugin, self).Process(parser_context, **kwargs)
    self.GetEntries(parser_context, cookie_data=cookie_data, url=url)
