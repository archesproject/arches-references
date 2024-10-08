<script setup lang="ts">
import { computed, inject, ref, useTemplateRef, watch } from "vue";
import { useRoute } from "vue-router";
import { useGettext } from "vue3-gettext";

import Tree from "primevue/tree";

import { getItemLabel } from "@/arches_vue_utils/utils.ts";
import {
    displayedRowKey,
    selectedLanguageKey,
    systemLanguageKey,
} from "@/arches_references/constants.ts";
import { routeNames } from "@/arches_references/routes.ts";
import { findNodeInTree, nodeIsList } from "@/arches_references/utils.ts";
import LetterCircle from "@/arches_references/components/misc/LetterCircle.vue";
import ListTreeControls from "@/arches_references/components/tree/ListTreeControls.vue";
import TreeRow from "@/arches_references/components/tree/TreeRow.vue";

import type { Ref } from "vue";
import type { RouteLocationNormalizedLoadedGeneric } from "vue-router";
import type { TreePassThroughMethodOptions } from "primevue/tree";
import type { TreeExpandedKeys, TreeSelectionKeys } from "primevue/tree";
import type { TreeNode } from "primevue/treenode";
import type { Language } from "@/arches_vue_utils/types";
import type {
    ControlledList,
    ControlledListItem,
    RowSetter,
} from "@/arches_references/types";

const { $gettext } = useGettext();

const moveLabels = Object.freeze({
    addChild: $gettext("Add child item"),
    moveUp: $gettext("Move item up"),
    moveDown: $gettext("Move item down"),
    changeParent: $gettext("Change item parent"),
});

const tree: Ref<TreeNode[]> = ref([]);
const selectedKeys: Ref<TreeSelectionKeys> = ref({});
const expandedKeys: Ref<TreeExpandedKeys> = ref({});
const movingItem: Ref<TreeNode | undefined> = ref();
const isMultiSelecting = ref(false);
const refetcher = ref(0);
const filterValue = ref("");
const treeComponent = useTemplateRef("treeComponent");

// For next new item's pref label (input textbox)
const newLabelFormValue = ref("");
const nextNewItem = ref<ControlledListItem>();
// For new list entry (input textbox)
const newListFormValue = ref("");
const nextNewList = ref<ControlledList>();
const rerenderTree = ref(0);
const nextFilterChangeNeedsExpandAll = ref(false);
const expandedKeysSnapshotBeforeSearch = ref<TreeExpandedKeys>({});

const selectedLanguage = inject(selectedLanguageKey) as Ref<Language>;
const systemLanguage = inject(systemLanguageKey) as Language;
const { setDisplayedRow } = inject(displayedRowKey) as unknown as {
    setDisplayedRow: RowSetter;
};

const route = useRoute();

const navigate = (newRoute: RouteLocationNormalizedLoadedGeneric) => {
    switch (newRoute.name) {
        case routeNames.splash:
            setDisplayedRow(null);
            expandedKeys.value = {};
            selectedKeys.value = {};
            break;
        case routeNames.list: {
            if (!tree.value.length) {
                return;
            }
            const list = tree.value.find(
                (node) => node.data.id === newRoute.params.id,
            );
            if (list) {
                setDisplayedRow(list.data);
                expandedKeys.value = {
                    ...expandedKeys.value,
                    [list.data.id]: true,
                };
                selectedKeys.value = { [list.data.id]: true };
            } else {
                setDisplayedRow(null);
            }
            break;
        }
        case routeNames.item: {
            if (!tree.value.length) {
                return;
            }
            const { found, path } = findNodeInTree(
                tree.value,
                newRoute.params.id as string,
            );
            if (found) {
                setDisplayedRow(found.data);
                const itemsToExpandIds = path.map(
                    (itemInPath: TreeNode) => itemInPath.key,
                );
                expandedKeys.value = {
                    ...expandedKeys.value,
                    ...Object.fromEntries(
                        [
                            found.data.controlled_list_id,
                            ...itemsToExpandIds,
                        ].map((x) => [x, true]),
                    ),
                };
                selectedKeys.value = { [found.data.id]: true };
            }
            break;
        }
    }
};

// React to route changes.
watch(
    [
        () => {
            return { ...route };
        },
    ],
    ([newRoute]) => {
        navigate(newRoute);
    },
);

// Navigate on initial load of the tree.
watch(tree, () => navigate(route), { once: true });

const updateSelectedAndExpanded = (node: TreeNode) => {
    if (isMultiSelecting.value || movingItem.value?.key) {
        return;
    }

    setDisplayedRow(node.data);
    expandedKeys.value = {
        ...expandedKeys.value,
        [node.key]: true,
    };
};

const expandAll = () => {
    const newExpandedKeys = {};
    for (const node of tree.value) {
        expandNode(node, newExpandedKeys);
    }
    expandedKeys.value = { ...newExpandedKeys };
};

const expandNode = (node: TreeNode, newExpandedKeys: TreeExpandedKeys) => {
    if (node.children && node.children.length) {
        newExpandedKeys[node.key] = true;

        for (const child of node.children) {
            expandNode(child, newExpandedKeys);
        }
    }
};

