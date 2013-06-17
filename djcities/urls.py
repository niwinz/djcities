# -*- coding: utf-8 -*-

from __future__ import absolute_import
from django.conf.urls import patterns, include, url

from .views import ProvincesForCountry, CitiesForCountry

urlpatterns = patterns('',
    url(r'regions/$', ProvincesForCountry.as_view(), name="regions"),
    url(r'cities/$', CitiesForCountry.as_view(), name="cities"),
)
