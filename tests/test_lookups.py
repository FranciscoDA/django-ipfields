import ipaddress
from .models import AddrTestModel, NetTestModel
from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist


class TestSupernetsLookup(TestCase):
    def test_ipv4_net_supernets_ipv4_net(self):
        instance1 = NetTestModel.objects.create(field='192.168.0.0/16')
        self.assertTrue(NetTestModel.objects.filter(field__supernets='192.168.1.0/24').exists())
        self.assertFalse(NetTestModel.objects.filter(field__supernets='192.0.0.0/8').exists())
        self.assertTrue(NetTestModel.objects.filter(field__supernets=ipaddress.IPv4Network('192.168.1.0/24')).exists())
        self.assertFalse(NetTestModel.objects.filter(field__supernets=ipaddress.IPv4Network('192.0.0.0/8')).exists())
    
    def test_ipv4_net_supernets_ipv4_addr(self):
        instance1 = NetTestModel.objects.create(field='192.168.0.0/16')
        self.assertTrue(NetTestModel.objects.filter(field__supernets='192.168.1.1').exists())
        self.assertTrue(NetTestModel.objects.filter(field__supernets=ipaddress.IPv4Address('192.168.1.1')).exists())

class TestSubnetsLookup(TestCase):
    def test_ipv4_net_subnets_ipv4_net(self):
        instance1 = NetTestModel.objects.create(field='192.168.1.0/24')
        self.assertTrue(NetTestModel.objects.filter(field__subnets='192.168.0.0/16').exists())
        self.assertFalse(NetTestModel.objects.filter(field__subnets='192.168.1.128/25').exists())

    def test_ipv4_net_subnets_ipv4_addr(self):
        instance1 = NetTestModel.objects.create(field='192.168.1.0/24')
        self.assertFalse(NetTestModel.objects.filter(field__subnets='192.168.1.1').exists())


class TestPrivateLookup(TestCase):
    def test_private_ipv4_net_is_private(self):
        instance1 = NetTestModel.objects.create(field='192.168.1.0/24')
        self.assertTrue(NetTestModel.objects.filter(field__isprivate=True).exists())
        self.assertFalse(NetTestModel.objects.filter(field__isprivate=False).exists())

    def test_public_ipv4_net_is_private(self):
        instance1 = NetTestModel.objects.create(field='111.111.111.0/24')
        self.assertFalse(NetTestModel.objects.filter(field__isprivate=True).exists())
        self.assertTrue(NetTestModel.objects.filter(field__isprivate=False).exists())

    def test_private_ipv4_addr_is_private(self):
        instance1 = AddrTestModel.objects.create(field='10.1.2.3')
        self.assertTrue(AddrTestModel.objects.filter(field__isprivate=True).exists())
        self.assertFalse(AddrTestModel.objects.filter(field__isprivate=False).exists())

    def test_public_ipv4_addr_is_private(self):
        instance1 = AddrTestModel.objects.create(field='8.8.8.8')
        self.assertFalse(AddrTestModel.objects.filter(field__isprivate=True).exists())
        self.assertTrue(AddrTestModel.objects.filter(field__isprivate=False).exists())

