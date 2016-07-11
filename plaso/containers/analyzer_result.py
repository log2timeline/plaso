# -*- coding: utf-8 -*-
"""Analyzer result container object definition."""

from plaso.containers import interface


class AnalyzerResult(interface.AttributeContainer):
  """Class for containing the results of processing."""

  def __init__(self):
    super(AnalyzerResult, self).__init__()
    self.analyzer_name = None
    self.attribute_name = None
    self.attribute_value = None
