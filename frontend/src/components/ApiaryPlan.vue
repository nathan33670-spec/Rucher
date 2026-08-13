<template>
  <div class="ap-plan">
    <div class="ap-toolbar">
      <v-btn icon size="x-small" variant="tonal" @click="zoomBy(1.25)" title="Zoomer"><v-icon>mdi-magnify-plus</v-icon></v-btn>
      <v-btn icon size="x-small" variant="tonal" @click="zoomBy(0.8)" title="Dézoomer"><v-icon>mdi-magnify-minus</v-icon></v-btn>
      <v-btn icon size="x-small" variant="tonal" @click="fit" title="Voir toute la photo"><v-icon>mdi-fit-to-screen</v-icon></v-btn>
      <span class="text-caption text-medium-emphasis ml-1">{{ Math.round(zoom * 100) }}%</span>
      <v-spacer />
      <span v-if="canEdit" class="text-caption text-medium-emphasis d-none d-sm-inline">Glissez une ruche pour la placer</span>
    </div>

    <div
      ref="vp"
      class="ap-viewport"
      :class="{ grabbing: panning }"
      @pointerdown="onDown"
      @pointermove="onMove"
      @pointerup="onUp"
      @pointercancel="onUp"
      @wheel.prevent="onWheel"
    >
      <div class="ap-stage" :style="stageStyle">
        <img v-if="photoUrl" :src="photoUrl" class="ap-photo" draggable="false" @load="onImgLoad" @dragstart.prevent />
        <div v-else class="ap-empty">
          <v-icon size="40" color="grey">mdi-image-off</v-icon>
          <div class="text-caption mt-1">Aucune photo aérienne</div>
        </div>

        <div
          v-for="(h, i) in hives"
          :key="h.id"
          class="ap-marker"
          :style="markerStyle(h, i)"
          @pointerdown="onMarkerDown($event, h)"
          @click.stop="$emit('select', h)"
        >
          <div class="ap-inner" :style="{ transform: `scale(${1 / zoom})` }">
            <div class="ap-diamond" :class="diamondClass(h)"><span>{{ shortLabel(h) }}</span></div>
            <div class="ap-name" :title="fullName(h)">{{ fullName(h) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'

const props = defineProps({
  photoUrl: { type: String, default: null },
  hives: { type: Array, default: () => [] },
  canEdit: { type: Boolean, default: false },
  selectedId: { type: [Number, null], default: null },
})
const emit = defineEmits(['select', 'move'])

const vp = ref(null)
const zoom = ref(1)
const pan = reactive({ x: 0, y: 0 })
const base = reactive({ w: 0, h: 0 })   // taille "fit" de la photo dans le viewport
const nat = reactive({ w: 0, h: 0 })    // taille naturelle de l'image

const stageStyle = computed(() => ({
  width: base.w + 'px',
  height: base.h + 'px',
  transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom.value})`,
}))

function vpSize() {
  const r = vp.value?.getBoundingClientRect()
  return { w: r?.width || 0, h: r?.height || 0 }
}

function computeFit() {
  const { w: vw, h: vh } = vpSize()
  if (!vw || !vh || !nat.w || !nat.h) return
  const s = Math.min(vw / nat.w, vh / nat.h)
  base.w = nat.w * s
  base.h = nat.h * s
  zoom.value = 1
  pan.x = (vw - base.w) / 2
  pan.y = (vh - base.h) / 2
}

function onImgLoad(e) {
  nat.w = e.target.naturalWidth
  nat.h = e.target.naturalHeight
  computeFit()
}
function fit() { computeFit() }

function zoomBy(f, cx, cy) {
  const { w: vw, h: vh } = vpSize()
  cx = cx ?? vw / 2; cy = cy ?? vh / 2
  const nz = Math.min(6, Math.max(0.5, zoom.value * f))
  // zoom centré sur (cx,cy)
  const sx = (cx - pan.x) / zoom.value
  const sy = (cy - pan.y) / zoom.value
  pan.x = cx - sx * nz
  pan.y = cy - sy * nz
  zoom.value = nz
}
function onWheel(e) {
  const r = vp.value.getBoundingClientRect()
  zoomBy(e.deltaY < 0 ? 1.12 : 0.89, e.clientX - r.left, e.clientY - r.top)
}

// ─── Interaction (pan / drag de marqueur) ─────────────────
const panning = ref(false)
let dragHive = null
let last = { x: 0, y: 0 }
let moved = false

function onDown(e) {
  if (dragHive) return
  panning.value = true; moved = false
  last = { x: e.clientX, y: e.clientY }
  vp.value.setPointerCapture?.(e.pointerId)
}
function onMove(e) {
  if (dragHive) {
    const p = toPercent(e.clientX, e.clientY)
    dragHive.position_x = p.x
    dragHive.position_y = p.y
    return
  }
  if (!panning.value) return
  const dx = e.clientX - last.x, dy = e.clientY - last.y
  if (Math.abs(dx) + Math.abs(dy) > 2) moved = true
  pan.x += dx; pan.y += dy
  last = { x: e.clientX, y: e.clientY }
}
function onUp(e) {
  if (dragHive) {
    const p = toPercent(e.clientX, e.clientY)
    emit('move', { id: dragHive.id, x: p.x, y: p.y })
    dragHive = null
  }
  panning.value = false
}

function toPercent(clientX, clientY) {
  const r = vp.value.getBoundingClientRect()
  const px = clientX - r.left, py = clientY - r.top
  const sx = (px - pan.x) / zoom.value
  const sy = (py - pan.y) / zoom.value
  return {
    x: Math.min(100, Math.max(0, (sx / base.w) * 100)),
    y: Math.min(100, Math.max(0, (sy / base.h) * 100)),
  }
}

function onMarkerDown(e, h) {
  if (!props.canEdit) return
  e.stopPropagation()
  dragHive = h
  vp.value.setPointerCapture?.(e.pointerId)
}

// ─── Position des marqueurs (en %) ────────────────────────
function pos(h, i) {
  // position enregistrée (0-100) ; sinon disposition en grille par défaut
  let x = h.position_x, y = h.position_y
  const legacy = (v) => v != null && v > 100   // anciennes valeurs en pixels
  if (x == null || y == null || legacy(x) || legacy(y)) {
    const col = i % 5, row = Math.floor(i / 5)
    x = 10 + col * 18
    y = 14 + row * 22
  }
  return { x, y }
}
function markerStyle(h, i) {
  const p = pos(h, i)
  return {
    left: p.x + '%',
    top: p.y + '%',
    zIndex: props.selectedId === h.id ? 5 : 2,
  }
}
function diamondClass(h) {
  return {
    'status-dead': h.status === 'dead',
    'status-active': h.status === 'active',
    'ownership-private': h.ownership === 'private',
    'ownership-associative': h.ownership !== 'private',
    selected: props.selectedId === h.id,
  }
}
function shortLabel(h) { return h.napi_number || ('#' + h.id) }
function fullName(h) { return h.name || h.napi_number || ('Ruche #' + h.id) }
</script>

<style scoped>
.ap-plan { width: 100%; }
.ap-toolbar { display: flex; align-items: center; gap: 4px; margin-bottom: 6px; }
.ap-viewport {
  position: relative;
  width: 100%;
  height: clamp(260px, 52vh, 520px);
  overflow: hidden;
  border-radius: 10px;
  border: 1px solid rgba(0,0,0,0.12);
  background: #eef1f3;
  touch-action: none;
  cursor: grab;
}
.ap-viewport.grabbing { cursor: grabbing; }
.ap-stage { position: absolute; top: 0; left: 0; transform-origin: 0 0; }
.ap-photo { display: block; width: 100%; height: 100%; -webkit-user-drag: none; user-select: none; }
.ap-empty {
  width: 320px; height: 200px; display: flex; flex-direction: column;
  align-items: center; justify-content: center; color: #9e9e9e;
  background: linear-gradient(135deg, #f5f0e1, #e8dcc8);
}

.ap-marker { position: absolute; transform: translate(-50%, -50%); cursor: v-bind("canEdit ? 'grab' : 'pointer'"); }
.ap-inner { transform-origin: center; text-align: center; }
.ap-diamond {
  width: 34px; height: 34px; transform: rotate(45deg);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 6px rgba(0,0,0,0.3); margin: 0 auto; border: 2px solid #fff;
}
.ap-diamond span { transform: rotate(-45deg); font-weight: 700; font-size: 0.72rem; color: #3e2723; }
.ap-diamond.status-active { background: #ffca28; }
.ap-diamond.status-dead { background: #bdbdbd; }
.ap-diamond.ownership-associative { background: linear-gradient(180deg, #81d4fa, #29b6f6); }
.ap-diamond.ownership-private { background: linear-gradient(180deg, #ffd54f, #ffb300); }
.ap-diamond.selected { box-shadow: 0 0 0 3px #1976d2, 0 2px 6px rgba(0,0,0,0.3); }
.ap-name {
  margin-top: 6px; background: rgba(255,255,255,0.95); padding: 1px 6px;
  border-radius: 6px; font-size: 0.72rem; max-width: 96px; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}
</style>
