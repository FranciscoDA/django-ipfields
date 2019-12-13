from ipaddress import \
    ip_address, ip_network, \
    IPv4Network, IPv6Network, \
    IPv4Address, IPv6Address
from django.forms import fields
from django.core.exceptions import ValidationError


def address_to_python(ip_version, value):
    try:
        func = {
            4: IPv4Address,
            6: IPv6Address
        }.get(ip_version, ip_address)
        return func(value)
    except ValueError as e:
        raise ValidationError(str(e))

def network_to_python(ip_version, value):
    try:
        func = {
            4: IPv4Network,
            6: IPv6Network
        }.get(ip_version, ip_network)
        return func(value)
    except ValueError as e:
        raise ValidationError(str(e))

class IpAddressFormField(fields.CharField):
    def __init__(self, *args, ip_version, **kwargs):
        self.ip_version = ip_version
        super().__init__(*args, **kwargs)
    
    def clean(self, value):
        if not self.required and (value is None or value == ''):
            return None
        return address_to_python(self.ip_version, value)

class IpNetworkFormField(fields.CharField):
    def __init__(self, *args, ip_version, **kwargs):
        self.ip_version = ip_version
        super().__init__(*args, **kwargs)
    
    def clean(self, value):
        return network_to_python(self.ip_version, value)
