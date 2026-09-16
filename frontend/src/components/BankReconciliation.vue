<template>
  <div>
    <!-- Suivi : ce qui reste à faire, mois par mois. Un mois oublié doit
         sauter aux yeux, pas se découvrir à la clôture. -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title class="text-subtitle-1 d-flex align-center flex-wrap ga-2">
        <v-icon class="mr-1" color="primary">mdi-bank-check</v-icon>
        Rapprochement bancaire
        <v-chip v-if="aFaire.length" size="small" color="warning" variant="tonal">
          {{ aFaire.length }} mois à rapprocher
        </v-chip>
        <v-chip v-else-if="suivi.length" size="small" color="success" variant="tonal">
          Tout est à jour
        </v-chip>
      </v-card-title>
      <v-card-text>
        <div class="d-flex flex-wrap ga-2">
          <v-chip
            v-for="m in suivi" :key="m.year + '-' + m.month"
            :color="m.validated ? 'success' : (m.total ? 'warning' : undefined)"
            :variant="estCourant(m) ? 'flat' : 'tonal'"
            size="small" link
            @click="ouvrir(m.year, m.month)"
          >
            <v-icon start size="14">
              {{ m.validated ? 'mdi-check-circle' : (m.total ? 'mdi-progress-clock' : 'mdi-minus-circle-outline') }}
            </v-icon>
            {{ m.label }}
            <span v-if="!m.validated && m.pending" class="ml-1">({{ m.pending }})</span>
          </v-chip>
        </div>
      </v-card-text>
    </v-card>

    <v-card v-if="mois" variant="outlined">
      <v-card-title class="d-flex align-center flex-wrap ga-2">
        <v-btn icon size="small" variant="text" @click="decaler(-1)"><v-icon>mdi-chevron-left</v-icon></v-btn>
        <span class="text-subtitle-1 font-weight-bold text-capitalize">{{ mois.label }}</span>
        <v-btn icon size="small" variant="text" @click="decaler(1)"><v-icon>mdi-chevron-right</v-icon></v-btn>
        <v-chip v-if="mois.validated" size="small" color="success" variant="flat" prepend-icon="mdi-lock">
          Validé
        </v-chip>
        <v-spacer />
        <span v-if="mois.validated && mois.validated_by_name" class="text-caption text-medium-emphasis">
          par {{ mois.validated_by_name }} le {{ dateCourte(mois.validated_at) }}
        </span>
      </v-card-title>

      <v-card-text>
        <!-- Les trois nombres qui font le rapprochement. -->
        <v-row dense class="mb-2">
          <v-col cols="12" sm="4">
            <div class="rb-tuile">
              <div class="text-caption text-medium-emphasis">Solde des écritures pointées</div>
              <div class="text-h6">{{ money(mois.reconciled_balance) }}</div>
              <div class="text-caption text-medium-emphasis">
                dont {{ money(mois.opening_balance) }} repris des mois précédents
              </div>
            </div>
          </v-col>
          <v-col cols="12" sm="4">
            <div class="rb-tuile">
              <div class="text-caption text-medium-emphasis">Solde du relevé bancaire</div>
              <v-text-field
                v-model.number="soldeReleve" type="number" step="0.01" suffix="€"
                density="compact" hide-details variant="outlined"
                :disabled="mois.validated || !canWrite"
                placeholder="à saisir"
                @blur="enregistrerSolde"
              />
            </div>
          </v-col>
          <v-col cols="12" sm="4">
            <div class="rb-tuile" :class="ecartClass">
              <div class="text-caption text-medium-emphasis">Écart</div>
              <div class="text-h6">
                {{ mois.difference === null ? '—' : money(mois.difference) }}
              </div>
              <div class="text-caption">
                {{ mois.difference === null
                  ? 'Saisissez le solde du relevé'
                  : (Math.abs(mois.difference) < 0.01
                    ? 'Les comptes tombent juste'
                    : 'Il manque une écriture d\'un côté ou de l\'autre') }}
              </div>
            </div>
          </v-col>
        </v-row>

        <div class="d-flex flex-wrap align-center ga-2 mb-2">
          <v-chip size="small" variant="tonal">
            {{ mois.counts.reconciled }} / {{ mois.counts.total }} pointée(s)
          </v-chip>
          <!-- Montant signé des écritures encore non pointées : c'est
               normalement lui qu'on retrouve dans l'écart. -->
          <v-chip v-if="mois.counts.pending" size="small" color="warning" variant="tonal">
            Non pointé : {{ money(mois.pending_total) }}
          </v-chip>
          <v-spacer />
          <v-btn
            v-if="canWrite && !mois.validated && mois.counts.pending"
            size="small" variant="text" prepend-icon="mdi-check-all"
            :loading="busy" @click="toutPointer(true)"
          >
            Tout pointer
          </v-btn>
          <v-btn
            v-if="canWrite && !mois.validated && mois.counts.reconciled"
            size="small" variant="text" prepend-icon="mdi-close"
            :loading="busy" @click="toutPointer(false)"
          >
            Tout dépointer
          </v-btn>
        </div>

        <v-alert v-if="erreur" type="error" density="compact" class="mb-3" closable
                 @click:close="erreur = ''">{{ erreur }}</v-alert>

        <v-table density="compact" class="rb-table">
          <thead>
            <tr>
              <th style="width:52px">Pointé</th>
              <th>Date</th>
              <th>Description</th>
              <th class="text-right">Montant</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in mois.transactions" :key="t.id"
                :class="{ 'rb-pointee': t.reconciled_at }">
              <td>
                <v-checkbox-btn
                  :model-value="!!t.reconciled_at"
                  :disabled="mois.validated || !canWrite || busy"
                  color="success"
                  @update:model-value="(v) => pointer(t, v)"
                />
              </td>
              <td class="text-no-wrap">{{ dateCourte(t.date) }}</td>
              <td>
                {{ t.description || '—' }}
                <v-icon v-if="t.source" size="13" class="ml-1" color="secondary"
                        title="Importée depuis SumUp">mdi-sync</v-icon>
              </td>
              <td class="text-right text-no-wrap"
                  :class="t.transaction_type === 'income' ? 'text-success' : 'text-error'">
                {{ t.transaction_type === 'income' ? '+' : '−' }}{{ money(t.amount) }}
              </td>
            </tr>
            <tr v-if="!mois.transactions.length">
              <td colspan="4" class="text-center text-medium-emphasis py-4">
                Aucune écriture ce mois-ci.
              </td>
            </tr>
          </tbody>
        </v-table>
      </v-card-text>

      <v-card-actions v-if="canWrite" class="px-4 pb-4 flex-wrap ga-2">
        <v-btn
          v-if="!mois.validated"
          color="primary" prepend-icon="mdi-check-decagram"
          :loading="busy" :disabled="!pretAValider" @click="valider"
        >
          Valider le rapprochement
        </v-btn>
        <span v-if="!mois.validated && !pretAValider" class="text-caption text-medium-emphasis">
          {{ raisonBlocage }}
        </span>
        <v-btn
          v-if="mois.validated && isAdmin"
          variant="text" color="warning" prepend-icon="mdi-lock-open-variant"
          :loading="busy" @click="rouvrir"
        >
          Rouvrir le mois
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '../services/api'
import { apiError } from '../services/toast'
import { money } from '../services/format'
import { confirmAction } from '../services/confirm'

