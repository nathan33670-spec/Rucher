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
      // Palette « miel » : chaude mais sobre. Le primaire est assez foncé
      // pour porter du texte blanc lisible (contraste AA), l'accent reste
      // l'ambre lumineux qui signe l'identité de l'application.
      honey: {
        dark: false,
        colors: {
          primary: '#9A6B0F',       // miel foncé — texte blanc lisible
          secondary: '#5D4037',     // brun ruche
          accent: '#C68A12',        // ambre lumineux (accents, focus)
          success: '#2E7D5B',       // vert profond, moins criard
          warning: '#B26A00',       // ambre soutenu
          error: '#B3261E',         // rouge sourd
          info: '#33618F',          // bleu ardoise
          background: '#FBF7F0',    // blanc chaud très subtil
          surface: '#FFFFFF',
          'surface-variant': '#EFE7DA',
          'on-surface-variant': '#4E443A',
        },
        variables: {
          'border-color': '#5D4037',
          'border-opacity': 0.13,
          'high-emphasis-opacity': 0.92,
          'medium-emphasis-opacity': 0.66,
          'hover-opacity': 0.05,
          'activated-opacity': 0.1,
        },
      },
    },
  },
  defaults: {
    // Cartes au filet fin plutôt qu'à l'ombre marquée : la hiérarchie
    // naît du trait et de l'espacement, ce qui allège l'ensemble.
    VCard: { rounded: 'lg', elevation: 0, border: true },
    VBtn: { rounded: 'lg' },
    VChip: { rounded: 'lg' },
    VDialog: { scrollable: true },
    VTextField: { variant: 'outlined', density: 'comfortable', color: 'primary' },
    VSelect: { variant: 'outlined', density: 'comfortable', color: 'primary' },
    VAutocomplete: { variant: 'outlined', density: 'comfortable', color: 'primary' },
    VCombobox: { variant: 'outlined', density: 'comfortable', color: 'primary' },
    VTextarea: { variant: 'outlined', density: 'comfortable', color: 'primary' },
    VFileInput: { variant: 'outlined', density: 'comfortable', color: 'primary' },
    VCheckbox: { color: 'primary', density: 'comfortable' },
    VSwitch: { color: 'primary', density: 'comfortable', inset: true },
    VRadioGroup: { color: 'primary' },
    VSlider: { color: 'primary' },
    VAlert: { variant: 'tonal', rounded: 'lg', border: 'start' },
    VTabs: { color: 'primary' },
    VSnackbar: { rounded: 'lg', location: 'top' },
    VProgressLinear: { color: 'primary', rounded: true },
    VTooltip: { location: 'top' },
    // Sous 960px (téléphones/tablettes portrait), les tableaux s'empilent
    // automatiquement en cartes lisibles au lieu de déborder horizontalement.
    VDataTable: { mobileBreakpoint: 'md', hover: true },
  },
})
