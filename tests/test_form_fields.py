from django.test import TestCase
from django.db.utils import IntegrityError
from django.forms import ModelForm

from .models import \
    AddrTestModel, NullableAddrTestModel, UniqueAddrTestModel, \
    NetTestModel, NullableNetTestModel, UniqueNetTestModel

from ipaddress import IPv4Address, IPv6Address, IPv4Network, IPv6Network


class AddrTestModelForm(ModelForm):
    class Meta:
        model = AddrTestModel
        exclude = []

class NullableAddrTestModelForm(ModelForm):
    class Meta:
        model = NullableAddrTestModel
        exclude = []

class UniqueAddrTestModelForm(ModelForm):
    class Meta:
        model = UniqueAddrTestModel
        exclude = []

class NetTestModelForm(ModelForm):
    class Meta:
        model = NetTestModel
        exclude = []

class NullableNetTestModelForm(ModelForm):
    class Meta:
        model = NullableNetTestModel
        exclude = []

class UniqueNetTestModelForm(ModelForm):
    class Meta:
        model = UniqueNetTestModel
        exclude = []

class TestAddrTestModelForm(TestCase):
    form_class = AddrTestModelForm

    def test_form_ipv4_valid(self):
        form = self.form_class({'field': '10.0.0.1'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['field'], IPv4Address('10.0.0.1'))

    def test_form_ipv4_invalid(self):
        form = self.form_class({'field': '10.0.0.0.1'})
        self.assertFalse(form.is_valid())
    
    def test_form_ipv4_change(self):
        instance = self.form_class.Meta.model.objects.create(field='10.1.2.3')
        form = self.form_class({'field': '10.1.2.4'}, instance=instance)
        self.assertTrue(form.is_valid())
        form.save()
        instance = self.form_class.Meta.model.objects.get(pk=instance.pk)
        self.assertEqual(instance.field, IPv4Address('10.1.2.4'))

    def test_form_ipv6_valid(self):
        form = self.form_class({'field': '2001:0:1::2'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['field'], IPv6Address('2001:0:1::2'))
    
    def test_form_ipv6_invalid(self):
        form = self.form_class({'field': '2001:0::1::2'})
        self.assertFalse(form.is_valid())
    
    def test_form_ipv6_change(self):
        instance = self.form_class.Meta.model.objects.create(field='2001:0:1::2')
        form = self.form_class({'field': '2001:0:1::3'}, instance=instance)
        self.assertTrue(form.is_valid())
        form.save()
        instance = self.form_class.Meta.model.objects.get(pk=instance.pk)
        self.assertEqual(instance.field, IPv6Address('2001:0:1::3'))

class TestNullableAddrTestModelForm(TestAddrTestModelForm):
    form_class = NullableAddrTestModelForm

    def test_null_ip(self):
        form = self.form_class({'field': None})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['field'], None)
    
    def test_null_ipv4(self):
        form = self.form_class({'field': None})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['field'], None)

class TestUniqueAddrTestModelForm(TestAddrTestModelForm):
    form_class = UniqueAddrTestModelForm
    def test_unique_ipv4(self):
        instance1 = self.form_class.Meta.model.objects.create(field='192.168.1.1')
        with self.assertRaises(IntegrityError):
            instance2 = self.form_class.Meta.model.objects.create(field='192.168.1.1')

    def test_unique_ipv6(self):
        instance1 = self.form_class.Meta.model.objects.create(field='abde::abde')
        with self.assertRaises(IntegrityError):
            instance2 = self.form_class.Meta.model.objects.create(field='abde::abde')