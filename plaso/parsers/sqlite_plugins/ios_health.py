"""SQLite parser plugin for iOS Health (healthdb_secure.sqlite) database."""

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthAchievementsEventData(events.EventData):
    """iOS Health achievement event data.

    Attributes:
      creation_time (dfdatetime.DateTimeValues): data and time of the creation of the
          achievement.
      creator_device (int): identifier of the device that created the achievement.
      earned_date (str): Date the achievement was earned.
      synchronization_provenance (int): synchronization provenance.
      template_unique_name (str): Unique name of the achievement template.
      value_canonical_unit (str): Unit of the value (e.g., "count").
      value_in_canonical_unit (float): Value of the achievement in canonical units.
    """

    DATA_TYPE = "ios:health:achievement"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.creation_time = None
        self.creator_device = None
        self.earned_date = None
        self.synchronization_provenance = None
        self.template_unique_name = None
        self.value_canonical_unit = None
        self.value_in_canonical_unit = None


class IOSHealthAllWatchSleepEventData(events.EventData):
    """iOS Health all watch sleep event data.

    Attributes:
      duration (float): duration in seconds.
      end_time (dfdatetime.DateTimeValues): date and time the sleep ended.
      sleep_state_code (int): sleep state code.
      start_time (dfdatetime.DateTimeValues): date and time the sleep started.
    """

    DATA_TYPE = "ios:health:all_watch_sleep"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.duration = None
        self.end_time = None
        self.sleep_state_code = None
        self.start_time = None


class IOSHealthHeadphoneAudioEventData(events.EventData):
    """iOS Health Headphone Audio Levels event data.

    Attributes:
      bundle_identifier (str): application bundle identifier.
      decibels (float): sound level from quantity_samples.quantity.
      device_local_identifier, (str): device local identifier.
      device_manufacturer (str): source_devices.manufacturer.
      device_model (str): source_devices.model.
      device_name (str): source_devices.name.
      end_time (dfdatetime.DateTimeValues): Cocoa time end date.
      start_time (dfdatetime.DateTimeValues): Cocoa time start date.
    """

    DATA_TYPE = "ios:health:headphone_audio_levels"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.bundle_identifier = None
        self.decibels = None
        self.device_local_identifier = None
        self.device_manufacturer = None
        self.device_model = None
        self.device_name = None
        self.end_time = None
        self.start_time = None


class IOSHealthHeartRateEventData(events.EventData):
    """iOS Health heart rate (sample) event data.

    Attributes:
      added_time (dfdatetime.DateTimeValues): data and time the sample was added to the
          database.
      bpm (int): beats per minute.
      context (float): context.
      device_name (str): source device name.
      end_time (dfdatetime.DateTimeValues): date and time the sample ended.
      hardware (str): source device hardware.
      manufacturer (str): source device manufacturer.
      series_count (int): quantity_sample_series.count.
      series_key (str): quantity_sample_series.hfd_key.
      software_version (str): software version.
      source_name (str): source name.
      source_options (str): source options.
      start_time (dfdatetime.DateTimeValues): date and time the sample started.
      time_zone (str): time zone.
    """

    DATA_TYPE = "ios:health:heart_rate"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.added_time = None
        self.bpm = None
        self.context = None
        self.device_name = None
        self.end_time = None
        self.hardware = None
        self.manufacturer = None
        self.series_count = None
        self.series_key = None
        self.software_version = None
        self.source_name = None
        self.source_options = None
        self.start_time = None
        self.time_zone = None


class IOSHealthHeightEventData(events.EventData):
    """iOS Health height (sample) event data.

    Attributes:
      height (float): height in meters.
      start_time (dfdatetime.DateTimeValues): date and time the sample started.
    """

    DATA_TYPE = "ios:health:height"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.height = None
        self.start_time = None


# TODO: merge with IOSHealthHeartRateEventData
class IOSHealthRestingHeartRateEventData(events.EventData):
    """iOS Health resting heart rate (sample) event data.

    Attributes:
      added_time (dfdatetime.DateTimeValues): date and time the sample was added to the
          database.
      end_time (dfdatetime.DateTimeValues): date and time the sample ended.
      hardware (str): device hardware.
      resting_heart_rate (int): resting heart rate in beats per minute (BPM).
      source_name (str): source name.
      start_time (dfdatetime.DateTimeValues): date and time the sample started.
    """

    DATA_TYPE = "ios:health:resting_heart_rate"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.added_time = None
        self.end_time = None
        self.hardware = None
        self.resting_heart_rate = None
        self.source_name = None
        self.start_time = None


class IOSHealthSourceDevicesEventData(events.EventData):
    """iOS Health Source Devices event data.

    Attributes:
      added_time (dfdatetime.DateTimeValues): date and time the device was added to the
          database.
      device_name (str): name of the device.
      firmware (str): firmware version of the device.
      hardware (str): hardware version of the device.
      local_identifier (str): local identifier.
      manufacturer (str): manufacturer of the device.
      model (str): model of the device.
      software (str): software version of the device.
      synchronization_identity (int): synchronization identifier.
      synchronization_provenance (int): synchronization provenance.
    """

    DATA_TYPE = "ios:health:source_devices"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.added_time = None
        self.device_name = None
        self.firmware = None
        self.hardware = None
        self.local_identifier = None
        self.manufacturer = None
        self.model = None
        self.software = None
        self.synchronization_identity = None
        self.synchronization_provenance = None


class IOSHealthStepsEventData(events.EventData):
    """iOS Health steps (sample) event data.

    Attributes:
      device (str): device used to record the data (e.g. Apple Watch).
      duration (float): duration in seconds.
      end_time (dfdatetime.DateTimeValues): date and time the sample ended.
      number_of_steps (float): total number of steps.
      start_time (dfdatetime.DateTimeValues): date and time the sample started.
    """

    DATA_TYPE = "ios:health:steps"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.device = None
        self.duration = None
        self.end_time = None
        self.number_of_steps = None
        self.start_time = None


class IOSHealthWeightEventData(events.EventData):
    """iOS Health weight (sample) event data.

    Attributes:
      start_time (dfdatetime.DateTimeValues): date and time the sample started.
      weight (float): Weight in kilograms.
    """

    DATA_TYPE = "ios:health:weight"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.start_time = None
        self.weight = None


