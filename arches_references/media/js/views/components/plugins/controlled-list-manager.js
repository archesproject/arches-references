import ko from 'knockout';
import ControlledListsMain from '@/arches-references/components/ControlledListsMain.vue';
import { definePreset } from '@primevue/themes';
import Aura from '@primevue/themes/aura';

import ControlledListManager from '@/arches-references/plugins/ControlledListManager.vue';
import createVueApplication from 'utils/create-vue-application';
import ControlledListManagerTemplate from 'templates/views/components/plugins/controlled-list-manager.htm';

import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  { path: '/plugins/controlled-list-manager', name: 'splash', component: ControlledListsMain },
  { path: '/plugins/controlled-list-manager/list/:id', name: 'list', component: ControlledListsMain },
  { path: '/plugins/controlled-list-manager/item/:id', name: 'item', component: ControlledListsMain },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Much of this might get merged upstream to core arches in 8.0?
const ControlledListsPreset = definePreset(Aura, {
    primitive: {
        sky: {
            950: '#2d3c4b',  // matches arches sidebar
        },
    },
    semantic: {
        primary: {
            50: '{sky.50}',
            100: '{sky.100}',
            200: '{sky.200}',
            300: '{sky.300}',
            400: '{sky.400}',
            500: '{sky.500}',
            600: '{sky.600}',
            700: '{sky.700}',
            800: '{sky.800}',
            900: '{sky.900}',
            950: '{sky.950}',
        },
    },
    components: {
        button: {
            root: {
                label: {
                    fontWeight: 600,
                },
            },
        },
        datatable: {
            column: {
                title: {
                    fontWeight: 600,
                },
            },
        },
        splitter: {
            handle: {
                background: '{surface.500}',
            },
        },
    },
});

const controlledListsTheme = {
    theme: {
        preset: ControlledListsPreset,
        options: {
            prefix: 'p',
            darkModeSelector: 'system',
            cssLayer: false
        },
    },
};

ko.components.register('controlled-list-manager', {
    viewModel: function() {
        createVueApplication(ControlledListManager, controlledListsTheme).then((vueApp) => {
            vueApp.use(router);
            vueApp.mount('#controlled-list-manager-mounting-point');
        });
    },
    template: ControlledListManagerTemplate,
});