const props = defineProps({
  canWrite: { type: Boolean, default: false },
  isAdmin: { type: Boolean, default: false },
})
const emit = defineEmits(['changed', 'message'])

const suivi = ref([])
const mois = ref(null)
const annee = ref(null)
const numMois = ref(null)
const soldeReleve = ref(null)
const busy = ref(false)
const erreur = ref('')

const aFaire = computed(() => suivi.value.filter((m) => !m.validated && m.total > 0))
const estCourant = (m) => m.year === annee.value && m.month === numMois.value

const ecartClass = computed(() => {
  if (!mois.value || mois.value.difference === null) return ''
  return Math.abs(mois.value.difference) < 0.01 ? 'rb-juste' : 'rb-ecart'
})

// Ce qui empêche de valider, dit avant de cliquer plutôt qu'après.
const pretAValider = computed(() => {
  const m = mois.value
  if (!m || m.validated) return false
  return m.statement_balance !== null && m.counts.pending === 0
    && m.difference !== null && Math.abs(m.difference) < 0.01
})
const raisonBlocage = computed(() => {
  const m = mois.value
  if (!m) return ''
  if (m.statement_balance === null) return 'Saisissez le solde du relevé bancaire.'
  if (m.counts.pending) return `${m.counts.pending} écriture(s) restent à pointer.`
  if (m.difference !== null && Math.abs(m.difference) >= 0.01) {
    return "L'écart doit être nul pour valider."
  }
  return ''
})