class IOSHealthWorkoutsEventData(events.EventData):
    """iOS Health workouts event data.

    Attributes:
      activity_type (str): workout activity type.
      duration (float): duration in seconds.
      end_time (dfdatetime.DateTimeValues): date and time the sample ended.
      goal (str): workout goal value.
      goal_type (str): workout goal type.
      start_time (dfdatetime.DateTimeValues): date and time the sample started.
      total_basal_energy_burned (float): basal energy (kcal).
      total_distance (float): total distance in kilometers.
      total_energy_burned (float): active energy (kcal).
      total_flights_climbed (float): flights climbed total.
      total_weekly_steps (float): steps total.
    """

    DATA_TYPE = "ios:health:workouts"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.activity_type = None
        self.duration = None
        self.end_time = None
        self.goal = None
        self.goal_type = None
        self.start_time = None
        self.total_basal_energy_burned = None
        self.total_distance = None
        self.total_energy_burned = None
        self.total_flights_climbed = None
        self.total_weekly_steps = None


class IOSHealthWristTemperatureEventData(events.EventData):
    """iOS Health wrist temperature event data.

    Attributes:
      added_time (dfdatetime.DateTimeValues): data and time the sample was added to the
          database.
      algorithm_version (float): algorithm version.
      device_hardware (str): device hardware.
      device_manufacturer (str): device manufacturer.
      device_model (str): device model.
      device_name (str): device name.
      end_time (dfdatetime.DateTimeValues): date and time the sample ended.
      software_version (str): software version.
      source_name (str): source name.
      start_time (dfdatetime.DateTimeValues): date and time the sample started.
      surface_temperature (float): skin surface temperature in Celsius (°C).
      wrist_temperature (float): wrist temperature in Celsius (°C).
    """

    DATA_TYPE = "ios:health:wrist_temperature"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.added_time = None
        self.algorithm_version = None
        self.device_hardware = None
        self.device_manufacturer = None
        self.device_model = None
        self.device_name = None
        self.end_time = None
        self.software_version = None
        self.source_name = None
        self.start_time = None
        self.surface_temperature = None
        self.wrist_temperature = None


