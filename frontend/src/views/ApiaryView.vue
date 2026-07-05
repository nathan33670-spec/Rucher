<template>
  <div>
    <div class="d-flex align-center mb-4">
      <h2>Ruchers</h2>
      <v-spacer />
      <v-btn v-if="auth.hasRole('yard_manager')" color="primary" prepend-icon="mdi-plus" @click="showForm = true">
        Nouveau rucher
      </v-btn>
    </div>

    <v-row>
      <v-col v-for="apiary in apiaries" :key="apiary.id" cols="12" sm="6" md="4">
        <v-card @click="$router.push(`/apiaries/${apiary.id}`)" class="cursor-pointer">
          <v-card-title>
            <v-icon color="primary" class="mr-2">mdi-hexagon-multiple</v-icon>
            {{ apiary.name }}
          </v-card-title>
          <v-card-subtitle>{{ apiary.address || 'Pas d\'adresse' }}</v-card-subtitle>
          <v-card-text>
            <v-chip size="small" color="secondary" class="mr-1">
              {{ apiary.description || '—' }}
            </v-chip>
          </v-card-text>
          <v-card-actions>
            <v-btn size="small" color="accent" variant="text" @click.stop="$router.push(`/visits/live/${apiary.id}`)">
              <v-icon class="mr-1">mdi-bee</v-icon> Mode Live
            </v-btn>
            <v-spacer />
            <v-btn v-if="auth.isAdmin" icon size="small" @click.stop="deleteApiary(apiary.id)">
              <v-icon color="error">mdi-delete</v-icon>
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Dialog nouveau rucher -->
    <v-dialog v-model="showForm" max-width="500">
      <v-card>
        <v-card-title>{{ editId ? 'Modifier' : 'Nouveau' }} rucher</v-card-title>
        <v-card-text>
          <v-text-field v-model="form.name" label="Nom" required />
          <v-text-field v-model="form.address" label="Adresse" />
          <v-row>
            <v-col><v-text-field v-model.number="form.latitude" label="Latitude" type="number" /></v-col>
            <v-col><v-text-field v-model.number="form.longitude" label="Longitude" type="number" /></v-col>
          </v-row>
          <v-textarea v-model="form.description" label="Description" rows="2" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showForm = false">Annuler</v-btn>
          <v-btn color="primary" @click="saveApiary">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const apiaries = ref([])
const showForm = ref(false)
const editId = ref(null)
const form = ref({ name: '', address: '', latitude: null, longitude: null, description: '' })

async function load() {
  try {
    const { data } = await api.get('/apiaries/')
    apiaries.value = data
  } catch (e) {
    console.error('Apiaries load error:', e)
  }
}

async function saveApiary() {
  try {
    if (editId.value) {
      await api.put(`/apiaries/${editId.value}`, form.value)
    } else {
      await api.post('/apiaries/', form.value)
    }
    showForm.value = false
    form.value = { name: '', address: '', latitude: null, longitude: null, description: '' }
    editId.value = null
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Erreur lors de l\'enregistrement')
  }
}

async function deleteApiary(id) {
  if (!confirm('Supprimer ce rucher et toutes ses ruches ?')) return
  try {
    await api.delete(`/apiaries/${id}`)
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Erreur lors de la suppression')
  }
}

onMounted(load)
</script>
