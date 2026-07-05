<template>
  <div>
    <div class="text-overline text-primary">Documentation</div>
    <h1 class="text-h4 font-weight-bold mb-2">Centre d'aide &amp; de formation</h1>
    <p class="text-subtitle-1 text-medium-emphasis mb-6">
      Tout pour utiliser l'application et bien s'occuper des ruches — accessible
      à tous, même sans connexion.
    </p>

    <h2 class="text-h6 font-weight-bold mb-2">Prise en main</h2>
    <v-row class="mb-4">
      <v-col v-for="c in prise" :key="c.title" cols="12" sm="6">
        <v-card :to="c.to" class="h-100" variant="tonal" color="primary" hover>
          <v-card-item>
            <template v-slot:prepend><v-icon size="34">{{ c.icon }}</v-icon></template>
            <v-card-title class="text-subtitle-1 font-weight-bold">{{ c.title }}</v-card-title>
          </v-card-item>
          <v-card-text class="pt-0">{{ c.desc }}</v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <h2 class="text-h6 font-weight-bold mb-2">Formation apicole</h2>
    <v-row class="mb-4">
      <v-col v-for="c in formation" :key="c.title" cols="12" sm="6">
        <v-card :to="c.to" class="h-100" variant="tonal" color="amber-darken-2" hover>
          <v-card-item>
            <template v-slot:prepend><v-icon size="34">{{ c.icon }}</v-icon></template>
            <v-card-title class="text-subtitle-1 font-weight-bold">{{ c.title }}</v-card-title>
          </v-card-item>
          <v-card-text class="pt-0">{{ c.desc }}</v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <template v-if="dynamic.length">
      <h2 class="text-h6 font-weight-bold mb-2">Pages de l'association</h2>
      <v-list lines="one" density="comfortable" class="rounded border">
        <v-list-item
          v-for="p in dynamic" :key="p.slug"
          :to="{ name: 'docs-page', params: { slug: p.slug } }"
          :title="p.title" :subtitle="p.category"
          prepend-icon="mdi-file-document-outline"
        />
      </v-list>
    </template>

    <v-alert v-if="isAdmin" type="info" variant="tonal" class="mt-6" density="comfortable">
      <b>Admin :</b> vous pouvez créer vos propres pages de documentation via
      « Nouvelle page » dans le menu de gauche (rédaction en Markdown).
    </v-alert>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../services/api'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const isAdmin = computed(() => auth.isAdmin)
const dynamic = ref([])

const prise = [
  { title: 'Mémo rapide', desc: "L'essentiel en 1 page pour saisir et suivre vos ruches.", icon: 'mdi-lightning-bolt', to: { name: 'docs-memo' } },
  { title: "Guide complet", desc: 'Chaque écran de l\'application expliqué, captures à l\'appui.', icon: 'mdi-book-open-page-variant', to: { name: 'docs-guide' } },
]
const formation = [
  { title: "Cycle de vie de l'abeille", desc: "De l'œuf à la butineuse : castes, durées, rôles.", icon: 'mdi-bee', to: { name: 'docs-cycle' } },
  { title: 'Le varroa', desc: 'Reconnaître, compter et traiter le varroa.', icon: 'mdi-bug', to: { name: 'docs-varroa' } },
  { title: 'Réglementation & registres', desc: 'Déclaration de ruches, registre d\'élevage, obligations.', icon: 'mdi-gavel', to: { name: 'docs-reglementation' } },
]

onMounted(async () => {
  try { const { data } = await api.get('/docs/'); dynamic.value = data } catch { /* public */ }
})
</script>
