import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'

// Les composants et directives sont auto-importés par vite-plugin-vuetify
// NE PAS les importer manuellement ici (cause des double-clics)

export default createVuetify({
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
  },
})
