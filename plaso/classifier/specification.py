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
"""The format specification classes."""


class Signature(object):
  """Class that defines a signature of a format specification.

  The signature consists of a byte string expression, an optional
  offset relative to the start of the data, and a value to indidate
  if the expression is bound to the offset.
  """
  def __init__(self, expression, offset=None, is_bound=False):
    """Initializes the signature.

    Args:
      expression: string containing the expression of the signature.
                  The expression consists of a byte string at the moment
                  regular expression (regexp) are not supported.
      offset: the offset of the signature or None by default. None is used
              to indicate the signature has no offset. A positive offset
              is relative from the start of the data a negative offset
              is relative from the end of the data.
      is_bound: boolean value to indicate the signature must be bound to
                the offset or False by default.
    """
    self.expression = expression
    self.offset = offset
    self.is_bound = is_bound


class Specification(object):
  """Class that contains a format specification."""

  def __init__(self, identifier):
    """Initializes the specification.

    Args:
      identifier: string containing a unique name for the format.
    """
    self.identifier = identifier
    self.mime_types = []
    self.signatures = []
    self.universal_type_identifiers = []

  def AddMimeType(self, mime_type):
    """Adds a MIME type."""
    self.mime_types.append(mime_type)

  def AddNewSignature(self, expression, offset=None, is_bound=False):
    """Adds a signature.

    Args:
      expression: string containing the expression of the signature.
      offset: the offset of the signature or None by default. None is used
              to indicate the signature has no offset. A positive offset
              is relative from the start of the data a negative offset
              is relative from the end of the data.
      is_bound: boolean value to indicate the signature must be bound to
                the offset or False by default.
    """
    self.signatures.append(
        Signature(expression, offset=offset, is_bound=is_bound))

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
    """A specifications iterator object."""
    return self._format_specifications.itervalues()

  def AddNewSpecification(self, identifier):
    """Adds a new specification.

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

  def AddSpecification(self, specification):
    """Adds a specification.

    Args:
      specification: the specification (instance of Specification).

    Raises:
      KeyError: if the store already contains a specification with
                the same identifier.
    """
    if specification.identifier in self._format_specifications:
      raise KeyError(
          u'Specification {0:s} is already defined in store.'.format(
              specification.identifier))

    self._format_specifications[specification.identifier] = specification

  def ReadFromFileObject(self, dummy_file_object):
    """Reads the specification store from a file-like object.

    Args:
      dummy_file_object: A file-like object.

    Raises:
      RuntimeError: because functionality is not implemented yet.
    """
    # TODO: implement this function.
    raise RuntimeError(u'Function not implemented.')

  def ReadFromFile(self, filename):
    """Reads the specification store from a file.

    Args:
      filename: The name of the file.
    """
    file_object = open(filename, 'r')
    self.ReadFromFileObject(file_object)
    file_object.close()
