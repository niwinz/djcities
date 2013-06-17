# -*- coding: utf-8 -*-

import io
import os
import sys
import os.path
import optparse
import zipfile
import requests

from django.core.management.base import BaseCommand
from django.utils.encoding import force_unicode
from django.db import transaction, IntegrityError, connection

from ...models import City, Country, Region, Timezone
from ... import settings as local_settings
from django.core.exceptions import MultipleObjectsReturned


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        optparse.make_option('--country', action='store', default=None, dest='country',
                             help='Download and import only data for this country.'),)

    def prepare(self):
        if not os.path.exists(local_settings.TMPDATA_DIR):
            print "Creating temporal data directory: {0}".format(local_settings.TMPDATA_DIR)
            os.mkdir(local_settings.TMPDATA_DIR)

    def download(self, name, sourcedata, dest_path):
        response = requests.get(sourcedata['source'])

        with io.open(dest_path, "bw") as f:
            f.write(response.content)
            #for chuck in response.iter_content(512):
            #    f.write(chuck)
            #    sys.stdout.write(".")
            #sys.stdout.write("\n")

    def extract(self, infile, outfile, filename):
        zfile = zipfile.ZipFile(infile)
        if zfile:
             with io.open(outfile, "wb") as f:
                f.write(zfile.read(filename))

    def download_datafiles(self):
        for name, sourcedata in local_settings.SOURCES.iteritems():
            print "Downloading: {0} from {1}".format(name, sourcedata['source'])

            dest_path = os.path.join(local_settings.TMPDATA_DIR, sourcedata['dest'])
            if os.path.exists(dest_path):
                print "File exists, skiping."
                continue

            if sourcedata['source'].endswith(".zip"):
                tmp_dest_path = dest_path + ".zip"
            else:
                tmp_dest_path = dest_path

            self.download(name, sourcedata, tmp_dest_path)

            if tmp_dest_path.endswith(".zip"):
                self.extract(tmp_dest_path, dest_path, sourcedata['file'])

    def file_content_parser(self, path):
        with io.open(path, "r") as f:
            for line in f:
                line = line.strip()
                if len(line) < 1 or line[0] == "#" or line[0] == 'CountryCode':
                    continue

                yield [e.strip() for e in line.split('\t')]

    @transaction.commit_on_success
    def handle(self, *args, **options):

        if "extra_sql" in options:
            extra_sql = options["extra_sql"]
            if extra_sql:
                if not os.path.exists(extra_sql):
                    raise RuntimeError("File {0} does not exists".format(extra_sql))

                cursor = connection.cursor()
                with io.open(extra_sql, "rt") as f:
                    for line in f:
                        if not line or line.strip().startswith('--'):
                            continue
                        print "ex: {0}".format(line.strip())
                        cursor.execute(line)

                cursor.close()

        # Remove old data
        Timezone.objects.all().delete()
        City.objects.all().delete()
        Region.objects.all().delete()
        Country.objects.all().delete()

        self._options = options
        self.prepare()
        self.download_datafiles()

        self.bulk_cities = []
        self.bulk_regions = []
        self.bulk_country = []
        self.bulk_timezone = []

        for name, sourcedata in sorted(local_settings.SOURCES.items(), key=lambda x: x[1]['sort']):
            dest_path = os.path.join(local_settings.TMPDATA_DIR, sourcedata['dest'])
            print "Parsing: {0} - {1}".format(name, dest_path)

            _parse_method = getattr(self, "{0}_import".format(name))

            for item in self.file_content_parser(dest_path):
                _parse_method(item)

    def timezone_import(self, items):
        if len(items) < 3:
            return

        if items[0] == "CountryCode":
            return

        country_code2, name, offset = items[0], items[1], items[2]

        try:
            tz = Timezone.objects.get(name=name)
        except Timezone.DoesNotExist:
            tz = Timezone(name=name)

        tz.country = self._get_country(country_code2)
        tz.country_code = country_code2
        tz.gmt_offset = offset
        tz.save()

    def country_import(self, items):
        geoname_id = items[16]
        code2 = force_unicode(items[0])
        code3 = force_unicode(items[1])
        name = force_unicode(items[4])
        continent = force_unicode(items[8])

        if self._options['country']:
            if code2.lower() != self._options['country'].lower():
                return
        try:
            country = Country.objects.get(code2=code2)
        except Country.DoesNotExist:
            country = Country(code2=code2)

        country.name = name
        country.code3 = code3
        country.continent = continent
        country.tld = items[9:1]

        if geoname_id:
            country.geoname_id = geoname_id

        sem = transaction.savepoint()
        try:
            country.save()
            transaction.savepoint_commit(sem)
        except IntegrityError:
            transaction.savepoint_rollback(sem)

    def region_import(self, items):
        if len(items) < 4:
            return

        items = [force_unicode(x) for x in items]

        raw_code = items[0].split(".")
        name = items[2]
        name_std = items[1]
        geoname_id = items[3]

        country_code2 = raw_code[0]
        geoname_code = raw_code[1]

        if self._options['country']:
            if country_code2.lower() != self._options['country'].lower():
                return

        try:
            country = self._get_country(country_code2)
        except Country.DoesNotExist:
            return

        try:
            region = Region.objects.get(name=name, country=country, is_subregion=False)
        except Region.DoesNotExist:
            region = Region(is_subregion=False, name=name)

        if country is None:
            import pdb; pdb.set_trace()

        region.country = country
        region.geoname_code = geoname_code
        region.name_std = name_std
        region.geoname_id = geoname_id

        sem = transaction.savepoint()
        try:
            region.save()
            transaction.savepoint_commit(sem)
        except IntegrityError:
            transaction.savepoint_rollback(sem)

    def subregion_import(self, items):
        raw_code = force_unicode(items[0]).split(".")
        name = force_unicode(items[2])
        name_std = force_unicode(items[1])
        geoname_id = items[3]

        country_code2 = raw_code[0]
        region_geoname_code = raw_code[1]
        subregion_geoname_code = raw_code[2]

        if self._options['country']:
            if country_code2.lower() != self._options['country'].lower():
                return

        try:
            country = self._get_country(country_code2)
        except Country.DoesNotExist:
            return

        try:
            region = self._get_region(country_code2, region_geoname_code)
        except Region.DoesNotExist:
            region = None

        try:
            subregion = Region.objects.get(geoname_code=subregion_geoname_code,
                            country=country, is_subregion=True)
        except Region.DoesNotExist:
            subregion = Region(is_subregion=True, parent=region)

        subregion.name = name
        subregion.name_std = name_std
        subregion.country = country
        subregion.geoname_code = subregion_geoname_code
        subregion.geoname_id = geoname_id

        sem = transaction.savepoint()
        try:
            subregion.save()
            transaction.savepoint_commit(sem)
        except IntegrityError:
            transaction.savepoint_rollback(sem)

    def city_import(self, items):
        geoname_id = items[0]
        name = force_unicode(items[2])
        name_std = force_unicode(items[1])
        alternate_names = force_unicode(items[3])
        country_code2 = items[8]
        region_geoname_code = items[10]
        subregion_geoname_code = items[11]
        timezone_name = items[17]

        if self._options['country']:
            if items[8].lower() != self._options['country'].lower():
                return

        timezone = Timezone.objects.get(name=timezone_name)
        country = self._get_country(country_code2)
        region = self._get_region(country_code2, region_geoname_code)
        subregion = self._get_sub_region(country_code2, region_geoname_code, subregion_geoname_code)

        try:
            city = City.objects.get(name=name, country=country, region=region, subregion=subregion)
        except City.DoesNotExist:
            city = City(name=name)

        city.region = region
        city.subregion = subregion
        city.latitude = items[4]
        city.longitude = items[5]
        city.timezone = timezone
        city.country = country
        city.name_std = name_std
        city.alternate_names = alternate_names
        city.geoname_id = geoname_id

        sem = transaction.savepoint()
        try:
            city.save()
            transaction.savepoint_commit(sem)
        except IntegrityError:
            transaction.savepoint_rollback(sem)

    def _get_country(self, country_id):
        """
        Simple lazy identity map for country_id->country
        """

        if not hasattr(self, '_country_codes'):
            self._country_codes = {}

        if self._options['country']:
            if country_id.lower() != self._options['country'].lower():
                return None

        if country_id not in self._country_codes.keys():
            self._country_codes[country_id] = Country.objects.get(code2=country_id)

        return self._country_codes[country_id]

    def _get_region(self, country_code2, region_geoname_code):
        if not hasattr(self, '_region_codes'):
            self._region_codes = {}

        if country_code2 not in self._region_codes:
            self._region_codes[country_code2] = {}

        if region_geoname_code not in self._region_codes[country_code2]:
            try:
                self._region_codes[country_code2][region_geoname_code] = Region.objects\
                    .get(country__code2=country_code2, geoname_code=region_geoname_code, is_subregion=False)
            except Region.DoesNotExist:
                return None

        return self._region_codes[country_code2][region_geoname_code]

    def _get_sub_region(self, country_code2, region_geoname_code, subregion_geoname_code):
        if not hasattr(self, '_sub_region_codes'):
            self._sub_region_codes = {}

        if country_code2 not in self._sub_region_codes:
            self._sub_region_codes[country_code2] = {}

        if subregion_geoname_code not in self._sub_region_codes[country_code2]:
            try:
                self._sub_region_codes[country_code2][subregion_geoname_code] = Region.objects\
                    .get(country__code2=country_code2, geoname_code=subregion_geoname_code, is_subregion=True)
            except Region.DoesNotExist:
                return None

        return self._sub_region_codes[country_code2][subregion_geoname_code]
