# Django-ipfields

This package allows defining django model fields as IP addresses or networks. Values are encoded into the database as a character string of binary digits. This allows compatibility with RDMSes other than PostgreSQL while allowing subnet/supernet queries.


This package was inspired by the [django-netfields](https://pypi.org/project/django-netfields/) package.

```py
from django.db import models
from ipfields import IpAddressField, IpNetworkField
class MyModel(models.Model):
    ipv4_addr     = IpAddressField(version=4) # forces ipv4 addresses
    ipv6_net      = IpNetworkField(version=6) # forces ipv6 networks
    nullable_addr = IpAddressField(null=True) # allows ipv4 and ipv6 addresses and null
```
Note that defining an IpAddressField or IpNetworkField with blank=True will result in an exception.

The Python classes used for values are the ones defined in the ipaddress standard library package:
* ipaddress.IPv4Address
* ipaddress.IPv6Address
* ipaddress.IPv4Network
* ipaddress.IPv6Network

Conversion from form string values to the appropiate python value is done through the ipaddress.ip_address and ipaddress.ip_network functions. Here are some valid examples:
* `192.168.1.1` IPv4 address
* `10.11.11.0/24` IPv4 network
* `2a03:2880:f110:83:face:b00c::25de` IPv4 address

Relevant lookups:
* __supernets: Matches rows where the column in the lhs is a supernet of the value in the rhs
* __startswith: Matches rows where the column in the lhs is a subnet of the value in the lhs

