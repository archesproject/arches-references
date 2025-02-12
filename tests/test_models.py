from django.test import TestCase

from arches_controlled_lists.models import ListItem

# these tests can be run from the command line via
# python manage.py test tests.test_models --settings="tests.test_settings"


class ListItemTests(TestCase):
    def test_uri_generation_guards_against_failure(self):
        # Don't bother setting up a list.
        item = ListItem(sortorder=0)
        item.id = None

        with self.assertRaises(RuntimeError):
            item.clean()

        item.full_clean(exclude={"list"})
        self.assertIsNotNone(item.uri)
