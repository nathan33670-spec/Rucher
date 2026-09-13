<template>
  <DocPage
    eyebrow="Guide — chapitre 1"
    title="Premiers pas"
    lead="Se connecter, comprendre l'écran, installer l'application sur son téléphone."
    intro="Ce chapitre s'adresse à quelqu'un qui ouvre l'application pour la <b>première fois</b>. Aucune connaissance informatique n'est nécessaire : chaque action est décrite avec l'endroit exact où cliquer."
    :sections="sections"
    :next="{ title: 'Chapitre 2 — Ruchers et ruches', to: { name: 'docs-guide-ruchers' } }"
    :prev="{ title: 'Sommaire du guide', to: { name: 'docs-guide' } }"
  />
</template>

<script setup>
import DocPage from '../../components/DocPage.vue'

const sections = [
  {
    id: 'adresse', t: "Ouvrir l'application",
    blocks: [
      { p: "L'application vit sur un site internet : il n'y a rien à installer pour commencer, un navigateur suffit (Chrome, Safari, Edge, Firefox)." },
      { steps: [
        "Ouvrez votre navigateur et saisissez l'adresse du site communiquée par l'association.",
        "La <b>page publique</b> s'affiche : elle présente l'association et les abeilles. Personne n'a besoin d'un compte pour la lire.",
        "Cliquez sur le bouton <b>« Accéder à l'application »</b> — il est présent <b>en haut à droite</b> de la page et une seconde fois <b>au centre</b>.",
      ] },
      { img: 'g-accueil.jpg', cap: "La page publique. Le bouton d'accès à l'application est en haut à droite." },
      { tip: "Mettez l'adresse en favori dès maintenant : vous n'aurez plus à la retaper." },
    ],
  },
  {
    id: 'connexion', t: 'Se connecter',
    blocks: [
      { p: "La connexion demande deux informations, fournies par un administrateur de l'association." },
      { table: { head: ['Champ', 'Ce qu\'il faut saisir'], rows: [
        ["<b>Nom d'utilisateur</b>", "Un identifiant court, en minuscules, <b>sans arobase</b> — par exemple <code>paulin</code>. Ce n'est <b>pas</b> votre adresse e-mail."],
        ['<b>Mot de passe</b>', "Celui qui vous a été remis. Vous pourrez le changer ensuite."],
      ] } },
      { steps: [
        "Cliquez dans le champ <b>Nom d'utilisateur</b> et saisissez votre identifiant.",
        "Cliquez dans le champ <b>Mot de passe</b> et saisissez-le. L'icône en forme d'œil, à droite du champ, permet de vérifier ce que vous avez tapé.",
        "Si vous êtes sur votre appareil personnel, cochez <b>« Rester connecté »</b> : vous n'aurez plus à vous reconnecter à chaque fois.",
        "Cliquez sur <b>Se connecter</b>.",
      ] },
      { img: 'g-login.jpg', cap: "L'écran de connexion." },
      { warn: "Un message rouge « Identifiants incorrects » signifie que l'identifiant ou le mot de passe ne correspond pas. Vérifiez d'abord que la touche <b>Majuscule</b> n'est pas verrouillée." },
    ],
  },
  {
    id: 'mdp-oublie', t: 'Mot de passe oublié',
    blocks: [
      { p: "Vous pouvez réinitialiser votre mot de passe vous-même, sans déranger personne — à condition que votre <b>adresse e-mail</b> soit enregistrée dans l'application (voir plus bas, « Mes coordonnées »)." },
      { steps: [
        "Sous le bouton <b>Se connecter</b>, cliquez sur le lien <b>« Mot de passe oublié ? »</b>.",
        "Saisissez <b>soit</b> votre nom d'utilisateur, <b>soit</b> votre adresse e-mail, puis cliquez sur <b>Envoyer le lien</b>.",
        "Consultez votre boîte e-mail : un message contient un lien <b>valable une heure</b> et utilisable <b>une seule fois</b>.",
        "Cliquez sur ce lien, choisissez un nouveau mot de passe, validez.",
      ] },
      { img: 'g-mdp-oublie.jpg', cap: "La demande de réinitialisation." },
      { note: "Par sécurité, l'application répond toujours la même chose, que le compte existe ou non : cela empêche de deviner qui est inscrit. Si aucun e-mail n'arrive, c'est probablement qu'aucune adresse n'est enregistrée sur le compte — demandez alors à un administrateur." },
      { p: "Changer son mot de passe par ce lien <b>déconnecte tous les autres appareils</b> : c'est voulu, cela met dehors quelqu'un qui aurait utilisé votre compte." },
    ],
  },
  {
    id: 'tableau-de-bord', t: 'Le tableau de bord',
    blocks: [
      { p: "Une fois connecté, vous arrivez sur le <b>tableau de bord</b> : la vue d'ensemble de ce qui vous concerne aujourd'hui." },
      { ul: [
        "<b>Visite rapide de mes ruches</b> — le gros bouton pour partir en visite (chapitre 3).",
        "<b>Prochains événements</b> — les sorties et réunions, avec votre réponse.",
        "<b>Alertes actives</b> — les problèmes signalés sur des ruches et non encore résolus.",
        "<b>Visites du mois</b> et quelques chiffres sur le rucher.",
        "<b>Stocks bas</b> — le matériel passé sous son seuil d'alerte.",
      ] },
      { img: 'g-dashboard.jpg', cap: "Le tableau de bord." },
    ],
  },
  {
    id: 'barre-haut', t: 'La barre du haut, bouton par bouton',
    blocks: [
      { p: "La barre supérieure est la même sur tous les écrans. De gauche à droite :" },
      { img: 'g-barre-haut.jpg', cap: "La barre supérieure (agrandie)." },
      { table: { head: ['Bouton', 'À quoi il sert'], rows: [
        ['☰ (trois traits)', "Ouvre ou referme le <b>menu de gauche</b>."],
        ['☁ nuage avec un chiffre', "N'apparaît que si des visites saisies <b>hors-ligne</b> attendent d'être envoyées. Cliquez dessus pour les synchroniser."],
        ['⚠ triangle rouge', "<b>Signaler un problème</b> sur une ruche, depuis n'importe quel écran (chapitre 3)."],
        ['🔔 cloche', "Vos <b>notifications</b> : alertes, nouvelles visites, nouveautés de l'application. Une pastille rouge indique les non lues."],
        ['Pastille de rôle', "Le rôle avec lequel vous travaillez. N'apparaît que si vous en avez plusieurs."],
        ['Votre prénom', "Le <b>menu de votre compte</b> : coordonnées, mot de passe, déconnexion."],
      ] } },
    ],
  },
  {
    id: 'menu', t: 'Le menu de gauche',
    blocks: [
      { p: "Le menu regroupe les écrans en trois familles. Certaines entrées n'apparaissent que selon votre rôle : c'est normal." },
      { img: 'g-menu.jpg', cap: "Le menu de navigation." },
      { table: { head: ['Famille', 'Écrans'], rows: [
        ['<b>Suivi du rucher</b>', 'Tableau de bord · Ruchers · Visite rapide · Historique des visites · Météo · Événements'],
        ['<b>Gestion</b>', 'Inventaire · Miellée · Sanitaire · Trésorerie <i>(trésorier et administrateur)</i>'],
        ['<b>Réglages</b>', 'Documentation · Utilisateurs <i>(admin)</i> · Notifications · Journal · Configuration <i>(admin)</i>'],
      ] } },
    ],
  },
  {
    id: 'compte', t: 'Votre compte : coordonnées et mot de passe',
    blocks: [
      { steps: [
        "Cliquez sur <b>votre prénom</b>, tout en haut à droite.",
        "<b>Mes coordonnées</b> : renseignez votre <b>adresse e-mail</b> et votre téléphone, puis <b>Enregistrer</b>.",
        "<b>Changer mon mot de passe</b> : saisissez l'actuel puis le nouveau, deux fois.",
        "<b>Se déconnecter</b> est la dernière ligne du menu.",
      ] },
      { img: 'g-menu-profil.jpg', cap: "Le menu du compte." },
      { warn: "Renseignez votre adresse e-mail sans attendre : <b>sans elle, le « mot de passe oublié » ne peut pas fonctionner</b>. Tant qu'elle manque, la mention « Adresse e-mail manquante » s'affiche sous l'entrée <b>Mes coordonnées</b>." },
    ],
  },
  {
    id: 'roles', t: 'Changer de rôle (si vous en avez plusieurs)',
    blocks: [
      { p: "Un administrateur peut travailler « en usager » pour éviter les fausses manœuvres. On ne peut que <b>se restreindre</b> : jamais prendre plus de droits que ceux attribués." },
      { steps: [
        "Cliquez sur la <b>pastille de rôle</b>, à gauche de votre prénom.",
        "Sous <b>« J'utilise le rôle »</b>, choisissez le rôle voulu : il s'applique immédiatement.",
        "Pour fixer le rôle pris <b>à chaque connexion</b>, ouvrez le menu de votre prénom et cliquez sur l'<b>étoile</b> devant le rôle souhaité.",
      ] },
      { img: 'g-roles.jpg', cap: "Le sélecteur de rôle." },
      { table: { head: ['Rôle', 'Ce qu\'il permet'], rows: [
        ['<b>Administrateur</b>', 'Tout, y compris les comptes, la configuration et le journal.'],
        ['<b>Responsable de rucher</b>', 'Gérer les ruchers, les ruches et toutes les visites de ses ruchers.'],
        ['<b>Trésorier</b>', 'La trésorerie, les factures et le bilan.'],
        ['<b>Usager</b>', 'Saisir ses visites, consulter, répondre aux événements.'],
        ['<b>Lecture seule</b>', 'Tout consulter, ne rien modifier.'],
      ] } },
    ],
  },
  {
    id: 'installer', t: "Installer l'application sur son téléphone",
    blocks: [
      { p: "Installée, l'application s'ouvre en plein écran comme une vraie application, se lance d'un geste, et permet de <b>saisir des visites sans réseau</b> au milieu des ruches." },
      { h3: 'Android (Chrome)' },
      { steps: [
        "Ouvrez le site dans Chrome.",
        "Cliquez sur le bouton <b>« Installer l'app »</b> proposé par l'application, ou ouvrez le menu ⋮ de Chrome puis <b>« Installer l'application »</b>.",
        "Confirmez : une icône apparaît sur votre écran d'accueil.",
      ] },
      { h3: 'iPhone / iPad (Safari)' },
      { steps: [
        "Ouvrez le site <b>dans Safari</b> (cela ne fonctionne pas depuis Chrome sur iPhone).",
        "Touchez le bouton <b>Partager</b> (le carré avec une flèche vers le haut), en bas de l'écran.",
        "Faites défiler et touchez <b>« Sur l'écran d'accueil »</b>, puis <b>Ajouter</b>.",
      ] },
      { warn: "Sur iPhone, les <b>notifications</b> ne fonctionnent qu'une fois l'application ajoutée à l'écran d'accueil. C'est une limitation d'Apple, pas de l'application." },
      { img: 'g-mobile-accueil.jpg', cap: "L'application sur téléphone." },
    ],
  },
  {
    id: 'mobile', t: 'Se repérer sur téléphone',
    blocks: [
      { p: "Sur petit écran, une <b>barre fixe en bas</b> donne accès aux cinq écrans les plus utilisés sur le terrain : <b>Accueil</b>, <b>Visite rapide</b>, <b>Ruchers</b>, <b>Historique visites</b>, <b>Météo</b>. Tout le reste passe par le menu ☰ en haut à gauche." },
      { img: 'g-mobile-nav.jpg', cap: "La barre de navigation du bas (agrandie)." },
    ],
  },
]
</script>
