from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path

from arches_references.views import (
    ListItemView,
    ListView,
    ListsView,
    ListItemImageView,
    ListItemImageMetadataView,
    ListItemValueView,
)

urlpatterns = [
    path("api/controlled_lists", ListsView.as_view(), name="controlled_lists"),
    path(
        "api/controlled_list/<uuid:list_id>",
        ListView.as_view(),
        name="controlled_list",
    ),
    path("api/controlled_list", ListView.as_view(), name="controlled_list_add"),
    path(
        "api/controlled_list_item/<uuid:item_id>",
        ListItemView.as_view(),
        name="controlled_list_item",
    ),
    path(
        "api/controlled_list_item",
        ListItemView.as_view(),
        name="controlled_list_item_add",
    ),
    path(
        "api/controlled_list_item_value/<uuid:value_id>",
        ListItemValueView.as_view(),
        name="controlled_list_item_value",
    ),
    path(
        "api/controlled_list_item_value",
        ListItemValueView.as_view(),
        name="controlled_list_item_value_add",
    ),
    path(
        "api/controlled_list_item_image/<uuid:image_id>",
        ListItemImageView.as_view(),
        name="controlled_list_item_image",
    ),
    path(
        "api/controlled_list_item_image",
        ListItemImageView.as_view(),
        name="controlled_list_item_image_add",
    ),
    path(
        "api/controlled_list_item_image_metadata/<uuid:metadata_id>",
        ListItemImageMetadataView.as_view(),
        name="controlled_list_item_image_metadata",
    ),
    path(
        "api/controlled_list_item_image_metadata",
        ListItemImageMetadataView.as_view(),
        name="controlled_list_item_image_metadata_add",
    ),
]

# Ensure Arches core urls are superseded by project-level urls
urlpatterns.append(path("", include("arches.urls")))

# Adds URL pattern to serve media files during development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Only handle i18n routing in active project. This will still handle the routes provided by Arches core and Arches applications,
# but handling i18n routes in multiple places causes application errors.
if settings.ROOT_URLCONF == __name__:
    if settings.SHOW_LANGUAGE_SWITCH is True:
        urlpatterns = i18n_patterns(*urlpatterns)

    urlpatterns.append(path("i18n/", include("django.conf.urls.i18n")))
