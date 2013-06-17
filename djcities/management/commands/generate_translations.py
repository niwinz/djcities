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
from django.db import transaction
from django.conf import settings

from ...models import City, Country, Region
from ... import settings as local_settings

PO_HEADER = u"""
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2012-06-13 16:29+0200\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"Language: \\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=2; plural=(n != 1)\\n"
"""


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        optparse.make_option('--force', action='append', default=[],
            help='Download and import even if matching files are up-to-date'
        ),
    )

    def prepare(self):
        if not os.path.exists(local_settings.TMPDATA_DIR):
            print "Creating temporal data directory: {0}".format(local_settings.TMPDATA_DIR)
            os.mkdir(local_settings.TMPDATA_DIR)

        # Generate all ids
        self.data = {}
        for pk, slug in Country.objects.values_list('geoname_id', 'name'):
            self.data[pk] = slug

        for item in Region.objects.values_list('geoname_id', 'name'):
            self.data[pk] = slug

        for item in City.objects.values_list('geoname_id', 'name'):
            self.data[pk] = slug

        self.langs = dict(settings.LANGUAGES).keys()

    def download(self, name, source, dest_path):
        response = requests.get(source)
        file_size = int(response.headers['content-length'])

        with io.open(dest_path, "bw") as f:
            for chuck in response.iter_content(512):
                f.write(chuck)
                sys.stdout.write(".")
            sys.stdout.write("\n")

    def extract(self, infile, outfile, filename):
        zfile = zipfile.ZipFile(infile)
        if zfile:
             with io.open(outfile, "wb") as f:
                f.write(zfile.read(filename))

    def download_datafiles(self):
        source = local_settings.TRANSLATIONS['source']
        filename = local_settings.TRANSLATIONS['file']
        dest_name = local_settings.TRANSLATIONS['dest']

        print "Downloading: {0}".format(dest_name)

        dest_path = os.path.join(local_settings.TMPDATA_DIR, dest_name)
        if os.path.exists(dest_path):
            print "File exists, skiping."
            return

        if source.endswith(".zip"):
            tmp_dest_path = dest_path + ".zip"
        else:
            tmp_dest_path = dest_path

        self.download(dest_name, source, tmp_dest_path)

        if tmp_dest_path.endswith(".zip"):
            self.extract(tmp_dest_path, dest_path, filename)

    def file_content_parser(self, path):
        with io.open(path, "r") as f:
            for line in f:
                line = line.strip()
                if len(line) < 1 or line[0] == "#":
                    continue

                yield [e.strip() for e in line.split('\t')]

    def _openfiles(self):
        self.files = {}
        for lang in self.langs:
            dst_file_path = os.path.join(local_settings.TMPDATA_DIR, "django_{0}.po".format(lang))
            self.files[lang] = io.open(dst_file_path, "w")
            self.files[lang].write(PO_HEADER.strip())
            self.files[lang].write(u"\n\n")

    def _closefiles(self):
        for name, f in self.files.iteritems():
            f.close()

    def insert_translation(self, lang, name, translation):
        f = self.files[lang]
        f.write(u'msgid "{0}"\n'.format(name))
        f.write(u'msgstr "{0}"\n\n'.format(translation))

    def parse(self, item):
        if len(item) > 4:
            return

        code, lang = int(item[1]), force_unicode(item[2]).strip()

        if not lang or lang not in self.langs:
            return

        if code not in self.data:
            return

        print item
        self.insert_translation(lang, self.data[code], item[3])

    @transaction.commit_on_success
    def handle(self, *args, **options):
        self.prepare()
        self.download_datafiles()

        dest_name = local_settings.TRANSLATIONS['dest']
        dest_path = os.path.join(local_settings.TMPDATA_DIR, dest_name)

        self._openfiles()

        for item in self.file_content_parser(dest_path):
            self.parse(item)

        self._closefiles()
