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

from ...models import City, Country, Region, Timezone
from ... import settings as local_settings

from os.path import abspath, dirname, join, normpath, exists
from os import mkdir, remove
from subprocess import Popen, PIPE
import tempfile
import shutil
import glob


class Command(BaseCommand):
    temp_path = "/tmp/cities-translations"

    def make_language_directories(self):
        cities_path = normpath(join(dirname(abspath(__file__)), "..", ".."))
        cities_locale_path = join(cities_path, "locale")

        if not exists(cities_locale_path):
            mkdir(cities_locale_path)

        for lang, lang_ in settings.LANGUAGES:
            lang_path = join(cities_locale_path, lang)

            if not exists(lang_path):
                mkdir(lang_path)

            lc_messages_path = join(lang_path, "LC_MESSAGES")
            if not exists(lc_messages_path):
                mkdir(lc_messages_path)

            real_file = join(lc_messages_path, 'django.po')
            yield lang, real_file

    def merge_po_file(self, temp_path, real_path):
        p = Popen(["msgmerge", real_path, temp_path], stdout=PIPE)

        with io.open(real_path + ".tmp", "wt", encoding="utf-8") as f:
            for line in p.stdout:
                f.write(line.decode("utf-8"))

        os.remove(temp_path)
        os.remove(real_path)

        shutil.copy(real_path + ".tmp", real_path)
        os.remove(real_path + ".tmp")

    def generate_new_po(self, lang):
        pathlist = glob.glob(join(self.temp_path, lang) + "*")
        output_path = join(self.temp_path, "{0}_django.po".format(lang))

        command = ["xgettext", "-language=Python", "-keyword=ugettext:1,2",
            "-o", output_path, "--from-code", "utf-8"]
        command += pathlist

        r = Popen(command, stdout=PIPE).wait()
        return output_path

    @transaction.commit_on_success
    def handle(self, *args, **options):
        languages = list(self.make_language_directories())

        # Clear temporal directories
        if exists(self.temp_path):
            shutil.rmtree(self.temp_path)
        mkdir(self.temp_path)

        for lang, real_path in languages:
            # Country
            countrys_path = join(self.temp_path, "{0}.country.py".format(lang))
            with io.open(countrys_path, "wt", encoding="utf-8") as f:
                for country in Country.objects.only('name'):
                    f.write(u'ugettext(u"{0}")\n'.format(country.name))

            regions_path = join(self.temp_path, "{0}.region.py".format(lang))
            with io.open(regions_path, "wt", encoding="utf-8") as f:
                for region in Region.objects.only('name'):
                    f.write(u'ugettext(u"{0}")\n'.format(region.name))

            city_path = join(self.temp_path, "{0}.city.py".format(lang))
            with io.open(city_path, "wt", encoding="utf-8") as f:
                for city in City.objects.only('name'):
                    f.write(u'ugettext(u"{0}")\n'.format(city.name))

            new_po_file = self.generate_new_po(lang)

            if exists(real_path):
                self.merge_po_file(new_po_file, real_path)
            else:
                shutil.copy(new_po_file, real_path)
                os.remove(new_po_file)

        shutil.rmtree(self.temp_path)
