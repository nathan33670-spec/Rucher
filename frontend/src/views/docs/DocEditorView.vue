<template>
  <div>
    <div class="d-flex align-center mb-4">
      <h1 class="text-h5 font-weight-bold">{{ editing ? 'Modifier la page' : 'Nouvelle page' }}</h1>
      <v-spacer />
      <v-btn variant="text" class="text-none" :to="{ name: 'docs-home' }">Annuler</v-btn>
    </div>

    <v-alert v-if="!isAdmin" type="error" variant="tonal">Réservé aux administrateurs.</v-alert>

    <template v-else>
      <v-row>
        <v-col cols="12" sm="8"><v-text-field v-model="form.title" label="Titre" variant="outlined" density="comfortable" /></v-col>
        <v-col cols="12" sm="4"><v-text-field v-model="form.category" label="Catégorie" variant="outlined" density="comfortable" hint="Regroupe les pages dans le menu" /></v-col>
      </v-row>
      <v-row>
        <v-col cols="6" sm="3"><v-text-field v-model.number="form.sort_order" type="number" label="Ordre" variant="outlined" density="comfortable" /></v-col>
        <v-col cols="6" sm="4" class="d-flex align-center"><v-switch v-model="form.is_published" label="Publiée" color="success" hide-details /></v-col>
      </v-row>

      <v-textarea
        v-model="form.content"
        label="Contenu (Markdown)"
        variant="outlined"
        rows="16"
        auto-grow
        hint="Titres avec #, listes avec -, gras avec **texte**, liens [texte](url), images ![alt](url)"
        persistent-hint
      />

      <div class="mt-2 mb-4">
        <div class="text-caption text-medium-emphasis mb-1">Aperçu :</div>
        <v-card variant="outlined" class="pa-4"><article class="doc-preview" v-html="preview"></article></v-card>
      </div>

      <v-alert v-if="error" type="error" density="compact" class="mb-3">{{ error }}</v-alert>
      <v-btn color="primary" :loading="saving" @click="save" prepend-icon="mdi-content-save">Enregistrer</v-btn>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import api from '../../services/api'
import { useAuthStore } from '../../stores/auth'

const props = defineProps({ slug: String })
const emit = defineEmits(['docs-changed'])
const auth = useAuthStore()
const router = useRouter()
const isAdmin = computed(() => auth.isAdmin)

const editing = ref(false)
const pageId = ref(null)
const saving = ref(false)
const error = ref('')
const form = ref({ title: '', category: 'Pages de l\'association', content: '# Titre\n\nÉcrivez ici…', is_published: true, sort_order: 100 })
const preview = computed(() => marked.parse(form.value.content || ''))

async function save() {
  error.value = ''
  if (!form.value.title.trim()) { error.value = 'Le titre est obligatoire.'; return }
  saving.value = true
  try {
    let slug
    if (editing.value) {
      const { data } = await api.put('/docs/' + pageId.value, form.value)
      slug = data.slug
    } else {
      const { data } = await api.post('/docs/', form.value)
      slug = data.slug
    }
    emit('docs-changed')
    router.push({ name: 'docs-page', params: { slug } })
  } catch (e) {
    error.value = e.response?.data?.detail || 'Erreur lors de l\'enregistrement.'
  } finally { saving.value = false }
}

onMounted(async () => {
  if (props.slug) {
    try {
      const { data } = await api.get('/docs/' + props.slug)
      editing.value = true
      pageId.value = data.id
      form.value = { title: data.title, category: data.category, content: data.content, is_published: data.is_published, sort_order: data.sort_order }
    } catch { /* nouvelle page */ }
  }
})
</script>

<style scoped>
.doc-preview :deep(h1) { font-size: 1.4rem; font-weight: 700; }
.doc-preview :deep(h2) { font-size: 1.2rem; font-weight: 700; margin-top: 16px; }
.doc-preview :deep(ul), .doc-preview :deep(ol) { padding-left: 20px; }
.doc-preview :deep(img) { max-width: 100%; }
</style>
