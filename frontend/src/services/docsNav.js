// Sections de documentation intégrées (statiques, riches, avec captures).
export const builtinSections = [
  {
    section: 'Prise en main',
    items: [
      { to: { name: 'docs-home' }, title: 'Accueil documentation', icon: 'mdi-book-open-variant' },
      { to: { name: 'docs-memo' }, title: 'Mémo rapide (utilisateur)', icon: 'mdi-lightning-bolt' },
      { to: { name: 'docs-guide' }, title: "Guide complet de l'application", icon: 'mdi-book-open-page-variant' },
    ],
  },
  {
    section: 'Formation apicole',
    items: [
      { to: { name: 'docs-cycle' }, title: "Cycle de vie de l'abeille", icon: 'mdi-bee' },
      { to: { name: 'docs-varroa' }, title: 'Le varroa', icon: 'mdi-bug' },
      { to: { name: 'docs-reglementation' }, title: 'Réglementation & registres', icon: 'mdi-gavel' },
    ],
  },
]
