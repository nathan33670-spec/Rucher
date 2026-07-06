import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'
import { fr } from 'vuetify/locale'

// Les composants et directives sont auto-importés par vite-plugin-vuetify
// NE PAS les importer manuellement ici (cause des double-clics)

export default createVuetify({
  locale: {
    locale: 'fr',
    fallback: 'en',
    messages: { fr },
  },
  theme: {
    defaultTheme: 'honey',
    themes: {
      honey: {
        dark: false,
        colors: {
          primary: '#F9A825',
          secondary: '#795548',
          accent: '#FF6F00',
          success: '#4CAF50',
          warning: '#FF9800',
          error: '#F44336',
          info: '#2196F3',
          background: '#FFF8E1',
          surface: '#FFFFFF',
        },
      },
    },
  },
  defaults: {
    VBtn: { rounded: 'lg' },
    VCard: { rounded: 'lg', elevation: 2 },
    VTextField: { variant: 'outlined', density: 'comfortable' },
    VSelect: { variant: 'outlined', density: 'comfortable' },
    // Sous 960px (téléphones/tablettes portrait), les tableaux s'empilent
    // automatiquement en cartes lisibles au lieu de déborder horizontalement.
    VDataTable: { mobileBreakpoint: 'md', hover: true },
  },
})
