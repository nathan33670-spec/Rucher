<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="640" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-crop</v-icon> Recadrer la photo
        <v-spacer />
        <v-btn icon size="small" variant="text" @click="close"><v-icon>mdi-close</v-icon></v-btn>
      </v-card-title>
      <v-card-text>
        <p class="text-body-2 text-medium-emphasis mb-2">
          Déplacez et zoomez la photo pour choisir le cadrage. La zone visible sera enregistrée.
        </p>
        <div
          ref="frame"
          class="pf-frame"
          @pointerdown="onDown" @pointermove="onMove" @pointerup="onUp" @pointercancel="onUp"
          @wheel.prevent="onWheel"
        >
          <img v-if="src" :src="src" class="pf-img" :style="imgStyle" draggable="false" @load="onLoad" @dragstart.prevent />
          <div class="pf-grid"></div>
        </div>
        <div class="d-flex align-center ga-2 mt-3">
          <v-btn icon size="small" variant="tonal" @click="zoomBy(0.83)"><v-icon>mdi-magnify-minus</v-icon></v-btn>
          <v-slider v-model="zoom" :min="1" :max="4" step="0.01" hide-details density="compact" @update:model-value="clampPan" />
          <v-btn icon size="small" variant="tonal" @click="zoomBy(1.2)"><v-icon>mdi-magnify-plus</v-icon></v-btn>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-btn variant="text" @click="close">Annuler</v-btn>
        <v-spacer />
        <v-btn color="primary" variant="flat" :loading="working" @click="apply">Appliquer le recadrage</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  src: { type: String, default: null },
  aspect: { type: Number, default: 3 / 2 },
  outWidth: { type: Number, default: 1400 },
})
const emit = defineEmits(['update:modelValue', 'cropped'])

const frame = ref(null)
const zoom = ref(1)
const pan = reactive({ x: 0, y: 0 })
const nat = reactive({ w: 0, h: 0 })
const fw = ref(0), fh = ref(0)
const working = ref(false)

const baseScale = computed(() => (nat.w && nat.h ? Math.max(fw.value / nat.w, fh.value / nat.h) : 1))
const scale = computed(() => baseScale.value * zoom.value)
const imgStyle = computed(() => ({
  width: nat.w * scale.value + 'px',
  height: nat.h * scale.value + 'px',
  transform: `translate(${pan.x}px, ${pan.y}px)`,
}))

watch(() => props.modelValue, (v) => { if (v) nextTick(measure) })

function measure() {
  const r = frame.value?.getBoundingClientRect()
  fw.value = r?.width || 0
  fh.value = fw.value / props.aspect
  reset()
}
function onLoad(e) { nat.w = e.target.naturalWidth; nat.h = e.target.naturalHeight; reset() }
function reset() {
  zoom.value = 1
  pan.x = (fw.value - nat.w * scale.value) / 2
  pan.y = (fh.value - nat.h * scale.value) / 2
  clampPan()
}
function clampPan() {
  const iw = nat.w * scale.value, ih = nat.h * scale.value
  pan.x = Math.min(0, Math.max(fw.value - iw, pan.x))
  pan.y = Math.min(0, Math.max(fh.value - ih, pan.y))
}
function zoomBy(f) { zoom.value = Math.min(4, Math.max(1, zoom.value * f)); clampPan() }
function onWheel(e) { zoomBy(e.deltaY < 0 ? 1.1 : 0.9) }

let dragging = false, last = { x: 0, y: 0 }
function onDown(e) { dragging = true; last = { x: e.clientX, y: e.clientY }; frame.value.setPointerCapture?.(e.pointerId) }
function onMove(e) {
  if (!dragging) return
  pan.x += e.clientX - last.x; pan.y += e.clientY - last.y
  last = { x: e.clientX, y: e.clientY }; clampPan()
}
function onUp() { dragging = false }

async function apply() {
  working.value = true
  try {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    await new Promise((res, rej) => { img.onload = res; img.onerror = rej; img.src = props.src })
    const s = scale.value
    const srcX = -pan.x / s, srcY = -pan.y / s
    const srcW = fw.value / s, srcH = fh.value / s
    const outW = props.outWidth, outH = Math.round(outW / props.aspect)
    const canvas = document.createElement('canvas')
    canvas.width = outW; canvas.height = outH
    canvas.getContext('2d').drawImage(img, srcX, srcY, srcW, srcH, 0, 0, outW, outH)
    canvas.toBlob((blob) => { emit('cropped', blob); working.value = false; close() }, 'image/jpeg', 0.85)
  } catch (e) {
    working.value = false
    close()
  }
}
function close() { emit('update:modelValue', false) }
</script>

<style scoped>
.pf-frame {
  position: relative; width: 100%; aspect-ratio: 3 / 2;
  overflow: hidden; border-radius: 10px; background: #222;
  touch-action: none; cursor: grab; user-select: none;
}
.pf-img { position: absolute; top: 0; left: 0; -webkit-user-drag: none; }
.pf-grid {
  position: absolute; inset: 0; pointer-events: none;
  background-image:
    linear-gradient(rgba(255,255,255,0.25) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.25) 1px, transparent 1px);
  background-size: 33.33% 33.33%;
}
</style>
