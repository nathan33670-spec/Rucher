/**
 * Adaptateur axios de la démonstration publique.
 *
 * La démo est servie en fichiers statiques : il n'y a **aucun serveur**
 * derrière, ni Python, ni base de données. Cet adaptateur se substitue au
 * transport HTTP d'axios et répond à la place de l'API, à partir d'un jeu de
 * données figé (« donnees.json »).
 *
 * Les écritures sont acceptées et gardées **en mémoire du navigateur** : on
 * peut créer une visite, modifier une ruche, ajouter une écriture, et le voir
 * aussitôt à l'écran. Tout est perdu au rechargement de la page, et c'est
 * volontaire — chaque visiteur repart d'une démo propre, et personne ne peut
 * abîmer celle du suivant.
 *
 * Ce fichier n'est inclus dans le paquet que si la variable VITE_DEMO vaut 1.
 */
import donneesInitiales from './donnees.json'

const PAUSE_MS = 120   // latence simulée : sans elle, les écrans « clignotent »

let base = null

/** Repart d'une copie fraîche du jeu de données. */
export function reinitialiser() {
  base = JSON.parse(JSON.stringify(donneesInitiales))
  base._seq = 10000
}

function prochainId() {
  base._seq += 1
  return base._seq
}

function chemin(config) {
  // axios donne l'URL relative à baseURL ; on retire la requête pour la traiter
  // séparément, et la barre finale pour ne pas multiplier les cas.
  const brut = (config.url || '').split('?')[0]
  return brut.replace(/\/+$/, '') || '/'
}

function parametres(config) {
  const q = (config.url || '').split('?')[1]
  const p = new URLSearchParams(q || '')
  for (const [k, v] of Object.entries(config.params || {})) p.set(k, String(v))
  return p
}

function corps(config) {
  if (!config.data) return {}
  if (typeof config.data === 'string') {
    try { return JSON.parse(config.data) } catch { return {} }
  }
  if (config.data instanceof FormData) {
    const o = {}
    for (const [k, v] of config.data.entries()) o[k] = v
    return o
  }
  return config.data
}

function reponse(config, data, status = 200) {
  return { data, status, statusText: 'OK', headers: {}, config }
}

function erreur(config, status, detail) {
  const e = new Error(detail)
  e.config = config
  e.response = { data: { detail }, status, statusText: 'Error', headers: {}, config }
  return e
}

/** Nom affichable d'un adhérent de la démo. */
function nomDe(id) {
  const u = (base['/users/'] || []).find((x) => x.id === id)
  return u ? `${u.first_name} ${u.last_name}` : 'Adhérent'
}

// ─── Collections que l'on sait créer / modifier / supprimer ───────────
// Le reste est accepté sans rien casser (voir plus bas) : une démo ne doit pas
// s'arrêter sur un bouton qu'on a oublié de câbler.
const COLLECTIONS = {
  '/apiaries': '/apiaries/',
  '/apiaries/hives': '/apiaries/hives/all',
  '/visits': '/visits/',
  '/inventory': '/inventory/',
  '/honey': '/honey/',
  '/sanitary': '/sanitary/',
  '/treasury': '/treasury/',
  '/events': '/events/',
  '/users': '/users/',
}

function collectionDe(p) {
  // La clé la plus longue qui préfixe le chemin gagne : « /apiaries/hives »
  // doit l'emporter sur « /apiaries ».
  let meilleure = null
  for (const prefixe of Object.keys(COLLECTIONS)) {
    if ((p === prefixe || p.startsWith(prefixe + '/')) &&
        (!meilleure || prefixe.length > meilleure.length)) {
      meilleure = prefixe
    }
  }
  return meilleure
}

function enrichirVisite(v) {
  const ruche = (base['/apiaries/hives/all'] || []).find((h) => h.id === v.hive_id)
  return {
    ...v,
    hive_name: ruche?.name ?? null,
    hive_number: ruche?.number ?? null,
    apiary_name: ruche?.apiary_name ?? null,
    author_name: nomDe(v.author_id ?? base['/users/me'].id),
  }
}

