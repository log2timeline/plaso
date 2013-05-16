#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""This file contains the format classifier classes.

Plaso is a tool that extracts events from files on a file system.
For this it either reads files from a mounted file system or from an image.
It uses an exhaustive approach to determine parse events from a file, meaning
that it passes the file first to parser A and if that fails it continues with
parser B.

The classifier is designed to be able to more quickly determine the format of
a file and limit the number of parsers part of the exhaustive approach.

The current version of the classifier uses signatures to identify file formats.
Some signatures must always be defined at a specific offset, this is referred to
as an offset-bound signature or bound for short. Other signatures are commonly
found at a specific offset but not necessarily. The last form of signatures is
unbound, meaning that they don't have a fixed or common location where they can
be found.

A specification is a collection of signatures with additional metadata that
defines a specific file format. These specifications are grouped into a store
for ease of use, e.g. so that they can be read from a configuration file all
at once.

The classifier requires a scanner to analyze the data in a file. The scanner
uses the specifications in a store to scan for the signatures or a certain
format.

The classifier allows for multiple methods of scanning a file:
* full:      the entire file is scanned. This is the default scanning method.
* head-tail: only the beginning (head) and the end (tail) of the file is
             scanned. This approach is more efficient for larger files.
             The buffer size is used as the size of the data that is scanned.
             Smaller files are scanned entirely.

The classifier returns zero or more classifications which point to a format
specification and the scan results for the signatures defined by
the specification.
"""
import logging
import os


class Classification(object):
  """This class represents a format classification.

     The format classification consists of a format specification and
     scan results.
  """

  def __init__(self, specification):
    """Initializes the classification.

    Args:
      specification: an instance of Specification that contains the format
                     specification.

    Raises:
      TypeError: if the specification is not of type Specification.
    """
    self.scan_results = []
    self._specification = specification

  @property
  def identifier(self):
    """The classification type."""
    return self._specification.identifier

  @property
  def magic_types(self):
    """The magic types or an empty list if none."""
    return self._specification.magic_types

  @property
  def mime_types(self):
    """The mime type or an empty list if none."""
    return self._specification.mime_types


class Classifier(object):
  """Class for classifying formats in raw data.

  The classifier is initialized with one or more specifications.
  After which it can be used to classify data in files or file-like objects.

  The actual scanning of the data is done by the scanner, these are separate
  to allow for the scanner to easily be replaced for a more efficient
  alternative if necessary.

  For an example of how the classifier is to be used see: classify.py.
  """
  BUFFER_SIZE = 16 * 1024 * 1024

  # Classifying modes
  FULL_SCAN = 0
  HEAD_TAIL_SCAN = 1

  def __init__(self, scanner, mode=0):
    """Initializes the classifier and sets up the scanning related structures.

    Args:
      scanner: an instance of the signature scanner.
      mode: the classifying mode, only applies to scanning a file or file-like
            object.
    """
    self._scanner = scanner
    self._mode = mode

  def _GetClassifications(self, scan_results):
    """Retrieves the classifications based on the scan results.

    Multiple scan results are combined into a single classification.

    Args:
      scan_results: a list containing instances of _ScanResult.

    Returns:
      a list of instances of Classification.
    """
    classifications = {}

    for scan_result in scan_results:
      specification = scan_result.specification
      identifier = specification.identifier

      logging.debug("scan result at offset: %08x specification: %s",
                    scan_result.file_offset, identifier)

      if identifier not in classifications:
        classifications[identifier] = Classification(specification)

      classifications[identifier].scan_results.append(scan_result)

    return classifications.values()

  def ClassifyBuffer(self, file_offset, data):
    """Classifies the data in a buffer, assumes all necessary data is available.

    Args:
      file_offset: the offset of the data relative to the start of the file.
      data: a buffer containing raw data.

    Returns:
      a list of classifications or an empty list.
    """
    scan_state = self._scanner.ScanStart()
    self._scanner.ScanBuffer(scan_state, file_offset, data)
    self._scanner.ScanStop(scan_state)

    return self._GetClassifications(scan_state.GetResults())

  def ClassifyFileObject(self, file_object):
    """Classifies the data in a file-like object.

    Args:
      file_object: a file-like object.

    Returns:
      a list of classifier classifications or an empty list.
    """
    scan_state = self._scanner.ScanStart()

    if self._mode == self.HEAD_TAIL_SCAN:
      if hasattr(file_object, "get_size"):
        file_size = file_object.get_size()
      else:
        file_object.seek(0, os.SEEK_END)
        file_size = file_object.tell()

    file_object.seek(0, os.SEEK_SET)
    file_offset = file_object.tell()

    if (self._mode == self.HEAD_TAIL_SCAN and
        file_size > (self.BUFFER_SIZE * 2)):
      data = file_object.read(self.BUFFER_SIZE)
      self._scanner.ScanBuffer(scan_state, file_offset, data)

      file_object.seek((-1 * self.BUFFER_SIZE), os.SEEK_END)
      file_offset = file_object.tell()
      data = file_object.read(self.BUFFER_SIZE)
      self._scanner.ScanBuffer(scan_state, file_offset, data)

    else:
      data = file_object.read(self.BUFFER_SIZE)
      while data:
        self._scanner.ScanBuffer(scan_state, file_offset, data)
        file_offset = file_object.tell()
        data = file_object.read(self.BUFFER_SIZE)

    self._scanner.ScanStop(scan_state)

    return self._GetClassifications(scan_state.GetResults())

  def ClassifyFile(self, filename):
    """Classifies the data in a file.

    Args:
      filename: the name of the file.

    Returns:
      a list of classifier classifications or an empty list.
    """
    classifications = []
    with open(filename, "rb") as file_object:
      classifications = self.ClassifyFileObject(file_object)
    return classifications
