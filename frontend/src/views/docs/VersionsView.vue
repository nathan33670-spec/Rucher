<template>
  <div class="versions-page">
    <v-btn variant="text" size="small" prepend-icon="mdi-arrow-left" :to="{ name: 'docs-home' }" class="mb-3">
      Documentation
    </v-btn>

    <div class="d-flex align-center flex-wrap ga-3 mb-2">
      <h2 class="mb-0">Versions de l'application</h2>
      <v-chip color="primary" variant="tonal" size="small">
        <v-icon start size="14">mdi-tag-outline</v-icon>
        Version installée : {{ current || '—' }}
      </v-chip>
    </div>
    <p class="text-body-2 r-muted mb-5">
      Ce qui change à chaque mise à jour. Une notification vous prévient dès
      qu'une nouvelle version est en service.
    </p>

    <v-alert v-if="error" type="error" density="compact" class="mb-4">{{ error }}</v-alert>
    <div v-if="loading" class="text-center py-8">
      <v-progress-circular indeterminate color="primary" />
    </div>

    <v-timeline v-else side="end" density="compact" truncate-line="both">
      <v-timeline-item
        v-for="(r, i) in releases" :key="r.version"
        :dot-color="i === 0 ? 'primary' : 'secondary'"
        :icon="i === 0 ? 'mdi-rocket-launch-outline' : 'mdi-tag-outline'"
        size="small"
      >
        <v-card variant="outlined" class="pa-3 mb-2">
          <div class="d-flex align-center flex-wrap ga-2 mb-1">
            <span class="text-subtitle-1 font-weight-bold">{{ r.version }}</span>
            <v-chip v-if="i === 0" size="x-small" color="primary" variant="flat">Actuelle</v-chip>
            <v-spacer />
            <span class="text-caption r-muted">{{ formatDate(r.date) }}</span>
          </div>
          <div class="text-body-2 font-weight-medium mb-2">{{ r.title }}</div>
          <ul class="release-notes">
            <li v-for="(h, k) in r.highlights" :key="k" class="text-body-2">{{ h }}</li>
          </ul>
        </v-card>
      </v-timeline-item>
    </v-timeline>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../services/api'
import { apiError } from '../../services/toast'

const releases = ref([])
const current = ref('')
const loading = ref(true)
const error = ref('')

function formatDate(d) {
  if (!d) return ''
  return new Date(d + 'T00:00:00').toLocaleDateString('fr-FR', {
    day: 'numeric', month: 'long', year: 'numeric',
  })
}

onMounted(async () => {
  try {
    const { data } = await api.get('/releases/')
    releases.value = data.releases || []
    current.value = data.current
  } catch (e) {
    error.value = apiError(e, "Impossible de charger le journal des versions")
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.versions-page {
  max-width: 760px;
  margin: 0 auto;
}

.release-notes {
  margin: 0;
  padding-left: 18px;
}

.release-notes li {
  margin-bottom: 4px;
}
</style>
