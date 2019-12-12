from ipaddress import \
        ip_address, ip_network, \
        IPv4Network, IPv6Network, \
        IPv4Address, IPv6Address, \
        IPV6LENGTH, IPV4LENGTH, \
        v4_int_to_packed, v6_int_to_packed

import django.db.models
from django.core.exceptions import ValidationError, ImproperlyConfigured

from .forms import address_to_python, IpAddressFormField, IpNetworkFormField


def _to_bin(byte_seq):
    return ''.join(format(byte, '08b') for byte in byte_seq)

def _addr_to_repr(ipaddr_obj):
    if ipaddr_obj is None:
        return None
    version = str(ipaddr_obj.version)
    return version + _to_bin(ipaddr_obj.packed)

def _net_to_repr(ipnet_obj):
    if ipnet_obj is None:
        return None
    version = str(ipnet_obj.version)
    return version + _to_bin(ipnet_obj.network_address.packed)[:ipnet_obj.prefixlen]

_address_class = {4: IPv4Address, 6: IPv6Address}
_network_class = {4: IPv4Network, 6: IPv6Network}
_max_len_by_protocol = lambda version: {4: 32, 6: 128}.get(version, 128)

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
        return _addr_to_repr(value)

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
        return _net_to_repr(value)

class IpFieldLookup(django.db.models.Lookup):
    def get_prep_lookup(self):
        rhs = self.rhs
        if isinstance(self.rhs, str):
            try:
                rhs = ip_address(rhs)
            except ValueError:
                try:
                    rhs = ip_network(rhs)
                except ValueError:
                    raise ValidationError(f'{rhs} does not appear to be an IPv4, IPv6 address or network.')
        if isinstance(rhs, (IPv4Address, IPv6Address)):
            return _addr_to_repr(rhs)
        elif isinstance(rhs, (IPv4Network, IPv6Network)):
            return _net_to_repr(rhs)
        else:
            raise ValidationError('Invalid rhs for lookup. Must be one of str, IPv4Address, IPv6Address, IPv4Network, IPv6Network.')

    def get_rhs_op(self, connection, rhs):
        if hasattr(self.rhs, 'as_sql') or self.bilateral_transforms:
            pattern = connection.pattern_ops[self.pattern_lookup_name].format(connection.pattern_esc)
            return pattern.format(rhs)
        else:
            return connection.operators[self.pattern_lookup_name] % rhs

@IpNetworkField.register_lookup
class SupernetLookup(IpFieldLookup):
    lookup_name = 'supernets'
    pattern_lookup_name = 'startswith'

    def process_lhs(self, compiler, connection, lhs=None):
        lhs = lhs or self.lhs
        if hasattr(lhs, 'resolve_expression'):
            lhs = lhs.resolve_expression(compiler.query)
        if hasattr(lhs, 'as_sql'):
            return compiler.compile(lhs)
        else:
            return self.get_db_prep_lookup(lhs, connection)

    def as_sql(self, compiler, connection):
        self.lhs, self.rhs = self.rhs, self.lhs
        lhs_sql, lhs_params = self.process_lhs(compiler, connection)
        rhs_sql, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        rhs_sql = self.get_rhs_op(connection, rhs_sql)

        return '%s %s' % (lhs_sql, rhs_sql), params

@IpNetworkField.register_lookup
class SubnetLookup(IpFieldLookup):
    lookup_name = 'subnets'
    pattern_lookup_name = 'startswith'

    def process_rhs(self, qn, connection):
        rhs, params = super().process_rhs(qn, connection)
        if self.rhs_is_direct_value() and params and not self.bilateral_transforms:
            params[0] = '%s%%' % connection.ops.prep_for_like_query(params[0])
        return rhs, params

    def as_sql(self, compiler, connection):
        lhs_sql, lhs_params = self.process_lhs(compiler, connection)
        rhs_sql, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        rhs_sql = self.get_rhs_op(connection, rhs_sql)

        return '%s %s' % (lhs_sql, rhs_sql), params