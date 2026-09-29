<template>
  <!--
    Bandeau en **flux normal**, ni fixe ni « sticky ».

    MainLayout ouvre son propre « v-layout » : une barre système posée dans la
    mise en page extérieure ne décalait pas celle de l'intérieur, et le
    bandeau passait par-dessus la barre du haut de l'application, qui s'en
    trouvait coupée. En restant dans le flux, il pousse simplement tout ce qui
    suit vers le bas.
  -->
  <div v-if="visible" ref="element" class="r-demo-banner">
    <v-icon size="16" class="r-demo-banner__icone">mdi-flask-outline</v-icon>
    <p class="r-demo-banner__texte">
      <b>Démonstration</b> — données inventées, aucun serveur.
      <span class="r-demo-banner__suite">
        Ce que vous modifiez reste dans votre navigateur et disparaît au
        rechargement.
      </span>
    </p>
    <button type="button" class="r-demo-banner__action" @click="recharger">
      Repartir à zéro
    </button>
    <button
      type="button" class="r-demo-banner__fermer"
      aria-label="Masquer le bandeau" @click="visible = false"
    >
      <v-icon size="16">mdi-close</v-icon>
    </button>
  </div>
</template>

<script setup>
/**
 * Bandeau de la démonstration publique.
 *
 * Il dit trois choses qu'il serait malhonnête de taire : les données sont
 * inventées, il n'y a pas de serveur, et rien de ce qu'on saisit n'est
 * conservé. Sans lui, un visiteur pourrait croire avoir perdu son travail.
 */
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const visible = ref(true)
const element = ref(null)

/**
 * Marque le document tant que le bandeau est affiché — voir la feuille de
 * style non « scoped » ci-dessous.
 *
 * Les mises en page qui ouvrent leur propre « v-layout » (l'application, la
 * documentation) placent leur barre à l'intérieur : le bandeau, resté dans le
 * flux, les pousse tout seul. La vitrine, elle, n'a pas de « v-layout » : sa
 * barre est fixée à la fenêtre et passerait sous le bandeau, à moitié cachée.
 * La feuille de style ci-dessous la décale, et elle seule.
 *
 * Corrigé en CSS et non en JavaScript : Vuetify récrit lui-même le « top » en
 * ligne à chaque recalcul de mise en page, et écrasait la correction.
 */
function marquer(actif) {
  document.documentElement.classList.toggle('r-demo-actif', actif)
}

/**
 * Publie la hauteur réelle du bandeau.
 *
 * Elle dépend de la largeur de l'écran et du repli du texte : une valeur
 * écrite en dur se trompait d'un pixel sur téléphone, et la barre de la
 * vitrine mordait sur le bandeau.
 */
function publierHauteur() {
  const h = visible.value && element.value ? element.value.offsetHeight : 0
  document.documentElement.style.setProperty('--r-demo-hauteur', `${h}px`)
}

function ajuster() {
  marquer(visible.value)
  publierHauteur()
}

let observateur = null

onMounted(() => {
  ajuster()
  // La hauteur change quand le texte se replie : on suit l'élément plutôt
  // que de se fier au seul redimensionnement de la fenêtre.
  if (element.value && 'ResizeObserver' in window) {
    observateur = new ResizeObserver(publierHauteur)
    observateur.observe(element.value)
  }
  window.addEventListener('resize', publierHauteur)
})

onBeforeUnmount(() => {
  observateur?.disconnect()
  window.removeEventListener('resize', publierHauteur)
  marquer(false)
})

watch(visible, async () => {
  await nextTick()
  ajuster()
})

function recharger() {
  // Le jeu de données vit en mémoire : un simple rechargement le rétablit.
  window.location.reload()
}
</script>

<!-- Non « scoped » : la règle doit atteindre des barres rendues par d'autres
     composants. Elle ne s'applique que si le bandeau est affiché. -->
<style>
:root {
  /* Repli avant la première mesure ; la valeur réelle est posée en
     JavaScript, car elle dépend du repli du texte. */
  --r-demo-hauteur: 32px;
}

/* Barres fixées à la fenêtre : celles qui ne sont pas dans une mise en page
   **imbriquée**. « v-app » est lui-même un « v-layout », d'où le double
   sélecteur — sans quoi la règle ne visait rien du tout.
   Les barres des mises en page imbriquées (application, documentation) sont
   positionnées à l'intérieur de celles-ci et déjà poussées par le bandeau,
   qui reste dans le flux du document. */
.r-demo-actif .v-app-bar:not(:where(.v-layout .v-layout *)),
.r-demo-actif .v-toolbar:not(:where(.v-layout .v-layout *)) {
  top: var(--r-demo-hauteur) !important;
}
</style>

<style scoped>
.r-demo-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;            /* ne se comprime pas : « v-app » est un flex */
  padding: 6px 12px;
  background: rgb(var(--v-theme-warning));
  color: rgb(var(--v-theme-on-warning, 0, 0, 0));
  font-size: 0.75rem;
  line-height: 1.3;
}
.r-demo-banner__icone {
  flex: 0 0 auto;
}
.r-demo-banner__texte {
  margin: 0;
  min-width: 0;
}
.r-demo-banner__action,
.r-demo-banner__fermer {
  flex: 0 0 auto;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
  padding: 2px 6px;
  border-radius: 4px;
}
.r-demo-banner__action {
  margin-left: auto;
  text-decoration: underline;
  white-space: nowrap;
}
.r-demo-banner__action:hover,
.r-demo-banner__fermer:hover {
  background: rgba(0, 0, 0, 0.08);
}
/* Sur écran étroit, on garde l'essentiel : la phrase longue tronquée ne
   dirait rien de plus. */
@media (max-width: 600px) {
  .r-demo-banner__suite {
    display: none;
  }
}
</style>