class IOSHealthPlugin(interface.SQLitePlugin):
    """SQLite parser plugin for iOS Health ((healthdb_secure.sqlite) database."""

    NAME = "ios_health"
    DATA_FORMAT = "iOS Health SQLite database (healthdb_secure.sqlite) file"

    _OBJECT_VALUE_QUERY = (
        "SELECT metadata_values.value_type AS value_type, "
        "metadata_values.string_value AS string_value, "
        "metadata_values.numerical_value AS numerical_value, "
        "metadata_values.date_value AS date_value, "
        "metadata_values.data_value AS data_value, "
        "metadata_keys.key as key "
        "FROM metadata_values JOIN metadata_keys "
        "ON metadata_keys.ROWID = metadata_values.key_id "
        "WHERE metadata_values.object_id = {0:d}"
    )

    REQUIRED_STRUCTURE = {
        "ACHAchievementsPlugin_earned_instances": frozenset(
            [
                "created_date",
                "creator_device",
                "earned_date",
                "sync_provenance",
                "template_unique_name",
                "value_canonical_unit",
                "value_in_canonical_unit",
            ]
        ),
        "data_provenances": frozenset(
            ["ROWID", "device_id", "source_id", "source_version", "tz_name"]
        ),
        "metadata_keys": frozenset(["ROWID", "key"]),
        "metadata_values": frozenset(["key_id", "numerical_value", "object_id"]),
        "objects": frozenset(["creation_date", "data_id", "provenance", "type"]),
        "quantity_samples": frozenset(["data_id", "quantity"]),
        "samples": frozenset(["data_id", "data_type", "end_date", "start_date"]),
        "source_devices": frozenset(
            [
                "ROWID",
                "creation_date",
                "firmware",
                "hardware",
                "localIdentifier",
                "manufacturer",
                "model",
                "name",
                "software",
                "sync_provenance",
            ]
        ),
        "sources": frozenset(["ROWID", "name", "product_type", "source_options"]),
        "workouts": frozenset(
            [
                "activity_type",
                "duration",
                "goal",
                "goal_type",
                "total_basal_energy_burned",
                "total_distance",
                "total_energy_burned",
                "total_flights_climbed",
                "total_w_steps",
            ]
        ),
    }

    QUERIES = [
        (
            (
                "SELECT template_unique_name, created_date, earned_date, "
                "value_in_canonical_unit, value_canonical_unit, creator_device, "
                "sync_provenance FROM ACHAchievementsPlugin_earned_instances"
            ),
            "_ParseAchievementRow",
        ),
        (
            (
                "SELECT "
                "data_provenances.origin_product_type AS origin_product_type, "
                "data_provenances.source_version AS software_version, "
                "data_provenances.tz_name AS tz_name, "
                "category_samples.value AS category_value, "
                "objects.creation_date AS creation_date, "
                "objects.type AS object_type, "
                "quantity_samples.quantity as quantity, "
                "samples.data_id AS sample_data_identifier, "
                "samples.data_type AS sample_type, "
                "samples.end_date AS end_date, "
                "samples.start_date AS start_date, "
                "source_devices.hardware AS device_hardware, "
                "source_devices.localIdentifier AS device_local_identifier, "
                "source_devices.manufacturer AS device_manufacturer, "
                "source_devices.model AS device_model, "
                "source_devices.name AS device_name, "
                "sources.name AS source_name, "
                "sources.product_type AS source_product_type, "
                "sources.source_options AS source_options "
                "FROM samples "
                "LEFT JOIN category_samples "
                "ON samples.data_id = category_samples.data_id "
                "LEFT JOIN objects ON objects.data_id = samples.data_id "
                "LEFT JOIN quantity_samples "
                "ON quantity_samples.data_id = samples.data_id "
                "LEFT JOIN data_provenances "
                "ON data_provenances.ROWID = objects.provenance "
                "LEFT JOIN source_devices "
                "ON source_devices.ROWID = data_provenances.device_id "
                "LEFT JOIN sources ON sources.ROWID = data_provenances.source_id"
            ),
            "_ParseSamplesRow",
        ),
        (
            # TODO: remove filter on __NONE__ handle this in _ParseSourceDevicesRow
            (
                "SELECT creation_date, firmware, hardware, localIdentifier, "
                "manufacturer, model, name, software, sync_provenance "
                "FROM source_devices WHERE name NOT LIKE '__NONE__' AND "
                "localIdentifier NOT LIKE '__NONE__'"
            ),
            "_ParseSourceDevicesRow",
        ),
        (
            (
                "SELECT samples.start_date AS start_date, "
                "samples.end_date AS end_date, "
                "workouts.activity_type AS activity_type, "
                "workouts.duration AS duration, "
                "workouts.total_distance AS total_distance, "
                "workouts.total_energy_burned AS total_energy_burned, "
                "workouts.total_basal_energy_burned AS total_basal_energy_burned, "
                "workouts.goal_type AS goal_type, workouts.goal AS goal, "
                "workouts.total_flights_climbed AS total_flights_climbed, "
                "workouts.total_w_steps AS total_w_steps "
                "FROM workouts LEFT JOIN samples ON samples.data_id = workouts.data_id"
            ),
            "_ParseWorkoutsRow",
        ),
    ]

    SCHEMAS = [
        {
            "ACHAchievementsPlugin_earned_instances": (
                "CREATE TABLE ACHAchievementsPlugin_earned_instances (ROWID INTEGER "
                "PRIMARY KEY AUTOINCREMENT, template_unique_name TEXT, created_date "
                "REAL, earned_date TEXT, value_in_canonical_unit REAL, "
                "value_canonical_unit TEXT, creator_device INTEGER, sync_provenance "
                "INTEGER)"
            ),
            "ACHAchievementsPlugin_templates": (
                "CREATE TABLE ACHAchievementsPlugin_templates (ROWID INTEGER "
                "PRIMARY KEY AUTOINCREMENT, unique_name TEXT UNIQUE NOT NULL, "
                "version INTEGER, minimum_engine_version INTEGER, created_date "
                "REAL, creator_device INTEGER, source_name TEXT, predicate TEXT, "
                "value_expression TEXT, progress_expression TEXT, goal_expression "
                "TEXT, triggers INTEGER, earn_limit INTEGER, visibility_predicate "
                "TEXT, visibility_start_date TEXT, visibility_end_date TEXT, "
                "availability_predicate TEXT, availability_start_date TEXT, "
                "availability_end_date TEXT, available_country_codes TEXT, "
                "alertability_predicate TEXT, alert_dates TEXT, "
                "duplicateremoval_strategy INTEGER, duplicateremoval_calendar_unit "
                "INTEGER, earn_date INTEGER, display_order INTEGER, "
                "displays_earned_instance_count INTEGER, canonical_unit TEXT, "
                "sync_provenance INTEGER, available_suffixes TEXT, grace_predicate "
                "TEXT, grace_visibility_predicate TEXT, grace_value_expression "
                "TEXT, grace_progress_expression TEXT, grace_goal_expression TEXT)"
            ),
            "account_owner_samples": (
                "CREATE TABLE account_owner_samples (data_id INTEGER PRIMARY KEY, "
                "name TEXT NOT NULL, birth_date BLOB)"
            ),
            "activity_caches": (
                "CREATE TABLE activity_caches (data_id INTEGER PRIMARY KEY "
                "REFERENCES samples (data_id) ON DELETE CASCADE, cache_index "
                "INTEGER, sequence INTEGER NOT NULL, activity_mode INTEGER, "
                "wheelchair_use INTEGER, energy_burned REAL, energy_burned_goal "
                "REAL, energy_burned_goal_date REAL, move_minutes REAL, "
                "move_minutes_goal REAL, move_minutes_goal_date REAL, brisk_minutes "
                "REAL, brisk_minutes_goal REAL, brisk_minutes_goal_date REAL, "
                "active_hours REAL, active_hours_goal REAL, active_hours_goal_date "
                "REAL, steps REAL, pushes REAL, walk_distance REAL, "
                "deep_breathing_duration REAL, flights INTEGER, energy_burned_stats "
                "BLOB, move_minutes_stats BLOB, brisk_minutes_stats BLOB)"
            ),
            "activitysharing_competition_lists": (
                "CREATE TABLE activitysharing_competition_lists (data_id INTEGER "
                "PRIMARY KEY, friend_uuid BLOB, type INTEGER, system_fields BLOB, "
                "owner INTEGER, UNIQUE(friend_uuid, type))"
            ),
            "activitysharing_competitions": (
                "CREATE TABLE activitysharing_competitions (data_id INTEGER PRIMARY "
                "KEY, friend_uuid BLOB, competition_uuid BLOB, competition_type "
                "INTEGER, current_cache_index INTEGER, last_pushed_cache_index "
                "INTEGER, scores BLOB, opponent_scores BLOB, start_date_components "
                "BLOB, duration_date_components BLOB, "
                "preferred_victory_badge_styles BLOB, maximum_points_per_day "
                "INTEGER, UNIQUE(friend_uuid, competition_uuid))"
            ),
            "allergy_record_samples": (
                "CREATE TABLE allergy_record_samples (data_id INTEGER PRIMARY KEY, "
                "allergy_codings BLOB NOT NULL, onset_date BLOB, asserter TEXT, "
                "reactions BLOB, criticality_coding BLOB, last_occurence_date BLOB, "
                "recorded_date BLOB, status_coding BLOB)"
            ),
            "binary_samples": (
                "CREATE TABLE binary_samples (data_id INTEGER PRIMARY KEY "
                "REFERENCES samples (data_id) ON DELETE CASCADE, payload BLOB)"
            ),
            "category_samples": (
                "CREATE TABLE category_samples (data_id INTEGER PRIMARY KEY, value "
                "INTEGER)"
            ),
            "cda_documents": (
                "CREATE TABLE cda_documents (data_id INTEGER PRIMARY KEY REFERENCES "
                "samples (data_id) ON DELETE CASCADE, document_data BLOB, title "
                "TEXT NOT NULL, patient_name TEXT NOT NULL, author_name TEXT NOT "
                "NULL, custodian_name TEXT NOT NULL)"
            ),
            "clinical_accounts": (
                "CREATE TABLE clinical_accounts (ROWID INTEGER PRIMARY KEY "
                "AUTOINCREMENT, identifier BLOB NOT NULL UNIQUE, user_enabled_flag "
                "INTEGER NOT NULL, relogin_needed_flag INTEGER NOT NULL, "
                "creation_date REAL NOT NULL, last_fetch_date REAL, "
                "last_full_fetch_date REAL, last_extracted_rowid INTEGER, "
                "last_submitted_rowid INTEGER, last_extracted_rules_version "
                "INTEGER, patient_hash TEXT, credential_id INTEGER REFERENCES "
                "clinical_credentials (ROWID) ON DELETE SET NULL, gateway_id "
                "INTEGER NOT NULL UNIQUE REFERENCES clinical_gateways (ROWID) ON "
                "DELETE NO ACTION, sync_identifier BLOB NOT NULL UNIQUE, "
                "modification_date REAL NOT NULL, sync_anchor INTEGER NOT NULL "
                "UNIQUE, sync_provenance INTEGER NOT NULL)"
            ),
            "clinical_authorization_sessions": (
                "CREATE TABLE clinical_authorization_sessions (ROWID INTEGER "
                "PRIMARY KEY AUTOINCREMENT, query TEXT NOT NULL, state BLOB NOT "
                "NULL UNIQUE, code TEXT, creation_date REAL NOT NULL, gateway_id "
                "INTEGER REFERENCES clinical_gateways (ROWID) ON DELETE CASCADE, "
                "account_id INTEGER REFERENCES clinical_accounts (ROWID) ON DELETE "
                "CASCADE, CHECK((account_id IS NULL AND gateway_id IS NOT NULL) OR "
                "(account_id IS NOT NULL AND gateway_id IS NULL)))"
            ),
            "clinical_credentials": (
                "CREATE TABLE clinical_credentials (ROWID INTEGER PRIMARY KEY "
                "AUTOINCREMENT, identifier BLOB NOT NULL, expiration_date REAL, "
                "scope TEXT, patient_id TEXT, creation_date REAL NOT NULL)"
            ),
            "clinical_deleted_accounts": (
                "CREATE TABLE clinical_deleted_accounts (ROWID INTEGER PRIMARY KEY "
                "AUTOINCREMENT, sync_identifier BLOB NOT NULL, deletion_date REAL "
                "NOT NULL, sync_provenance INTEGER NOT NULL, "
                "UNIQUE(sync_identifier))"
            ),
            "clinical_gateways": (
                "CREATE TABLE clinical_gateways (ROWID INTEGER PRIMARY KEY "
                "AUTOINCREMENT, external_id TEXT NOT NULL, last_reported_status "
                "INTEGER NOT NULL, revision INTEGER NOT NULL, raw_content BLOB NOT "
                "NULL, sync_anchor INTEGER NOT NULL UNIQUE, sync_provenance INTEGER "
                "NOT NULL, UNIQUE(external_id))"
            ),
            "clinical_record_samples": (
                "CREATE TABLE clinical_record_samples (data_id INTEGER PRIMARY KEY, "
                "display_name TEXT NOT NULL, fhir_resource_resource_type TEXT, "
                "fhir_resource_identifier TEXT, fhir_resource_data BLOB, "
                "fhir_resource_source_url TEXT, fhir_resource_last_updated_date "
                "REAL)"
            ),
            "concept_index": (
                "CREATE TABLE concept_index (ROWID INTEGER PRIMARY KEY "
                "AUTOINCREMENT, sample_uuid BLOB NOT NULL, concept_identifier "
                "INTEGER NOT NULL, version INTEGER NOT NULL, key_path TEXT NOT "
                "NULL, compound_index INTEGER, type INTEGER, ontology_version "
                "INTEGER NOT NULL DEFAULT 0)"
            ),
            "condition_record_samples": (
                "CREATE TABLE condition_record_samples (data_id INTEGER PRIMARY "
                "KEY, condition_codings BLOB NOT NULL, category_codings BLOB NOT "
                "NULL, asserter TEXT, abatement BLOB, onset BLOB, recorded_date "
                "BLOB, clinical_status_coding BLOB, verification_status_coding "
                "BLOB, severity_codings BLOB, body_sites_codings BLOB)"
            ),
            "correlations": (
                "CREATE TABLE correlations (ROWID INTEGER PRIMARY KEY "
                "AUTOINCREMENT, correlation INTEGER, object INTEGER, provenance "
                "INTEGER, UNIQUE(correlation, object))"
            ),
            "data_provenances": (
                "CREATE TABLE data_provenances (ROWID INTEGER PRIMARY KEY "
                "AUTOINCREMENT, sync_provenance INTEGER NOT NULL, "
                "origin_product_type TEXT NOT NULL, origin_build TEXT NOT NULL, "
                "local_product_type TEXT NOT NULL, local_build TEXT NOT NULL, "
                "source_id INTEGER NOT NULL, device_id INTEGER NOT NULL, "
                "source_version TEXT NOT NULL, tz_name TEXT NOT NULL, "
                "origin_major_version INTEGER NOT NULL, origin_minor_version "
                "INTEGER NOT NULL, origin_patch_version INTEGER NOT NULL, "
                "derived_flags INTEGER NOT NULL, UNIQUE(sync_provenance, "
                "origin_product_type, origin_build, local_product_type, "
                "local_build, source_id, device_id, source_version, tz_name, "
                "origin_major_version, origin_minor_version, origin_patch_version))"
            ),
            "data_series": (
                "CREATE TABLE data_series (data_id INTEGER PRIMARY KEY REFERENCES "
                "samples (data_id) ON DELETE CASCADE, frozen INTEGER NOT NULL "
                "DEFAULT 0, count INTEGER NOT NULL DEFAULT 0, insertion_era INTEGER "
                "NOT NULL DEFAULT 0, hfd_key INTEGER UNIQUE NOT NULL)"
            ),
            "devices": (
                "CREATE TABLE devices (ROWID INTEGER PRIMARY KEY AUTOINCREMENT, "
                "device_uuid BLOB, device_name TEXT, device_service INTEGER, "
                "device_last_connect REAL, device_enabled BOOLEAN default 1, "
                "UNIQUE(device_uuid, device_service))"
            ),
            "diagnostic_test_report_samples": (
                "CREATE TABLE diagnostic_test_report_samples (data_id INTEGER "
                "PRIMARY KEY, diagnostic_test_codings BLOB, panel_name TEXT NOT "
                "NULL, results BLOB, effective_start_date BLOB, status_coding BLOB "
                "NOT NULL, effective_end_date BLOB, issue_date BLOB NOT NULL)"
            ),
            "diagnostic_test_result_samples": (
                "CREATE TABLE diagnostic_test_result_samples (data_id INTEGER "
                "PRIMARY KEY, diagnostic_test_codings BLOB NOT NULL, value BLOB, "
                "reference_ranges BLOB, effective_start_date BLOB, category TEXT "
                "NOT NULL, issue_date BLOB, effective_end_date BLOB, status_coding "
                "BLOB NOT NULL, interpretation_codings BLOB, comments TEXT, "
                "body_site_codings BLOB, method_codings BLOB, performers BLOB)"
            ),
            "external_sync_ids": (
                "CREATE TABLE external_sync_ids (object_id INTEGER PRIMARY KEY "
                "REFERENCES objects (data_id) ON DELETE CASCADE, source_id INTEGER "
                "NOT NULL, object_code INTEGER NOT NULL, sid TEXT NOT NULL, version "
                "REAL NOT NULL, deleted INTEGER NON NULL)"
            ),
            "fitness_friend_achievements": (
                "CREATE TABLE fitness_friend_achievements (data_id INTEGER PRIMARY "
                "KEY, friend_uuid BLOB, template_unique_name TEXT, completed_date "
                "REAL, value)"
            ),
            "fitness_friend_activity_snapshots": (
                "CREATE TABLE fitness_friend_activity_snapshots (data_id INTEGER "
                "PRIMARY KEY, friend_uuid BLOB, active_hours REAL, "
                "active_hours_goal REAL, brisk_minutes REAL, brisk_minutes_goal "
                "REAL, energy_burned REAL, energy_burned_goal REAL, move_minutes "
                "REAL, move_minutes_goal REAL, activity_move_mode INTEGER, steps "
                "REAL, walk_run_distance REAL, snapshot_index INTEGER, source_uuid "
                "BLOB, uploaded_date REAL, vulcan_count REAL, vulcan_condition "
                "INTEGER, timezone_offset INTEGER, UNIQUE(friend_uuid, "
                "snapshot_index, source_uuid))"
            ),
            "fitness_friend_workouts": (
                "CREATE TABLE fitness_friend_workouts (data_id INTEGER PRIMARY KEY, "
                "friend_uuid BLOB, duration REAL, total_energy_burned REAL, "
                "total_basal_energy_burned REAL, total_distance REAL, activity_type "
                "INTEGER, goal_type INTEGER, goal REAL, bundle_id TEXT, "
                "is_watch_workout INTEGER, is_indoor_workout INTEGER, "
                "device_manufacturer TEXT, device_model TEXT, activity_move_mode "
                "INTEGER DEFAULT 0)"
            ),
            "key_value_secure": (
                "CREATE TABLE key_value_secure (ROWID INTEGER PRIMARY KEY "
                "AUTOINCREMENT, category INTEGER NOT NULL, domain TEXT NOT NULL, "
                "key TEXT NOT NULL, value, provenance INTEGER NOT NULL, mod_date "
                "REAL NOT NULL, UNIQUE(category, domain, key))"
            ),
            "medical_records": (
                "CREATE TABLE medical_records (data_id INTEGER PRIMARY KEY, note "
                "TEXT, entered_in_error INTEGER NON NULL, modified_date REAL, "
                "fhir_identifier TEXT NON NULL, locale TEXT, extraction_version "
                "INTEGER NON NULL, sort_date REAL NON NULL, sort_date_key_path TEXT "
                "NON NULL)"
            ),
            "medication_dispense_record_samples": (
                "CREATE TABLE medication_dispense_record_samples (data_id INTEGER "
                "PRIMARY KEY, medication_codings BLOB NOT NULL, quantity_dispensed "
                "BLOB, preparation_date BLOB, hand_over_date BLOB, dosages BLOB, "
                "earliest_dosage_date BLOB, status_coding BLOB, "
                "days_supply_quantity BLOB)"
            ),
            "medication_order_samples": (
                "CREATE TABLE medication_order_samples (data_id INTEGER PRIMARY "
                "KEY, medication_codings BLOB NOT NULL, prescriber TEXT, "
                "number_of_fills INTEGER NOT NULL, dosages BLOB, "
                "earliest_dosage_date BLOB, written_date BLOB, ended_date BLOB, "
                "status_coding BLOB NOT NULL, reason_codings BLOB, "
                "reason_ended_codings BLOB)"
            ),
            "medication_record_samples": (
                "CREATE TABLE medication_record_samples (data_id INTEGER PRIMARY "
                "KEY, medication_codings BLOB NOT NULL, assertion_type INTEGER NOT "
                "NULL, asserter TEXT, assertion_date BLOB, status_coding BLOB NOT "
                "NULL, dosages BLOB, earliest_dosage_date BLOB, "
                "reason_for_use_codings BLOB, not_taken INTEGER NOT NULL, "
                "reasons_not_taken_codings BLOB, effective_start_date BLOB, "
                "effective_end_date BLOB)"
            ),
            "metadata_keys": (
                "CREATE TABLE metadata_keys (ROWID INTEGER PRIMARY KEY "
                "AUTOINCREMENT, key TEXT UNIQUE)"
            ),
            "metadata_values": (
                "CREATE TABLE metadata_values (ROWID INTEGER PRIMARY KEY "
                "AUTOINCREMENT, key_id INTEGER, object_id INTEGER, value_type "
                "INTEGER NOT NULL DEFAULT 0, string_value TEXT, numerical_value "
                "REAL, date_value REAL, data_value BLOB)"
            ),
            "object_authorizations": (
                "CREATE TABLE object_authorizations (ROWID INTEGER PRIMARY KEY "
                "AUTOINCREMENT, object BLOB NOT NULL REFERENCES objects (uuid) ON "
                "DELETE CASCADE, source BLOB NOT NULL, status INTEGER NOT NULL, "
                "sync_provenance INTEGER NOT NULL, modification_date REAL NOT NULL, "
                "UNIQUE(object, source, sync_provenance))"
            ),
            "objects": (
                "CREATE TABLE objects (data_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "uuid BLOB UNIQUE, provenance INTEGER NOT NULL REFERENCES "
                "data_provenances (ROWID) ON DELETE CASCADE, type INTEGER, "
                "creation_date REAL)"
            ),
            "original_fhir_resources": (
                "CREATE TABLE original_fhir_resources (ROWID INTEGER PRIMARY KEY "
                "AUTOINCREMENT, type TEXT NOT NULL, account_id INTEGER NOT NULL "
                "REFERENCES clinical_accounts (ROWID) ON DELETE CASCADE, id TEXT "
                "NOT NULL, sync_provenance INTEGER NOT NULL, raw_content BLOB NOT "
                "NULL, received_date REAL NOT NULL, received_date_timezone TEXT NOT "
                "NULL, fhir_version TEXT NOT NULL, source_url TEXT, "
                "extraction_hints INTEGER, origin_major_version INTEGER NOT NULL, "
                "origin_minor_version INTEGER NOT NULL, origin_patch_version "
                "INTEGER NOT NULL, origin_build TEXT NOT NULL, UNIQUE(type, "
                "account_id, id))"
            ),
            "original_fhir_resources_last_seen": (
                "CREATE TABLE original_fhir_resources_last_seen (ROWID INTEGER "
                "PRIMARY KEY AUTOINCREMENT, resource_id INTEGER NOT NULL REFERENCES "
                "original_fhir_resources (ROWID) ON DELETE CASCADE, last_seen_date "
                "REAL NOT NULL)"
            ),
            "pending_associations": (
                "CREATE TABLE pending_associations (ROWID INTEGER PRIMARY KEY "
                "AUTOINCREMENT, parent_uuid BLOB NOT NULL, child_uuid BLOB NOT "
                "NULL, provenance INTEGER NOT NULL, UNIQUE(parent_uuid, "
                "child_uuid))"
            ),
            "procedure_record_samples": (
                "CREATE TABLE procedure_record_samples (data_id INTEGER PRIMARY "
                "KEY, procedure_codings BLOB NOT NULL, performers BLOB, "
                "execution_start_date BLOB, execution_end_date BLOB, not_performed "
                "INTEGER NOT NULL, status_coding BLOB NOT NULL, category_codings "
                "BLOB, reason_codings BLOB, reasons_not_performed_codings BLOB, "
                "outcome_codings BLOB, complications_codings BLOB, "
                "follow_ups_codings BLOB, body_sites_codings BLOB)"
            ),
            "quantity_sample_series": (
                "CREATE TABLE quantity_sample_series (data_id INTEGER PRIMARY KEY "
                "REFERENCES samples (data_id) ON DELETE CASCADE, count INTEGER NOT "
                "NULL DEFAULT 0, insertion_era INTEGER, hfd_key INTEGER UNIQUE NOT "
                "NULL)"
            ),
            "quantity_sample_statistics": (
                "CREATE TABLE quantity_sample_statistics (owner_id INTEGER PRIMARY "
                "KEY REFERENCES quantity_samples (data_id) ON DELETE CASCADE, min "
                "REAL, max REAL, most_recent REAL, most_recent_date REAL, "
                "most_recent_duration REAL)"
            ),
            "quantity_samples": (
                "CREATE TABLE quantity_samples (data_id INTEGER PRIMARY KEY, "
                "quantity REAL, original_quantity REAL, original_unit INTEGER "
                "REFERENCES unit_strings (ROWID) ON DELETE NO ACTION)"
            ),
            "samples": (
                "CREATE TABLE samples (data_id INTEGER PRIMARY KEY, start_date "
                "REAL, end_date REAL, data_type INTEGER)"
            ),
            "schema_user_versions": (
                "CREATE TABLE schema_user_versions (schema TEXT NOT NULL PRIMARY "
                "KEY, version INTEGER NOT NULL, modification_date DOUBLE NOT NULL)"
            ),
            "source_devices": (
                "CREATE TABLE source_devices( ROWID INT, name TEXT, manufacturer "
                "TEXT, model TEXT, hardware TEXT, firmware TEXT, software TEXT, "
                "localIdentifier TEXT, FDAUDI TEXT, creation_date REAL, "
                "sync_provenance INT, uuid )"
            ),
            "sources": (
                "CREATE TABLE sources( ROWID INT, uuid, bundle_id TEXT, name TEXT, "
                "source_options INT, local_device INT, product_type TEXT, deleted "
                "INT, mod_date REAL, provenance INT, sync_anchor INT, "
                "owner_bundle_id TEXT )"
            ),
            "unit_strings": (
                "CREATE TABLE unit_strings (ROWID INTEGER PRIMARY KEY "
                "AUTOINCREMENT, unit_string TEXT UNIQUE)"
            ),
            "unknown_record_samples": (
                "CREATE TABLE unknown_record_samples (data_id INTEGER PRIMARY KEY, "
                "display_name TEXT)"
            ),
            "vaccination_record_samples": (
                "CREATE TABLE vaccination_record_samples (data_id INTEGER PRIMARY "
                "KEY, vaccination_codings BLOB NOT NULL, expiration_date BLOB, "
                "dose_number TEXT, dose_quantity TEXT, performer TEXT, "
                "body_site_codings BLOB, reaction TEXT, not_given INTEGER NOT NULL, "
                "administration_date BLOB NOT NULL, status_coding BLOB, "
                "patient_reported INTEGER NOT NULL, route_codings BLOB, "
                "reasons_codings BLOB, reasons_not_given_codings BLOB)"
            ),
            "workout_events": (
                "CREATE TABLE workout_events (ROWID INTEGER PRIMARY KEY "
                "AUTOINCREMENT, owner_id INTEGER NOT NULL REFERENCES workouts "
                "(data_id) ON DELETE CASCADE, date REAL NOT NULL, type INTEGER NOT "
                "NULL, duration REAL NOT NULL, metadata BLOB, session_uuid BLOB, "
                "error BLOB)"
            ),
            "workouts": (
                "CREATE TABLE workouts (data_id INTEGER PRIMARY KEY, duration REAL, "
                "total_energy_burned REAL, total_basal_energy_burned REAL, "
                "total_distance REAL, activity_type INTEGER, goal_type INTEGER, "
                "goal REAL, total_w_steps REAL, total_flights_climbed REAL, "
                "condenser_version INTEGER, condenser_date REAL)"
            ),
        }
    ]

    REQUIRE_SCHEMA_MATCH = False

    # TODO: consider adding output formatters for
    # * distance conversion: miles = km * 0.621371
    # * duration conversion: "hh:mm:ss"
    # * temparature conversion: fahrenheit = (celcius * 1.8) + 32
    # * weigth conversion: lbs = kg * 2.20462262
    # * weigth conversion: stones = kg / 6.35029317
    # * weigth conversion: pounds = ((stones - int(stones)) * 14) + 0.5

    def _GetObjectValues(self, database, object_identifier):
        """Retrieves the object values.

        Args:
          database (SQLiteDatabase): database.
          object_identifier (int): object identifier.

        Returns:
          dict[str, object]: object values.
        """
        object_values = {}
        for row in database.Query(self._OBJECT_VALUE_QUERY.format(object_identifier)):
            key = row["key"]
            value_type = row["value_type"]

            if value_type == 0:
                value = row["string_value"]
            elif value_type == 1:
                value = row["numerical_value"]
            else:
                raise RuntimeError(f"Unsupported value type: {value_type:d}")

            object_values[key] = value

        return object_values

    def _ParseAchievementRow(self, parser_mediator, query, row, **unused_kwargs):
        """Parses an achievement row.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          query (str): query that created the row.
          row (sqlite3.Row): row.
        """
        query_hash = hash(query)

        event_data = IOSHealthAchievementsEventData()
        event_data.template_unique_name = self._GetRowValue(
            query_hash, row, "template_unique_name"
        )
        event_data.creation_time = self._GetCocoaTimeRowValue(
            query_hash, row, "created_date"
        )
        # TODO: change into a date and time value.
        event_data.earned_date = self._GetRowValue(query_hash, row, "earned_date")
        event_data.value_in_canonical_unit = self._GetRowValue(
            query_hash, row, "value_in_canonical_unit"
        )
        event_data.value_canonical_unit = self._GetRowValue(
            query_hash, row, "value_canonical_unit"
        )
        event_data.creator_device = self._GetRowValue(query_hash, row, "creator_device")
        event_data.synchronization_provenance = self._GetRowValue(
            query_hash, row, "sync_provenance"
        )
        parser_mediator.ProduceEventData(event_data)

    def _ParseAllWatchSleepSample(self, parser_mediator, query_hash, row):
        """Parses an all watch sleep sample.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          query_hash (int): hash of the query, that uniquely identifies the query that
              produced the row.
          row (sqlite3.Row): row that contains the sample.
        """
        event_data = IOSHealthAllWatchSleepEventData()
        event_data.end_time = self._GetCocoaTimeRowValue(query_hash, row, "end_date")
        event_data.start_time = self._GetCocoaTimeRowValue(
            query_hash, row, "start_date"
        )
        event_data.sleep_state_code = self._GetRowValue(
            query_hash, row, "category_value"
        )
        if (
            event_data.end_time
            and event_data.start_time
            and event_data.end_time.timestamp is not None
            and event_data.start_time.timestamp is not None
        ):
            event_data.duration = (
                event_data.end_time.timestamp - event_data.start_time.timestamp
            )

        parser_mediator.ProduceEventData(event_data)

    def _ParseHeadphoneAudioLevelSample(
        self, parser_mediator, query_hash, row, object_values
    ):
        """Parses a headphone audio level sample.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          query_hash (int): hash of the query, that uniquely identifies the query that
              produced the row.
          row (sqlite3.Row): row that contains the sample.
          object_values (dict[string, object]): object values.
        """
        event_data = IOSHealthHeadphoneAudioEventData()
        event_data.bundle_identifier = object_values.get(
            "_HKPrivateMediaSourceBundleIdentifier"
        )
        event_data.decibels = self._GetRowValue(query_hash, row, "quantity")
        event_data.device_local_identifier = self._GetRowValue(
            query_hash, row, "device_local_identifier"
        )
        event_data.device_manufacturer = self._GetRowValue(
            query_hash, row, "device_manufacturer"
        )
        event_data.device_model = self._GetRowValue(query_hash, row, "device_model")
        event_data.device_name = self._GetRowValue(query_hash, row, "device_name")
        event_data.end_time = self._GetCocoaTimeRowValue(query_hash, row, "end_date")
        event_data.start_time = self._GetCocoaTimeRowValue(
            query_hash, row, "start_date"
        )

        parser_mediator.ProduceEventData(event_data)

    def _ParseHeartRateSample(self, parser_mediator, query_hash, row, object_values):
        """Parses a heart rate sample.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          query_hash (int): hash of the query, that uniquely identifies the query that
              produced the row.
          row (sqlite3.Row): row that contains the sample.
          object_values (dict[string, object]): object values.
        """
        quantity = self._GetRowValue(query_hash, row, "quantity")

        event_data = IOSHealthHeartRateEventData()
        event_data.added_time = self._GetCocoaTimeRowValue(
            query_hash, row, "creation_date"
        )
        event_data.bpm = int((quantity or 0.0) * 60.0)
        event_data.context = object_values.get("_HKPrivateHeartRateContext")
        # TODO: remove device name of "__NONE__"
        event_data.device_name = self._GetRowValue(query_hash, row, "device_name")
        event_data.end_time = self._GetCocoaTimeRowValue(query_hash, row, "end_date")
        event_data.hardware = self._GetRowValue(query_hash, row, "device_hardware")
        event_data.manufacturer = self._GetRowValue(
            query_hash, row, "device_manufacturer"
        )
        event_data.software_version = self._GetRowValue(
            query_hash, row, "software_version"
        )
        event_data.source_name = self._GetRowValue(query_hash, row, "source_name")
        event_data.source_options = self._GetRowValue(query_hash, row, "source_options")
        event_data.start_time = self._GetCocoaTimeRowValue(
            query_hash, row, "start_date"
        )
        event_data.time_zone = self._GetRowValue(query_hash, row, "tz_name")

        parser_mediator.ProduceEventData(event_data)

    def _ParseHeightSample(self, parser_mediator, query_hash, row):
        """Parses a height sample.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          query_hash (int): hash of the query, that uniquely identifies the query that
              produced the row.
          row (sqlite3.Row): row that contains the sample.
        """
        quantity = self._GetRowValue(query_hash, row, "quantity")
        if quantity is None:
            return

        event_data = IOSHealthHeightEventData()
        event_data.height = quantity
        event_data.start_time = self._GetCocoaTimeRowValue(
            query_hash, row, "start_date"
        )

        parser_mediator.ProduceEventData(event_data)

    def _ParseRestingHeartRateSample(self, parser_mediator, query_hash, row):
        """Parses a resting heart rate sample.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          query_hash (int): hash of the query, that uniquely identifies the query that
              produced the row.
          row (sqlite3.Row): row that contains the sample.
        """
        quantity = self._GetRowValue(query_hash, row, "quantity")
        if quantity is None:
            return

        event_data = IOSHealthRestingHeartRateEventData()
        event_data.added_time = self._GetCocoaTimeRowValue(
            query_hash, row, "creation_date"
        )
        event_data.end_time = self._GetCocoaTimeRowValue(query_hash, row, "end_date")
        event_data.hardware = self._GetRowValue(query_hash, row, "source_product_type")
        event_data.resting_heart_rate = int(quantity)
        event_data.source_name = self._GetRowValue(query_hash, row, "source_name")
        event_data.start_time = self._GetCocoaTimeRowValue(
            query_hash, row, "start_date"
        )

        parser_mediator.ProduceEventData(event_data)

    def _ParseSamplesRow(
        self, parser_mediator, query, row, database=None, **unused_kwargs
    ):
        """Parses a samples rate row.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          query (str): query that created the row.
          row (sqlite3.Row): row.
          database (Optional[SQLiteDatabase]): database.
        """
        query_hash = hash(query)

        sample_type = self._GetRowValue(query_hash, row, "sample_type")

        if sample_type == 2:
            self._ParseHeightSample(parser_mediator, query_hash, row)

        elif sample_type == 3:
            self._ParseWeightSample(parser_mediator, query_hash, row)

        elif sample_type == 5:
            object_type = self._GetRowValue(query_hash, row, "object_type")
            if object_type != 2:
                sample_data_identifier = self._GetRowValue(
                    query_hash, row, "sample_data_identifier"
                )
                object_values = self._GetObjectValues(database, sample_data_identifier)
                self._ParseHeartRateSample(
                    parser_mediator, query_hash, row, object_values
                )

        elif sample_type == 7:
            self._ParseStepsSample(parser_mediator, query_hash, row)

        elif sample_type == 63:
            self._ParseAllWatchSleepSample(parser_mediator, query_hash, row)

        elif sample_type == 70:
            sample_data_identifier = self._GetRowValue(
                query_hash, row, "sample_data_identifier"
            )
            object_values = self._GetObjectValues(database, sample_data_identifier)
            self._ParseWristTemperatureSample(
                parser_mediator, query_hash, row, object_values
            )

        elif sample_type == 118:
            self._ParseRestingHeartRateSample(parser_mediator, query_hash, row)

        elif sample_type == 173:
            sample_data_identifier = self._GetRowValue(
                query_hash, row, "sample_data_identifier"
            )
            object_values = self._GetObjectValues(database, sample_data_identifier)

            if (
                "_HKPrivateMetadataKeyHeadphoneAudioDataIsTransient"
                not in object_values
            ):
                self._ParseHeadphoneAudioLevelSample(
                    parser_mediator, query_hash, row, object_values
                )

    def _ParseSourceDevicesRow(self, parser_mediator, query, row, **unused_kwargs):
        """Parses a source devices row.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          query_hash (int): hash of the query, that uniquely identifies the query that
              produced the row.
          row (sqlite3.Row): row that contains the sample.
        """
        query_hash = hash(query)

        firmware = self._GetRowValue(query_hash, row, "firmware")
        local_identifier = self._GetRowValue(query_hash, row, "localIdentifier")

        event_data = IOSHealthSourceDevicesEventData()
        event_data.added_time = self._GetCocoaTimeRowValue(
            query_hash, row, "creation_date"
        )
        event_data.device_name = self._GetRowValue(query_hash, row, "name")
        event_data.firmware = firmware or None
        event_data.hardware = self._GetRowValue(query_hash, row, "hardware")
        event_data.local_identifier = local_identifier or None
        event_data.manufacturer = self._GetRowValue(query_hash, row, "manufacturer")
        event_data.model = self._GetRowValue(query_hash, row, "model")
        event_data.software = self._GetRowValue(query_hash, row, "software")
        event_data.synchronization_provenance = self._GetRowValue(
            query_hash, row, "sync_provenance"
        )
        parser_mediator.ProduceEventData(event_data)

    def _ParseStepsSample(self, parser_mediator, query_hash, row):
        """Parses a steps sample.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          query_hash (int): hash of the query, that uniquely identifies the query that
              produced the row.
          row (sqlite3.Row): row that contains the sample.
        """
        quantity = self._GetRowValue(query_hash, row, "quantity")
        if quantity is None:
            return

        event_data = IOSHealthStepsEventData()
        event_data.device = self._GetRowValue(query_hash, row, "origin_product_type")
        event_data.end_time = self._GetCocoaTimeRowValue(query_hash, row, "end_date")
        event_data.number_of_steps = quantity
        event_data.start_time = self._GetCocoaTimeRowValue(
            query_hash, row, "start_date"
        )
        if (
            event_data.end_time
            and event_data.start_time
            and event_data.end_time.timestamp is not None
            and event_data.start_time.timestamp is not None
        ):
            event_data.duration = (
                event_data.end_time.timestamp - event_data.start_time.timestamp
            )

        parser_mediator.ProduceEventData(event_data)

    def _ParseWeightSample(self, parser_mediator, query_hash, row):
        """Parses a weight sample.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          query_hash (int): hash of the query, that uniquely identifies the query that
              produced the row.
          row (sqlite3.Row): row that contains the sample.
        """
        quantity = self._GetRowValue(query_hash, row, "quantity")
        if quantity is None:
            return

        event_data = IOSHealthWeightEventData()
        event_data.start_time = self._GetCocoaTimeRowValue(
            query_hash, row, "start_date"
        )
        event_data.weight = self._GetRowValue(query_hash, row, "quantity")
        parser_mediator.ProduceEventData(event_data)

    def _ParseWorkoutsRow(self, parser_mediator, query, row, **unused_kwargs):
        """Parses a workouts row.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          query_hash (int): hash of the query, that uniquely identifies the query that
              produced the row.
          row (sqlite3.Row): row that contains the sample.
        """
        query_hash = hash(query)

        event_data = IOSHealthWorkoutsEventData()
        event_data.activity_type = self._GetRowValue(query_hash, row, "activity_type")
        event_data.duration = self._GetRowValue(query_hash, row, "duration")
        event_data.end_time = self._GetCocoaTimeRowValue(query_hash, row, "end_date")
        event_data.goal = self._GetRowValue(query_hash, row, "goal")
        event_data.goal_type = self._GetRowValue(query_hash, row, "goal_type")
        event_data.start_time = self._GetCocoaTimeRowValue(
            query_hash, row, "start_date"
        )
        event_data.total_basal_energy_burned = self._GetRowValue(
            query_hash, row, "total_basal_energy_burned"
        )
        event_data.total_distance = self._GetRowValue(query_hash, row, "total_distance")
        event_data.total_energy_burned = self._GetRowValue(
            query_hash, row, "total_energy_burned"
        )
        event_data.total_flights_climbed = self._GetRowValue(
            query_hash, row, "total_flights_climbed"
        )
        event_data.total_weekly_steps = self._GetRowValue(
            query_hash, row, "total_w_steps"
        )
        parser_mediator.ProduceEventData(event_data)

    def _ParseWristTemperatureSample(self, parser_mediator, query, row, object_values):
        """Parses a wrist temperature sample.

        Args:
          parser_mediator (ParserMediator): mediates interactions.
          query (str): query that created the row.
          row (sqlite3.Row): row.
          object_values (dict[string, object]): object values.
        """
        query_hash = hash(query)

        event_data = IOSHealthWristTemperatureEventData()
        event_data.algorithm_version = object_values.get("HKAlgorithmVersion")
        event_data.added_time = self._GetCocoaTimeRowValue(
            query_hash, row, "creation_date"
        )
        event_data.device_hardware = self._GetRowValue(
            query_hash, row, "device_hardware"
        )
        event_data.device_manufacturer = self._GetRowValue(
            query_hash, row, "device_manufacturer"
        )
        event_data.device_model = self._GetRowValue(query_hash, row, "device_model")
        event_data.device_name = self._GetRowValue(query_hash, row, "device_name")
        event_data.end_time = self._GetCocoaTimeRowValue(query_hash, row, "end_date")
        event_data.software_version = self._GetRowValue(
            query_hash, row, "software_version"
        )
        event_data.source_name = self._GetRowValue(query_hash, row, "source_name")
        event_data.start_time = self._GetCocoaTimeRowValue(
            query_hash, row, "start_date"
        )
        event_data.surface_temperature = object_values.get(
            "_HKPrivateMetadataKeySkinSurfaceTemperature"
        )
        event_data.wrist_temperature = self._GetRowValue(query_hash, row, "quantity")

        parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthPlugin)
