<template>
  <div style="max-width: 820px;">
    <div class="d-flex flex-wrap align-center justify-space-between ga-2 mb-4">
      <h2>Réglages de l'association</h2>
    </div>

    <!-- ═══ ACCÈS ═══ -->
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="primary">mdi-shield-lock-outline</v-icon>
        Cloisonnement des accès
      </v-card-title>
      <v-card-text>
        <p class="text-body-2 r-muted mb-4">
          Par défaut, la trésorerie et le journal d'activité sont réservés au bureau.
          Vous pouvez les ouvrir <b>en lecture seule</b> à tous les membres.
        </p>

        <v-switch
          v-model="access.treasury_read_all"
          color="primary"
          hide-details
          density="comfortable"
          @update:model-value="saveAccess"
        >
          <template v-slot:label>
            <div>
              <div class="font-weight-medium">Trésorerie visible par tous les membres</div>
              <div class="text-caption r-muted">
                Lecture seule : consultation des écritures et du bilan. Seuls
                les administrateurs et trésoriers peuvent saisir ou modifier.
              </div>
            </div>
          </template>
        </v-switch>

        <v-divider class="my-4" />

        <v-switch
          v-model="access.audit_read_all"
          color="primary"
          hide-details
          density="comfortable"
          @update:model-value="saveAccess"
        >
          <template v-slot:label>
            <div>
              <div class="font-weight-medium">Journal d'activité visible par tous</div>
              <div class="text-caption r-muted">
                Le journal montre qui a fait quoi dans toute l'association.
              </div>
            </div>
          </template>
        </v-switch>
      </v-card-text>
    </v-card>

    <!-- ═══ E-MAIL ═══ -->
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="primary">mdi-email-outline</v-icon>
        Envoi d'e-mails
        <v-spacer />
        <v-chip size="small" :color="mail.smtp_host ? 'success' : 'warning'" variant="tonal">
          {{ mail.smtp_host ? 'Configuré' : 'Non configuré' }}
        </v-chip>
      </v-card-title>
      <v-card-text>
        <p class="text-body-2 r-muted mb-4">
          Sert au récapitulatif hebdomadaire. Avec Gmail, utilisez un
          <b>mot de passe d'application</b> — le mot de passe du compte ne fonctionne pas.
        </p>

        <v-row dense>
          <v-col cols="12" sm="7">
            <v-text-field v-model="mail.smtp_host" label="Serveur SMTP" placeholder="smtp.gmail.com" density="compact" />
          </v-col>
          <v-col cols="6" sm="2">
            <v-text-field v-model.number="mail.smtp_port" label="Port" type="number" density="compact" />
          </v-col>
          <v-col cols="6" sm="3">
            <v-select v-model="mail.smtp_tls" :items="tlsOptions" label="Chiffrement" density="compact" />
          </v-col>
          <v-col cols="12" sm="6">
            <v-text-field v-model="mail.smtp_user" label="Identifiant" placeholder="adresse@gmail.com" density="compact" />
          </v-col>
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="mail.smtp_password"
              label="Mot de passe"
              type="password"
              :placeholder="mail.password_set ? 'Déjà enregistré — laisser vide pour conserver' : ''"
              :hint="mail.password_set ? 'Un mot de passe est enregistré. Laissez vide pour le conserver.' : ''"
              persistent-hint
              density="compact"
            />
          </v-col>
          <v-col cols="12">
            <v-text-field v-model="mail.smtp_from" label="Adresse d'expédition" placeholder="rucher@association.fr" density="compact" />
          </v-col>
        </v-row>

        <v-divider class="my-4" />

        <div class="text-subtitle-2 font-weight-bold mb-2">Récapitulatif hebdomadaire</div>
        <v-row dense>
          <v-col cols="12">
            <v-textarea
              v-model="mail.recipients"
              label="Destinataires"
              placeholder="bureau@asso.fr, tresorier@asso.fr"
              hint="Adresses séparées par des virgules. Les identifiants de connexion (paulin, luc…) ne sont pas des adresses e-mail."
              persistent-hint
              rows="2"
              density="compact"
            />
          </v-col>
          <v-col cols="12" sm="4">
            <v-select v-model="mail.digest_weekday" :items="weekdays" label="Jour d'envoi" density="compact" />
          </v-col>
          <v-col cols="6" sm="4">
            <v-text-field v-model.number="mail.digest_hour" label="Heure" type="number" min="0" max="23" suffix="h" density="compact" />
          </v-col>
          <v-col cols="6" sm="4" class="d-flex align-center">
            <v-switch v-model="mail.digest_enabled" color="primary" label="Envoi actif" hide-details density="compact" />
          </v-col>
          <v-col cols="12">
            <v-text-field v-model="mail.app_base_url" label="Adresse de l'application" placeholder="https://ruches.corsicajack.fr"
              hint="Utilisée pour le bouton « Ouvrir l'application » dans l'e-mail" persistent-hint density="compact" />
          </v-col>
        </v-row>
      </v-card-text>
      <v-card-actions class="px-4 pb-4 flex-wrap ga-2">
        <v-btn color="primary" :loading="savingMail" prepend-icon="mdi-content-save" @click="saveMail">
          Enregistrer
        </v-btn>
        <v-btn variant="tonal" :loading="testing" prepend-icon="mdi-send-check-outline" @click="showTest = true">
          Envoyer un test
        </v-btn>
        <v-spacer />
        <v-btn variant="text" :loading="sendingDigest" prepend-icon="mdi-email-fast-outline" @click="sendDigestNow">
          Envoyer le récapitulatif maintenant
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- Dialog test -->
    <v-dialog v-model="showTest" max-width="440">
      <v-card>
        <v-card-title>Message de test</v-card-title>
        <v-card-text>
          <p class="text-body-2 r-muted mb-3">
            Enregistrez vos réglages avant de tester. Laissez vide pour
            envoyer aux destinataires du récapitulatif.
          </p>
          <v-text-field v-model="testTo" label="Adresse de test" placeholder="moi@exemple.fr" density="compact" hide-details />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showTest = false">Annuler</v-btn>
          <v-btn color="primary" :loading="testing" @click="sendTest">Envoyer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="okSnack" color="success" timeout="3500">{{ okMsg }}</v-snackbar>
    <v-snackbar v-model="errSnack" color="error" timeout="6000">{{ errMsg }}</v-snackbar>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'

