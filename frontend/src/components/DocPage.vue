<template>
  <DocArticle :eyebrow="eyebrow" :title="title" :lead="lead">
    <!-- Le contenu passe par un élément interne : « v-html » posé sur
         « v-alert » remplacerait sa structure et casserait la mise en page. -->
    <v-alert v-if="intro" type="info" variant="tonal" density="comfortable" class="mb-6">
      <span v-html="intro"></span>
    </v-alert>

    <!-- Sommaire de la page -->
    <v-card v-if="sections.length > 1" variant="tonal" class="mb-6 pa-1">
      <v-list density="compact" nav>
        <v-list-item
          v-for="(s, i) in sections" :key="s.id"
          :href="'#' + s.id" :title="(i + 1) + '. ' + s.t"
        />
      </v-list>
    </v-card>

    <section v-for="(s, si) in sections" :key="s.id" :id="s.id" class="doc-section">
      <h2>{{ (si + 1) + '. ' + s.t }}</h2>
      <template v-for="(b, bi) in s.blocks" :key="bi">
        <h3 v-if="b.h3" v-html="b.h3"></h3>
        <p v-else-if="b.p" v-html="b.p"></p>
        <ul v-else-if="b.ul">
          <li v-for="(l, i) in b.ul" :key="i" v-html="l"></li>
        </ul>

        <!-- Pas à pas : « où cliquer », numéroté -->
        <ol v-else-if="b.steps" class="doc-steps">
          <li v-for="(l, i) in b.steps" :key="i" v-html="l"></li>
        </ol>

        <figure v-else-if="b.img">
          <img :src="'/docs-img/' + b.img" :alt="b.cap || s.t" loading="lazy" />
          <figcaption v-if="b.cap">{{ b.cap }}</figcaption>
        </figure>

        <v-table v-else-if="b.table" density="compact" class="doc-table mb-4">
          <thead>
            <tr><th v-for="(h, i) in b.table.head" :key="i">{{ h }}</th></tr>
          </thead>
          <tbody>
            <tr v-for="(r, i) in b.table.rows" :key="i">
              <td v-for="(c, j) in r" :key="j" v-html="c"></td>
            </tr>
          </tbody>
        </v-table>

        <pre v-else-if="b.code" class="doc-code">{{ b.code }}</pre>

        <v-alert
          v-else-if="b.note || b.tip || b.warn"
          :type="b.warn ? 'warning' : (b.tip ? 'success' : 'info')"
          variant="tonal" density="comfortable" class="my-4"
        >
          <span v-html="b.warn || b.tip || b.note"></span>
        </v-alert>
      </template>
    </section>

    <div v-if="next || prev" class="d-flex flex-wrap ga-3 mt-8">
      <v-btn v-if="prev" :to="prev.to" variant="tonal" prepend-icon="mdi-arrow-left">
        {{ prev.title }}
      </v-btn>
      <v-btn v-if="next" :to="next.to" color="primary" append-icon="mdi-arrow-right">
        {{ next.title }}
      </v-btn>
    </div>
  </DocArticle>
</template>

<script setup>
import DocArticle from './DocArticle.vue'

defineProps({
  eyebrow: String,
  title: String,
  lead: String,
  intro: String,
  sections: { type: Array, default: () => [] },
  prev: Object,
  next: Object,
})
</script>

<style scoped>
.doc-section { margin-bottom: 34px; scroll-margin-top: 78px; }

/* Le pas à pas se lit comme une recette : un numéro bien visible par action. */
.doc-steps { list-style: none; padding-left: 0; counter-reset: etape; }
.doc-steps > li {
  counter-increment: etape;
  position: relative;
  padding: 6px 0 6px 42px;
  line-height: 1.65;
  margin-bottom: 6px;
}
.doc-steps > li::before {
  content: counter(etape);
  position: absolute; left: 0; top: 4px;
  width: 28px; height: 28px; border-radius: 50%;
  background: rgb(var(--v-theme-primary)); color: #fff;
  font-size: .85rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.doc-table :deep(th) { font-weight: 700; white-space: nowrap; }
.doc-code {
  background: rgba(0,0,0,.06); border-radius: 10px; padding: 12px 14px;
  font-size: .85rem; overflow-x: auto; margin-bottom: 14px;
  font-family: ui-monospace, Menlo, Consolas, monospace; line-height: 1.6;
}
</style>
