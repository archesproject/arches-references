import io
import os

from django.core import management
from django.urls import reverse
from django.test import TestCase
from django.test.client import Client
from django.test.utils import captured_stdout

from arches_references.models import List, ListItem
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
        input_file = os.path.join(PROJECT_TEST_ROOT, "data", "controlled_lists.xlsx")
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

    @classmethod
    def setUpTestData(cls):

        skos = SKOSReader()
        rdf = skos.read_file(
            os.path.join(PROJECT_TEST_ROOT, "data", "concept_label_test_collection.xml")
        )
        ret = skos.save_concepts_from_skos(rdf)

        client = Client()
        client.login(username="admin", password="admin")
        response = client.get(
            reverse(
                "make_collection",
                kwargs={"conceptid": "7c90899a-dbe9-4574-9175-e69481a80b3c"},
            )
        )

    def test_migrate_collections_to_controlled_lists(self):
        output = io.StringIO()
        management.call_command(
            "controlled_lists",
            operation="migrate_collections_to_controlled_lists",
            collections_to_migrate=["Concept Label Import Test"],
            host="http://localhost:8000/plugins/controlled-list-manager/item/",
            preferred_sort_language="en",
            overwrite=False,
            stdout=output,
        )

        imported_list = List.objects.get(name="Concept Label Import Test")
        imported_items = imported_list.list_items.all()
        self.assertEqual(len(imported_items), 3)

    def test_no_matching_collection_error(self):
        expected_output = "Failed to find the following collections in the database: Collection That Doesn't Exist"
        with captured_stdout() as output:
            management.call_command(
                "controlled_lists",
                operation="migrate_collections_to_controlled_lists",
                collections_to_migrate=["Collection That Doesn't Exist"],
                host="http://localhost:8000/plugins/controlled-list-manager/item/",
                preferred_sort_language="en",
                overwrite=False,
                stdout=output,
                stderr=output,
            )
        self.assertIn(expected_output, output.getvalue().strip())
