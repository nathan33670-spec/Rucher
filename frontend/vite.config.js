import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'

export default defineConfig({
  plugins: [vue(), vuetify({ autoImport: true })],
  appType: 'spa',
  optimizeDeps: {
    // Pré-bundler TOUS les composants Vuetify utilisés dans l'app dès le démarrage.
    // Les vues étant chargées en lazy (() => import(...)), sans cette liste Vite
    // découvre les composants « à la demande » au premier accès à chaque page,
    // ce qui déclenche une re-optimisation + un rechargement complet de la page
    // (symptôme « premier clic = refresh, second clic = la page s'affiche »).
    include: [
      'vue', 'vue-router', 'pinia', 'axios',
      'vuetify',
      'chart.js', 'vue-chartjs', 'idb',
      // Composants Vuetify (auto-importés via vite-plugin-vuetify)
      'vuetify/components/VAlert',
      'vuetify/components/VApp',
      'vuetify/components/VAppBar',
      'vuetify/components/VBadge',
      'vuetify/components/VBottomNavigation',
      'vuetify/components/VBtn',
      'vuetify/components/VBtnToggle',
      'vuetify/components/VCard',
      'vuetify/components/VCheckbox',
      'vuetify/components/VChip',
      'vuetify/components/VCombobox',
      'vuetify/components/VDataTable',
      'vuetify/components/VDialog',
      'vuetify/components/VDivider',
      'vuetify/components/VFileInput',
      'vuetify/components/VForm',
      'vuetify/components/VGrid',
      'vuetify/components/VIcon',
      'vuetify/components/VLayout',
      'vuetify/components/VList',
      'vuetify/components/VMain',
      'vuetify/components/VNavigationDrawer',
      'vuetify/components/VProgressCircular',
      'vuetify/components/VProgressLinear',
      'vuetify/components/VSelect',
      'vuetify/components/VSlider',
      'vuetify/components/VSnackbar',
      'vuetify/components/VSwitch',
      'vuetify/components/VTabs',
      'vuetify/components/VTextField',
      'vuetify/components/VTextarea',
      'vuetify/components/VTimeline',
      'vuetify/components/VToolbar',
    ],
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: ['ruches.corsicajack.fr'],
    proxy: {
      '^/api/': 'http://backend:8000',
      '/ws': { target: 'http://backend:8000', ws: true },
    },
  },
})
