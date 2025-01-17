import uuid

from django.db.models.fields.json import JSONField
from django.utils.translation import get_language, gettext as _

from arches.app.datatypes.base import BaseDataType
from arches.app.models.graph import GraphValidationError

from arches_references.models import ListItem


class ReferenceDataType(BaseDataType):
    rest_framework_model_field = JSONField(null=True)

    def validate(
        self,
        value,
        row_number=None,
        source="",
        node=None,
        nodeid=None,
        strict=False,
        **kwargs,
    ):
        errors = []
        title = _("Invalid Reference Datatype Value")
        if value is None:
            return errors

        if type(value) == list and len(value):
            for reference in value:
                if "uri" in reference and len(reference["uri"]):
                    pass
                else:
                    errors.append(
                        {
                            "type": "ERROR",
                            "message": _(
                                "Reference objects require a 'uri' property and corresponding value"
                            ),
                            "title": title,
                        }
                    )
                if "labels" in reference:
                    pref_label_languages = []
                    for label in reference["labels"]:
                        if not all(
                            key in label
                            for key in ("id", "value", "language_id", "valuetype_id")
                        ):
                            errors.append(
                                {
                                    "type": "ERROR",
                                    "message": _(
                                        "Reference labels require properties: id(uuid), value(string), language_id(e.g. 'en'), and valuetype_id(e.g. 'prefLabel')"
                                    ),
                                    "title": title,
                                }
                            )
                        if label["valuetype_id"] == "prefLabel":
                            pref_label_languages.append(label["language_id"])

                    if len(set(pref_label_languages)) < len(pref_label_languages):
                        errors.append(
                            {
                                "type": "ERROR",
                                "message": _(
                                    "A reference can have only one prefLabel per language"
                                ),
                                "title": title,
                            }
                        )
        else:
            errors.append(
                {
                    "type": "ERROR",
                    "message": _("Reference value must be a list of reference objects"),
                    "title": title,
                }
            )
        return errors

    def transform_value_for_tile(self, value, **kwargs):
        list_id = kwargs.get("controlledList")
        if (
            isinstance(value, list)
            and isinstance(value[0], dict)
            and "value" in value[0]
        ):
            value = value[0]["value"]
        if isinstance(value, str):
            found_item = self.lookup_listitem_from_label(value, list_id)
            if found_item:
                value = [found_item.build_tile_value()]
        return value

    def lookup_listitem_from_label(self, value, list_id):
        return (
            ListItem.objects.filter(list_id=list_id, list_item_values__value=value)
            .order_by("sortorder")
            .first()
        )

    def clean(self, tile, nodeid):
        super().clean(tile, nodeid)
        if tile.data[nodeid] == []:
            tile.data[nodeid] = None

    def transform_export_values(self, value, *args, **kwargs):
        return ",".join(value)

    def get_display_value(self, tile, node, **kwargs):
        labels = []
        requested_language = kwargs.pop("language", None)
        current_language = requested_language or get_language()
        node_data = self.get_tile_data(tile)[str(node.nodeid)]
        if node_data:
            for item in node_data:
                for label in item["labels"]:
                    if (
                        label["language_id"] == current_language
                        and label["valuetype_id"] == "prefLabel"
                    ):
                        labels.append(label.get("value", ""))
        return ", ".join(labels)

    def collects_multiple_values(self):
        return True

    def default_es_mapping(self):
        return {
            "properties": {
                "uri": {"type": "keyword"},
                "id": {"type": "keyword"},
                "labels": {
                    "properties": {},
                },
            }
        }

    def validate_node(self, node):
        try:
            uuid.UUID(node.config["controlledList"])
        except (TypeError, KeyError):
            raise GraphValidationError(
                _("A reference datatype node requires a controlled list")
            )
