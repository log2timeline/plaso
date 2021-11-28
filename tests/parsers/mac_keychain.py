#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Keychain password database parser."""

import unittest

from plaso.lib import definitions
from plaso.parsers import mac_keychain

from tests.parsers import test_lib


class MacKeychainParserTest(test_lib.ParserTestCase):
  """Tests for keychain file parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = mac_keychain.KeychainParser()
    storage_writer = self._ParseFile(['login.keychain'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 8)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_ssgp = (
        'b8e44863af1cb0785b89681d22e2721997ccfb8adb8853e726aff94c8830b05a')

    expected_event_values = {
        'account_name': 'moxilo',
        'data_type': 'mac:keychain:application',
        'date_time': '2014-01-26 14:51:48',
        'entry_name': 'Secret Application',
        'ssgp_hash': expected_ssgp,
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:keychain:application',
        'date_time': '2014-01-26 14:52:29',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_ssgp = (
        '72bd40987413638e081b8d1497573343f193ab4574c08f08cb618ca729488a68'
        '2fd9f179c2134ab89c2096a3f335eb61bf4377ca15209197c5ead3a775149db3'
        'c5a306d1a2db4f9c3c20949280892c994049a55e8323a7d51b9c51826057d743'
        'ced5f6fb23a2fea5de833fe49fbd92bf7a4d536d64cca1abf9ee09f92025e48e'
        '41331fbd7801d81f953a39b1d8c523cd0575834240e5e566b1aaf31b960dfd77'
        '4a180958f6c06e372ea0a8b211d3f9a1c207984b6e51c55904ddaf9ac12bc4bf'
        '255356178b07bfaa70de9ece90420f0a289b4a73f63c624d9e6a138b6dbb0559'
        '64641e7526167712f205b7333dec36063127c66fc1633c3c0aac6833b3487894'
        '8b2d45270ce754a07c8f06beb18d98ca9565fa7c57cca083804b8a96dfbf7d5f'
        '5c24c1c391f1a38ecf8d6919b21a398ce89bdffd0aa99eb60a3c4ad9c1d0d074'
        '143ad0e71d5986bf8bf13f166c61cff3bc384e3a79f6f6c57ed52fef2c66d267'
        'bab006e6e2495afb55162bf0b88111b2429c83bb7b59a54df745aa23055d7b0f'
        'd6c0543203397640b46109e1382441945447457461aa01edc75169f2b462d508'
        '7519957ab587e07203ad1377ad76255a5a64398fe329760951bd8bca7bbe8c2b'
        '4d8b987370a6c7eb05613051d19a4d0f588e05a1a51e43831a2b07b7d50a6379'
        '130f6fb2bbeab2b016899fca2e9d8e60429da995da9de0f326eb498212a6671f'
        '0125402cc387371f61775008fa049b446df792704880f45869dd4b7c89b77f58'
        '06fe61faf7e790e59ba02d5e8b8dd880313fc5921bee4d5e9d0a67c1c16f898d'
        'cc99cd403f63e652109ee4be4c28bbbf98cfe59047145f9fbface4ebf4f1ce1e'
        '4d7d108a689e2744b464ed539a305f3b40fe8248b93556d14810d70469457651'
        'c507af61bd692622f30996bfa8ac8aa29f712b6d035883ae37855e223de43a85'
        '9264ecea0f2b5b87396cb030edc79d1943eb53267137d1e5fbbe2fb74756ecb1'
        '58d8e81008453a537085d67feeddb155a8c3f76deecb02d003d8d16c487111c4'
        'b43518ec66902876aab00a5dcfd3cc6fc713a1b9bdba533d84bd7b4a3d9f778e'
        'd7ee477a53df012a778b2d833d2a18cb88b23ca69b0806bb38bd38fbbc78e261'
        '15a8b465ceaa8bfa8ecb97a446bc12434da6d2dd7355ec3c7297960f4b996e5b'
        '22e8f256c6094d7f2ed4f7c89c060faf')

    expected_event_values = {
        'data_type': 'mac:keychain:application',
        'date_time': '2014-01-26 14:53:29',
        'entry_name': 'Secret Note',
        'ssgp_hash': expected_ssgp,
        'text_description': 'secure note'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_ssgp = (
        '83ccacf55a8cb656d340ec405e9d8b308fac54bb79c5c9b0219bd0d700c3c521')

    expected_event_values = {
        'account_name': 'MrMoreno',
        'data_type': 'mac:keychain:internet',
        'date_time': '2014-01-26 14:54:33',
        'entry_name': 'plaso.kiddaland.net',
        'protocol': 'http',
        'ssgp_hash': expected_ssgp,
        'type_protocol': 'dflt',
        'where': 'plaso.kiddaland.net'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)


if __name__ == '__main__':
  unittest.main()
