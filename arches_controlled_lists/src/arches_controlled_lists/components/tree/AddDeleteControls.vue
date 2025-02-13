<script setup lang="ts">
import { computed, inject, ref } from "vue";
import { useGettext } from "vue3-gettext";

import { useConfirm } from "primevue/useconfirm";
import { useToast } from "primevue/usetoast";
import Button from "primevue/button";
import SplitButton from "primevue/splitbutton";

import {
    deleteItems,
    deleteLists,
    fetchLists,
} from "@/arches_controlled_lists/api.ts";
import {
    CONTRAST,
    DANGER,
    DEFAULT_ERROR_TOAST_LIFE,
    ERROR,
    PRIMARY,
    SECONDARY,
    displayedRowKey,
    selectedLanguageKey,
} from "@/arches_controlled_lists/constants.ts";
import {
    dataIsItem,
    listAsNode,
    shouldUseContrast,
} from "@/arches_controlled_lists/utils.ts";

import type { Ref } from "vue";
import type { TreeSelectionKeys } from "primevue/tree";
import type { TreeNode } from "primevue/treenode";
import type { Language } from "@/arches_vue_utils/types";
import type {
    ControlledList,
    ControlledListItem,
    IconLabels,
    RowSetter,
    Selectable,
} from "@/arches_controlled_lists/types";

const {
    displayedRow,
    setDisplayedRow,
}: { displayedRow: Ref<Selectable>; setDisplayedRow: RowSetter } = inject(
    displayedRowKey,
) as unknown as { displayedRow: Ref<Selectable>; setDisplayedRow: RowSetter };
const selectedLanguage = inject(selectedLanguageKey) as Ref<Language>;

const tree = defineModel<TreeNode[]>({ required: true });
const selectedKeys = defineModel<TreeSelectionKeys>("selectedKeys", {
    required: true,
});
const isMultiSelecting = defineModel<boolean>("isMultiSelecting", {
    required: true,
});
const nextNewList = defineModel<ControlledList>("nextNewList");
const newListFormValue = defineModel<string>("newListFormValue", {
    required: true,
});

// For new list entry (input textbox)
const newListCounter = ref(1);

const { $gettext, $ngettext } = useGettext();
const confirm = useConfirm();
const toast = useToast();

const multiSelectStateFromDisplayedRow = computed(() => {
    if (!displayedRow.value || !displayedRow.value.id) {
        return {};
    }
    const newSelectedKeys: TreeSelectionKeys = {
        [displayedRow.value.id]: { checked: true, partialChecked: false },
    };

    const recurse = (items: ControlledListItem[]) => {
        for (const child of items) {
            newSelectedKeys[child.id] = {
                checked: false,
                partialChecked: true,
            };
            recurse(child.children);
        }
    };
    if (dataIsItem(displayedRow.value)) {
        recurse((displayedRow.value as ControlledListItem).children);
    } else {
        recurse((displayedRow.value as ControlledList).items);
    }
    return newSelectedKeys;
});

const deleteSelectOptions = [
    {
        label: $gettext("Delete Multiple"),
        command: () => {
            isMultiSelecting.value = true;
            selectedKeys.value = { ...multiSelectStateFromDisplayedRow.value };
        },
    },
];

const iconLabels: IconLabels = {
    list: $gettext("List"),
    item: $gettext("Item"),
};

const createList = () => {
    const newList: ControlledList = {
        id: newListCounter.value.toString(),
        name: newListFormValue.value,
        dynamic: false,
        search_only: false,
        items: [],
        nodes: [],
    };

    nextNewList.value = newList;
    newListCounter.value += 1;

    tree.value.push(listAsNode(newList, selectedLanguage.value, iconLabels));

    selectedKeys.value = { [newList.id]: true };
    setDisplayedRow(newList);
};

const toDelete = computed(() => {
    if (!selectedKeys.value) {
        return [];
    }
    if (isMultiSelecting.value) {
        return Object.entries(selectedKeys.value)
            .filter(([, v]) => v.checked)
            .map(([k]) => k);
    }
    return Object.entries(selectedKeys.value)
        .filter(([, v]) => v)
        .map(([k]) => k);
});

