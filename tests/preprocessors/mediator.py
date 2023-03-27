#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the preprocess mediator."""

import unittest

from plaso.containers import artifacts
from plaso.containers import sessions
from plaso.engine import knowledge_base
from plaso.preprocessors import mediator
from plaso.storage.fake import writer as fake_writer

from tests import test_lib as shared_test_lib


class PreprocessMediatorTest(shared_test_lib.BaseTestCase):
  """Tests for the preprocess mediator."""

  # pylint: disable=protected-access

  def testAddTimeZoneInformation(self):
    """Tests the AddTimeZoneInformation function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter()
    knowledge_base_object = knowledge_base.KnowledgeBase()
    preprocessor_mediator = mediator.PreprocessMediator(
        session, storage_writer, knowledge_base_object)

    time_zone_artifact = artifacts.TimeZoneArtifact(
        localized_name='Eastern (standaardtijd)', mui_form='@tzres.dll,-112',
        name='Eastern Standard Time')

    storage_writer.Open()

    try:
      preprocessor_mediator.AddTimeZoneInformation(time_zone_artifact)

      with self.assertRaises(KeyError):
        preprocessor_mediator.AddTimeZoneInformation(time_zone_artifact)

    finally:
      storage_writer.Close()

  def testProducePreprocessingWarning(self):
    """Tests the ProducePreprocessingWarning method."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter()
    knowledge_base_object = knowledge_base.KnowledgeBase()
    preprocessor_mediator = mediator.PreprocessMediator(
        session, storage_writer, knowledge_base_object)

    storage_writer.Open()

    try:
      preprocessor_mediator.ProducePreprocessingWarning(
          'test_plugin', 'test message')
    finally:
      storage_writer.Close()

  def testSetTimeZone(self):
    """Tests the SetTimeZone function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter()
    knowledge_base_object = knowledge_base.KnowledgeBase()
    preprocessor_mediator = mediator.PreprocessMediator(
        session, storage_writer, knowledge_base_object)

    time_zone_artifact = artifacts.TimeZoneArtifact(
        localized_name='Eastern (standaardtijd)', mui_form='@tzres.dll,-112',
        name='Eastern Standard Time')

    storage_writer.Open()

    try:
      preprocessor_mediator.AddTimeZoneInformation(time_zone_artifact)
    finally:
      storage_writer.Close()

    # Set an IANA time zone name.
    preprocessor_mediator.SetTimeZone('Europe/Zurich')
    self.assertEqual(knowledge_base_object._time_zone.zone, 'Europe/Zurich')

    # Set a Windows time zone name.
    preprocessor_mediator.SetTimeZone('Eastern Standard Time')
    self.assertEqual(knowledge_base_object._time_zone.zone, 'America/New_York')

    # Set a localized Windows time zone name.
    preprocessor_mediator.SetTimeZone('Eastern (standaardtijd)')
    self.assertEqual(knowledge_base_object._time_zone.zone, 'America/New_York')

    # Set a MUI form Windows time zone name.
    preprocessor_mediator.SetTimeZone('@tzres.dll,-112')
    self.assertEqual(knowledge_base_object._time_zone.zone, 'America/New_York')

    with self.assertRaises(ValueError):
      preprocessor_mediator.SetTimeZone('Bogus')


if __name__ == '__main__':
  unittest.main()
