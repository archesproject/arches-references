<script setup lang="ts">
import arches from "arches";
import { computed, inject } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";

import { itemKey, CONTRAST, PRIMARY } from "@/arches-references/constants.ts";
import { shouldUseContrast } from "@/arches-references/utils.ts";

import type { Ref } from "vue";
import type {
    ControlledListItem,
    ControlledListItemImage,
    LabeledChoice,
    NewControlledListItemImageMetadata,
} from "@/arches-references/types";

const { labeledChoices, image, makeMetadataEditable } = defineProps<{
    labeledChoices: LabeledChoice[];
    image: ControlledListItemImage;
    makeMetadataEditable: (
        clickedMetadata: NewControlledListItemImageMetadata,
        index: number,
    ) => void;
}>();
const item = inject(itemKey) as Ref<ControlledListItem>;

const { $gettext } = useGettext();

const newMetadata: Ref<NewControlledListItemImageMetadata> = computed(() => {
    const otherNewMetadataIds = image.metadata
        .filter((metadatum) => typeof metadatum.id === "number")
        .map((metadatum) => metadatum.id as number);

    const maxOtherNewMetadataId = Math.max(...otherNewMetadataIds, 0);

    const nextMetadataType =
        labeledChoices.find(
            (choice) =>
                !image.metadata
                    .map((metadatum) => metadatum.metadata_type)
                    .includes(choice.type),
        ) ?? labeledChoices[0];

    return {
        id: maxOtherNewMetadataId + 1,
        metadata_type: nextMetadataType.type,
        metadata_label: nextMetadataType.label,
        language_id: arches.activeLanguage,
        list_item_image_id: image.id,
        value: "",
    };
});

const addMetadata = () => {
    const staticNewMetadata = newMetadata.value;
    item.value.images
        .find((imageFromItem) => imageFromItem.id === image.id)!
        .metadata.push(staticNewMetadata);
    makeMetadataEditable(staticNewMetadata, -1);
};
</script>

<template>
    <Button
        class="add-metadata"
        raised
        icon="fa fa-plus-circle"
        :severity="shouldUseContrast() ? CONTRAST : PRIMARY"
        :label="$gettext('Add metadata')"
        @click="addMetadata"
    />
</template>

<style scoped>
.add-metadata {
    display: flex;
    height: 3rem;
    margin-top: 1rem;
}
</style>