// ─── Traitement d'une requête ─────────────────────────────────────────
function traiter(config) {
  const p = chemin(config)
  const methode = (config.method || 'get').toLowerCase()
  const params = parametres(config)
  const envoi = corps(config)

  // --- Connexion : n'importe quel couple est accepté, c'est une démo ---
  if (p === '/users/login') {
    return reponse(config, {
      access_token: 'demo', token_type: 'bearer', user: base['/users/me'],
    })
  }
  if (p === '/users/logout' || p === '/users/switch-role') {
    return reponse(config, base['/users/me'])
  }
  if (p === '/notifications/vapid-public-key') {
    // Pas de notifications push dans la démo : le refuser proprement évite un
    // écran d'erreur, l'application sait se passer de cette clé.
    throw erreur(config, 503, 'Notifications indisponibles dans la démonstration.')
  }

  if (methode === 'get') {
    // Correspondance directe, avec ou sans barre finale.
    for (const cle of [p, p + '/', p.replace(/\/$/, '')]) {
      if (cle in base) return reponse(config, base[cle])
    }

    // Ruches d'un rucher donné.
    let m = p.match(/^\/apiaries\/(\d+)\/hives$/)
    if (m) return reponse(config, base._hives_by_apiary[m[1]] || [])

    // Dernière visite d'une ruche.
    m = p.match(/^\/apiaries\/hives\/(\d+)\/last-visit$/)
    if (m) return reponse(config, base['/visits/last'][m[1]] || null)

    // Dernières visites d'un lot de ruches.
    if (p === '/visits/last') {
      const ids = (params.get('hive_ids') || '').split(',').filter(Boolean)
      const out = {}
      for (const id of ids) if (base['/visits/last'][id]) out[id] = base['/visits/last'][id]
      return reponse(config, ids.length ? out : base['/visits/last'])
    }

    // Résumé sanitaire d'une ruche.
    m = p.match(/^\/sanitary\/hive\/(\d+)\/summary$/)
    if (m) {
      const lignes = base['/sanitary/'].filter((s) => s.hive_id === Number(m[1]))
      return reponse(config, {
        last_treatment: lignes.find((s) => s.record_type === 'treatment') || null,
        last_count: lignes.find((s) => s.record_type === 'count') || null,
      })
    }

    // Rapprochement d'un mois.
    m = p.match(/^\/treasury\/reconciliation\/(\d+)\/(\d+)$/)
    if (m) {
      const mois = base['/treasury/reconciliation']
        .find((r) => r.year === Number(m[1]) && r.month === Number(m[2]))
      const lignes = base['/treasury/'].filter((t) => t.date.startsWith(`${m[1]}-${String(m[2]).padStart(2, '0')}`))
      return reponse(config, {
        ...(mois || { year: Number(m[1]), month: Number(m[2]), validated: false }),
        statement_balance: null,
        reconciled_balance: lignes.filter((t) => t.reconciled_at)
          .reduce((s, t) => s + (t.transaction_type === 'income' ? t.amount : -t.amount), 0),
        opening_balance: 0, notes: null, transactions: lignes,
      })
    }

    // Détail d'une campagne.
    m = p.match(/^\/mail\/campaigns\/(\d+)$/)
    if (m) {
      const c = base['/mail/campaigns'].find((x) => x.id === Number(m[1]))
      if (!c) throw erreur(config, 404, 'Campagne introuvable')
      return reponse(config, {
        ...c,
        body: "Ceci est le corps du message tel qu'il a été envoyé.",
        body_html: '<p>Ceci est le corps du message tel qu\'il a été envoyé.</p>',
        attachments: [], recipients: [],
        poll: base._poll_by_campaign?.[String(c.id)] || null,
      })
    }

    // Élément d'une collection, par identifiant.
    const prefixe = collectionDe(p)
    if (prefixe) {
      const mm = p.match(/\/(\d+)$/)
      if (mm) {
        const liste = base[COLLECTIONS[prefixe]] || []
        const trouve = liste.find((x) => x.id === Number(mm[1]))
        if (trouve) return reponse(config, trouve)
      }
    }

    // Tout le reste : une liste vide vaut mieux qu'une erreur en pleine démo.
    return reponse(config, [])
  }

  // --- Écritures ---
  const prefixe = collectionDe(p)
  const cle = prefixe ? COLLECTIONS[prefixe] : null
  const liste = cle ? base[cle] : null
  const idDansUrl = Number((p.match(/\/(\d+)(?:\/[a-z-]+)?$/) || [])[1]) || null

  if (methode === 'post' && liste && !idDansUrl) {
    const cree = { ...envoi, id: prochainId(), created_at: new Date().toISOString() }
    if (cle === '/visits/') {
      cree.author_id = base['/users/me'].id
      cree.visited_at = cree.visited_at || new Date().toISOString()
      Object.assign(cree, enrichirVisite(cree))
      base['/visits/last'][String(cree.hive_id)] = cree
      base['/visits/stats'].total += 1
      base['/visits/stats'].month += 1
    }
    liste.unshift(cree)
    return reponse(config, cree, 201)
  }

  if ((methode === 'put' || methode === 'patch') && liste && idDansUrl) {
    const i = liste.findIndex((x) => x.id === idDansUrl)
    if (i >= 0) {
      liste[i] = { ...liste[i], ...envoi }
      if (cle === '/visits/') liste[i] = enrichirVisite(liste[i])
      return reponse(config, liste[i])
    }
  }

  if (methode === 'delete' && liste && idDansUrl) {
    const i = liste.findIndex((x) => x.id === idDansUrl)
    if (i >= 0) {
      const [oté] = liste.splice(i, 1)
      return reponse(config, oté, 200)
    }
  }

  // Action non câblée (notifications, envoi de courriel, import…) : on répond
  // favorablement et sans rien faire. Le bandeau de la démo prévient déjà que
  // rien n'est conservé ; renvoyer une erreur donnerait l'impression d'un
  // produit cassé, ce qui serait trompeur dans l'autre sens.
  return reponse(config, { detail: 'Action simulée — démonstration' })
}

/** Le compte sous lequel la démonstration s'ouvre. */
export function utilisateurDemo() {
  if (!base) reinitialiser()
  return base['/users/me']
}


/** Adaptateur à poser sur l'instance axios. */
export function adaptateurDemo(config) {
  if (!base) reinitialiser()
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      try {
        resolve(traiter(config))
      } catch (e) {
        if (e.response) reject(e)
        else {
          // Une erreur de l'adaptateur lui-même ne doit pas ressembler à une
          // panne du produit : on le dit franchement dans la console.
          console.error('[démo] requête non gérée', config.url, e)
          reject(erreur(config, 500, 'Cette action n\'est pas disponible dans la démonstration.'))
        }
      }
    }, PAUSE_MS)
  })
}
