<template>
  <article class="doc-article">
    <div v-if="eyebrow" class="text-overline text-primary">{{ eyebrow }}</div>
    <h1 class="text-h4 font-weight-bold mb-2">{{ title }}</h1>
    <p v-if="lead" class="text-subtitle-1 text-medium-emphasis mb-4">{{ lead }}</p>
    <v-divider class="mb-6" />
    <slot />
    <v-divider class="mt-8 mb-3" />
    <p class="text-caption text-medium-emphasis">
      Rucher Manager — Documentation. Contenu d'information ; en cas de doute
      réglementaire ou sanitaire, référez-vous aux sources officielles.
    </p>
  </article>
</template>

<script setup>
defineProps({ title: String, lead: String, eyebrow: String })
</script>

<style scoped>
.doc-article :deep(h2) { font-size: 1.4rem; font-weight: 700; margin: 30px 0 10px; }
.doc-article :deep(h3) { font-size: 1.12rem; font-weight: 700; margin: 22px 0 8px; }
.doc-article :deep(p) { line-height: 1.7; margin-bottom: 12px; }
.doc-article :deep(ul), .doc-article :deep(ol) { padding-left: 22px; margin-bottom: 14px; line-height: 1.75; }
.doc-article :deep(li) { margin-bottom: 4px; }
.doc-article :deep(img) {
  max-width: 100%; border-radius: 12px; border: 1px solid rgba(0,0,0,.12);
  margin: 12px 0; box-shadow: 0 2px 14px rgba(0,0,0,.08);
}
.doc-article :deep(figure) { margin: 16px 0; }
.doc-article :deep(figcaption) { font-size: .85rem; color: rgba(0,0,0,.6); text-align: center; margin-top: 4px; }
.doc-article :deep(code) { background: rgba(0,0,0,.06); padding: 2px 6px; border-radius: 6px; font-size: .9em; }
.doc-article :deep(a) { color: rgb(var(--v-theme-primary)); }
</style>
