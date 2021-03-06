from __future__ import unicode_literals
from django.test import TestCase
from django.utils import six
from rest_framework import serializers
from tests.models import (
    ManyToManyTarget, ManyToManySource, ForeignKeyTarget, ForeignKeySource,
    NullableForeignKeySource, OneToOneTarget, NullableOneToOneSource,
)


# ManyToMany
class ManyToManyTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManyToManyTarget
        fields = ('id', 'name', 'sources')


class ManyToManySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManyToManySource
        fields = ('id', 'name', 'targets')


# ForeignKey
class ForeignKeyTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeyTarget
        fields = ('id', 'name', 'sources')


class ForeignKeySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeySource
        fields = ('id', 'name', 'target')


# Nullable ForeignKey
class NullableForeignKeySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NullableForeignKeySource
        fields = ('id', 'name', 'target')


# Nullable OneToOne
class NullableOneToOneTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = OneToOneTarget
        fields = ('id', 'name', 'nullable_source')


# TODO: Add test that .data cannot be accessed prior to .is_valid

class PKManyToManyTests(TestCase):
    def setUp(self):
        for idx in range(1, 4):
            target = ManyToManyTarget(name='target-%d' % idx)
            target.save()
            source = ManyToManySource(name='source-%d' % idx)
            source.save()
            for target in ManyToManyTarget.objects.all():
                source.targets.add(target)

    def test_many_to_many_retrieve(self):
        queryset = ManyToManySource.objects.all()
        serializer = ManyToManySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'targets': [1]},
            {'id': 2, 'name': 'source-2', 'targets': [1, 2]},
            {'id': 3, 'name': 'source-3', 'targets': [1, 2, 3]}
        ]
        with self.assertNumQueries(4):
            self.assertEqual(serializer.data, expected)

    def test_many_to_many_retrieve_prefetch_related(self):
        queryset = ManyToManySource.objects.all().prefetch_related('targets')
        serializer = ManyToManySourceSerializer(queryset, many=True)
        with self.assertNumQueries(2):
            serializer.data

    def test_reverse_many_to_many_retrieve(self):
        queryset = ManyToManyTarget.objects.all()
        serializer = ManyToManyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': [1, 2, 3]},
            {'id': 2, 'name': 'target-2', 'sources': [2, 3]},
            {'id': 3, 'name': 'target-3', 'sources': [3]}
        ]
        with self.assertNumQueries(4):
            self.assertEqual(serializer.data, expected)

    def test_many_to_many_update(self):
        data = {'id': 1, 'name': 'source-1', 'targets': [1, 2, 3]}
        instance = ManyToManySource.objects.get(pk=1)
        serializer = ManyToManySourceSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(serializer.data, data)

        # Ensure source 1 is updated, and everything else is as expected
        queryset = ManyToManySource.objects.all()
        serializer = ManyToManySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'targets': [1, 2, 3]},
            {'id': 2, 'name': 'source-2', 'targets': [1, 2]},
            {'id': 3, 'name': 'source-3', 'targets': [1, 2, 3]}
        ]
        self.assertEqual(serializer.data, expected)

    def test_reverse_many_to_many_update(self):
        data = {'id': 1, 'name': 'target-1', 'sources': [1]}
        instance = ManyToManyTarget.objects.get(pk=1)
        serializer = ManyToManyTargetSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(serializer.data, data)

        # Ensure target 1 is updated, and everything else is as expected
        queryset = ManyToManyTarget.objects.all()
        serializer = ManyToManyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': [1]},
            {'id': 2, 'name': 'target-2', 'sources': [2, 3]},
            {'id': 3, 'name': 'target-3', 'sources': [3]}
        ]
        self.assertEqual(serializer.data, expected)

    def test_many_to_many_create(self):
        data = {'id': 4, 'name': 'source-4', 'targets': [1, 3]}
        serializer = ManyToManySourceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(serializer.data, data)
        self.assertEqual(obj.name, 'source-4')

        # Ensure source 4 is added, and everything else is as expected
        queryset = ManyToManySource.objects.all()
        serializer = ManyToManySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'targets': [1]},
            {'id': 2, 'name': 'source-2', 'targets': [1, 2]},
            {'id': 3, 'name': 'source-3', 'targets': [1, 2, 3]},
            {'id': 4, 'name': 'source-4', 'targets': [1, 3]},
        ]
        self.assertEqual(serializer.data, expected)

    def test_reverse_many_to_many_create(self):
        data = {'id': 4, 'name': 'target-4', 'sources': [1, 3]}
        serializer = ManyToManyTargetSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(serializer.data, data)
        self.assertEqual(obj.name, 'target-4')

        # Ensure target 4 is added, and everything else is as expected
        queryset = ManyToManyTarget.objects.all()
        serializer = ManyToManyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': [1, 2, 3]},
            {'id': 2, 'name': 'target-2', 'sources': [2, 3]},
            {'id': 3, 'name': 'target-3', 'sources': [3]},
            {'id': 4, 'name': 'target-4', 'sources': [1, 3]}
        ]
        self.assertEqual(serializer.data, expected)


