# -*- coding: utf-8 -*-
"""This file contains the Windows NT time zone definitions.

The Windows time zone names can be obtained from the following
Windows Registry key:
HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Time Zones
"""

# Dictionary to map Windows time zone names to Python equivalents.
# Note that spaces have been stripped from the Windows time zone names.

TIME_ZONES = {
    u'AlaskanStandardTime': u'US/Alaska',
    u'Arabic Standard Time': u'Asia/Baghdad',
    u'AtlanticStandardTime': u'Canada/Atlantic',
    u'AzoresStandardTime': u'Atlantic/Azores',
    u'CanadaCentralStandardTime': u'CST6CDT',
    u'CapeVerdeStandardTime': u'Atlantic/Azores',
    u'CentralAmericaStandardTime': u'CST6CDT',
    u'CentralDaylightTime': u'CST6CDT',
    u'CentralEuropeanStandardTime': u'Europe/Belgrade',
    u'CentralEuropeStandardTime': u'Europe/Belgrade',
    u'Central Standard Time': u'CST6CDT',
    u'CentralStandardTime': u'CST6CDT',
    u'ChinaStandardTime': u'Asia/Bangkok',
    u'EasternDaylightTime': u'EST5EDT',
    u'EasternStandardTime': u'EST5EDT',
    u'E.EuropeStandardTime': u'Egypt',
    u'EgyptStandardTime': u'Egypt',
    u'GMTStandardTime': u'GMT',
    u'GreenwichStandardTime': u'GMT',
    u'HawaiianStandardTime': u'US/Hawaii',
    u'IndiaStandardTime': u'Asia/Kolkata',
    u'IsraelStandardTime': u'Egypt',
    u'KoreaStandardTime': u'Asia/Seoul',
    u'MalayPeninsulaStandardTime': u'Asia/Kuching',
    u'MexicoStandardTime2': u'MST7MDT',
    u'MexicoStandardTime': u'CST6CDT',
    u'MountainDaylightTime': u'MST7MDT',
    u'MountainStandardTime': u'MST7MDT',
    u'NewfoundlandStandardTime': u'Canada/Newfoundland',
    u'NorthAsiaEastStandardTime': u'Asia/Bangkok',
    u'PacificDaylightTime': u'PST8PDT',
    u'PacificSAStandardTime': u'Canada/Atlantic',
    u'Pacific Standard Time': u'PST8PDT',
    u'PacificStandardTime': u'PST8PDT',
    u'RomanceStandardTime': u'Europe/Belgrade',
    u'RomanceDaylightTime': u'Europe/Belgrade',
    u'SamoaStandardTime': u'US/Samoa',
    u'SAPacificStandardTime': u'EST5EDT',
    u'SAWesternStandardTime': u'Canada/Atlantic',
    u'SingaporeStandardTime': u'Asia/Bangkok',
    u'SouthAfricaStandardTime': u'Egypt',
    u'TaipeiStandardTime': u'Asia/Bangkok',
    u'TokyoStandardTime': u'Asia/Tokyo',
    u'@tzres.dll,-1010': u'Asia/Aqtau',
    u'@tzres.dll,-1020': u'Asia/Dhaka',
    u'@tzres.dll,-1021': u'Asia/Dhaka',
    u'@tzres.dll,-1022': u'Asia/Dhaka',
    u'@tzres.dll,-104': u'America/Cuiaba',
    u'@tzres.dll,-105': u'America/Cuiaba',
    u'@tzres.dll,-1070': u'Asia/Tbilisi',
    u'@tzres.dll,-10': u'Atlantic/Azores',
    u'@tzres.dll,-110': u'EST5EDT',
    u'@tzres.dll,-111': u'EST5EDT',
    u'@tzres.dll,-1120': u'America/Cuiaba',
    u'@tzres.dll,-112': u'EST5EDT',
    u'@tzres.dll,-1140': u'Pacific/Fiji',
    u'@tzres.dll,-11': u'Atlantic/Azores',
    u'@tzres.dll,-120': u'EST5EDT',
    u'@tzres.dll,-121': u'EST5EDT',
    u'@tzres.dll,-122': u'EST5EDT',
    u'@tzres.dll,-12': u'Atlantic/Azores',
    u'@tzres.dll,-130': u'EST5EDT',
    u'@tzres.dll,-131': u'EST5EDT',
    u'@tzres.dll,-132': u'EST5EDT',
    u'@tzres.dll,-140': u'CST6CDT',
    u'@tzres.dll,-141': u'CST6CDT',
    u'@tzres.dll,-142': u'CST6CDT',
    u'@tzres.dll,-1460': u'Pacific/Port_Moresby',
    u'@tzres.dll,-150': u'America/Guatemala',
    u'@tzres.dll,-151': u'America/Guatemala',
    u'@tzres.dll,-152': u'America/Guatemala',
    u'@tzres.dll,-1530': u'Asia/Yekaterinburg',
    u'@tzres.dll,-160': u'CST6CDT',
    u'@tzres.dll,-161': u'CST6CDT',
    u'@tzres.dll,-162': u'CST6CDT',
    u'@tzres.dll,-1630': u'Europe/Nicosia',
    u'@tzres.dll,-1660': u'America/Bahia',
    u'@tzres.dll,-1661': u'America/Bahia',
    u'@tzres.dll,-1662': u'America/Bahia',
    u'@tzres.dll,-170': u'America/Mexico_City',
    u'@tzres.dll,-171': u'America/Mexico_City',
    u'@tzres.dll,-172': u'America/Mexico_City',
    u'@tzres.dll,-180': u'MST7MDT',
    u'@tzres.dll,-181': u'MST7MDT',
    u'@tzres.dll,-182': u'MST7MDT',
    u'@tzres.dll,-190': u'MST7MDT',
    u'@tzres.dll,-191': u'MST7MDT',
    u'@tzres.dll,-192': u'MST7MDT',
    u'@tzres.dll,-200': u'MST7MDT',
    u'@tzres.dll,-201': u'MST7MDT',
    u'@tzres.dll,-202': u'MST7MDT',
    u'@tzres.dll,-20': u'Atlantic/Cape_Verde',
    u'@tzres.dll,-210': u'PST8PDT',
    u'@tzres.dll,-211': u'PST8PDT',
    u'@tzres.dll,-212': u'PST8PDT',
    u'@tzres.dll,-21': u'Atlantic/Cape_Verde',
    u'@tzres.dll,-220': u'US/Alaska',
    u'@tzres.dll,-221': u'US/Alaska',
    u'@tzres.dll,-222': u'US/Alaska',
    u'@tzres.dll,-22': u'Atlantic/Cape_Verde',
    u'@tzres.dll,-230': u'US/Hawaii',
    u'@tzres.dll,-231': u'US/Hawaii',
    u'@tzres.dll,-232': u'US/Hawaii',
    u'@tzres.dll,-260': u'GMT',
    u'@tzres.dll,-261': u'GMT',
    u'@tzres.dll,-262': u'GMT',
    u'@tzres.dll,-271': u'UTC',
    u'@tzres.dll,-272': u'UTC',
    u'@tzres.dll,-280': u'Europe/Budapest',
    u'@tzres.dll,-281': u'Europe/Budapest',
    u'@tzres.dll,-282': u'Europe/Budapest',
    u'@tzres.dll,-290': u'Europe/Warsaw',
    u'@tzres.dll,-291': u'Europe/Warsaw',
    u'@tzres.dll,-292': u'Europe/Warsaw',
    u'@tzres.dll,-300': u'Europe/Paris',
    u'@tzres.dll,-301': u'Europe/Paris',
    u'@tzres.dll,-302': u'Europe/Paris',
    u'@tzres.dll,-320': u'Europe/Berlin',
    u'@tzres.dll,-321': u'Europe/Berlin',
    u'@tzres.dll,-322': u'Europe/Berlin',
    u'@tzres.dll,-331': u'Europe/Nicosia',
    u'@tzres.dll,-332': u'Europe/Nicosia',
    u'@tzres.dll,-340': u'Africa/Cairo',
    u'@tzres.dll,-341': u'Africa/Cairo',
    u'@tzres.dll,-342': u'Africa/Cairo',
    u'@tzres.dll,-350': u'Europe/Sofia',
    u'@tzres.dll,-351': u'Europe/Sofia',
    u'@tzres.dll,-352': u'Europe/Sofia',
    u'@tzres.dll,-365': u'Egypt',
    u'@tzres.dll,-371': u'Asia/Jerusalem',
    u'@tzres.dll,-372': u'Asia/Jerusalem',
    u'@tzres.dll,-380': u'Africa/Harare',
    u'@tzres.dll,-381': u'Africa/Harare',
    u'@tzres.dll,-382': u'Africa/Harare',
    u'@tzres.dll,-390': u'Asia/Kuwait',
    u'@tzres.dll,-391': u'Asia/Kuwait',
    u'@tzres.dll,-392': u'Asia/Kuwait',
    u'@tzres.dll,-400': u'Asia/Baghdad',
    u'@tzres.dll,-401': u'Asia/Baghdad',
    u'@tzres.dll,-402': u'Asia/Baghdad',
    u'@tzres.dll,-40': u'Brazil/East',
    u'@tzres.dll,-410': u'Africa/Nairobi',
    u'@tzres.dll,-411': u'Africa/Nairobi',
    u'@tzres.dll,-412': u'Africa/Nairobi',
    u'@tzres.dll,-41': u'Brazil/East',
    u'@tzres.dll,-42': u'Brazil/East',
    u'@tzres.dll,-420': u'Europe/Moscow',
    u'@tzres.dll,-421': u'Europe/Moscow',
    u'@tzres.dll,-422': u'Europe/Moscow',
    u'@tzres.dll,-434': u'Asia/Tbilisi',
    u'@tzres.dll,-435': u'Asia/Tbilisi',
    u'@tzres.dll,-440': u'Asia/Muscat',
    u'@tzres.dll,-441': u'Asia/Muscat',
    u'@tzres.dll,-442': u'Asia/Muscat',
    u'@tzres.dll,-447': u'Asia/Baku',
    u'@tzres.dll,-448': u'Asia/Baku',
    u'@tzres.dll,-449': u'Asia/Baku',
    u'@tzres.dll,-450': u'Asia/Yerevan',
    u'@tzres.dll,-451': u'Asia/Yerevan',
    u'@tzres.dll,-452': u'Asia/Yerevan',
    u'@tzres.dll,-460': u'Asia/Kabul',
    u'@tzres.dll,-461': u'Asia/Kabul',
    u'@tzres.dll,-462': u'Asia/Kabul',
    u'@tzres.dll,-471': u'Asia/Yekaterinburg',
    u'@tzres.dll,-472': u'Asia/Yekaterinburg',
    u'@tzres.dll,-480': u'Asia/Karachi',
    u'@tzres.dll,-481': u'Asia/Karachi',
    u'@tzres.dll,-482': u'Asia/Karachi',
    u'@tzres.dll,-490': u'Asia/Kolkata',
    u'@tzres.dll,-491': u'Asia/Kolkata',
    u'@tzres.dll,-492': u'Asia/Kolkata',
    u'@tzres.dll,-500': u'Asia/Kathmandu',
    u'@tzres.dll,-501': u'Asia/Kathmandu',
    u'@tzres.dll,-502': u'Asia/Kathmandu',
    u'@tzres.dll,-510': u'Asia/Dhaka',
    u'@tzres.dll,-511': u'Asia/Aqtau',
    u'@tzres.dll,-512': u'Asia/Aqtau',
    u'@tzres.dll,-570': u'Asia/Chongqing',
    u'@tzres.dll,-571': u'Asia/Chongqing',
    u'@tzres.dll,-572': u'Asia/Chongqing',
    u'@tzres.dll,-60': u'America/Buenos_Aires',
    u'@tzres.dll,-611': u'Australia/Perth',
    u'@tzres.dll,-612': u'Australia/Perth',
    u'@tzres.dll,-621': u'Asia/Seoul',
    u'@tzres.dll,-622': u'Asia/Seoul',
    u'@tzres.dll,-631': u'Asia/Tokyo',
    u'@tzres.dll,-632': u'Asia/Tokyo',
    u'@tzres.dll,-650': u'Australia/Darwin',
    u'@tzres.dll,-651': u'Australia/Darwin',
    u'@tzres.dll,-652': u'Australia/Darwin',
    u'@tzres.dll,-660': u'Australia/Adelaide',
    u'@tzres.dll,-661': u'Australia/Adelaide',
    u'@tzres.dll,-662': u'Australia/Adelaide',
    u'@tzres.dll,-670': u'Australia/Sydney',
    u'@tzres.dll,-671': u'Australia/Sydney',
    u'@tzres.dll,-672': u'Australia/Sydney',
    u'@tzres.dll,-680': u'Australia/Brisbane',
    u'@tzres.dll,-681': u'Australia/Brisbane',
    u'@tzres.dll,-682': u'Australia/Brisbane',
    u'@tzres.dll,-691': u'Australia/Hobart',
    u'@tzres.dll,-692': u'Australia/Hobart',
    u'@tzres.dll,-70': u'Canada/Newfoundland',
    u'@tzres.dll,-71': u'Canada/Newfoundland',
    u'@tzres.dll,-721': u'Pacific/Port_Moresby',
    u'@tzres.dll,-722': u'Pacific/Port_Moresby',
    u'@tzres.dll,-72': u'Canada/Newfoundland',
    u'@tzres.dll,-731': u'Pacific/Fiji',
    u'@tzres.dll,-732': u'Pacific/Fiji',
    u'@tzres.dll,-740': u'Pacific/Auckland',
    u'@tzres.dll,-741': u'Pacific/Auckland',
    u'@tzres.dll,-742': u'Pacific/Auckland',
    u'@tzres.dll,-80': u'Canada/Atlantic',
    u'@tzres.dll,-81': u'Canada/Atlantic',
    u'@tzres.dll,-82': u'Canada/Atlantic',
    u'@tzres.dll,-840': u'America/Argentina/Buenos_Aires',
    u'@tzres.dll,-841': u'America/Argentina/Buenos_Aires',
    u'@tzres.dll,-842': u'America/Argentina/Buenos_Aires',
    u'@tzres.dll,-870': u'Asia/Karachi',
    u'@tzres.dll,-871': u'Asia/Karachi',
    u'@tzres.dll,-872': u'Asia/Karachi',
    u'@tzres.dll,-880': u'UTC',
    u'@tzres.dll,-930': u'UTC',
    u'@tzres.dll,-931': u'UTC',
    u'@tzres.dll,-932': u'UTC',
    u'USEasternStandardTime': u'EST5EDT',
    u'USMountainStandardTime': u'MST7MDT',
    u'W.AustraliaStandardTime': u'Australia/Perth',
    u'W.CentralAfricaStandardTime': u'Europe/Belgrade',
    u'W.EuropeStandardTime': u'Europe/Belgrade',
    u'(UTC) Coordinated Universal Time': u'UTC',
}

