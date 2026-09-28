<template>
  <div class="r-editor" :class="{ 'r-editor--error': !!error }">
    <div class="r-editor__barre">
      <v-btn
        v-for="b in boutons" :key="b.cmd + (b.arg || '')"
        :icon="b.icon" size="x-small" variant="text" density="comfortable"
        :title="b.titre" @mousedown.prevent @click="commande(b)"
      />
      <v-divider vertical class="mx-1" />
      <v-btn icon="mdi-link-variant" size="x-small" variant="text"
             density="comfortable" title="Insérer un lien"
             @mousedown.prevent @click="poserLien" />
      <v-btn icon="mdi-format-clear" size="x-small" variant="text"
             density="comfortable" title="Effacer la mise en forme"
             @mousedown.prevent @click="commande({ cmd: 'removeFormat' })" />
    </div>

    <div
      ref="zone"
      class="r-editor__zone"
      contenteditable="true"
      role="textbox"
      aria-multiline="true"
      :aria-label="label"
      @input="remonter"
      @blur="remonter"
      @paste="collerEnTexte"
    />

    <div class="r-editor__pied">
      <span v-if="error" class="r-editor__erreur">{{ error }}</span>
      <span v-else>{{ hint }}</span>
    </div>
  </div>
</template>

<script setup>
/**
 * Éditeur de texte enrichi, sans dépendance.
 *
 * S'appuie sur « contenteditable » et document.execCommand. Cette API est
 * officiellement dépréciée mais reste la seule à fonctionner partout sans
 * embarquer une bibliothèque entière ; ce qu'elle produit est de toute façon
 * redésinfecté côté serveur avant tout envoi, donc sa réputation de produire
 * du HTML approximatif est ici sans conséquence.
 */
import { ref, onMounted, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: 'Message' },
  hint: { type: String, default: '' },
  error: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const zone = ref(null)

const boutons = [
  { cmd: 'bold', icon: 'mdi-format-bold', titre: 'Gras' },
  { cmd: 'italic', icon: 'mdi-format-italic', titre: 'Italique' },
  { cmd: 'underline', icon: 'mdi-format-underline', titre: 'Souligné' },
  { cmd: 'formatBlock', arg: 'h3', icon: 'mdi-format-header-3', titre: 'Titre' },
  { cmd: 'insertUnorderedList', icon: 'mdi-format-list-bulleted', titre: 'Liste à puces' },
  { cmd: 'insertOrderedList', icon: 'mdi-format-list-numbered', titre: 'Liste numérotée' },
  { cmd: 'formatBlock', arg: 'blockquote', icon: 'mdi-format-quote-close', titre: 'Citation' },
]

function commande(b) {
  zone.value?.focus()
  document.execCommand(b.cmd, false, b.arg || null)
  remonter()
}

function poserLien() {
  zone.value?.focus()
  const url = window.prompt("Adresse du lien (https://…)")
  if (!url) return
  // Un lien « javascript: » serait retiré par le serveur, mais autant ne pas
  // le laisser s'installer dans l'éditeur non plus.
  if (!/^(https?:|mailto:|tel:)/i.test(url)) {
    window.alert("Seules les adresses http, https, mailto et tel sont acceptées.")
    return
  }
  document.execCommand('createLink', false, url)
  remonter()
}

/** Le collage garde le texte, pas la mise en forme du document d'origine. */
function collerEnTexte(e) {
  e.preventDefault()
  const texte = (e.clipboardData || window.clipboardData).getData('text/plain')
  document.execCommand('insertText', false, texte)
}

function remonter() {
  emit('update:modelValue', zone.value?.innerHTML || '')
}

onMounted(() => { if (zone.value) zone.value.innerHTML = props.modelValue || '' })

// Réinitialisation depuis le parent (après envoi) : on ne réécrit pas la zone
// pendant la frappe, sinon le curseur sauterait à chaque caractère.
watch(() => props.modelValue, (v) => {
  if (zone.value && !v && zone.value.innerHTML) zone.value.innerHTML = ''
})

defineExpose({ vider: () => { if (zone.value) zone.value.innerHTML = '' } })
</script>

<style scoped>
.r-editor {
  border: 1px solid rgba(var(--v-border-color), 0.38);
  border-radius: 4px;
}
.r-editor--error { border-color: rgb(var(--v-theme-error)); }
.r-editor__barre {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2px;
  padding: 4px 6px;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.24);
}
.r-editor__zone {
  min-height: 220px;
  padding: 12px 14px;
  outline: none;
  line-height: 1.6;
  overflow-wrap: anywhere;
}
.r-editor__zone:focus { box-shadow: inset 0 0 0 1px rgb(var(--v-theme-primary)); }
.r-editor__zone :deep(ul),
.r-editor__zone :deep(ol) { padding-left: 22px; }
.r-editor__zone :deep(blockquote) {
  margin: 8px 0;
  padding-left: 12px;
  border-left: 3px solid rgba(var(--v-border-color), 0.4);
}
.r-editor__pied {
  padding: 2px 14px 6px;
  font-size: 0.75rem;
  opacity: 0.8;
}
.r-editor__erreur { color: rgb(var(--v-theme-error)); }
</style>
