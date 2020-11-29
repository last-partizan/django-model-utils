from datetime import datetime

from django.test.testcases import TestCase
from freezegun import freeze_time

from tests.models import Status, StatusCustomManager, StatusPlainTuple


class StatusModelTests(TestCase):
    def setUp(self):
        self.model = Status
        self.on_hold = Status.STATUS.on_hold
        self.active = Status.STATUS.active

    def test_created(self):
        with freeze_time(datetime(2016, 1, 1)):
            c1 = self.model.objects.create()
        self.assertTrue(c1.status_changed, datetime(2016, 1, 1))

        self.model.objects.create()
        self.assertEqual(self.model.active.count(), 2)
        self.assertEqual(self.model.deleted.count(), 0)

    def test_modification(self):
        t1 = self.model.objects.create()
        date_created = t1.status_changed
        t1.status = self.on_hold
        t1.save()
        self.assertEqual(self.model.active.count(), 0)
        self.assertEqual(self.model.on_hold.count(), 1)
        self.assertTrue(t1.status_changed > date_created)
        date_changed = t1.status_changed
        t1.save()
        self.assertEqual(t1.status_changed, date_changed)
        date_active_again = t1.status_changed
        t1.status = self.active
        t1.save()
        self.assertTrue(t1.status_changed > date_active_again)

    def test_save_with_update_fields_overrides_status_changed_provided(self):
        '''
        Tests if the save method updated status_changed field
        accordingly when update_fields is used as an argument
        and status_changed is provided
        '''
        with freeze_time(datetime(2020, 1, 1)):
            t1 = Status.objects.create()

        with freeze_time(datetime(2020, 1, 2)):
            t1.status = Status.on_hold
            t1.save(update_fields=['status', 'status_changed'])

        self.assertEqual(t1.status_changed, datetime(2020, 1, 2))

    def test_save_with_update_fields_overrides_status_changed_not_provided(self):
        '''
        Tests if the save method updated status_changed field
        accordingly when update_fields is used as an argument
        with status and status_changed is not provided
        '''
        with freeze_time(datetime(2020, 1, 1)):
            t1 = Status.objects.create()

        with freeze_time(datetime(2020, 1, 2)):
            t1.status = Status.on_hold
            t1.save(update_fields=['status'])

        self.assertEqual(t1.status_changed, datetime(2020, 1, 2))


class StatusModelPlainTupleTests(StatusModelTests):
    def setUp(self):
        self.model = StatusPlainTuple
        self.on_hold = StatusPlainTuple.STATUS[2][0]
        self.active = StatusPlainTuple.STATUS[0][0]


class StatusModelDefaultManagerTests(TestCase):

    def test_default_manager_is_not_status_model_generated_ones(self):
        # Regression test for GH-251
        # The logic behind order for managers seems to have changed in Django 1.10
        # and affects default manager.
        # This code was previously failing because the first custom manager (which filters
        # with first Choice value, here 'first_choice') generated by StatusModel was
        # considered as default manager...
        # This situation only happens when we define a model inheriting from an "abstract"
        # class which defines an "objects" manager.

        StatusCustomManager.objects.create(status='first_choice')
        StatusCustomManager.objects.create(status='second_choice')
        StatusCustomManager.objects.create(status='second_choice')

        # ...which made this count() equal to 1 (only 1 element with status='first_choice')...
        self.assertEqual(StatusCustomManager._default_manager.count(), 3)

        # ...and this one equal to 0, because of 2 successive filters of 'first_choice'
        # (default manager) and 'second_choice' (explicit filter below).
        self.assertEqual(StatusCustomManager._default_manager.filter(status='second_choice').count(), 2)
