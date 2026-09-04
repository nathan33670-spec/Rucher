<template>
  <div class="ap-plan">
    <div class="ap-toolbar">
      <!-- Le zoom reste accessible à tous, mais par action explicite : la
           molette est laissée à la page (voir onWheel). -->
      <v-btn icon size="x-small" variant="tonal" @click="zoomBy(1.3)" title="Zoomer" :disabled="!photoUrl">
        <v-icon>mdi-magnify-plus</v-icon>
      </v-btn>
      <v-btn icon size="x-small" variant="tonal" @click="zoomBy(0.77)" title="Dézoomer" :disabled="!photoUrl || zoom <= 1">
        <v-icon>mdi-magnify-minus</v-icon>
      </v-btn>
      <v-btn icon size="x-small" variant="tonal" @click="fit" title="Voir toute la photo" :disabled="!photoUrl || zoom === 1">
        <v-icon>mdi-fit-to-screen</v-icon>
      </v-btn>
      <span class="text-caption r-muted ml-1">{{ Math.round(zoom * 100) }}%</span>

      <v-spacer />

      <!-- Mode édition : hors de ce mode, ni la photo ni les ruches ne bougent. -->
      <v-btn
        v-if="canEdit"
        size="x-small"
        :variant="editing ? 'flat' : 'tonal'"
        :color="editing ? 'primary' : undefined"
        :prepend-icon="editing ? 'mdi-check' : 'mdi-cursor-move'"
        @click="editing = !editing"
      >
        {{ editing ? 'Terminer' : 'Déplacer les ruches' }}
      </v-btn>
    </div>

    <v-alert v-if="editing" type="info" variant="tonal" density="compact" class="mb-2">
      Mode édition : glissez une ruche pour la placer, ou faites glisser la photo
      pour la cadrer. Touchez « Terminer » pour verrouiller le plan.
    </v-alert>

    <div
      ref="vp"
      class="ap-viewport"
      :class="{ grabbing: panning, 'ap-viewport--locked': !interactive }"
      :style="viewportStyle"
      @pointerdown="onDown"
      @pointermove="onMove"
      @pointerup="onUp"
      @pointercancel="onUp"
      @wheel="onWheel"
    >
      <div class="ap-stage" :style="stageStyle">
        <img v-if="photoUrl" :src="photoUrl" class="ap-photo" draggable="false" @load="onImgLoad" @dragstart.prevent />
        <div v-else class="ap-empty">
          <v-icon size="40" color="grey-lighten-1">mdi-image-off</v-icon>
          <div class="text-caption mt-1">Aucune photo aérienne</div>
        </div>

        <div
          v-for="(h, i) in hives"
          :key="h.id"
          class="ap-marker"
          :class="{ 'ap-marker--draggable': editing }"
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
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'

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
const base = reactive({ w: 0, h: 0 })
const aspect = ref(3 / 2)

// Mode édition : seul état dans lequel la photo et les ruches peuvent bouger.
const editing = ref(false)

// Le plan ne capte le geste que s'il y a quelque chose à déplacer : en mode
// édition, ou lorsqu'on a volontairement zoomé (sinon le zoom serait inutile).
const interactive = computed(() => editing.value || zoom.value > 1)

