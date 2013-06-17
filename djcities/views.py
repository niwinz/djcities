# -*- coding: utf-8 -*-

from django.http import HttpResponseBadRequest, HttpResponseNotFound
from .models import Country, Region


class ProvincesForCountry(JsonView):
    def get(self, request):
        if "country" not in request.GET:
            return HttpResponseBadRequest()
        elif not request.GET["country"]:
            return self.render_json({'list': []})

        try:
            country = Country.objects.get(pk=request.GET['country'])
        except Country.DoesNotExist:
            return HttpResponseNotFound()

        return self.render_json({'list': [x.to_dict() for x in country.filtered_regions.all()]})


class CitiesForCountry(JsonView):
    def get(self, request):
        if "country" not in request.GET:
            return HttpResponseBadRequest()
        elif not request.GET["country"]:
            return self.render_json({'list': []})

        try:
            country = Country.objects.get(pk=request.GET['country'])
        except Country.DoesNotExist:
            return HttpResponseNotFound()

        return self.render_json({'list': [x.to_dict() for x in country.cities.all()]})
