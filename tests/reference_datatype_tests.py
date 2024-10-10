from arches.app.datatypes.datatypes import DataTypeFactory
from arches.app.models.tile import Tile
from arches_references.models import List, ListItem, ListItemValue
from django.test import TestCase

# these tests can be run from the command line via
# python manage.py test tests.reference_datatype_tests --settings="tests.test_settings"


class ReferenceDataTypeTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        from tests.test_views import ListTests

        return ListTests.setUpTestData()

    def test_validate(self):
        reference = DataTypeFactory().get_instance("reference")

        for value in [
            "",
            [],
            [{}],  # reference has no 'uri'
            [{"uri": ""}],  # reference uri is empty
        ]:
            with self.subTest(reference_value=value):
                errors = reference.validate(value)
                self.assertTrue(len(errors) > 0)

        data = {
            "uri": "https://www.domain.com/label",
            "labels": [
                {
                    "id": "23b4efbd-2e46-4b3f-8d75-2f3b2bb96af2",
                    "value": "label",
                    "language_id": "en",
                    "valuetype_id": "prefLabel",
                },
                {
                    "id": "e8676242-f0c7-4e3d-b031-fded4960cd86",
                    "language_id": "de",
                    "valuetype_id": "prefLabel",
                },
            ],
        }

        errors = reference.validate(value=[data])  # label missing value property
        self.assertIsNotNone(errors)

        data["labels"][1]["value"] = "a label"
        data["labels"][1]["language_id"] = "en"

        errors = reference.validate(value=[data])  # too many prefLabels per language
        self.assertIsNotNone(errors)

        data["labels"][1]["value"] = "ein label"
        data["labels"][1]["language_id"] = "de"

        errors = reference.validate(value=[data])  # data should be valid
        self.assertTrue(len(errors) == 0)

    def test_tile_clean(self):
        reference = DataTypeFactory().get_instance("reference")
        nodeid = "72048cb3-adbc-11e6-9ccf-14109fd34195"
        resourceinstanceid = "40000000-0000-0000-0000-000000000000"
        data = [
            {
                "uri": "https://www.domain.com/label",
                "labels": [
                    {
                        "id": "23b4efbd-2e46-4b3f-8d75-2f3b2bb96af2",
                        "value": "label",
                        "language_id": "en",
                        "valuetype_id": "prefLabel",
                    },
                ],
                "listid": "fd9508dc-2aab-4c46-85ae-dccce1200035",
            }
        ]

        tile_info = {
            "resourceinstance_id": resourceinstanceid,
            "parenttile_id": "",
            "nodegroup_id": nodeid,
            "tileid": "",
            "data": {nodeid: {"en": data}},
        }

        tile1 = Tile(tile_info)
        reference.clean(tile1, nodeid)
        self.assertIsNotNone(tile1.data[nodeid])

        tile1.data[nodeid] = []
        reference.clean(tile1, nodeid)
        self.assertIsNone(tile1.data[nodeid])

    def test_transform_value_for_tile(self):
        reference = DataTypeFactory().get_instance("reference")
        list1_pk = str(List.objects.get(name="list1").pk)
        config = {"controlledList": list1_pk}

        tile_value1 = reference.transform_value_for_tile("label1-pref", **config)
        self.assertTrue(isinstance(tile_value1, list))
        self.assertTrue("uri" in tile_value1[0])
        self.assertTrue("labels" in tile_value1[0])
        self.assertTrue("listid" in tile_value1[0])

        self.assertIsNone(reference.transform_value_for_tile(None, **config))

        # Test deterministic sorting:
        #   Force two items to have the same prefLabel in a list,
        #   expect the list item with lower sortorder to be returned
        expected_list_item_pk = str(
            ListItem.objects.get(
                list_item_values__value="label2-pref", list_id=list1_pk
            ).pk
        )
        ListItemValue.objects.filter(
            value="label3-pref", list_item_id__list_id=list1_pk
        ).update(value="label2-pref")
        tile_value2 = reference.transform_value_for_tile("label2-pref", **config)
        self.assertEqual(
            tile_value2[0]["labels"][0]["list_item_id"], expected_list_item_pk
        )
