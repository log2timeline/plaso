#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""This file contains the format specification classes of the classifier."""


class _Signature(object):
  """Class that defines a signature for a format specification.

  The signature consists of a byte string expression, an optional
  offset relative to the start of the data, and a value to indidate
  if the expression is bound to the offset.

  This class is intended to be used internally in the classifier.
  """

  # TODO: add support for regexp type of expressions
  def __init__(self, expression, offset=None, is_bound=False):
    """Initializes the signature.

    Args:
      expression: string containing the expression of the signature.
                  The expression consists of a byte string at the moment
                  regular expression (regexp) are not supported.
      offset: the offset of the signature or None by default. None is used
              to indicate the signature has no offset.
      is_bound: boolean value to indicate the signature must be bound to
                the offset or False by default.
    """
    # TODO: add sanity checking
    self.expression = expression
    self.offset = offset
    self.is_bound = is_bound


class Specification(object):
  """Class that contains the format specification for the classifier."""

  def __init__(self, identifier):
    """Initializes the specification.

    Args:
      identifier: string containing a unique name for the format.
    """
    self.mime_types = []
    self.signatures = []
    self.universal_type_identifiers = []

    self.identifier = identifier

  def AddSignature(self, expression, offset=None, is_bound=False):
    """Adds a signature.

    Args:
      expression: string containing the expression of the signature.
      offset: the offset of the signature or None by default. None is used
              to indicate the signature has no offset.
      is_bound: boolean value to indicate the signature must be bound to
                the offset or False by default.
    """
    self.signatures.append(
        _Signature(expression, offset=offset, is_bound=is_bound))

  def AddMimeType(self, mime_type):
    """Adds a MIME type."""
    self.mime_types.append(mime_type)

  def AddUniversalTypeIdentifier(self, universal_type_identifiers):
    """Adds a Universal Type Identifier (UTI)."""
    self.universal_type_identifiers.append(universal_type_identifiers)


class SpecificationStore(object):
  """Class that servers as a store for specifications."""

  def __init__(self):
    """Initializes the specification store."""
    self._format_specifications = {}

  @property
  def specifications(self):
    """A list containing the specifications."""
    return self._format_specifications.values()

  def AddSpecification(self, identifier):
    """Adds a specification.

    Args:
      identifier: a string containing the format identifier,
                  which should be unique for the store.

    Returns:
      a instance of Specification.

    Raises:
      ValueError: if the store already contains a specification with
                  the same identifier.
    """
    if identifier in self._format_specifications:
      raise ValueError("specification {0:s} is already defined in "
                       "store.".format(identifier))

    self._format_specifications[identifier] = Specification(identifier)

    return self._format_specifications[identifier]

  def ReadFromFileObject(self, file_object):
    """Reads the specification store from a file-like object.

    Args:
      file_object: A file-like object.

    Raises:
      RuntimeError: because functionality is not implemented yet.
    """
    # TODO: implement this function
    _ = file_object

    raise RuntimeError("not implemented yet")

  def ReadFromFile(self, filename):
    """Reads the specification store from a file.

    Args:
      filename: The name of the file.
    """
    file_object = open(filename, "r")
    self.ReadFromFileObject(file_object)
    file_object.close()
