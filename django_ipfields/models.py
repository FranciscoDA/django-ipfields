from ipaddress import \
        ip_address, ip_network, \
        IPv4Network, IPv6Network, \
        IPv4Address, IPv6Address, \
        IPV6LENGTH, IPV4LENGTH

import django.db.models
from django.core.exceptions import ValidationError, ImproperlyConfigured

from .forms import address_to_python, IpAddressFormField, IpNetworkFormField


def _to_bin(byte_seq):
    return ''.join(format(byte, '08b') for byte in byte_seq)

def addr_to_repr(ipaddr_obj):
    if ipaddr_obj is None:
        return None
    version = str(ipaddr_obj.version)
    return version + _to_bin(ipaddr_obj.packed)

def net_to_repr(ipnet_obj):
    if ipnet_obj is None:
        return None
    version = str(ipnet_obj.version)
    return version + _to_bin(ipnet_obj.network_address.packed)[:ipnet_obj.prefixlen]

_address_class = {4: IPv4Address, 6: IPv6Address}
_network_class = {4: IPv4Network, 6: IPv6Network}
_max_len_by_protocol = lambda version: {4: IPV4LENGTH, 6: IPV6LENGTH}.get(version, IPV6LENGTH)

def _add_len_to_value(value):
    class Wrapper(type(value)):
        def __len__(self):
            return self.max_prefixlen
    return Wrapper(value)

IP_VERSION_CHOICES = (4, 6, None)

class IpAddressField(django.db.models.CharField):
    def __init__(self, *args, ip_version=None, **kwargs):
        if ip_version not in IP_VERSION_CHOICES:
            raise ImproperlyConfigured('ip_version must be one of %s', IP_VERSION_CHOICES)
        self.ip_version = ip_version
        # just enough room to hold an ip address (bit per bit) + 1 char for version 
        kwargs['max_length'] = _max_len_by_protocol(self.ip_version) + 1
        if kwargs.get('blank'):
            raise ImproperlyConfigured('IP address fields cannot be blank')
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        return IpAddressFormField(ip_version=self.ip_version, required=not self.null, **kwargs)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        version, value = int(value[0]), value[1:]
        value = int(value, 2)
        try:
            return _address_class[version](value)
        except ValueError as e:
            raise ValidationError(str(e))
        except KeyError as e:
            raise ValidationError('Unsupported protocol version: %s', params=(version,))

    def to_python(self, value):
        if value is None or value == '':
            return None
        if isinstance(value, (IPv4Address, IPv6Address)):
            if hasattr(value, '__len__'):
                return value
            else:
                return _add_len_to_value(value)
        value = address_to_python(self.ip_version, value)
        return _add_len_to_value(value)

    def get_prep_value(self, value):
        if isinstance(value, str):
            value = self.to_python(value)
        return addr_to_repr(value)

class IpNetworkField(django.db.models.CharField):
    def __init__(self, *args, ip_version=None, **kwargs):
        if ip_version not in IP_VERSION_CHOICES:
            raise ImproperlyConfigured('ip_version must be one of %s', IP_VERSION_CHOICES)
        self.ip_version = ip_version
        kwargs['max_length'] = _max_len_by_protocol(self.ip_version) + 1
        if kwargs.get('blank'):
            raise ImproperlyConfigured('IP network fields cannot be blank')
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        return IpNetworkFormField(ip_version=self.ip_version, required=not self.null, **kwargs)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        version, value = int(value[0]), value[1:]
        prefixlen = len(value)
        # right-pad with zeros before converting to int
        value = int(format(value, f'<0{_max_len_by_protocol(version)}s'), 2)
        try:
            return _network_class[version]((value, prefixlen))
        except ValueError as e:
            raise ValidationError(str(e))
        except KeyError as e:
            raise ValidationError('Unsupported protocol version: %s', params=(version,))

    def to_python(self, value):
        if value is None or value == '':
            return None
        if isinstance(value, (IPv4Network, IPv6Network)):
            if hasattr(value, '__len__'):
                return value
            else:
                return _add_len_to_value(value)
        return _add_len_to_value(ip_network(value))

    def get_prep_value(self, value):
        if isinstance(value, str):
            value = self.to_python(value)
        return net_to_repr(value)


