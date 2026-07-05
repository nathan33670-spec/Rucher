<template>
  <div>
    <div v-if="loading" class="text-center pa-8"><v-progress-circular indeterminate color="primary" /></div>

    <div v-else-if="page">
      <div class="d-flex align-center mb-2">
        <div>
          <div class="text-overline text-primary">{{ page.category }}</div>
          <h1 class="text-h4 font-weight-bold">{{ page.title }}</h1>
        </div>
        <v-spacer />
        <template v-if="isAdmin">
          <v-btn icon size="small" variant="text" :to="{ name: 'docs-edit', params: { slug: page.slug } }"><v-icon>mdi-pencil</v-icon></v-btn>
          <v-btn icon size="small" variant="text" color="error" @click="remove"><v-icon>mdi-delete</v-icon></v-btn>
        </template>
      </div>
      <v-divider class="mb-4" />
      <article class="doc-article" v-html="html"></article>
    </div>

    <v-alert v-else type="error" variant="tonal">Page introuvable.</v-alert>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import api from '../../services/api'
import { useAuthStore } from '../../stores/auth'

const props = defineProps({ slug: String })
const emit = defineEmits(['docs-changed'])
const auth = useAuthStore()
const router = useRouter()
const isAdmin = computed(() => auth.isAdmin)

const loading = ref(true)
const page = ref(null)
const html = computed(() => (page.value ? marked.parse(page.value.content || '') : ''))

async function load() {
  loading.value = true
  page.value = null
  try {
    const { data } = await api.get('/docs/' + props.slug)
    page.value = data
  } catch { page.value = null }
  finally { loading.value = false }
}

async function remove() {
  if (!confirm('Supprimer cette page ?')) return
  await api.delete('/docs/' + page.value.id)
  emit('docs-changed')
  router.push({ name: 'docs-home' })
}

watch(() => props.slug, load)
onMounted(load)
</script>

<style scoped>
.doc-article :deep(h1) { font-size: 1.6rem; font-weight: 700; margin: 20px 0 10px; }
.doc-article :deep(h2) { font-size: 1.35rem; font-weight: 700; margin: 26px 0 10px; }
.doc-article :deep(h3) { font-size: 1.1rem; font-weight: 700; margin: 20px 0 8px; }
.doc-article :deep(p) { line-height: 1.7; margin-bottom: 12px; }
.doc-article :deep(ul), .doc-article :deep(ol) { padding-left: 22px; margin-bottom: 14px; line-height: 1.75; }
.doc-article :deep(img) { max-width: 100%; border-radius: 12px; margin: 10px 0; }
.doc-article :deep(code) { background: rgba(0,0,0,.06); padding: 2px 6px; border-radius: 6px; }
.doc-article :deep(pre) { background: rgba(0,0,0,.06); padding: 12px; border-radius: 10px; overflow-x: auto; }
.doc-article :deep(blockquote) { border-left: 4px solid rgba(0,0,0,.15); padding-left: 12px; color: rgba(0,0,0,.6); }
.doc-article :deep(table) { border-collapse: collapse; width: 100%; }
.doc-article :deep(th), .doc-article :deep(td) { border: 1px solid rgba(0,0,0,.15); padding: 6px 10px; text-align: left; }
.doc-article :deep(a) { color: rgb(var(--v-theme-primary)); }
</style>
