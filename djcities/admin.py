# -*- coding: utf-8 -*-

from django.contrib import admin
from . import models

admin.site.register(models.Country)
admin.site.register(models.Region)
admin.site.register(models.City)
admin.site.register(models.Timezone)