const stageStyle = computed(() => ({
  width: base.w + 'px',
  height: base.h + 'px',
  transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom.value})`,
}))

// Hauteur bornée : sur grand écran, la photo occupait toute la page au
// détriment du reste. On borne la LARGEUR à partir de la hauteur maximale et
// du format de la photo : la zone reste proportionnée, sans rognage, et se
// centre quand elle est plus étroite que la carte.
const MAX_H = 440
const viewportStyle = computed(() => ({
  aspectRatio: String(aspect.value),
  maxWidth: Math.round(MAX_H * aspect.value) + 'px',
  margin: '0 auto',
}))

function measure() {
  const r = vp.value?.getBoundingClientRect()
  base.w = r?.width || 0
  base.h = r?.height || 0
  clampPan()
}

// L'image couvre toujours la zone : impossible de « sortir » de la photo.
function clampPan() {
  const iw = base.w * zoom.value, ih = base.h * zoom.value
  pan.x = Math.min(0, Math.max(base.w - iw, pan.x))
  pan.y = Math.min(0, Math.max(base.h - ih, pan.y))
}

function onImgLoad(e) {
  const nw = e.target.naturalWidth, nh = e.target.naturalHeight
  if (nw && nh) aspect.value = nw / nh
  zoom.value = 1; pan.x = 0; pan.y = 0
  nextTick(measure)
}
function fit() { zoom.value = 1; pan.x = 0; pan.y = 0; measure() }

function zoomBy(f, cx, cy) {
  cx = cx ?? base.w / 2; cy = cy ?? base.h / 2
  const nz = Math.min(6, Math.max(1, zoom.value * f))
  const sx = (cx - pan.x) / zoom.value
  const sy = (cy - pan.y) / zoom.value
  pan.x = cx - sx * nz
  pan.y = cy - sy * nz
  zoom.value = nz
  clampPan()
}

// La molette appartient à la page. Zoomer à la molette rendait le défilement
// impossible dès que le curseur passait sur le plan. Ctrl+molette reste
// disponible, c'est la convention des cartes.
function onWheel(e) {
  if (!e.ctrlKey) return
  e.preventDefault()
  const r = vp.value.getBoundingClientRect()
  zoomBy(e.deltaY < 0 ? 1.12 : 0.89, e.clientX - r.left, e.clientY - r.top)
}

// Quitter le mode édition remet le plan tel qu'il sera vu par les autres.
watch(editing, (on) => { if (!on) fit() })

// ─── Déplacement (pan) / glisser d'un marqueur ────────────
const panning = ref(false)
let dragHive = null
let last = { x: 0, y: 0 }

function onDown(e) {
  // Hors interaction, on laisse passer le geste : la page défile normalement.
  if (!interactive.value || dragHive) return
  panning.value = true
  last = { x: e.clientX, y: e.clientY }
  vp.value.setPointerCapture?.(e.pointerId)
}
function onMove(e) {
  if (dragHive) {
    const p = toPercent(e.clientX, e.clientY)
    dragHive.position_x = p.x; dragHive.position_y = p.y
    return
  }
  if (!panning.value) return
  pan.x += e.clientX - last.x
  pan.y += e.clientY - last.y
  last = { x: e.clientX, y: e.clientY }
  clampPan()
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
  const sx = (clientX - r.left - pan.x) / zoom.value
  const sy = (clientY - r.top - pan.y) / zoom.value
  return {
    x: Math.min(100, Math.max(0, (sx / base.w) * 100)),
    y: Math.min(100, Math.max(0, (sy / base.h) * 100)),
  }
}

function onMarkerDown(e, h) {
  // Une ruche ne se déplace qu'en mode édition : ailleurs, le geste doit
  // rester un simple appui qui sélectionne la ruche.
  if (!props.canEdit || !editing.value) return
  e.stopPropagation()
  dragHive = h
  vp.value.setPointerCapture?.(e.pointerId)
}

// ─── Marqueurs (positions en %) ───────────────────────────
function pos(h, i) {
  let x = h.position_x, y = h.position_y
  const legacy = (v) => v != null && v > 100
  if (x == null || y == null || legacy(x) || legacy(y)) {
    const col = i % 5, row = Math.floor(i / 5)
    x = 10 + col * 18; y = 14 + row * 22
  }
  return { x, y }
}
function markerStyle(h, i) {
  const p = pos(h, i)
  return { left: p.x + '%', top: p.y + '%', zIndex: props.selectedId === h.id ? 5 : 2 }
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

const onResize = () => measure()
onMounted(() => { measure(); window.addEventListener('resize', onResize) })
onUnmounted(() => window.removeEventListener('resize', onResize))
</script>

<style scoped>
.ap-plan { width: 100%; }
.ap-toolbar { display: flex; align-items: center; gap: 4px; margin-bottom: 6px; flex-wrap: wrap; }

.ap-viewport {
  position: relative;
  width: 100%;
  overflow: hidden;
  border-radius: 10px;
  border: 1px solid var(--r-hairline);
  background: #222;
  /* Le geste tactile revient à la page tant qu'il n'y a rien à déplacer :
     sinon le plan bloquait le défilement sur téléphone. */
  touch-action: auto;
  cursor: default;
  /* Un glisser sur le plan ne doit pas sélectionner les étiquettes. */
  user-select: none;
  -webkit-user-select: none;
}

/* Plan verrouillé : aucun curseur de déplacement, on ne promet rien. */
.ap-viewport--locked { cursor: default; }

.ap-viewport:not(.ap-viewport--locked) {
  touch-action: none;
  cursor: grab;
}
.ap-viewport.grabbing { cursor: grabbing; }

.ap-stage { position: absolute; top: 0; left: 0; transform-origin: 0 0; }
.ap-photo { display: block; width: 100%; height: 100%; object-fit: cover; -webkit-user-drag: none; user-select: none; }
.ap-empty {
  width: 100%; height: 100%; min-height: 220px; display: flex; flex-direction: column;
  align-items: center; justify-content: center; color: #9e9e9e;
  background: linear-gradient(135deg, #f5f0e1, #e8dcc8);
}

.ap-marker { position: absolute; transform: translate(-50%, -50%); cursor: pointer; }
.ap-marker--draggable { cursor: grab; }
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
.ap-diamond.selected { box-shadow: 0 0 0 3px #9A6B0F, 0 2px 6px rgba(0,0,0,0.3); }
.ap-name {
  margin-top: 6px; background: rgba(255,255,255,0.95); padding: 1px 6px;
  border-radius: 6px; font-size: 0.72rem; max-width: 96px; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}
</style>
