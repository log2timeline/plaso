#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""The parser context object."""


class ParserContext(object):
  """Class that implements the parser context."""

  def __init__(self, knowledge_base):
    """Initializes a parser context object.

    Args:
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.
    """
    super(ParserContext, self).__init__()
    self._knowledge_base = knowledge_base

  @property
  def codepage(self):
    """The codepage."""
    return self._knowledge_base.codepage

  @property
  def knowledge_base(self):
    """The knowledge base."""
    return self._knowledge_base

  @property
  def platform(self):
    """The platform."""
    return self._knowledge_base.platform

  @property
  def timezone(self):
    """The timezone object."""
    return self._knowledge_base.timezone

  @property
  def year(self):
    """The year."""
    return self._knowledge_base.year
