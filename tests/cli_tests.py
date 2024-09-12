import io
import os

from django.core import management
from django.urls import reverse
from django.test import TestCase
from django.test.client import Client
from django.test.utils import captured_stdout
from django.core.management.base import CommandError

from arches_references.models import List, ListItem, ListItemValue
from arches.app.utils.skos import SKOSReader

from .test_settings import PROJECT_TEST_ROOT


# these tests can be run from the command line via
# python manage.py test tests.cli_tests --settings="tests.test_settings"


class ListExportPackageTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        from tests.test_views import ListTests

        return ListTests.setUpTestData()

    def test_export_controlled_list(self):
        export_file_name = "export_controlled_lists.xlsx"
        file_path = os.path.join(PROJECT_TEST_ROOT, export_file_name)
        self.addCleanup(os.remove, file_path)
        output = io.StringIO()
        # packages command does not yet fully avoid print()
        with captured_stdout():
            management.call_command(
                "packages",
                operation="export_controlled_lists",
                dest_dir=PROJECT_TEST_ROOT,
                file_name=export_file_name,
                stdout=output,
            )
        self.assertTrue(os.path.exists(file_path))


class ListImportPackageTests(TestCase):

    def test_import_controlled_list(self):
        input_file = os.path.join(
            PROJECT_TEST_ROOT, "fixtures", "data", "controlled_lists.xlsx"
        )
        output = io.StringIO()
        # packages command does not yet fully avoid print()
        with captured_stdout():
            management.call_command(
                "packages",
                operation="import_controlled_lists",
                source=input_file,
                stdout=output,
            )
        list_pk = "e962bdaf-8243-4fbb-bd43-39bc1f54c168"
        self.assertTrue(List.objects.filter(pk=list_pk).exists())

    ### TODO Add test for creating new language if language code not in db but found in import file


class RDMToControlledListsETLTests(TestCase):
    fixtures = ["polyhierarchical_collections"]

    def test_migrate_collections_to_controlled_lists(self):
        output = io.StringIO()
        management.call_command(
            "controlled_lists",
            operation="migrate_collections_to_controlled_lists",
            collections_to_migrate=[
                "Polyhierarchical Collection Test",
                "Polyhierarchy Collection 2",
            ],
            host="http://localhost:8000/plugins/controlled-list-manager/item/",
            preferred_sort_language="en",
            overwrite=False,
            stdout=output,
        )

        imported_list = List.objects.get(name="Polyhierarchical Collection Test")
        imported_items = imported_list.list_items.all()
        self.assertEqual(len(imported_items), 3)

        imported_item_values = ListItemValue.objects.filter(
            list_item__in=imported_items
        )
        self.assertQuerySetEqual(
            imported_item_values.values_list("value", flat=True).order_by("value"),
            [
                "French Test Concept 1",
                "French Test Concept 2",
                "French Test Concept 3",
                "Test Concept 1",
                "Test Concept 2",
                "Test Concept 3",
            ],
        )

        imported_list_2 = List.objects.get(name="Polyhierarchy Collection 2")
        imported_items_2 = imported_list_2.list_items.all()
        imported_item_values_2 = ListItemValue.objects.filter(
            list_item__in=imported_items_2
        )

        # Check that new uuids were generated for polyhierarchical concepts
        self.assertNotEqual(
            imported_item_values.filter(value="Test Concept 1"),
            imported_item_values_2.filter(value="Test Concept 1"),
        )

        # Check that items with multiple prefLabels in different languages have same listitemid
        self.assertEqual(
            imported_item_values.get(value="Test Concept 1").list_item_id,
            imported_item_values.get(value="French Test Concept 1").list_item_id,
        )

        # But that items with prefLabels in different languages have different listitemvalue ids
        self.assertNotEqual(
            imported_item_values.get(value="Test Concept 1").pk,
            imported_item_values.get(value="French Test Concept 1").pk,
        )

    def test_no_matching_collection_error(self):
        expected_output = "Failed to find the following collections in the database: Collection That Doesn't Exist"
        output = io.StringIO()
        management.call_command(
            "controlled_lists",
            operation="migrate_collections_to_controlled_lists",
            collections_to_migrate=["Collection That Doesn't Exist"],
            host="http://localhost:8000/plugins/controlled-list-manager/item/",
            preferred_sort_language="en",
            overwrite=False,
            stderr=output,
        )
        self.assertIn(expected_output, output.getvalue().strip())

    def test_no_matching_language_error(self):
        expected_output = (
            "The preferred sort language, nonexistent, does not exist in the database."
        )
        output = io.StringIO()
        with self.assertRaises(CommandError) as e:
            management.call_command(
                "controlled_lists",
                operation="migrate_collections_to_controlled_lists",
                collections_to_migrate=["Polyhierarchical Collection Test"],
                host="http://localhost:8000/plugins/controlled-list-manager/item/",
                preferred_sort_language="nonexistent",
                overwrite=False,
                stderr=output,
            )
        self.assertEqual(expected_output, str(e.exception))