function dateCourte(d) {
  return d ? new Date(d).toLocaleDateString('fr-FR') : ''
}

async function chargerSuivi() {
  try {
    const { data } = await api.get('/treasury/reconciliation?months=12')
    suivi.value = data
  } catch (e) { erreur.value = apiError(e, 'Suivi indisponible') }
}

async function ouvrir(an, mo) {
  annee.value = an
  numMois.value = mo
  erreur.value = ''
  try {
    const { data } = await api.get(`/treasury/reconciliation/${an}/${mo}`)
    mois.value = data
    soldeReleve.value = data.statement_balance
  } catch (e) { erreur.value = apiError(e, 'Mois indisponible') }
}

function decaler(pas) {
  let an = annee.value
  let mo = numMois.value + pas
  if (mo === 0) { an -= 1; mo = 12 }
  if (mo === 13) { an += 1; mo = 1 }
  ouvrir(an, mo)
}

async function appliquer(promesse, succes) {
  busy.value = true
  erreur.value = ''
  try {
    const { data } = await promesse
    mois.value = data
    soldeReleve.value = data.statement_balance
    await chargerSuivi()
    emit('changed')
    if (succes) emit('message', succes)
  } catch (e) {
    erreur.value = apiError(e, "L'opération a échoué")
  } finally {
    busy.value = false
  }
}

const base = () => `/treasury/reconciliation/${annee.value}/${numMois.value}`

function pointer(t, valeur) {
  appliquer(api.post(`${base()}/pointer`,
                     { transaction_ids: [t.id], reconciled: !!valeur }))
}

function toutPointer(valeur) {
  const ids = mois.value.transactions
    .filter((t) => !!t.reconciled_at !== valeur)
    .map((t) => t.id)
  if (!ids.length) return
  appliquer(api.post(`${base()}/pointer`, { transaction_ids: ids, reconciled: valeur }))
}

function enregistrerSolde() {
  if (mois.value.validated) return
  const v = soldeReleve.value === '' || soldeReleve.value === undefined ? null : soldeReleve.value
  if (v === mois.value.statement_balance) return
  appliquer(api.put(base(), { statement_balance: v }))
}

function valider() {
  appliquer(api.post(`${base()}/valider`),
            `Rapprochement de ${mois.value.label} validé — les administrateurs sont prévenus`)
}

async function rouvrir() {
  if (!(await confirmAction(
    `Rouvrir le rapprochement de ${mois.value.label} ? Les administrateurs en seront avertis.`
  ))) return
  appliquer(api.post(`${base()}/rouvrir`), `${mois.value.label} rouvert`)
}

onMounted(async () => {
  await chargerSuivi()
  const maintenant = new Date()
  // Ouvrir le premier mois à rapprocher s'il y en a un : c'est ce qu'on vient
  // faire ici. Sinon, le mois en cours.
  const cible = aFaire.value[0]
  await ouvrir(cible ? cible.year : maintenant.getFullYear(),
               cible ? cible.month : maintenant.getMonth() + 1)
})

defineExpose({ rafraichir: async () => { await chargerSuivi(); await ouvrir(annee.value, numMois.value) } })
</script>

<style scoped>
.rb-tuile {
  border: 1px solid rgba(0, 0, 0, .12);
  border-radius: 10px;
  padding: 10px 12px;
  height: 100%;
}
.rb-juste { border-color: rgb(var(--v-theme-success)); }
.rb-ecart { border-color: rgb(var(--v-theme-error)); }
.rb-table :deep(td) { vertical-align: middle; }
.rb-pointee { background: rgba(var(--v-theme-success), .06); }
</style>