class PKForeignKeyTests(TestCase):
    def setUp(self):
        target = ForeignKeyTarget(name='target-1')
        target.save()
        new_target = ForeignKeyTarget(name='target-2')
        new_target.save()
        for idx in range(1, 4):
            source = ForeignKeySource(name='source-%d' % idx, target=target)
            source.save()

    def test_foreign_key_retrieve(self):
        queryset = ForeignKeySource.objects.all()
        serializer = ForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': 1},
            {'id': 2, 'name': 'source-2', 'target': 1},
            {'id': 3, 'name': 'source-3', 'target': 1}
        ]
        with self.assertNumQueries(1):
            self.assertEqual(serializer.data, expected)

    def test_reverse_foreign_key_retrieve(self):
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': [1, 2, 3]},
            {'id': 2, 'name': 'target-2', 'sources': []},
        ]
        with self.assertNumQueries(3):
            self.assertEqual(serializer.data, expected)

    def test_reverse_foreign_key_retrieve_prefetch_related(self):
        queryset = ForeignKeyTarget.objects.all().prefetch_related('sources')
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        with self.assertNumQueries(2):
            serializer.data

    def test_foreign_key_update(self):
        data = {'id': 1, 'name': 'source-1', 'target': 2}
        instance = ForeignKeySource.objects.get(pk=1)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(serializer.data, data)

        # Ensure source 1 is updated, and everything else is as expected
        queryset = ForeignKeySource.objects.all()
        serializer = ForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': 2},
            {'id': 2, 'name': 'source-2', 'target': 1},
            {'id': 3, 'name': 'source-3', 'target': 1}
        ]
        self.assertEqual(serializer.data, expected)

    def test_foreign_key_update_incorrect_type(self):
        data = {'id': 1, 'name': 'source-1', 'target': 'foo'}
        instance = ForeignKeySource.objects.get(pk=1)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'target': ['Incorrect type. Expected pk value, received %s.' % six.text_type.__name__]})

    def test_reverse_foreign_key_update(self):
        data = {'id': 2, 'name': 'target-2', 'sources': [1, 3]}
        instance = ForeignKeyTarget.objects.get(pk=2)
        serializer = ForeignKeyTargetSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        # We shouldn't have saved anything to the db yet since save
        # hasn't been called.
        queryset = ForeignKeyTarget.objects.all()
        new_serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': [1, 2, 3]},
            {'id': 2, 'name': 'target-2', 'sources': []},
        ]
        self.assertEqual(new_serializer.data, expected)

        serializer.save()
        self.assertEqual(serializer.data, data)

        # Ensure target 2 is update, and everything else is as expected
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': [2]},
            {'id': 2, 'name': 'target-2', 'sources': [1, 3]},
        ]
        self.assertEqual(serializer.data, expected)

    def test_foreign_key_create(self):
        data = {'id': 4, 'name': 'source-4', 'target': 2}
        serializer = ForeignKeySourceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(serializer.data, data)
        self.assertEqual(obj.name, 'source-4')

        # Ensure source 4 is added, and everything else is as expected
        queryset = ForeignKeySource.objects.all()
        serializer = ForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': 1},
            {'id': 2, 'name': 'source-2', 'target': 1},
            {'id': 3, 'name': 'source-3', 'target': 1},
            {'id': 4, 'name': 'source-4', 'target': 2},
        ]
        self.assertEqual(serializer.data, expected)

    def test_reverse_foreign_key_create(self):
        data = {'id': 3, 'name': 'target-3', 'sources': [1, 3]}
        serializer = ForeignKeyTargetSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(serializer.data, data)
        self.assertEqual(obj.name, 'target-3')

        # Ensure target 3 is added, and everything else is as expected
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': [2]},
            {'id': 2, 'name': 'target-2', 'sources': []},
            {'id': 3, 'name': 'target-3', 'sources': [1, 3]},
        ]
        self.assertEqual(serializer.data, expected)

    def test_foreign_key_update_with_invalid_null(self):
        data = {'id': 1, 'name': 'source-1', 'target': None}
        instance = ForeignKeySource.objects.get(pk=1)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'target': ['This field may not be null.']})

    def test_foreign_key_with_empty(self):
        """
        Regression test for #1072

        https://github.com/tomchristie/django-rest-framework/issues/1072
        """
        serializer = NullableForeignKeySourceSerializer()
        self.assertEqual(serializer.data['target'], None)


