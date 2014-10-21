# -*- coding: utf-8 -*-

from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.db import models

from .settings import *


CONTINENT_CHOICES = (
    ('OC', _(u'Oceania')),
    ('EU', _(u'Europe')),
    ('AF', _(u'Africa')),
    ('NA', _(u'North America')),
    ('AN', _(u'Antarctica')),
    ('SA', _(u'South America')),
    ('AS', _(u'Asia')),
)


def slugify_uniquely(value, model, slugfield="slug"):
    """
    Returns a slug on a name which is unique within a model's table
    self.slug = SlugifyUniquely(self.name, self.__class__)
    """
    suffix = 0
    potential = base = slugify(value)
    if len(potential) == 0:
        potential = 'null'
    while True:
        if suffix:
            potential = "-".join([base, str(suffix)])
        if not model.objects.filter(**{slugfield: potential}).count():
            return potential
        suffix += 1


class Base(models.Model):
    """
    Base model with boilerplate for all models.
    """

    geoname_id = models.IntegerField(null=True, blank=True, unique=True)
    slug = models.SlugField(max_length=200, blank=True)
    name = models.CharField(max_length=200, db_index=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.name, self.__class__)
        super(Base, self).save(*args, **kwargs)


class Country(Base):
    """
    Country model.
    """

    code2 = models.CharField(max_length=2, null=True, blank=True, unique=True)
    code3 = models.CharField(max_length=3, null=True, blank=True, unique=True)
    continent = models.CharField(max_length=2, db_index=True,
        choices=CONTINENT_CHOICES)
    tld = models.CharField(max_length=5, blank=True, db_index=True)

    class Meta:
        verbose_name_plural = _(u'countries')
        ordering = ['name']

    @property
    def filtered_regions(self):
        if self.code2 in COUNTRIES_WITH_SUBREGION_PROVINCES:
            return self.regions.only_subregions().all()
        return self.regions.only_regions().all()


class RegionManager(models.Manager):
    use_for_related_fields = True

    def only_subregions(self):
        return self.get_query_set()\
            .filter(is_subregion=True)

    def only_regions(self):
        return self.get_query_set()\
            .filter(is_subregion=False)


class Region(Base):
    """
    Region/State model.

    Can search regions or subregions with some helpers
    methods introduced to related manager.

    Examples::

    >>> c = Country.objects.get(code2="ES")
    >>> c.regions.only_subregions()
    [<Region: Ceuta>, <Region: Melilla>, <Region: Murcia>, <Region: Provincia de Castello>, '...']

    >>> c.regions.only_regions()
    [<Region: Andalusia>, <Region: Aragon>, <Region: Asturias>, <Region: Balearic Islands>, '...']
    """

    name_std = models.CharField(max_length=200)
    country = models.ForeignKey(Country, related_name="regions", on_delete = models.CASCADE)
    geoname_code = models.CharField(max_length=50, null=True, blank=True,
        db_index=True)

    is_subregion = models.BooleanField(default=False)
    parent = models.ForeignKey("self", null=True, default=None, related_name="subregions")

    objects = RegionManager()

    class Meta:
        verbose_name = _('region/state')
        verbose_name_plural = _('regions/states')
        ordering = ['name']

    def get_display_name(self):
        return u'%s, %s' % (self.name, self.country.name)

    def to_dict(self):
        return {
            "id": self.pk,
            "name": self.name,
            "slug": self.slug,
            "geoname_id": self.geoname_id,
        }


class City(Base):
    """
    City model.
    """

    name_std = models.CharField(max_length=200, db_index=True)
    alternate_names = models.TextField(null=True, blank=True, default='')

    latitude = models.DecimalField(max_digits=8, decimal_places=5,
        null=True, blank=True)

    longitude = models.DecimalField(max_digits=8, decimal_places=5,
        null=True, blank=True)

    region = models.ForeignKey("Region", blank=True, null=True, related_name="cities")
    subregion = models.ForeignKey("Region", blank=True, null=True, related_name="cities_as_subregion")
    country = models.ForeignKey("Country", related_name="cities", on_delete = models.CASCADE)
    timezone = models.ForeignKey("Timezone", related_name="cities", on_delete = models.CASCADE, null=True, default=None)

    class Meta:
        unique_together = ('country', 'name')
        verbose_name_plural = _(u'cities')
        ordering = ['name']

    def get_display_name(self):
        if self.region_id:
            return u'%s, %s, %s' % (self.name, self.region.name,
                self.country.name)

        return u'%s, %s' % (self.name, self.country.name)

    def to_dict(self):
        return {
            "id": self.pk,
            "name": self.name,
            "slug": self.slug,
        }


class Timezone(models.Model):
    country_code = models.CharField(max_length=100)
    name = models.CharField(max_length=200, unique=True)
    gmt_offset = models.CharField(max_length=50)
    country = models.ForeignKey("Country", related_name="timezones",
        on_delete = models.CASCADE,
        null=True, default=None)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return u"{0} (GMT{1})".format(self.name, self.gmt_offset)