const access = ref({ treasury_read_all: false, audit_read_all: false })
const mail = ref({
  smtp_host: '', smtp_port: 587, smtp_user: '', smtp_password: '',
  smtp_tls: 'starttls', smtp_from: '', recipients: '',
  digest_enabled: true, digest_weekday: 0, digest_hour: 8,
  app_base_url: '', password_set: false,
})
const savingMail = ref(false)
const testing = ref(false)
const sendingDigest = ref(false)
const showTest = ref(false)
const testTo = ref('')
const okSnack = ref(false); const okMsg = ref('')
const errSnack = ref(false); const errMsg = ref('')

const tlsOptions = [
  { title: 'STARTTLS (recommandé)', value: 'starttls' },
  { title: 'SSL/TLS', value: 'ssl' },
  { title: 'Aucun', value: 'none' },
]
const weekdays = [
  { title: 'Lundi', value: 0 }, { title: 'Mardi', value: 1 },
  { title: 'Mercredi', value: 2 }, { title: 'Jeudi', value: 3 },
  { title: 'Vendredi', value: 4 }, { title: 'Samedi', value: 5 },
  { title: 'Dimanche', value: 6 },
]

function ok(m) { okMsg.value = m; okSnack.value = true }
function fail(e, fallback) {
  errMsg.value = e?.response?.data?.detail || fallback
  errSnack.value = true
}

async function load() {
  try {
    const [a, m] = await Promise.all([
      api.get('/settings/access'),
      api.get('/settings/mail'),
    ])
    access.value = a.data
    mail.value = { ...m.data, smtp_password: '' }
  } catch (e) { fail(e, 'Chargement des réglages impossible') }
}

async function saveAccess() {
  try {
    const { data } = await api.put('/settings/access', access.value)
    access.value = data
    ok('Réglages d\'accès enregistrés')
  } catch (e) {
    fail(e, 'Enregistrement impossible')
    await load()
  }
}

async function saveMail() {
  savingMail.value = true
  try {
    const { data } = await api.put('/settings/mail', mail.value)
    mail.value = { ...data, smtp_password: '' }
    ok('Réglages e-mail enregistrés')
  } catch (e) { fail(e, 'Enregistrement impossible') }
  finally { savingMail.value = false }
}

async function sendTest() {
  testing.value = true
  try {
    const { data } = await api.post('/settings/mail/test', { to: testTo.value || null })
    showTest.value = false
    ok(data.detail)
  } catch (e) { fail(e, "Échec de l'envoi de test") }
  finally { testing.value = false }
}

async function sendDigestNow() {
  sendingDigest.value = true
  try {
    const { data } = await api.post('/reports/weekly/send')
    ok(data.detail)
  } catch (e) { fail(e, "Échec de l'envoi du récapitulatif") }
  finally { sendingDigest.value = false }
}

onMounted(load)
</script>