class PKNullableForeignKeyTests(TestCase):
    def setUp(self):
        target = ForeignKeyTarget(name='target-1')
        target.save()
        for idx in range(1, 4):
            if idx == 3:
                target = None
            source = NullableForeignKeySource(name='source-%d' % idx, target=target)
            source.save()

    def test_foreign_key_retrieve_with_null(self):
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': 1},
            {'id': 2, 'name': 'source-2', 'target': 1},
            {'id': 3, 'name': 'source-3', 'target': None},
        ]
        self.assertEqual(serializer.data, expected)

    def test_foreign_key_create_with_valid_null(self):
        data = {'id': 4, 'name': 'source-4', 'target': None}
        serializer = NullableForeignKeySourceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(serializer.data, data)
        self.assertEqual(obj.name, 'source-4')

        # Ensure source 4 is created, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': 1},
            {'id': 2, 'name': 'source-2', 'target': 1},
            {'id': 3, 'name': 'source-3', 'target': None},
            {'id': 4, 'name': 'source-4', 'target': None}
        ]
        self.assertEqual(serializer.data, expected)

    def test_foreign_key_create_with_valid_emptystring(self):
        """
        The emptystring should be interpreted as null in the context
        of relationships.
        """
        data = {'id': 4, 'name': 'source-4', 'target': ''}
        expected_data = {'id': 4, 'name': 'source-4', 'target': None}
        serializer = NullableForeignKeySourceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(serializer.data, expected_data)
        self.assertEqual(obj.name, 'source-4')

        # Ensure source 4 is created, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': 1},
            {'id': 2, 'name': 'source-2', 'target': 1},
            {'id': 3, 'name': 'source-3', 'target': None},
            {'id': 4, 'name': 'source-4', 'target': None}
        ]
        self.assertEqual(serializer.data, expected)

    def test_foreign_key_update_with_valid_null(self):
        data = {'id': 1, 'name': 'source-1', 'target': None}
        instance = NullableForeignKeySource.objects.get(pk=1)
        serializer = NullableForeignKeySourceSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(serializer.data, data)

        # Ensure source 1 is updated, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': None},
            {'id': 2, 'name': 'source-2', 'target': 1},
            {'id': 3, 'name': 'source-3', 'target': None}
        ]
        self.assertEqual(serializer.data, expected)

    def test_foreign_key_update_with_valid_emptystring(self):
        """
        The emptystring should be interpreted as null in the context
        of relationships.
        """
        data = {'id': 1, 'name': 'source-1', 'target': ''}
        expected_data = {'id': 1, 'name': 'source-1', 'target': None}
        instance = NullableForeignKeySource.objects.get(pk=1)
        serializer = NullableForeignKeySourceSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(serializer.data, expected_data)

        # Ensure source 1 is updated, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': None},
            {'id': 2, 'name': 'source-2', 'target': 1},
            {'id': 3, 'name': 'source-3', 'target': None}
        ]
        self.assertEqual(serializer.data, expected)


class PKNullableOneToOneTests(TestCase):
    def setUp(self):
        target = OneToOneTarget(name='target-1')
        target.save()
        new_target = OneToOneTarget(name='target-2')
        new_target.save()
        source = NullableOneToOneSource(name='source-1', target=new_target)
        source.save()

    def test_reverse_foreign_key_retrieve_with_null(self):
        queryset = OneToOneTarget.objects.all()
        serializer = NullableOneToOneTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'nullable_source': None},
            {'id': 2, 'name': 'target-2', 'nullable_source': 1},
        ]
        self.assertEqual(serializer.data, expected)