const expandPathsToFilterResults = (newFilterValue: string) => {
    // https://github.com/primefaces/primevue/issues/3996
    if (filterValue.value && !newFilterValue) {
        expandedKeys.value = { ...expandedKeysSnapshotBeforeSearch.value };
        expandedKeysSnapshotBeforeSearch.value = {};
        // Rerender to avoid error emitted in PrimeVue tree re: aria-selected.
        rerenderTree.value += 1;
    }
    // Expand all on the first interaction with the filter, or if the user
    // has collapsed a node and changes the filter.
    if (
        (!filterValue.value && newFilterValue) ||
        (nextFilterChangeNeedsExpandAll.value &&
            filterValue.value !== newFilterValue)
    ) {
        expandedKeysSnapshotBeforeSearch.value = { ...expandedKeys.value };
        expandAll();
    }
    nextFilterChangeNeedsExpandAll.value = false;
};

const getInputElement = () => {
    if (treeComponent.value !== null) {
        return treeComponent.value.$el.ownerDocument.querySelector(
            'input[data-pc-name="pcfilter"]',
        ) as HTMLInputElement;
    }
};

const restoreFocusToInput = () => {
    // The current implementation of collapsing all nodes when
    // backspacing out the search value relies on rerendering the
    // <Tree> component. Restore focus to the input element.
    if (rerenderTree.value > 0) {
        const inputEl = getInputElement();
        if (inputEl) {
            inputEl.focus();
        }
    }
};

const snoopOnFilterValue = () => {
    // If we wait to react to the emitted filter event, the templated rows
    // will have already rendered. (<TreeRow> bolds search terms.)
    const inputEl = getInputElement();
    if (inputEl) {
        expandPathsToFilterResults(inputEl.value);
        filterValue.value = inputEl.value;
    }
};

const filterCallbackWrapped = computed(() => {
    // Access some hidden functionality of the PrimeVue <Tree> to make
    // filter lookups lazy, that is, making use of the current state of the
    // label values and the selected language when doing the filtering.
    // "Hidden", because we need to violate the type of filter-by, which
    // should be a string. If we abuse it to be something that returns
    // a 1-element array containing a getter when split() is called on it,
    // that getter can return the best label to filter against.
    return {
        split: () => {
            return [
                (node: TreeNode) => {
                    if (nodeIsList(node)) {
                        return node.data.name;
                    }
                    return getItemLabel(
                        node.data,
                        selectedLanguage.value.code,
                        systemLanguage.code,
                    ).value;
                },
            ];
        },
    };
});

// Factored out because of vue-tsc problems inside the pt object
const ptNodeContent = ({ instance }: TreePassThroughMethodOptions) => {
    if (instance.$el && instance.node.key === movingItem.value?.key) {
        instance.$el.classList.add("is-adjusting-parent");
    }
    return { style: { height: "4rem" } };
};
</script>

<template>
    <ListTreeControls
        :key="refetcher"
        v-model:tree="tree"
        v-model:rerender-tree="rerenderTree"
        v-model:expanded-keys="expandedKeys"
        v-model:selected-keys="selectedKeys"
        v-model:moving-item="movingItem"
        v-model:is-multi-selecting="isMultiSelecting"
        v-model:next-new-list="nextNewList"
        v-model:new-list-form-value="newListFormValue"
    />
    <Tree
        v-if="tree"
        ref="treeComponent"
        :key="rerenderTree"
        v-model:selection-keys="selectedKeys"
        v-model:expanded-keys="expandedKeys"
        :value="tree"
        :filter="true"
        :filter-by="filterCallbackWrapped as unknown as string"
        filter-mode="lenient"
        :filter-placeholder="$gettext('Find')"
        :selection-mode="isMultiSelecting ? 'checkbox' : 'single'"
        :pt="{
            root: {
                style: {
                    flexGrow: 1,
                    overflowY: 'hidden',
                    paddingBottom: '5rem',
                },
            },
            pcFilter: {
                root: {
                    ariaLabel: $gettext('Find'),
                    style: { width: '100%', fontSize: 'small' },
                },
            },
            filterIcon: { style: { display: 'flex' } },
            wrapper: {
                style: {
                    overflowY: 'auto',
                    maxHeight: '100%',
                    paddingBottom: '1rem',
                },
            },
            container: { style: { fontSize: '1.4rem' } },
            nodeContent: ptNodeContent,
            nodeLabel: {
                style: {
                    textWrap: 'nowrap',
                    marginLeft: '0.5rem',
                    width: '100%',
                },
            },
            hooks: {
                onBeforeUpdate: snoopOnFilterValue,
                onMounted: restoreFocusToInput,
            },
        }"
        @node-collapse="nextFilterChangeNeedsExpandAll = true"
        @node-select="updateSelectedAndExpanded"
    >
        <template #nodeicon="slotProps">
            <LetterCircle :labelled="slotProps.node.data" />
        </template>
        <template #default="slotProps">
            <TreeRow
                v-model:tree="tree"
                v-model:expanded-keys="expandedKeys"
                v-model:selected-keys="selectedKeys"
                v-model:moving-item="movingItem"
                v-model:refetcher="refetcher"
                v-model:rerender-tree="rerenderTree"
                v-model:next-new-item="nextNewItem"
                v-model:new-label-form-value="newLabelFormValue"
                v-model:new-list-form-value="newListFormValue"
                v-model:filter-value="filterValue"
                :move-labels
                :node="slotProps.node"
                :is-multi-selecting="isMultiSelecting"
            />
        </template>
    </Tree>
</template>

<style scoped>
:deep(.is-adjusting-parent) {
    border: dashed;
}

:deep(.p-tree-filter-input) {
    height: 3.5rem;
    font-size: 1.4rem;
}
</style>
