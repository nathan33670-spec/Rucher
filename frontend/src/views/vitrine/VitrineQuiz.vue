<template>
  <div>
    <header class="quiz-hero">
      <div class="quiz-hero-inner">
        <v-icon size="46" class="mb-1">mdi-help-circle</v-icon>
        <div class="quiz-eyebrow">Testez vos connaissances</div>
        <h1 class="quiz-title">Le grand quiz de l'abeille</h1>
        <p class="quiz-lead">{{ questions.length }} questions pour vérifier ce que vous avez retenu du reportage.</p>
      </div>
    </header>

    <v-container class="py-8" style="max-width: 720px;">
      <!-- En cours -->
      <template v-if="!finished">
        <div class="d-flex align-center justify-space-between mb-2">
          <span class="text-caption text-medium-emphasis">Question {{ index + 1 }} / {{ questions.length }}</span>
          <span class="text-caption font-weight-bold" style="color:#c17d1a;">Score : {{ score }}</span>
        </div>
        <v-progress-linear :model-value="(index / questions.length) * 100" color="amber-darken-2" height="8" rounded class="mb-5" />

        <v-card class="pa-4 quiz-card" flat>
          <h2 class="quiz-q">{{ current.q }}</h2>
          <div class="mt-4 d-flex flex-column ga-2">
            <v-btn
              v-for="(opt, i) in current.options"
              :key="i"
              :color="optionColor(i)"
              :variant="optionVariant(i)"
              size="large"
              class="text-none justify-start quiz-opt"
              :disabled="answered && i !== selected && i !== current.answer"
              @click="choose(i)"
            >
              <v-icon start>{{ optionIcon(i) }}</v-icon>
              <span class="text-wrap text-left">{{ opt }}</span>
            </v-btn>
          </div>

          <v-expand-transition>
            <v-alert v-if="answered" :type="selected === current.answer ? 'success' : 'error'" variant="tonal" class="mt-4">
              <b>{{ selected === current.answer ? 'Bravo !' : 'Pas tout à fait…' }}</b> {{ current.explain }}
            </v-alert>
          </v-expand-transition>

          <div class="text-right mt-4">
            <v-btn v-if="answered" color="amber-darken-2" class="text-none" @click="nextQuestion">
              {{ index < questions.length - 1 ? 'Question suivante' : 'Voir mon résultat' }}
              <v-icon end>mdi-chevron-right</v-icon>
            </v-btn>
          </div>
        </v-card>
      </template>

      <!-- Résultat -->
      <template v-else>
        <v-card class="pa-6 text-center quiz-card" flat>
          <div class="quiz-score-ring" :style="ringStyle">
            <div>
              <div class="quiz-score-num">{{ score }}<span class="quiz-score-den">/{{ questions.length }}</span></div>
            </div>
          </div>
          <h2 class="text-h5 font-weight-bold mt-4">{{ verdict.title }}</h2>
          <p class="text-body-1 text-medium-emphasis mt-1 mb-4">{{ verdict.text }}</p>
          <div class="d-flex flex-wrap justify-center ga-2">
            <v-btn color="amber-darken-2" class="text-none" prepend-icon="mdi-restart" @click="restart">Recommencer</v-btn>
            <v-btn variant="tonal" class="text-none" :to="{ name: 'vitrine-home' }" prepend-icon="mdi-book-open-page-variant">Relire le reportage</v-btn>
          </div>
        </v-card>
      </template>
    </v-container>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { quizQuestions } from '../../data/quiz'

const questions = quizQuestions
const index = ref(0)
const score = ref(0)
const selected = ref(null)
const answered = ref(false)
const finished = ref(false)

const current = computed(() => questions[index.value])

function choose(i) {
  if (answered.value) return
  selected.value = i
  answered.value = true
  if (i === current.value.answer) score.value++
}

function nextQuestion() {
  if (index.value < questions.length - 1) {
    index.value++
    selected.value = null
    answered.value = false
  } else {
    finished.value = true
  }
}

function restart() {
  index.value = 0; score.value = 0; selected.value = null; answered.value = false; finished.value = false
}

function optionColor(i) {
  if (!answered.value) return 'grey-darken-3'
  if (i === current.value.answer) return 'success'
  if (i === selected.value) return 'error'
  return 'grey'
}
function optionVariant(i) {
  if (!answered.value) return 'tonal'
  if (i === current.value.answer || i === selected.value) return 'flat'
  return 'tonal'
}
function optionIcon(i) {
  if (!answered.value) return 'mdi-circle-outline'
  if (i === current.value.answer) return 'mdi-check-circle'
  if (i === selected.value) return 'mdi-close-circle'
  return 'mdi-circle-outline'
}

const verdict = computed(() => {
  const r = score.value / questions.length
  if (r === 1) return { title: 'Reine des abeilles ! 👑', text: "Un sans-faute : vous connaissez vos butineuses sur le bout des antennes." }
  if (r >= 0.75) return { title: 'Excellente ruche ! 🐝', text: 'Très belle performance — vous maîtrisez le sujet.' }
  if (r >= 0.5) return { title: 'Bonne butineuse', text: "Pas mal du tout ! Une relecture du reportage vous fera passer au niveau supérieur." }
  return { title: 'Jeune larve', text: "C'est un début ! Parcourez le reportage et retentez votre chance." }
})

const ringStyle = computed(() => {
  const deg = (score.value / questions.length) * 360
  return { background: `conic-gradient(#e0932f ${deg}deg, rgba(224,138,30,0.15) ${deg}deg)` }
})
</script>

<style scoped>
.quiz-hero {
  background: linear-gradient(135deg, #f2b134, #d9772b);
  color: #fff; text-align: center; padding: 48px 16px;
}
.quiz-eyebrow { text-transform: uppercase; letter-spacing: 2px; font-size: 0.8rem; font-weight: 700; opacity: 0.92; }
.quiz-title { font-size: clamp(1.8rem, 4.5vw, 2.7rem); font-weight: 800; margin: 6px 0 8px; }
.quiz-lead { opacity: 0.95; }

.quiz-card { border: 1px solid rgba(0,0,0,0.08); border-radius: 16px; }
.quiz-q { font-size: 1.25rem; font-weight: 700; line-height: 1.4; }
.quiz-opt { height: auto !important; min-height: 52px; white-space: normal; padding: 10px 16px; }

.quiz-score-ring {
  width: 150px; height: 150px; border-radius: 50%;
  margin: 0 auto; display: flex; align-items: center; justify-content: center;
}
.quiz-score-ring > div {
  width: 116px; height: 116px; border-radius: 50%;
  background: rgb(var(--v-theme-surface));
  display: flex; align-items: center; justify-content: center;
}
.quiz-score-num { font-size: 2.6rem; font-weight: 900; color: #c17d1a; line-height: 1; }
.quiz-score-den { font-size: 1.1rem; color: rgba(0,0,0,0.5); }

@media (prefers-color-scheme: dark) {
  .quiz-card { border-color: rgba(255,255,255,0.1); }
  .quiz-score-den { color: rgba(255,255,255,0.6); }
}
</style>
