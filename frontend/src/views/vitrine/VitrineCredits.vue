<template>
  <div>
    <header class="cr-hero">
      <div>
        <div class="cr-eyebrow">Transparence</div>
        <h1 class="cr-title">Crédits &amp; sources</h1>
        <p class="cr-lead">Toutes les photos de ce reportage sont libres de droits (licences Creative Commons ou domaine public).</p>
      </div>
    </header>

    <v-container class="py-8" style="max-width: 900px;">
      <p class="text-body-2 text-medium-emphasis mb-6">
        Ce site de sensibilisation est proposé à titre pédagogique par notre association apicole.
        Les contenus s'appuient sur les connaissances communément admises en apidologie. Les images
        proviennent de la banque <b>Openverse</b> et sont créditées ci-dessous conformément à leurs licences.
      </p>

      <v-row>
        <v-col v-for="c in credits" :key="c.key" cols="12" sm="6" md="4">
          <v-card class="cr-card h-100" flat variant="outlined">
            <div class="d-flex">
              <img :src="thumb(c.key)" :alt="c.title" class="cr-thumb" loading="lazy" />
              <div class="pa-3">
                <div class="text-caption text-medium-emphasis">{{ chapterName(c.key) }}</div>
                <div class="text-body-2 font-weight-bold">{{ c.creator }}</div>
                <v-chip size="x-small" color="amber-darken-2" variant="tonal" class="mt-1">
                  {{ licenseLabel(c) }}
                </v-chip>
                <div v-if="c.source" class="mt-1">
                  <a :href="c.source" target="_blank" rel="noopener" class="cr-link text-caption">Voir la source ↗</a>
                </div>
              </div>
            </div>
          </v-card>
        </v-col>
      </v-row>

      <v-alert type="info" variant="tonal" class="mt-6" density="comfortable">
        Vous êtes l'auteur d'une image et souhaitez une correction de crédit ou un retrait ?
        Contactez l'association et nous procéderons immédiatement.
      </v-alert>
    </v-container>
  </div>
</template>

<script setup>
import { imageCredits } from '../../data/credits'
import { chaptersBySlug } from '../../data/reportage'

const credits = imageCredits
const SECTION_RE = /^(.*)-(\d+)$/

function isSection(key) { return SECTION_RE.test(key) }
function thumb(key) {
  return isSection(key) ? '/vitrine/sec/' + key + '.jpg' : '/vitrine/' + key + '.jpg'
}
function chapterName(key) {
  if (key === 'home') return 'Page d\'accueil'
  const m = key.match(SECTION_RE)
  if (m && chaptersBySlug[m[1]]) return chaptersBySlug[m[1]].nav + ' · illustration'
  return chaptersBySlug[key]?.nav || key
}
function licenseLabel(c) {
  const v = c.license_version ? ' ' + c.license_version : ''
  if (c.license === 'PDM' || c.license === 'CC0') return c.license
  return 'CC ' + c.license + v
}
</script>

<style scoped>
.cr-hero { background: linear-gradient(135deg, #6a994e, #3d6b3a); color: #fff; padding: 44px 18px; }
.cr-hero > div { max-width: 900px; margin: 0 auto; }
.cr-eyebrow { text-transform: uppercase; letter-spacing: 2px; font-size: 0.8rem; font-weight: 700; opacity: 0.9; }
.cr-title { font-size: clamp(1.8rem, 4vw, 2.6rem); font-weight: 800; margin: 6px 0 8px; }
.cr-lead { max-width: 620px; opacity: 0.95; }
.cr-card { border-radius: 14px; overflow: hidden; }
.cr-thumb { width: 96px; height: 96px; object-fit: cover; flex-shrink: 0; }
.cr-link { color: rgb(var(--v-theme-primary)); text-decoration: none; }
.cr-link:hover { text-decoration: underline; }
</style>
