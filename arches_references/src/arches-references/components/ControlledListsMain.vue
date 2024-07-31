<script setup lang="ts">
import arches from "arches";
import { provide, ref } from "vue";
import { useRouter } from "vue-router";

import ConfirmDialog from "primevue/confirmdialog";
import Toast from "primevue/toast";

import {
    displayedRowKey,
    routes,
    selectedLanguageKey,
} from "@/arches-references/constants.ts";
import { dataIsList } from "@/arches-references/utils.ts";

import ListHeader from "@/arches-references/components/misc/ListHeader.vue";
import MainSplitter from "@/arches-references/components/MainSplitter.vue";

import type { Ref } from "vue";
import type { Language } from "arches/arches/app/src/arches/types";
import type { Selectable } from "@/arches-references/types";

const router = useRouter();

const displayedRow: Ref<Selectable | null> = ref(null);
function setDisplayedRow(row: Selectable | null) {
    displayedRow.value = row;
    if (row === null) {
        router.push({ name: routes.splash });
        return;
    }
    if (typeof row.id === "number") {
        return;
    }
    if (dataIsList(row)) {
        router.push({ name: routes.list, params: { id: row.id } });
    } else {
        router.push({ name: routes.item, params: { id: row.id } });
    }
}
provide(displayedRowKey, { displayedRow, setDisplayedRow });

const selectedLanguage: Ref<Language> = ref(
    (arches.languages as Language[]).find(
        (lang) => lang.code === arches.activeLanguage,
    ) as Language,
);
provide(selectedLanguageKey, selectedLanguage);
</script>

<template>
    <!-- Subtract size of arches toolbars -->
    <div style="width: calc(100vw - 50px); height: calc(100vh - 50px)">
        <div class="list-editor-container">
            <ListHeader />
            <MainSplitter />
        </div>
    </div>
    <Toast />
    <ConfirmDialog
        :draggable="false"
        :pt="{
            root: {
                style: {
                    fontSize: 'small',
                },
            },
            header: {
                style: {
                    background: 'var(--p-primary-950)',
                    color: 'white',
                    borderRadius: '1rem',
                    marginBottom: '1rem',
                },
            },
            title: {
                style: {
                    fontWeight: 800,
                },
            },
        }"
    />
</template>

<style scoped>
.list-editor-container {
    display: flex;
    flex-direction: column;
    height: 100%;
}
</style>
