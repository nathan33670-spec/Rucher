<template>
  <div>
    <!-- Hero -->
    <section class="v-hero">
      <img src="/vitrine/home.jpg" alt="Abeille butinant une fleur" class="v-hero-img" />
      <div class="v-hero-overlay">
        <div class="v-hero-eyebrow">Un reportage sur les abeilles</div>
        <h1 class="v-hero-title">Le Peuple des abeilles</h1>
        <p class="v-hero-sub">
          De l'œuf à la butineuse, de la fleur au pot de miel : plongée au cœur d'une
          société vieille de millions d'années, et de son rôle irremplaçable pour la nature.
        </p>
        <v-btn size="large" color="amber-darken-2" class="text-none mt-3" @click="goFirst" prepend-icon="mdi-book-open-page-variant">
          Commencer le reportage
        </v-btn>
      </div>
    </section>

    <!-- Intro -->
    <v-container class="py-10" style="max-width: 820px;">
      <div class="text-center">
        <div class="v-eyebrow">Pourquoi les abeilles comptent</div>
        <h2 class="v-h2">Une petite ouvrière, un immense service</h2>
        <p class="v-intro">
          En pollinisant fleurs et cultures, les abeilles soutiennent une grande partie de
          notre alimentation et l'équilibre de la nature. Ce reportage raconte leur vie, leur
          ruche, la chimie de leur miel — et ce que nous pouvons faire pour les protéger.
        </p>
      </div>

      <div class="v-quick">
        <div v-for="s in highlights" :key="s.l" class="v-quick-item">
          <div class="v-quick-v">{{ s.v }}</div>
          <div class="v-quick-l">{{ s.l }}</div>
        </div>
      </div>
    </v-container>

    <!-- Sommaire : toutes les pages du reportage -->
    <v-container class="pb-12" style="max-width: 1040px;">
      <div class="text-center mb-6">
        <div class="v-eyebrow">Le sommaire</div>
        <h2 class="v-h2">{{ chapters.length }} chapitres à explorer</h2>
      </div>
      <v-row>
        <v-col v-for="(c, i) in chapters" :key="c.slug" cols="12" sm="6" md="4">
          <v-card class="v-chapcard h-100" :to="{ name: 'vitrine-chapter', params: { slug: c.slug } }" flat hover>
            <div class="v-chapcard-top">
              <img :src="'/vitrine/' + c.slug + '.jpg'" :alt="c.title" class="v-chapcard-img" loading="lazy" />
              <div class="v-chapcard-veil" :style="cardStyle(c)"></div>
              <span class="v-chapnum">{{ (i + 1).toString().padStart(2, '0') }}</span>
              <v-icon size="34">{{ c.icon }}</v-icon>
            </div>
            <v-card-item>
              <div class="text-overline text-medium-emphasis">{{ c.eyebrow }}</div>
              <v-card-title class="text-subtitle-1 font-weight-bold text-wrap">{{ c.title }}</v-card-title>
              <v-card-text class="px-0 text-body-2 text-medium-emphasis">{{ c.lead }}</v-card-text>
            </v-card-item>
          </v-card>
        </v-col>
      </v-row>
    </v-container>

    <!-- Teaser Quiz -->
    <section class="v-quiz">
      <v-container style="max-width: 900px;">
        <div class="v-quiz-card">
          <div class="v-quiz-icon"><v-icon size="46">mdi-help-circle</v-icon></div>
          <div class="flex-grow-1">
            <div class="v-eyebrow" style="color:#ffe4a0;">Interactif</div>
            <h2 class="text-h5 font-weight-bold mb-1" style="color:#fff;">Connaissez-vous vraiment les abeilles ?</h2>
            <p class="mb-0" style="color:#f4ead6;">12 questions pour tester vos connaissances après la lecture.</p>
          </div>
          <v-btn size="large" color="amber-darken-2" class="text-none" :to="{ name: 'vitrine-quiz' }" prepend-icon="mdi-play">
            Lancer le quiz
          </v-btn>
        </div>
      </v-container>
    </section>

    <!-- Notre rucher (photo réelle du site) -->
    <section class="v-rucher">
      <img src="/accueil-canal.jpg" alt="Le canal de la Croix Bonnet à Bois-d'Arcy" class="v-rucher-img" />
      <div class="v-rucher-text">
        <div class="v-eyebrow">Sur le terrain</div>
        <h2 class="v-h2" style="color:#fff;">Notre rucher, au bord du canal</h2>
        <p style="color:#f0e8d8; line-height:1.7;">
          L'association veille sur ses colonies le long du canal de la Croix Bonnet,
          à Bois-d'Arcy (78) — un site calme et fleuri, idéal pour la santé des abeilles.
        </p>
      </div>
    </section>

    <!-- Bandeau final vers l'app -->
    <section class="v-cta">
      <v-container style="max-width: 780px;" class="text-center">
        <v-icon size="40" color="amber-lighten-2" class="mb-2">mdi-bee</v-icon>
        <h2 class="v-cta-title">Notre association veille sur ses ruches</h2>
        <p class="v-cta-sub">
          Au bord du canal de la Croix Bonnet, à Bois-d'Arcy, nous suivons et protégeons nos
          colonies toute l'année.
        </p>
        <v-btn size="large" color="amber-darken-2" class="text-none" :to="{ name: 'login' }" prepend-icon="mdi-login">
          Accéder à l'application
        </v-btn>
      </v-container>
    </section>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { chapters } from '../../data/reportage'

