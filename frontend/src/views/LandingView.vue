<template>
  <div>
    <!-- Barre publique -->
    <v-app-bar color="primary" flat density="comfortable">
      <v-app-bar-title class="font-weight-bold">
        <v-icon start>mdi-bee</v-icon> Rucher — Association apicole
      </v-app-bar-title>
      <v-spacer />
      <v-btn variant="text" class="text-none d-none d-sm-flex" :to="{ name: 'docs-home' }" prepend-icon="mdi-book-open-variant">
        Documentation
      </v-btn>
      <v-btn variant="flat" color="amber-darken-3" class="text-none" :to="{ name: 'login' }" prepend-icon="mdi-login">
        Accéder à l'application
      </v-btn>
    </v-app-bar>

    <v-main>
      <!-- Hero -->
      <section class="hero">
        <img src="/accueil-canal.jpg" alt="Le canal de la Croix Bonnet à Bois-d'Arcy" class="hero-img" />
        <div class="hero-overlay">
          <h1 class="hero-title">Protégeons les abeilles</h1>
          <p class="hero-sub">
            Chaque colonie compte. Notre association veille sur ses ruches
            au bord du canal de la Croix Bonnet, à Bois-d'Arcy.
          </p>
          <v-btn size="large" color="amber-darken-2" class="text-none mt-2" :to="{ name: 'login' }" prepend-icon="mdi-login">
            Accéder à l'application
          </v-btn>
        </div>
      </section>

      <!-- Contenu générique -->
      <v-container class="py-10" style="max-width: 960px;">
        <v-row>
          <v-col cols="12" class="text-center mb-4">
            <h2 class="text-h5 font-weight-bold">Pourquoi protéger les abeilles ?</h2>
            <p class="text-body-1 text-medium-emphasis mt-2">
              Les abeilles pollinisent une grande partie de ce que nous mangeons.
              Préserver leurs colonies, c'est protéger la biodiversité et nos paysages.
            </p>
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="12" sm="4" v-for="c in cards" :key="c.title">
            <v-card variant="tonal" color="amber-darken-2" class="h-100 pa-2" flat>
              <v-card-item>
                <v-icon size="40" color="amber-darken-3">{{ c.icon }}</v-icon>
                <v-card-title class="text-subtitle-1 font-weight-bold mt-2">{{ c.title }}</v-card-title>
                <v-card-text class="px-0 text-body-2">{{ c.text }}</v-card-text>
              </v-card-item>
            </v-card>
          </v-col>
        </v-row>

        <v-row class="mt-6">
          <v-col cols="12" class="text-center">
            <v-icon color="teal" class="mb-2">mdi-map-marker</v-icon>
            <h3 class="text-h6 font-weight-bold">Notre rucher</h3>
            <p class="text-body-1 text-medium-emphasis">
              Notre association a installé son rucher le long du
              <b>canal de la Croix Bonnet</b>, à Bois-d'Arcy (78) — un site calme et fleuri,
              idéal pour la santé de nos colonies.
            </p>
            <v-btn variant="text" color="primary" class="text-none mt-2" :to="{ name: 'login' }">
              Membre de l'association ? Connectez-vous →
            </v-btn>
          </v-col>
        </v-row>
      </v-container>

      <v-footer color="grey-lighten-4" class="justify-center text-caption text-medium-emphasis py-4">
        🐝 Association apicole — Bois-d'Arcy · Rucher du canal de la Croix Bonnet
      </v-footer>
    </v-main>
  </div>
</template>

<script setup>
const cards = [
  { icon: 'mdi-flower', title: 'Pollinisation', text: "Près d'une culture sur trois dépend des pollinisateurs." },
  { icon: 'mdi-sprout', title: 'Biodiversité', text: 'Les abeilles maintiennent l\'équilibre de nombreux écosystèmes.' },
  { icon: 'mdi-hand-heart', title: 'Engagement', text: 'Nous suivons, soignons et protégeons nos colonies toute l\'année.' },
]
</script>

<style scoped>
.hero { position: relative; }
.hero-img { width: 100%; height: clamp(260px, 42vh, 460px); object-fit: cover; display: block; }
.hero-overlay {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; padding: 16px;
  background: linear-gradient(180deg, rgba(0,0,0,0.15), rgba(0,0,0,0.35));
  color: #fff;
}
.hero-title { font-size: clamp(2rem, 5vw, 3.2rem); font-weight: 800; text-shadow: 0 2px 12px rgba(0,0,0,0.4); }
.hero-sub { max-width: 620px; margin-top: 12px; font-size: clamp(1rem, 2vw, 1.2rem); text-shadow: 0 1px 8px rgba(0,0,0,0.5); }
</style>
