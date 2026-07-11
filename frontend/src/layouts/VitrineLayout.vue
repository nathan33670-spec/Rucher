<template>
  <div>
    <!-- Tiroir de navigation (sommaire du reportage) -->
    <v-navigation-drawer v-model="drawer" temporary>
      <v-list-item :to="{ name: 'vitrine-home' }" prepend-icon="mdi-bee" title="Le Peuple des abeilles" @click="drawer = false" />
      <v-divider />
      <v-list density="compact" nav>
        <v-list-subheader>Le reportage</v-list-subheader>
        <v-list-item
          v-for="c in chapters"
          :key="c.slug"
          :to="{ name: 'vitrine-chapter', params: { slug: c.slug } }"
          :prepend-icon="c.icon"
          :title="c.nav"
          @click="drawer = false"
        />
      </v-list>
      <template v-slot:append>
        <div class="pa-2">
          <v-btn block color="amber-darken-2" class="text-none" :to="{ name: 'login' }" prepend-icon="mdi-login">
            Accéder à l'application
          </v-btn>
        </div>
      </template>
    </v-navigation-drawer>

    <!-- Barre supérieure : marque à gauche, UN bouton vers l'app à droite -->
    <v-app-bar color="white" flat density="comfortable" class="vitrine-bar" scroll-behavior="elevate">
      <v-app-bar-nav-icon @click="drawer = !drawer" aria-label="Sommaire" />
      <v-app-bar-title class="font-weight-bold" style="cursor: pointer;" @click="$router.push({ name: 'vitrine-home' })">
        <v-icon color="amber-darken-3" class="mr-1">mdi-bee</v-icon>
        <span class="d-none d-sm-inline">Le Peuple des abeilles</span>
        <span class="d-sm-none">Les abeilles</span>
      </v-app-bar-title>
      <v-spacer />
      <v-btn variant="flat" color="amber-darken-3" class="text-none" :to="{ name: 'login' }" prepend-icon="mdi-login">
        <span class="d-none d-sm-inline">Accéder à l'application</span>
        <span class="d-sm-none">L'application</span>
      </v-btn>
    </v-app-bar>

    <v-main>
      <router-view />

      <v-footer class="vitrine-footer">
        <v-container style="max-width: 1000px;">
          <div class="d-flex flex-wrap ga-6 justify-space-between">
            <div style="max-width: 340px;">
              <div class="font-weight-bold mb-1"><v-icon size="18" class="mr-1">mdi-bee</v-icon> Le Peuple des abeilles</div>
              <p class="text-caption text-medium-emphasis mb-0">
                Un reportage de sensibilisation proposé par notre association apicole —
                rucher du canal de la Croix Bonnet, Bois-d'Arcy (78).
              </p>
            </div>
            <div>
              <div class="text-caption font-weight-bold mb-1">Le reportage</div>
              <router-link
                v-for="c in chapters.slice(0, 7)" :key="c.slug"
                class="vitrine-flink d-block"
                :to="{ name: 'vitrine-chapter', params: { slug: c.slug } }"
              >{{ c.nav }}</router-link>
            </div>
            <div>
              <div class="text-caption font-weight-bold mb-1">&nbsp;</div>
              <router-link
                v-for="c in chapters.slice(7)" :key="c.slug"
                class="vitrine-flink d-block"
                :to="{ name: 'vitrine-chapter', params: { slug: c.slug } }"
              >{{ c.nav }}</router-link>
            </div>
          </div>
          <v-divider class="my-3" />
          <div class="text-caption text-medium-emphasis text-center">
            🐝 Association apicole — Bois-d'Arcy · Protégeons les pollinisateurs
          </div>
        </v-container>
      </v-footer>
    </v-main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { chapters } from '../data/reportage'

const drawer = ref(false)
</script>

<style scoped>
.vitrine-bar { border-bottom: 1px solid rgba(0,0,0,0.08); }
.vitrine-footer { background: #1b1a17; color: #f4ead6; padding: 32px 8px 16px; }
.vitrine-flink { color: #f0c987; text-decoration: none; font-size: 0.86rem; line-height: 1.9; }
.vitrine-flink:hover { text-decoration: underline; }
</style>
