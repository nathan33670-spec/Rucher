<template>
  <v-layout>
    <v-app-bar color="primary" density="comfortable" flat>
      <v-app-bar-nav-icon class="d-md-none" @click="drawer = !drawer" />
      <v-app-bar-title class="font-weight-bold">
        <v-icon start>mdi-book-open-variant</v-icon> Documentation — Rucher
      </v-app-bar-title>
      <v-spacer />
      <v-btn variant="text" class="text-none d-none d-sm-flex" :to="{ name: 'vitrine-home' }" prepend-icon="mdi-home">Accueil</v-btn>
      <v-btn variant="flat" color="amber-darken-3" class="text-none" :to="appTarget" prepend-icon="mdi-login">
        {{ isAuth ? "Ouvrir l'app" : 'Se connecter' }}
      </v-btn>
    </v-app-bar>

    <v-navigation-drawer v-model="drawer" :permanent="$vuetify.display.mdAndUp" width="300">
      <v-list density="compact" nav>
        <template v-for="sec in sections" :key="sec.section">
          <v-list-subheader class="font-weight-bold">{{ sec.section }}</v-list-subheader>
          <v-list-item
            v-for="item in sec.items"
            :key="item.title + (item.to.params?.slug || '')"
            :to="item.to"
            :prepend-icon="item.icon"
            :title="item.title"
          >
            <template v-if="isAdmin && item.pageId" v-slot:append>
              <v-icon size="16" class="mr-1" @click.prevent.stop="editPage(item)">mdi-pencil</v-icon>
              <v-icon size="16" color="error" @click.prevent.stop="askDelete(item)">mdi-delete</v-icon>
            </template>
          </v-list-item>
        </template>

        <v-divider class="my-2" />
        <v-list-item
          v-if="isAdmin"
          :to="{ name: 'docs-new' }"
          prepend-icon="mdi-plus-box"
          title="Nouvelle page"
          base-color="primary"
        />
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <v-container class="py-6 px-4" style="max-width: 900px;">
        <router-view @docs-changed="loadDynamic" />
      </v-container>
    </v-main>

    <!-- Confirmation suppression -->
    <v-dialog v-model="showDelete" max-width="420">
      <v-card>
        <v-card-title>Supprimer la page</v-card-title>
        <v-card-text>Supprimer définitivement « {{ delItem?.title }} » ?</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showDelete = false">Annuler</v-btn>
          <v-btn color="error" :loading="deleting" @click="confirmDelete">Supprimer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'
import { builtinSections } from '../services/docsNav'

const auth = useAuthStore()
const router = useRouter()
const drawer = ref(true)
const dynamic = ref([])

const isAuth = computed(() => auth.isAuthenticated)
const isAdmin = computed(() => auth.isAdmin)
const appTarget = computed(() => (auth.isAuthenticated ? { name: 'dashboard' } : { name: 'login' }))

// Regroupe les pages dynamiques par catégorie
const sections = computed(() => {
  const secs = [...builtinSections]
  const byCat = {}
  for (const p of dynamic.value) {
    ;(byCat[p.category] ||= []).push({
      to: { name: 'docs-page', params: { slug: p.slug } },
      title: p.title, icon: 'mdi-file-document-outline', pageId: p.id ?? p.slug, slug: p.slug,
    })
  }
  for (const [cat, items] of Object.entries(byCat)) {
    secs.push({ section: cat, items })
  }
  return secs
})

async function loadDynamic() {
  try {
    const { data } = await api.get('/docs/')
    dynamic.value = data
  } catch { dynamic.value = [] }
}

function editPage(item) { router.push({ name: 'docs-edit', params: { slug: item.slug } }) }

const showDelete = ref(false)
const delItem = ref(null)
const deleting = ref(false)
function askDelete(item) { delItem.value = item; showDelete.value = true }
async function confirmDelete() {
  deleting.value = true
  try {
    // la liste publique ne renvoie pas d'id : on retrouve la page par slug
    const { data } = await api.get('/docs/' + delItem.value.slug)
    await api.delete('/docs/' + data.id)
    showDelete.value = false
    await loadDynamic()
    router.push({ name: 'docs-home' })
  } finally { deleting.value = false }
}

onMounted(loadDynamic)
</script>
