<script setup lang="ts">
import { inject } from "vue";
import { useGettext } from "vue3-gettext";

import { getItemLabel } from "@/arches_vue_utils/utils.ts";
import {
    itemKey,
    selectedLanguageKey,
    systemLanguageKey,
} from "@/arches_references/constants.ts";
import LetterCircle from "@/arches_references/components/misc/LetterCircle.vue";

import type { Ref } from "vue";
import type { Language } from "@/arches_vue_utils/types";
import type { ControlledListItem } from "@/arches_references/types";

const selectedLanguage = inject(selectedLanguageKey) as Ref<Language>;
const systemLanguage = inject(systemLanguageKey) as Language;
const item = inject(
    itemKey,
) as Ref<ControlledListItem> as Ref<ControlledListItem>;

const { $gettext } = useGettext();

const iconLabel = (item: ControlledListItem) => {
    return item.guide ? $gettext("Guide Item") : $gettext("Indexable Item");
};
</script>

<template>
    <span class="item-header">
        <LetterCircle :labelled="item" />
        <h3>
            {{
                getItemLabel(item, selectedLanguage.code, systemLanguage.code)
                    .value
            }}
        </h3>
        <span class="item-type">{{ iconLabel(item) }}</span>
        <a
            v-if="item.uri"
            :href="item.uri"
            rel="noreferrer"
            target="_blank"
            style="font-size: small; color: blue; text-decoration: underline"
        >
            {{ item.uri }}
        </a>
    </span>
</template>

<style scoped>
.item-header {
    display: inline-flex;
    align-items: center;
    gap: 1rem;
    margin: 1rem 1rem 0rem 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid;
    width: 100%;
}

h3 {
    margin: 0;
}

.item-type {
    font-size: small;
    font-weight: 200;
}
</style>
