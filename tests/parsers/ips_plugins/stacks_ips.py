#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple IPS file parser plugin for recovery logd report."""

import unittest

from plaso.parsers.ips_plugins import stacks_ips

from tests.parsers.ips_plugins import test_lib


class AppleRecoveryLogdIPSPluginTest(test_lib.IPSPluginTestCase):
  """Tests for the Apple stacks crash IPS file parser."""

  def testProcess(self):
    """Tests for the Process function."""
    plugin = stacks_ips.AppleStacksIPSPlugin()
    storage_writer = self._ParseIPSFileWithPlugin(
        ['ips_files', 'stacks-2023-02-10-100716.ips'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    expected_event_values = {
        'bug_type': '288',
        'crash_reporter_key': '5766d7cc74220076933d9cd16b3b7ade2754d67c',
        'device_model': 'iPad11,1',
        'event_time': '2023-02-10T10:07:16.000-05:00',
        'kernel_version': 'Darwin Kernel Version 22.1.0: Thu Oct  6 19:33:53 '
                          'PDT 2022; root:xnu-8792.42.7~1/RELEASE_ARM64_T8020',
        'incident_identifier': '7749B4FF-840A-46F8-BE88-2B19FF8ABFF3',
        'process_list': (
          'ACCHWComponentAuthService, ASPCarryLog, AccessibilityUIServer, '
          'AccountSubscriber, AirDrop, AppPredictionIntentsHelperServi, '
          'AppSSODaemon, AppStore, AppleCredentialManagerDaemon, '
          'AssetCacheLocatorService, AuthenticationServicesAgent, BlueTool, '
          'CAReportingService, CMFSyncAgent, CacheDeleteAppContainerCaches, '
          'CacheDeleteExtension, CalendarFocusConfigurationExten, '
          'CalendarWidgetExtension, Camera, CategoriesService, '
          'CloudKeychainProxy, CommCenter, CommCenterMobileHelper, '
          'ContainerMetadataExtractor, ContextService, DesktopServicesHelper, '
          'EnforcementService, Family, FamilyControlsAgent, Files, GSSCred, '
          'GeneralMapsWidget, GoogleNews, HeuristicInterpreter, '
          'IDSBlastDoorService, IMDPersistenceAgent, '
          'InteractiveLegacyProfilesSubscr, KonaSynthesizer, '
          'LegacyProfilesSubscriber, MTLCompilerService, MacinTalkAUSP, '
          'MailShortcutsExtension, MailWidgetExtension, ManagedSettingsAgent, '
          'ManagementTestSubscriber, MessagesActionExtension, '
          'MessagesBlastDoorService, MessagesViewService, '
          'MobileBackupCacheDeleteService, MobileCal, MobileGestaltHelper, '
          'MobileMail, MobileSMS, MobileSafari, NewsToday2, OTACrashCopier, '
          'OTATaskingAgent, PasscodeSettingsSubscriber, '
          'PerfPowerTelemetryClientRegistr, PhotosReliveWidget, PosterBoard, '
          'PowerUIAgent, Preferences, ProtectedCloudKeySyncing, '
          'RemindersWidgetExtension, ReportCrash, SBRendererService, SCHelper, '
          'SafariBookmarksSyncAgent, SafariViewService, ScreenTimeAgent, '
          'ScreenTimeWidgetExtension, ScreenshotService, SharingXPCHelper, '
          'Signal, SiriTTSSynthesizerAU, SnapchatHomeScreenWidget, Spotlight, '
          'SpringBoard, StatusKitAgent, StocksWidget, '
          'TVRemoteConnectionService, Telegram, ThreeBarsXPCService, '
          'ThumbnailExtension, ThumbnailExtensionSecure, TipsWidget, '
          'TrustedPeersHelper, UARPUpdaterServiceAFU, UARPUpdaterServiceHID, '
          'UARPUpdaterServiceLegacyAudio, UARPUpdaterServiceUSBPD, '
          'UsageTrackingAgent, UserEventAgent, UserFontManager, WeatherWidget, '
          'WiFiCloudAssetsXPCService, WidgetKitExtension, '
          'WirelessRadioManagerd, WorldClockWidget, accessoryupdaterd, '
          'accountsd, adid, adprivacyd, aggregated, akd, amfid, amsaccountsd, '
          'amsengagementd, analyticsd, aned, announced, apfs_iosd, '
          'applecamerad, appstorecomponentsd, appstored, apsd, asd, '
          'askpermissiond, assetsd, assistantd, atc, audioclocksyncd, awdd, '
          'axassetsd, backboardd, biomed, biomesyncd, biometrickitd, bird, '
          'bluetoothd, bluetoothuserd, bookassetd, calaccessd, callservicesd, '
          'captiveagent, cdpd, cfprefsd, chronod, ckdiscretionaryd, '
          'clipserviced, cloudd, cloudpaird, cloudphotod, '
          'com.apple.AppleUserHIDDrivers, com.apple.CloudDocs.MobileDocum, '
          'com.apple.DictionaryServiceHelp, com.apple.DocumentManagerCore.D, '
          'com.apple.DriverKit-AppleBCMWLA, com.apple.FaceTime.FTConversati, '
          'com.apple.MapKit.SnapshotServic, com.apple.MobileSoftwareUpdate., c'
          'om.apple.PDFKit.PDFExtensionVi, com.apple.Safari.History, '
          'com.apple.Safari.SafeBrowsing.S, com.apple.Safari.SandboxBroker, '
          'com.apple.SiriTTSService.TrialP, com.apple.StreamingUnzipService, '
          'com.apple.VideoSubscriberAccoun, com.apple.WebKit.GPU, '
          'com.apple.WebKit.Networking, com.apple.WebKit.WebContent, '
          'com.apple.accessibility.mediaac, com.apple.quicklook.ThumbnailsA, '
          'com.apple.quicklook.extension.p, com.apple.sbd, '
          'com.apple.siri.embeddedspeech, configd, contactsd, '
          'containermanagerd, contentlinkingd, contextstored, coreauthd, '
          'coreduetd, coreidvd, corespeechd, coresymbolicationd, countryd, '
          'crash_mover, ctkd, dasd, dataaccessd, deleted, deleted_helper, '
          'destinationd, diagnosticextensionsd, distnoted, dmd, donotdisturbd, '
          'dprivacyd, driverkitd, duetexpertd, extensionkitservice, '
          'fairplayd.A2, familycircled, familynotificationd, filecoordinationd,'
          ' fileproviderd, financed, findmydeviced, fitnesscoachingd, fmfd, '
          'fmflocatord, followupd, fontservicesd, fseventsd, gamecontrollerd, '
          'geod, handwritingd, healthd, homed, iconservicesagent, '
          'identityservicesd, imagent, ind, installcoordinationd, '
          'intelligenceplatformd, intents_helper, itunescloudd, itunesstored, '
          'kbd, kernel_task, keybagd, languageassetd, launchd, linkd, '
          'localizationswitcherd, locationd, lockdownd, logd, logd_helper, lsd,'
          ' mDNSResponder, maild, mapspushd, mediaanalysisd, medialibraryd, '
          'mediaremoted, mediaserverd, metrickitd, misagent, misd, '
          'mmaintenanced, mobileactivationd, mobileassetd, mobiletimerd, navd,'
          ' ndoagent, nearbyd, nehelper, nesessionmanager, networkserviceproxy,'
          ' nfcd, notifyd, nsurlsessiond, online-auth-agent, osanalyticshelper,'
          ' ospredictiond, parsec-fbf, parsecd, passd, passwordbreachd, pasted,'
          ' peopled, pfd, photoanalysisd, pipelined, pkd, powerd, '
          'privacyaccountingd, profiled, progressd, promotedcontentd, rapportd,'
          ' recentsd, remindd, remoted, remotemanagementd, '
          'remotepairingdeviced, replayd, reversetemplated, revisiond, '
          'routined, rtcreportingd, runningboardd, searchd, searchpartyd, '
          'securityd, seld, seserviced, sessionkitd, sharingd, siriactionsd, '
          'siriinferenced, siriknowledged, sociallayerd, softwareupdated, '
          'splashboardd, storekitd, studentd, suggestd, swcd, symptomsd, '
          'symptomsd-diag, syncdefaultsd, tailspind, tccd, thermalmonitord, '
          'timed, touchsetupd, translationd, transparencyd, triald, trustd, '
          'useractivityd, usermanagerd, videosubscriptionsd, voiced, watchdogd,'
          ' watchlistd, weatherd, webbookmarksd, wifianalyticsd, wifid, '
          'wifip2pd'
        ),
        'os_version': 'iPhone OS 16.1 (20B82)',
        'reason': 'sysdiagnose (stackshot only) trigger: Power + Volume Up'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
