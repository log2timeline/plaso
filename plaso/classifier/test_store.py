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
"""This file contains a function to create test specification store."""


from plaso.classifier import specification


def CreateSpecificationStore():
  """Creates a specification store for testing purposes.

  Returns:
    an instance of SpecificationStore.
  """
  store = specification.SpecificationStore()

  test_specification = store.AddSpecification("7zip")
  test_specification.AddMimeType("application/x-7z-compressed")
  test_specification.AddUniversalTypeIdentifier("org.7-zip.7-zip-archive")
  test_specification.AddSignature("7z\xbc\xaf\x27\x1c", offset=0)

  test_specification = store.AddSpecification("esedb")
  test_specification.AddSignature("\xef\xcd\xab\x89", offset=4, is_bound=True)

  test_specification = store.AddSpecification("evt")
  test_specification.AddSignature(
      "\x30\x00\x00\x00LfLe\x01\x00\x00\x00\x01\x00\x00\x00", offset=0,
      is_bound=True)

  test_specification = store.AddSpecification("evtx")
  test_specification.AddSignature("ElfFile\x00", offset=0, is_bound=True)

  test_specification = store.AddSpecification("ewf")
  test_specification.AddSignature(
      "EVF\x09\x0d\x0a\xff\x00", offset=0, is_bound=True)

  test_specification = specification.Specification("ewf_logical")
  test_specification.AddSignature(
      "LVF\x09\x0d\x0a\xff\x00", offset=0, is_bound=True)

  test_specification = store.AddSpecification("lnk")
  test_specification.AddSignature(
      "\x4c\x00\x00\x00\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00"
      "\x00\x00\x00\x46", offset=0)

  test_specification = store.AddSpecification("msiecf_index_dat")
  test_specification.AddSignature(
      "Client UrlCache MMF Ver ", offset=0, is_bound=True)

  test_specification = store.AddSpecification("nk2")
  test_specification.AddSignature(
      "\x0d\xf0\xad\xba\xa0\x00\x00\x00\x01\x00\x00\x00", offset=0,
      is_bound=True)

  test_specification = store.AddSpecification("olecf")
  test_specification.AddSignature(
      "\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", offset=0, is_bound=True)
  test_specification.AddSignature(
      "\x0e\x11\xfc\x0d\xd0\xcf\x11\x0e", offset=0, is_bound=True)

  test_specification = store.AddSpecification("pff")
  test_specification.AddSignature("!BDN", offset=0, is_bound=True)

  test_specification = store.AddSpecification("qcow")
  test_specification.AddSignature("QFI\xfb", offset=0, is_bound=True)

  test_specification = store.AddSpecification("rar")
  test_specification.AddMimeType("application/x-rar-compressed")
  test_specification.AddUniversalTypeIdentifier("com.rarlab.rar-archive")
  test_specification.AddSignature("Rar!\x1a\x07\x00", offset=0, is_bound=True)

  test_specification = store.AddSpecification("regf")
  test_specification.AddSignature("regf", offset=0, is_bound=True)

  test_specification = store.AddSpecification("thumbache_db_cache")
  test_specification.AddSignature("CMMM", offset=0, is_bound=True)

  test_specification = store.AddSpecification("thumbache_db_index")
  test_specification.AddSignature("IMMM", offset=0, is_bound=True)

  test_specification = store.AddSpecification("zip")
  test_specification.AddMimeType("application/zip")
  test_specification.AddUniversalTypeIdentifier("com.pkware.zip-archive")
  test_specification.AddSignature("PK00", offset=0, is_bound=True)  # WinZip 8
  test_specification.AddSignature("PK\x01\x02")
  test_specification.AddSignature("PK\x03\x04", offset=0)
  test_specification.AddSignature("PK\x05\x05")
  # will be at offset 0 when the archive is empty
  test_specification.AddSignature("PK\x05\x06")
  test_specification.AddSignature("PK\x06\x06")
  test_specification.AddSignature("PK\x06\x07")
  test_specification.AddSignature("PK\x06\x08")
  # will be at offset 0 when this is spanned archive
  test_specification.AddSignature("PK\x07\x08")

  return store
