<template>
  <article v-if="chapter" class="reportage">
    <!-- En-tête de chapitre : photo + dégradé -->
    <header class="chap-hero">
      <img :src="'/vitrine/' + chapter.slug + '.jpg'" :alt="chapter.title" class="chap-hero-img" loading="eager" />
      <div class="chap-hero-veil" :style="heroVeil"></div>
      <div class="chap-hero-inner">
        <v-icon size="46" class="chap-hero-icon">{{ chapter.icon }}</v-icon>
        <div class="chap-eyebrow">{{ chapter.eyebrow }}</div>
        <h1 class="chap-title">{{ chapter.title }}</h1>
        <p class="chap-lead">{{ chapter.lead }}</p>
      </div>
      <div v-if="credit" class="chap-hero-credit">
        📷 {{ credit.creator }} · {{ credit.license }}
      </div>
    </header>

    <v-container class="py-8" style="max-width: 820px;">
      <section v-for="(s, i) in chapter.sections" :key="i" class="mb-8">
        <h2 v-if="s.h" class="chap-h2">{{ s.h }}</h2>

        <p v-for="(p, pi) in (s.p || [])" :key="'p' + pi" class="chap-p" v-html="p"></p>

        <ul v-if="s.li" class="chap-ul">
          <li v-for="(l, li) in s.li" :key="'l' + li" v-html="l"></li>
        </ul>

        <!-- Statistiques -->
        <div v-if="s.stats" class="chap-stats">
          <div v-for="(st, si) in s.stats" :key="'s' + si" class="chap-stat">
            <div class="chap-stat-v">{{ st.v }}</div>
            <div class="chap-stat-l">{{ st.l }}</div>
          </div>
        </div>

        <!-- Citation -->
        <blockquote v-if="s.quote" class="chap-quote">{{ s.quote }}</blockquote>

        <!-- Encadré « le saviez-vous » -->
        <aside v-if="s.note" class="chap-note">
          <div class="chap-note-title"><v-icon size="18" class="mr-1">mdi-lightbulb-on</v-icon>{{ s.note.title }}</div>
          <div v-html="s.note.text"></div>
        </aside>
      </section>

      <!-- Navigation entre chapitres -->
      <v-divider class="my-6" />
      <div class="chap-nav">
        <v-btn v-if="prev" variant="tonal" class="text-none chap-nav-btn" :to="{ name: 'vitrine-chapter', params: { slug: prev.slug } }">
          <v-icon start>mdi-chevron-left</v-icon>
          <span class="text-truncate">{{ prev.nav }}</span>
        </v-btn>
        <v-spacer />
        <v-btn v-if="next" color="amber-darken-2" variant="flat" class="text-none chap-nav-btn" :to="{ name: 'vitrine-chapter', params: { slug: next.slug } }">
          <span class="text-truncate">{{ next.nav }}</span>
          <v-icon end>mdi-chevron-right</v-icon>
        </v-btn>
      </div>

      <!-- Appel vers l'application -->
      <v-card class="mt-8 pa-4 text-center" variant="tonal" color="primary">
        <v-icon size="34" class="mb-1">mdi-bee</v-icon>
        <div class="text-subtitle-1 font-weight-bold mb-1">Notre association veille sur ses ruches</div>
        <p class="text-body-2 text-medium-emphasis mb-3">
          Membre de l'association ? Accédez à l'espace de gestion des ruchers.
        </p>
        <v-btn color="amber-darken-2" class="text-none" :to="{ name: 'login' }" prepend-icon="mdi-login">
          Accéder à l'application
        </v-btn>
      </v-card>
    </v-container>
  </article>

  <v-container v-else class="py-16 text-center">
    <v-icon size="56" color="grey">mdi-bee-flower</v-icon>
    <h2 class="text-h6 mt-3">Chapitre introuvable</h2>
    <v-btn class="mt-4 text-none" color="primary" :to="{ name: 'vitrine-home' }">Retour au sommaire</v-btn>
  </v-container>
</template>

<script setup>
import { computed } from 'vue'
import { chapters, chaptersBySlug } from '../data/reportage'
import { creditsByKey } from '../data/credits'

const props = defineProps({ slug: { type: String, required: true } })