const deleteSelected = async () => {
    if (!selectedKeys.value) {
        return;
    }
    const allListIds = tree.value.map((node) => node.data.id);

    const listIdsToDelete = toDelete.value.filter((id) =>
        allListIds.includes(id),
    );
    const itemIdsToDelete = toDelete.value.filter(
        (id) => !listIdsToDelete.includes(id),
    );

    selectedKeys.value = {};

    // Do items first so that cascade deletion doesn't cause item deletion to fail.
    let anyDeleted = false;
    if (itemIdsToDelete.length) {
        try {
            anyDeleted = await deleteItems(itemIdsToDelete);
        } catch (error) {
            if (error instanceof Error) {
                error.message.split("|").forEach((detail: string) => {
                    toast.add({
                        severity: ERROR,
                        life: DEFAULT_ERROR_TOAST_LIFE,
                        summary: $gettext("Item deletion failed"),
                        detail,
                    });
                });
            }
        }
    }
    if (listIdsToDelete.length) {
        try {
            anyDeleted = (await deleteLists(listIdsToDelete)) || anyDeleted;
        } catch (error) {
            if (error instanceof Error) {
                error.message.split("|").forEach((detail) => {
                    toast.add({
                        severity: ERROR,
                        life: DEFAULT_ERROR_TOAST_LIFE,
                        summary: $gettext("List deletion failed"),
                        detail,
                    });
                });
            }
        }
    }
    if (anyDeleted) {
        setDisplayedRow(null);
    }

    isMultiSelecting.value = false;
};

const confirmDelete = () => {
    const numItems = toDelete.value.length;
    confirm.require({
        message: $ngettext(
            "Are you sure you want to delete %{numItems} item (including all children)?",
            "Are you sure you want to delete %{numItems} items (including all children)?",
            numItems,
            { numItems: numItems.toLocaleString() },
        ),
        header: $gettext("Confirm deletion"),
        icon: "fa fa-exclamation-triangle",
        acceptProps: {
            label: $gettext("Delete"),
            severity: shouldUseContrast() ? CONTRAST : DANGER,
            style: { fontSize: "small" },
        },
        rejectProps: {
            label: $gettext("Cancel"),
            severity: shouldUseContrast() ? CONTRAST : SECONDARY,
            style: { fontSize: "small" },
        },
        accept: async () => {
            await deleteSelected().then(fetchListsAndPopulateTree);
        },
        reject: () => {},
    });
};

const fetchListsAndPopulateTree = async () => {
    /*
    Currently, rather than inspecting the results of the batched
    delete requests, we just refetch everything. This requires being
    a little clever about resorting the ordered response from the API
    to preserve the existing sort (and avoid confusion).
    */
    const priorSortedListIds = tree.value.map((node) => node.key);

    await fetchLists()
        .then(
            ({ controlled_lists }: { controlled_lists: ControlledList[] }) => {
                tree.value = controlled_lists
                    .map((list) =>
                        listAsNode(list, selectedLanguage.value, iconLabels),
                    )
                    .sort(
                        (a, b) =>
                            priorSortedListIds.indexOf(a.key) -
                            priorSortedListIds.indexOf(b.key),
                    );
            },
        )
        .catch((error: Error) => {
            toast.add({
                severity: ERROR,
                life: DEFAULT_ERROR_TOAST_LIFE,
                summary: $gettext("Unable to fetch lists"),
                detail: error.message,
            });
        });
};

await fetchListsAndPopulateTree();
</script>

<template>
    <Button
        class="list-button"
        :label="$gettext('Add New List')"
        raised
        :severity="shouldUseContrast() ? CONTRAST : PRIMARY"
        @click="createList"
    />
    <SplitButton
        class="list-button"
        :label="$gettext('Delete')"
        :menu-button-props="{ 'aria-label': $gettext('Delete multiple') }"
        raised
        :disabled="!toDelete.length"
        :severity="shouldUseContrast() ? CONTRAST : DANGER"
        :model="deleteSelectOptions"
        :pt="{
            pcButton: {
                root: { style: { width: '100%', fontSize: 'inherit' } },
            },
        }"
        @click="confirmDelete"
    />
</template>

<style scoped>
.list-button {
    height: 4rem;
    margin: 0.5rem;
    flex: 0.5;
    justify-content: center;
    text-wrap: nowrap;
    font-size: inherit;
}
</style>
