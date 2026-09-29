<template>
  <v-banner
    v-if="visible"
    class="r-demo-banner"
    density="compact"
    icon="mdi-flask-outline"
    color="warning"
    lines="two"
  >
    <v-banner-text class="text-caption">
      <b>Démonstration</b> — données inventées, aucun serveur derrière.
      Vous pouvez tout essayer : ce que vous modifiez reste dans votre
      navigateur et disparaît au rechargement.
    </v-banner-text>
    <template v-slot:actions>
      <v-btn size="small" variant="text" @click="recharger">Repartir à zéro</v-btn>
      <v-btn size="small" variant="text" icon="mdi-close" @click="visible = false" />
    </template>
  </v-banner>
</template>

<script setup>
/**
 * Bandeau de la démonstration publique.
 *
 * Il dit trois choses qu'il serait malhonnête de taire : les données sont
 * inventées, il n'y a pas de serveur, et rien de ce qu'on saisit n'est
 * conservé. Sans lui, un visiteur pourrait croire avoir perdu son travail.
 */
import { ref } from 'vue'

const visible = ref(true)

function recharger() {
  // Le jeu de données vit en mémoire : un simple rechargement le rétablit.
  window.location.reload()
}
</script>

<style scoped>
.r-demo-banner {
  position: sticky;
  top: 0;
  z-index: 1100;
}
</style>
