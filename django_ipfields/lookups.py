import django.db.models
from django.core.exceptions import ValidationError

from ipaddress import \
        ip_address, ip_network, \
        IPv4Network, IPv6Network, \
        IPv4Address, IPv6Address, \
        IPV6LENGTH, IPV4LENGTH
from .models import IpNetworkField, IpAddressField, addr_to_repr, net_to_repr


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
            return addr_to_repr(rhs)
        elif isinstance(rhs, (IPv4Network, IPv6Network)):
            return net_to_repr(rhs)
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

@IpNetworkField.register_lookup
@IpAddressField.register_lookup
class PrivateLookup(django.db.models.Lookup):
    lookup_name = 'isprivate'
    prepare_rhs = False # prevent casting to lhs output_type in self.get_prep_lookup

    PRIVATE_NETWORKS = (
        net_to_repr(IPv4Network('192.168.0.0/16')),
        net_to_repr(IPv4Network('10.0.0.0/8')),
        net_to_repr(IPv4Network('172.16.0.0/12')),
        net_to_repr(IPv6Network('fc00::0/8')),
        net_to_repr(IPv6Network('fd00::0/8'))
    )

    def process_lhs(self, compiler, connection, lhs=None):
        # we want to build an SQL expression as follows:
        # <LHS> LIKE <NETWORK0>%, <LHS> LIKE <NETWORK1>%, ..., <LHS> LIKE <NETWORKN>%
        # where:
        #   <NETWORKN> are elements from self.PRIVATE_NETWORKS
        #   <LHS> is the original lhs in the queryset
        lhs, lhs_params = super().process_lhs(compiler, connection, lhs)
        lhs_params = []

        def mk_like_expression(lhs, network):
            p0 = "'%s'" % connection.ops.prep_for_like_query(network)
            return '%s %s' % (lhs, connection.pattern_ops['startswith'].format(connection.pattern_esc).format(p0))

        lhs_new = ' OR '.join(mk_like_expression(lhs, network) for network in self.PRIVATE_NETWORKS)
        return lhs_new, []

    def as_sql(self, compiler, connection):
        lhs_sql, lhs_params = self.process_lhs(compiler, connection)
        rhs_sql, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        sql = '(%s) = %s' % (lhs_sql, rhs_sql), params
        return sql
