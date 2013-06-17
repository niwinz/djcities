"""
Settings for this application.

See:

 - http://en.wikipedia.org/wiki/List_of_languages_by_number_of_native_speakers
 - http://download.geonames.org/export/dump/iso-languagecodes.txt


DATA_DIR
    Absolute path to download and extract data into. Default is
    cities_light/data. Overridable in settings.CITIES_LIGHT_DATA_DIR
"""

from django.conf import settings

import os.path
import re

ALPHA_REGEXP = re.compile('[\W_]+', re.UNICODE)

SOURCES = {
    'country': {
        'source': getattr(settings, 'CITIES_COUNTRY_SOURCES',
            'http://download.geonames.org/export/dump/countryInfo.txt'),
        'dest': 'countries.txt',
        'sort': 1,
    },
    'timezone': {
        'source': getattr(settings, 'CITIES_TIMEZONES',
            'http://download.geonames.org/export/dump/timeZones.txt'),
        'dest': 'timezones.txt',
        'sort': 2,
    },
    'region': {
        'source': getattr(settings, 'CITIES_REGION_SOURCES',
            'http://download.geonames.org/export/dump/admin1CodesASCII.txt'),
        'dest': 'regions.txt',
        'sort': 3,
    },
    'subregion': {
        'source': getattr(settings, 'CITIES_SUBREGION_SOURCES',
            'http://download.geonames.org/export/dump/admin2Codes.txt'),
        'dest': 'subregions.txt',
        'sort': 4,
    },

    'city': {
        'source': getattr(settings, 'CITIES_CITY_SOURCES',
            'http://download.geonames.org/export/dump/cities15000.zip'),
        'dest': 'cities.txt',
        'file': 'cities15000.txt',
        'sort': 5,
    },
}

TRANSLATIONS = {
    'source':'http://download.geonames.org/export/dump/alternateNames.zip',
    'file': 'alternateNames.txt',
    'dest': 'translations.txt',
}

TMPDATA_DIR = getattr(settings, "CITIES_TMPDATA_DIR",
    os.path.join("/tmp", "django-cities")
)

# Countries whose provinces are subregions, not regions
COUNTRIES_WITH_SUBREGION_PROVINCES = getattr(settings, "COUNTRIES_WITH_SUBREGION_PROVINCES", ['ES'])
