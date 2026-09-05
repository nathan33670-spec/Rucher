<template>
  <v-card variant="outlined" class="mb-4 pa-3 filter-bar">
    <div class="d-flex align-center ga-2 mb-2">
      <v-icon size="16" color="secondary">mdi-filter-variant</v-icon>
      <span class="text-caption font-weight-medium">Filtres</span>
      <v-chip v-if="activeCount" size="x-small" color="primary" variant="tonal">
        {{ activeCount }} actif{{ activeCount > 1 ? 's' : '' }}
      </v-chip>
      <v-spacer />
      <span class="text-caption r-muted">{{ countLabel }}</span>
      <v-btn
        v-if="activeCount" size="x-small" variant="text" density="comfortable"
        prepend-icon="mdi-filter-remove-outline" @click="reset"
      >
        Réinitialiser
      </v-btn>
    </div>

    <v-row dense>
      <v-col v-for="f in fields" :key="f.key" cols="12" :sm="f.wide ? 12 : 6" :md="colWidth">
        <v-text-field
          v-if="f.type === 'search'"
          :model-value="modelValue[f.key]"
          :label="f.label"
          prepend-inner-icon="mdi-magnify"
          density="compact" hide-details clearable
          @update:model-value="(v) => set(f.key, v)"
        />
        <v-select
          v-else-if="f.type === 'select'"
          :model-value="modelValue[f.key]"
          :items="f.items"
          :label="f.label"
          :prepend-inner-icon="f.icon"
          item-title="title" item-value="value"
          density="compact" hide-details clearable
          @update:model-value="(v) => set(f.key, v)"
        />
        <v-text-field
          v-else-if="f.type === 'date'"
          :model-value="modelValue[f.key]"
          :label="f.label"
          type="date"
          density="compact" hide-details clearable
          @update:model-value="(v) => set(f.key, v)"
        />
      </v-col>
    </v-row>
  </v-card>
</template>

<script setup>
import { computed } from 'vue'

/**
 * Barre de filtres commune aux écrans de liste.
 *
 * Trier une colonne ne suffit pas : pour ne voir que l'historique d'une ruche,
 * il faut pouvoir restreindre la liste, pas seulement la réordonner. Le même
 * composant partout garde le geste identique d'un écran à l'autre.
 */
const props = defineProps({
  /** { key, label, type: 'search'|'select'|'date', items?, icon?, wide? } */
  fields: { type: Array, required: true },
  modelValue: { type: Object, required: true },
  total: { type: Number, default: 0 },
  shown: { type: Number, default: 0 },
  itemLabel: { type: String, default: 'élément' },
})
const emit = defineEmits(['update:modelValue'])

const colWidth = computed(() => {
  const n = props.fields.length
  if (n <= 2) return 6
  if (n === 3) return 4
  return 3
})

const activeCount = computed(
  () => Object.values(props.modelValue).filter((v) => v !== null && v !== '' && v !== undefined).length,
)

const countLabel = computed(() => {
  const plural = props.shown > 1 ? 's' : ''
  if (!activeCount.value) return `${props.total} ${props.itemLabel}${props.total > 1 ? 's' : ''}`
  return `${props.shown} ${props.itemLabel}${plural} sur ${props.total}`
})

function set(key, value) {
  emit('update:modelValue', { ...props.modelValue, [key]: value === '' ? null : value })
}

function reset() {
  const cleared = {}
  for (const k of Object.keys(props.modelValue)) cleared[k] = null
  emit('update:modelValue', cleared)
}
</script>

<style scoped>
.filter-bar {
  background: rgba(0, 0, 0, 0.015);
}
</style>
