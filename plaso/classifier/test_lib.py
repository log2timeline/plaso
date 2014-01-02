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
"""Shared test cases."""

from plaso.classifier import specification


def CreateSpecificationStore():
  """Creates a format specification store for testing purposes.

  Returns:
    A format specification store (instance of SpecificationStore).
  """
  store = specification.SpecificationStore()

  test_specification = store.AddNewSpecification('7zip')
  test_specification.AddMimeType('application/x-7z-compressed')
  test_specification.AddUniversalTypeIdentifier('org.7-zip.7-zip-archive')
  test_specification.AddNewSignature('7z\xbc\xaf\x27\x1c', offset=0)

  test_specification = store.AddNewSpecification('esedb')
  test_specification.AddNewSignature(
      '\xef\xcd\xab\x89', offset=4, is_bound=True)

  test_specification = store.AddNewSpecification('evt')
  test_specification.AddNewSignature(
      '\x30\x00\x00\x00LfLe\x01\x00\x00\x00\x01\x00\x00\x00', offset=0,
      is_bound=True)

  test_specification = store.AddNewSpecification('evtx')
  test_specification.AddNewSignature('ElfFile\x00', offset=0, is_bound=True)

  test_specification = store.AddNewSpecification('ewf')
  test_specification.AddNewSignature(
      'EVF\x09\x0d\x0a\xff\x00', offset=0, is_bound=True)

  test_specification = specification.Specification('ewf_logical')
  test_specification.AddNewSignature(
      'LVF\x09\x0d\x0a\xff\x00', offset=0, is_bound=True)

  test_specification = store.AddNewSpecification('lnk')
  test_specification.AddNewSignature(
      '\x4c\x00\x00\x00\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00'
      '\x00\x00\x00\x46', offset=0)

  test_specification = store.AddNewSpecification('msiecf_index_dat')
  test_specification.AddNewSignature(
      'Client UrlCache MMF Ver ', offset=0, is_bound=True)

  test_specification = store.AddNewSpecification('nk2')
  test_specification.AddNewSignature(
      '\x0d\xf0\xad\xba\xa0\x00\x00\x00\x01\x00\x00\x00', offset=0,
      is_bound=True)

  test_specification = store.AddNewSpecification('olecf')
  test_specification.AddNewSignature(
      '\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1', offset=0, is_bound=True)
  test_specification.AddNewSignature(
      '\x0e\x11\xfc\x0d\xd0\xcf\x11\x0e', offset=0, is_bound=True)

  test_specification = store.AddNewSpecification('pff')
  test_specification.AddNewSignature('!BDN', offset=0, is_bound=True)

  test_specification = store.AddNewSpecification('qcow')
  test_specification.AddNewSignature('QFI\xfb', offset=0, is_bound=True)

  test_specification = store.AddNewSpecification('rar')
  test_specification.AddMimeType('application/x-rar-compressed')
  test_specification.AddUniversalTypeIdentifier('com.rarlab.rar-archive')
  test_specification.AddNewSignature(
      'Rar!\x1a\x07\x00', offset=0, is_bound=True)

  test_specification = store.AddNewSpecification('regf')
  test_specification.AddNewSignature('regf', offset=0, is_bound=True)

  test_specification = store.AddNewSpecification('thumbache_db_cache')
  test_specification.AddNewSignature('CMMM', offset=0, is_bound=True)

  test_specification = store.AddNewSpecification('thumbache_db_index')
  test_specification.AddNewSignature('IMMM', offset=0, is_bound=True)

  test_specification = store.AddNewSpecification('zip')
  test_specification.AddMimeType('application/zip')
  test_specification.AddUniversalTypeIdentifier('com.pkware.zip-archive')
  # WinZip 8 signature.
  test_specification.AddNewSignature('PK00', offset=0, is_bound=True)
  test_specification.AddNewSignature('PK\x01\x02')
  test_specification.AddNewSignature('PK\x03\x04', offset=0)
  test_specification.AddNewSignature('PK\x05\x05')
  # Will be at offset 0 when the archive is empty.
  test_specification.AddNewSignature('PK\x05\x06', offset=-22, is_bound=True)
  test_specification.AddNewSignature('PK\x06\x06')
  test_specification.AddNewSignature('PK\x06\x07')
  test_specification.AddNewSignature('PK\x06\x08')
  # Will be at offset 0 when this is spanned archive.
  test_specification.AddNewSignature('PK\x07\x08')

  return store
