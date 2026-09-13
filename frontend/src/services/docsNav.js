// Sections de documentation intégrées (statiques, riches, avec captures).
export const builtinSections = [
  {
    section: 'Prise en main',
    items: [
      { to: { name: 'docs-home' }, title: 'Accueil documentation', icon: 'mdi-book-open-variant' },
      { to: { name: 'docs-memo' }, title: 'Mémo rapide (utilisateur)', icon: 'mdi-lightning-bolt' },
      { to: { name: 'docs-versions' }, title: 'Versions et nouveautés', icon: 'mdi-rocket-launch-outline' },
    ],
  },
  {
    // Le guide est découpé en chapitres : une page par grand domaine se lit
    // et se retrouve bien mieux qu'un seul document de plusieurs écrans.
    section: "Guide de l'application",
    items: [
      { to: { name: 'docs-guide' }, title: 'Sommaire du guide', icon: 'mdi-book-open-page-variant' },
      { to: { name: 'docs-guide-premiers-pas' }, title: '1. Premiers pas', icon: 'mdi-login-variant' },
      { to: { name: 'docs-guide-ruchers' }, title: '2. Ruchers et ruches', icon: 'mdi-hexagon-multiple' },
      { to: { name: 'docs-guide-visites' }, title: '3. Visiter ses ruches', icon: 'mdi-clipboard-text-outline' },
      { to: { name: 'docs-guide-gestion' }, title: '4. Miellée, sanitaire, stocks', icon: 'mdi-bee-flower' },
      { to: { name: 'docs-guide-suivi' }, title: '5. Notifications, météo, événements', icon: 'mdi-bell-outline' },
      { to: { name: 'docs-guide-admin' }, title: '6. Administration', icon: 'mdi-account-cog' },
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