const router = useRouter()

const highlights = [
  { v: '1/3', l: 'de notre alimentation dépend des pollinisateurs' },
  { v: '60 000', l: "abeilles dans une ruche en été" },
  { v: '4 M', l: 'de fleurs visitées pour 1 kg de miel' },
]

function goFirst() {
  router.push({ name: 'vitrine-chapter', params: { slug: chapters[0].slug } })
}

function cardStyle(c) {
  const [a, b] = c.hero || ['#f6b73c', '#e08a1e']
  return { background: `linear-gradient(150deg, ${a}b3, ${b}66 55%, rgba(0,0,0,0.35))` }
}
</script>

<style scoped>
.v-hero { position: relative; }
.v-hero-img { width: 100%; height: clamp(320px, 56vh, 560px); object-fit: cover; display: block; }
.v-hero-overlay {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; padding: 20px;
  background: linear-gradient(180deg, rgba(0,0,0,0.28), rgba(0,0,0,0.5));
  color: #fff;
}
.v-hero-eyebrow { text-transform: uppercase; letter-spacing: 3px; font-size: 0.85rem; font-weight: 700; color: #ffd98a; }
.v-hero-title { font-size: clamp(2.4rem, 6vw, 4rem); font-weight: 900; line-height: 1.05; margin: 8px 0 12px; text-shadow: 0 3px 18px rgba(0,0,0,0.45); }
.v-hero-sub { max-width: 640px; font-size: clamp(1.05rem, 2.2vw, 1.28rem); line-height: 1.6; text-shadow: 0 1px 10px rgba(0,0,0,0.5); }

.v-eyebrow { text-transform: uppercase; letter-spacing: 2px; font-size: 0.8rem; font-weight: 700; color: #c17d1a; }
.v-h2 { font-size: clamp(1.5rem, 3.5vw, 2.1rem); font-weight: 800; margin: 6px 0 12px; }
.v-intro { font-size: 1.1rem; line-height: 1.8; color: rgba(0,0,0,0.68); }

.v-quick { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 26px; }
.v-quick-item { flex: 1 1 160px; text-align: center; padding: 18px 12px; border-radius: 16px; background: rgba(224,138,30,0.10); }
.v-quick-v { font-size: 2rem; font-weight: 900; color: #c17d1a; }
.v-quick-l { font-size: 0.86rem; color: rgba(0,0,0,0.6); margin-top: 4px; }

.v-chapcard { border: 1px solid rgba(0,0,0,0.07); border-radius: 16px; overflow: hidden; transition: transform .15s ease; }
.v-chapcard:hover { transform: translateY(-3px); }
.v-chapcard-top {
  height: 132px; color: #fff;
  display: flex; align-items: center; justify-content: center; gap: 12px;
  position: relative; overflow: hidden;
}
.v-chapcard-img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.v-chapcard-veil { position: absolute; inset: 0; }
.v-chapnum { position: absolute; left: 14px; top: 6px; font-size: 1.7rem; font-weight: 900; opacity: 0.85; text-shadow: 0 2px 8px rgba(0,0,0,0.4); z-index: 1; }
.v-chapcard-top .v-icon { position: relative; z-index: 1; filter: drop-shadow(0 2px 6px rgba(0,0,0,0.4)); }

.v-quiz { padding: 8px 12px 40px; }
.v-quiz-card {
  display: flex; flex-wrap: wrap; align-items: center; gap: 18px;
  background: linear-gradient(135deg, #3a2f14, #7a5a1e);
  border-radius: 20px; padding: 24px 26px;
}
.v-quiz-icon { color: #ffd98a; }

.v-rucher { position: relative; min-height: 360px; display: flex; align-items: center; }
.v-rucher-img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.v-rucher-text {
  position: relative; max-width: 560px; margin-left: clamp(16px, 8vw, 120px);
  padding: 28px; border-radius: 18px;
  background: rgba(20,18,14,0.62); backdrop-filter: blur(2px);
}

.v-cta { background: #1b1a17; color: #f4ead6; padding: 56px 12px; }
.v-cta-title { font-size: clamp(1.5rem, 3.5vw, 2.1rem); font-weight: 800; margin-bottom: 8px; }
.v-cta-sub { max-width: 560px; margin: 0 auto 18px; color: #d9cbb3; line-height: 1.6; }

@media (prefers-color-scheme: dark) {
  .v-intro { color: rgba(255,255,255,0.75); }
  .v-quick-item { background: rgba(255,193,76,0.12); }
  .v-quick-l { color: rgba(255,255,255,0.7); }
  .v-chapcard { border-color: rgba(255,255,255,0.1); }
}
</style>