const chapter = computed(() => chaptersBySlug[props.slug] || null)
const credit = computed(() => creditsByKey[props.slug] || null)
const index = computed(() => chapters.findIndex((c) => c.slug === props.slug))
const prev = computed(() => (index.value > 0 ? chapters[index.value - 1] : null))
const next = computed(() => (index.value >= 0 && index.value < chapters.length - 1 ? chapters[index.value + 1] : null))

const heroVeil = computed(() => {
  const [a, b] = chapter.value?.hero || ['#f6b73c', '#e08a1e']
  return { background: `linear-gradient(160deg, ${a}cc 0%, ${a}66 40%, rgba(0,0,0,0.72) 100%)` }
})
</script>

<style scoped>
.chap-hero {
  color: #fff;
  text-align: center;
  position: relative;
  overflow: hidden;
  min-height: clamp(320px, 46vh, 480px);
  display: flex;
  align-items: center;
  justify-content: center;
}
.chap-hero-img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.chap-hero-veil { position: absolute; inset: 0; }
.chap-hero-veil::after {
  content: '';
  position: absolute; inset: 0;
  background-image: radial-gradient(rgba(255,255,255,0.10) 2px, transparent 2px);
  background-size: 26px 26px;
  opacity: 0.5;
}
.chap-hero-inner { position: relative; max-width: 780px; margin: 0 auto; padding: 56px 18px; }
.chap-hero-icon { opacity: 0.95; margin-bottom: 8px; }
.chap-hero-credit {
  position: absolute; right: 8px; bottom: 6px;
  font-size: 0.68rem; color: rgba(255,255,255,0.75);
  background: rgba(0,0,0,0.28); padding: 2px 8px; border-radius: 8px;
}
.chap-eyebrow { text-transform: uppercase; letter-spacing: 2px; font-size: 0.8rem; font-weight: 700; opacity: 0.9; }
.chap-title { font-size: clamp(1.9rem, 4.5vw, 3rem); font-weight: 800; line-height: 1.1; margin: 6px 0 12px; text-shadow: 0 2px 12px rgba(0,0,0,0.18); }
.chap-lead { max-width: 640px; margin: 0 auto; font-size: clamp(1.02rem, 2vw, 1.2rem); line-height: 1.6; opacity: 0.97; }

.chap-h2 { font-size: 1.5rem; font-weight: 800; margin: 8px 0 12px; color: rgb(var(--v-theme-primary)); }
.chap-p { font-size: 1.05rem; line-height: 1.8; margin-bottom: 14px; }
.chap-ul { padding-left: 20px; margin-bottom: 14px; }
.chap-ul li { line-height: 1.75; margin-bottom: 8px; }

.chap-stats { display: flex; flex-wrap: wrap; gap: 12px; margin: 16px 0; }
.chap-stat { flex: 1 1 120px; text-align: center; padding: 16px 10px; border-radius: 14px; background: rgba(224, 138, 30, 0.10); }
.chap-stat-v { font-size: 1.7rem; font-weight: 800; color: rgb(var(--v-theme-primary)); line-height: 1.1; }
.chap-stat-l { font-size: 0.82rem; color: rgba(0,0,0,0.6); margin-top: 4px; }

.chap-quote {
  border-left: 4px solid #e0932f;
  padding: 6px 0 6px 16px;
  margin: 18px 0;
  font-size: 1.2rem;
  font-style: italic;
  color: rgba(0,0,0,0.72);
}

.chap-note {
  background: #fff7e6;
  border: 1px solid #f3d79b;
  border-radius: 14px;
  padding: 14px 16px;
  margin: 16px 0;
  line-height: 1.7;
}
.chap-note-title { font-weight: 800; color: #b5730a; display: flex; align-items: center; margin-bottom: 4px; }

.chap-nav { display: flex; align-items: center; gap: 10px; }
.chap-nav-btn { max-width: 46%; }

@media (prefers-color-scheme: dark) {
  .chap-stat { background: rgba(255, 193, 76, 0.12); }
  .chap-stat-l { color: rgba(255,255,255,0.7); }
  .chap-quote { color: rgba(255,255,255,0.82); }
  .chap-note { background: rgba(245, 190, 90, 0.08); border-color: rgba(245, 190, 90, 0.3); }
}
</style>
