# -*- coding: utf-8 -*-
"""Analyzer result attribute container."""

from acstore.containers import interface
from acstore.containers import manager


class AnalyzerResult(interface.AttributeContainer):
  """Attribute container to store results of analyzers.

  Analyzers can produce results with different attribute names. For example, the
  'hashing' analyzer could produce an attribute 'md5_hash', with a value of
  'd41d8cd98f00b204e9800998ecf8427e'.

  Attributes:
    analyzer_name (str): name of the analyzer that produce the result.
    attribute_name (str): name of the attribute produced.
    attribute_value (str): value of the attribute produced.
  """

  CONTAINER_TYPE = 'analyzer_result'

  def __init__(self):
    """Initializes an analyzer result."""
    super(AnalyzerResult, self).__init__()
    self.analyzer_name = None
    self.attribute_name = None
    self.attribute_value = None


manager.AttributeContainersManager.RegisterAttributeContainer(AnalyzerResult)
