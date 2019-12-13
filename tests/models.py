from django.db import models
from django_ipfields import IpAddressField, IpNetworkField

class AddrTestModel(models.Model):
    field = IpAddressField(null=False)

class NullableAddrTestModel(models.Model):
    field = IpAddressField(null=True)

class UniqueAddrTestModel(models.Model):
    field = IpAddressField(unique=True)

class NetTestModel(models.Model):
    field = IpNetworkField(null=False)

class NullableNetTestModel(models.Model):
    field = IpNetworkField(null=True)

class UniqueNetTestModel(models.Model):
    field = IpNetworkField(unique=True)

class NetBoolTestModel(models.Model):
    netfield = IpNetworkField(null=False)
    boolfield = models.BooleanField(null=False)