# Values of @tzres.dll,-[0-9]+
# 10	(UTC-01:00) Azores
# 11	Azores Daylight Time
# 12	Azores Standard Time
# 20	(UTC-01:00) Cape Verde Is.
# 21	Cape Verde Daylight Time
# 22	Cape Verde Standard Time
# 30	(UTC-02:00) Mid-Atlantic
# 31	Mid-Atlantic Daylight Time
# 32	Mid-Atlantic Standard Time
# 40	(UTC-03:00) Brasilia
# 41	E. South America Daylight Time
# 42	E. South America Standard Time
# 50	(UTC-03:00) Greenland
# 51	Greenland Daylight Time
# 52	Greenland Standard Time
# 60	(UTC-03:00) Buenos Aires, Georgetown
# 61	SA Eastern Daylight Time
# 62	SA Eastern Standard Time
# 70	(UTC-03:30) Newfoundland
# 71	Newfoundland Daylight Time
# 72	Newfoundland Standard Time
# 80	(UTC-04:00) Atlantic Time (Canada)
# 81	Atlantic Daylight Time
# 82	Atlantic Standard Time
# 90	(UTC-04:00) Santiago
# 91	Pacific SA Daylight Time
# 92	Pacific SA Standard Time
# 100	(UTC-04:00) Caracas, La Paz
# 101	SA Western Daylight Time
# 102	SA Western Standard Time
# 103	(UTC-04:00) Manaus
# 104	Central Brazilian Daylight Time
# 105	Central Brazilian Standard Time
# 110	(UTC-05:00) Eastern Time (US & Canada)
# 111	Eastern Daylight Time
# 112	Eastern Standard Time
# 120	(UTC-05:00) Bogota, Lima, Quito, Rio Branco
# 121	SA Pacific Daylight Time
# 122	SA Pacific Standard Time
# 130	(UTC-05:00) Indiana (East)
# 131	US Eastern Daylight Time
# 132	US Eastern Standard Time
# 140	(UTC-06:00) Saskatchewan
# 141	Canada Central Daylight Time
# 142	Canada Central Standard Time
# 150	(UTC-06:00) Central America
# 151	Central America Daylight Time
# 152	Central America Standard Time
# 160	(UTC-06:00) Central Time (US & Canada)
# 161	Central Daylight Time
# 162	Central Standard Time
# 170	(UTC-06:00) Guadalajara, Mexico City, Monterrey
# 171	Central Daylight Time (Mexico)
# 172	Central Standard Time (Mexico)
# 180	(UTC-07:00) Chihuahua, La Paz, Mazatlan
# 181	Mountain Daylight Time (Mexico)
# 182	Mountain Standard Time (Mexico)
# 190	(UTC-07:00) Mountain Time (US & Canada)
# 191	Mountain Daylight Time
# 192	Mountain Standard Time
# 200	(UTC-07:00) Arizona
# 201	US Mountain Daylight Time
# 202	US Mountain Standard Time
# 210	(UTC-08:00) Pacific Time (US & Canada)
# 211	Pacific Daylight Time
# 212	Pacific Standard Time
# 213	(UTC-08:00) Tijuana, Baja California
# 214	Pacific Daylight Time (Mexico)
# 215	Pacific Standard Time (Mexico)
# 220	(UTC-09:00) Alaska
# 221	Alaskan Daylight Time
# 222	Alaskan Standard Time
# 230	(UTC-10:00) Hawaii
# 231	Hawaiian Daylight Time
# 232	Hawaiian Standard Time
# 240	(UTC-11:00) Midway Island, Samoa
# 241	Samoa Daylight Time
# 242	Samoa Standard Time
# 250	(UTC-12:00) International Date Line West
# 251	Dateline Daylight Time
# 252	Dateline Standard Time
# 260	(UTC) Dublin, Edinburgh, Lisbon, London
# 261	GMT Daylight Time
# 262	GMT Standard Time
# 270	(UTC) Casablanca, Monrovia, Reykjavik
# 271	Greenwich Daylight Time
# 272	Greenwich Standard Time
# 280	(UTC+01:00) Belgrade, Bratislava, Budapest, Ljubljana, Prague
# 281	Central Europe Daylight Time
# 282	Central Europe Standard Time
# 290	(UTC+01:00) Sarajevo, Skopje, Warsaw, Zagreb
# 291	Central European Daylight Time
# 292	Central European Standard Time
# 300	(UTC+01:00) Brussels, Copenhagen, Madrid, Paris
# 301	Romance Daylight Time
# 302	Romance Standard Time
# 310	(UTC+01:00) West Central Africa
# 311	W. Central Africa Daylight Time
# 312	W. Central Africa Standard Time
# 320	(UTC+01:00) Amsterdam, Berlin, Bern, Rome, Stockholm, Vienna
# 321	W. Europe Daylight Time
# 322	W. Europe Standard Time
# 330	(UTC+02:00) Minsk
# 331	E. Europe Daylight Time
# 332	E. Europe Standard Time
# 333	(UTC+02:00) Amman
# 334	Jordan Daylight Time
# 335	Jordan Standard Time
# 340	(UTC+02:00) Cairo
# 341	Egypt Daylight Time
# 342	Egypt Standard Time
# 350	(UTC+02:00) Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius
# 351	FLE Daylight Time
# 352	FLE Standard Time
# 360	(UTC+02:00) Athens, Bucharest, Istanbul
# 361	GTB Daylight Time
# 362	GTB Standard Time
# 363	(UTC+02:00) Beirut
# 364	Middle East Daylight Time
# 365	Middle East Standard Time
# 370	(UTC+02:00) Jerusalem
# 371	Jerusalem Daylight Time
# 372	Jerusalem Standard Time
# 380	(UTC+02:00) Harare, Pretoria
# 381	South Africa Daylight Time
# 382	South Africa Standard Time
# 383	(UTC+02:00) Windhoek
# 384	Namibia Daylight Time
# 385	Namibia Standard Time
# 390	(UTC+03:00) Kuwait, Riyadh
# 391	Arab Daylight Time
# 392	Arab Standard Time
# 400	(UTC+03:00) Baghdad
# 401	Arabic Daylight Time
# 402	Arabic Standard Time
# 410	(UTC+03:00) Nairobi
# 411	E. Africa Daylight Time
# 412	E. Africa Standard Time
# 420	(UTC+03:00) Moscow, St. Petersburg, Volgograd
# 421	Russian Daylight Time
# 422	Russian Standard Time
# 430	(UTC+03:30) Tehran
# 431	Iran Daylight Time
# 432	Iran Standard Time
# 433	(UTC+03:00) Tbilisi
# 434	Georgian Daylight Time
# 435	Georgian Standard Time
# 440	(UTC+04:00) Abu Dhabi, Muscat
# 441	Arabian Daylight Time
# 442	Arabian Standard Time
# 447	(UTC+04:00) Baku
# 448	Azerbaijan Daylight Time
# 449	Azerbaijan Standard Time
# 450	(UTC+04:00) Yerevan
# 451	Caucasus Daylight Time
# 452	Caucasus Standard Time
# 460	(UTC+04:30) Kabul
# 461	Afghanistan Daylight Time
# 462	Afghanistan Standard Time
# 470	(UTC+05:00) Ekaterinburg
# 471	Ekaterinburg Daylight Time
# 472	Ekaterinburg Standard Time
# 480	(UTC+05:00) Islamabad, Karachi, Tashkent
# 481	West Asia Daylight Time
# 482	West Asia Standard Time
# 490	(UTC+05:30) Chennai, Kolkata, Mumbai, New Delhi
# 491	India Daylight Time
# 492	India Standard Time
# 500	(UTC+05:45) Kathmandu
# 501	Nepal Daylight Time
# 502	Nepal Standard Time
# 510	(UTC+06:00) Astana, Dhaka
# 511	Central Asia Daylight Time
# 512	Central Asia Standard Time
# 520	(UTC+06:00) Almaty, Novosibirsk
# 521	N. Central Asia Daylight Time
# 522	N. Central Asia Standard Time
# 530	(UTC+05:30) Sri Jayawardenepura
# 531	Sri Lanka Daylight Time
# 532	Sri Lanka Standard Time
# 540	(UTC+06:30) Yangon (Rangoon)
# 541	Myanmar Daylight Time
# 542	Myanmar Standard Time
# 550	(UTC+07:00) Krasnoyarsk
# 551	North Asia Daylight Time
# 552	North Asia Standard Time
# 560	(UTC+07:00) Bangkok, Hanoi, Jakarta
# 561	SE Asia Daylight Time
# 562	SE Asia Standard Time
# 570	(UTC+08:00) Beijing, Chongqing, Hong Kong, Urumqi
# 571	China Daylight Time
# 572	China Standard Time
# 580	(UTC+08:00) Irkutsk, Ulaan Bataar
# 581	North Asia East Daylight Time
# 582	North Asia East Standard Time
# 590	(UTC+08:00) Kuala Lumpur, Singapore
# 591	Malay Peninsula Daylight Time
# 592	Malay Peninsula Standard Time
# 600	(UTC+08:00) Taipei
# 601	Taipei Daylight Time
# 602	Taipei Standard Time
# 610	(UTC+08:00) Perth
# 611	W. Australia Daylight Time
# 612	W. Australia Standard Time
# 620	(UTC+09:00) Seoul
# 621	Korea Daylight Time
# 622	Korea Standard Time
# 630	(UTC+09:00) Osaka, Sapporo, Tokyo
# 631	Tokyo Daylight Time
# 632	Tokyo Standard Time
# 640	(UTC+09:00) Yakutsk
# 641	Yakutsk Daylight Time
# 642	Yakutsk Standard Time
# 650	(UTC+09:30) Darwin
# 651	AUS Central Daylight Time
# 652	AUS Central Standard Time
# 660	(UTC+09:30) Adelaide
# 661	Cen. Australia Daylight Time
# 662	Cen. Australia Standard Time
# 670	(UTC+10:00) Canberra, Melbourne, Sydney
# 671	AUS Eastern Daylight Time
# 672	AUS Eastern Standard Time
# 680	(UTC+10:00) Brisbane
# 681	E. Australia Daylight Time
# 682	E. Australia Standard Time
# 690	(UTC+10:00) Hobart
# 691	Tasmania Daylight Time
# 692	Tasmania Standard Time
# 700	(UTC+10:00) Vladivostok
# 701	Vladivostok Daylight Time
# 702	Vladivostok Standard Time
# 710	(UTC+10:00) Guam, Port Moresby
# 711	West Pacific Daylight Time
# 712	West Pacific Standard Time
# 720	(UTC+11:00) Magadan, Solomon Is., New Caledonia
# 721	Central Pacific Daylight Time
# 722	Central Pacific Standard Time
# 730	(UTC+12:00) Fiji, Kamchatka, Marshall Is.
# 731	Fiji Daylight Time
# 732	Fiji Standard Time
# 740	(UTC+12:00) Auckland, Wellington
# 741	New Zealand Daylight Time
# 742	New Zealand Standard Time
# 750	(UTC+13:00) Nuku'alofa
# 751	Tonga Daylight Time
# 752	Tonga Standard Time
# 770	(UTC-03:00) Montevideo
# 771	Montevideo Daylight Time
# 772	Montevideo Standard Time
# 790	(UTC-04:00) La Paz
# 791	SA Western Daylight Time
# 792	SA Western Standard Time
# 810	(UTC-04:30) Caracas
# 811	Venezuela Daylight Time
# 812	Venezuela Standard Time
# 830	(UTC-03:00) Georgetown
# 831	SA Eastern Daylight Time
# 832	SA Eastern Standard Time
# 840	(UTC-03:00) Buenos Aires
# 841	Argentina Daylight Time
# 842	Argentina Standard Time
# 860	(UTC+05:00) Tashkent
# 870	(UTC+05:00) Islamabad, Karachi
# 871	Pakistan Daylight Time
# 872	Pakistan Standard Time
# 880	(UTC) Monrovia, Reykjavik
# 890	(UTC) Casablanca
# 891	Morocco Daylight Time
# 892	Morocco Standard Time
# 910	(UTC+04:00) Port Louis
# 911	Mauritius Daylight Time
# 912	Mauritius Standard Time
# 930	(UTC) Coordinated Universal Time
# 931	Coordinated Universal Time
# 932	Coordinated Universal Time
# 940	(UTC-03:00) Cayenne
# 950	(UTC-04:00) Georgetown, La Paz, San Juan
# 960	(UTC-04:00) Asuncion
# 961	Paraguay Daylight Time
# 962	Paraguay Standard Time
# 970	(UTC+12:00) Fiji, Marshall Is.
# 980	(UTC+12:00) Petropavlovsk-Kamchatsky
# 981	Kamchatka Daylight Time
# 982	Kamchatka Standard Time
# 990	(UTC-05:00) Bogota, Lima, Quito
# 1010	(UTC+06:00) Astana
# 1020	(UTC+06:00) Dhaka
# 1021	Bangladesh Daylight Time
# 1022	Bangladesh Standard Time
# 1030	(UTC+08:00) Irkutsk
# 1040	(UTC+08:00) Ulaanbaatar
# 1041	Ulaanbaatar Daylight Time
# 1042	Ulaanbaatar Standard Time
# 1050	(UTC-11:00) Samoa
# 1060	(UTC-11:00) Midway Islands
# 1061	North Pacific Daylight Time
# 1062	North Pacific Standard Time
# 1070	(UTC+04:00) Tbilisi
# 1080	(UTC+06:00) Novosibirsk
# 1100	(UTC-08:00) Baja California
# 1110	(UTC-03:00) Cayenne, Fortaleza
# 1120	(UTC-04:00) Cuiaba
# 1130	(UTC-04:00) Georgetown, La Paz, Manaus, San Juan
# 1140	(UTC+12:00) Fiji
# 1150	(UTC-01:00) Coordinated Universal Time-01
# 1151	UTC-01
# 1152	UTC-01
# 1160	(UTC-02:00) Coordinated Universal Time-02
# 1161	UTC-02
# 1162	UTC-02
# 1170	(UTC-03:00) Coordinated Universal Time-03
# 1171	UTC-03
# 1172	UTC-03
# 1180	(UTC-04:00) Coordinated Universal Time-04
# 1181	UTC-04
# 1182	UTC-04
# 1190	(UTC-05:00) Coordinated Universal Time-05
# 1191	UTC-05
# 1192	UTC-05
# 1200	(UTC-06:00) Coordinated Universal Time-06
# 1201	UTC-06
# 1202	UTC-06
# 1210	(UTC-07:00) Coordinated Universal Time-07
# 1211	UTC-07
# 1212	UTC-07
# 1220	(UTC-08:00) Coordinated Universal Time-08
# 1221	UTC-08
# 1222	UTC-08
# 1230	(UTC-09:00) Coordinated Universal Time-09
# 1231	UTC-09
# 1232	UTC-09
# 1240	(UTC-10:00) Coordinated Universal Time-10
# 1241	UTC-10
# 1242	UTC-10
# 1250	(UTC-11:00) Coordinated Universal Time-11
# 1251	UTC-11
# 1252	UTC-11
# 1260	(UTC-12:00) Coordinated Universal Time-12
# 1261	UTC-12
# 1262	UTC-12
# 1270	(UTC+01:00) Coordinated Universal Time+01
# 1271	UTC+01
# 1272	UTC+01
# 1280	(UTC+02:00) Coordinated Universal Time+02
# 1281	UTC+02
# 1282	UTC+02
# 1290	(UTC+03:00) Coordinated Universal Time+03
# 1291	UTC+03
# 1292	UTC+03
# 1300	(UTC+04:00) Coordinated Universal Time+04
# 1301	UTC+04
# 1302	UTC+04
# 1310	(UTC+05:00) Coordinated Universal Time+05
# 1311	UTC+05
# 1312	UTC+05
# 1320	(UTC+06:00) Coordinated Universal Time+06
# 1321	UTC+06
# 1322	UTC+06
# 1330	(UTC+07:00) Coordinated Universal Time+07
# 1331	UTC+07
# 1332	UTC+07
# 1340	(UTC+08:00) Coordinated Universal Time+08
# 1341	UTC+08
# 1342	UTC+08
# 1350	(UTC+09:00) Coordinated Universal Time+09
# 1351	UTC+09
# 1352	UTC+09
# 1360	(UTC+10:00) Coordinated Universal Time+10
# 1361	UTC+10
# 1362	UTC+10
# 1370	(UTC+11:00) Coordinated Universal Time+11
# 1371	UTC+11
# 1372	UTC+11
# 1380	(UTC+12:00) Coordinated Universal Time+12
# 1381	UTC+12
# 1382	UTC+12
# 1390	(UTC+13:00) Coordinated Universal Time+13
# 1391	UTC+13
# 1392	UTC+13
# 1410	(UTC+02:00) Damascus
# 1411	Syria Daylight Time
# 1412	Syria Standard Time
# 1420	(UTC+12:00) Petropavlovsk-Kamchatsky - Old
# 1440	(UTC+01:00) Windhoek
# 1460	(UTC+11:00) Solomon Is., New Caledonia
# 1470	(UTC+11:00) Magadan
# 1471	Magadan Daylight Time
# 1472	Magadan Standard Time
# 1490	(UTC+02:00) Athens, Bucharest
# 1500	(UTC+02:00) Istanbul
# 1501	Turkey Daylight Time
# 1502	Turkey Standard Time
# 1520	(UTC+04:00) Moscow, St. Petersburg, Volgograd
# 1530	(UTC+06:00) Ekaterinburg
# 1540	(UTC+07:00) Novosibirsk
# 1550	(UTC+08:00) Krasnoyarsk
# 1560	(UTC+09:00) Irkutsk
# 1570	(UTC+10:00) Yakutsk
# 1580	(UTC+11:00) Vladivostok
# 1590	(UTC+12:00) Magadan
# 1600	(UTC+03:00) Kaliningrad
# 1601	Kaliningrad Daylight Time
# 1602	Kaliningrad Standard Time
# 1620	(UTC+03:00) Kaliningrad, Minsk
# 1630	(UTC+02:00) Nicosia
# 1640	(UTC+13:00) Samoa
# 1660	(UTC-03:00) Salvador
# 1661	Bahia Daylight Time
# 1662	Bahia Standard Time
# 1680	(UTC+02:00) E. Europe
# 1700	(UTC+03:00) Amman
# 1720	(UTC+02:00) Tripoli
# 1721	Libya Daylight Time
# 1722	Libya Standard Time
# 1740	(UTC+05:00) Ashgabat, Tashkent
# 1760	(UTC-02:00) Mid-Atlantic - Old
