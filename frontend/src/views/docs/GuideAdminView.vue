<template>
  <DocPage
    eyebrow="Guide — chapitre 6"
    title="Administration"
    lead="Gérer les comptes, importer les adhérents par fichier CSV, régler l'association, lire le journal."
    intro="Ce chapitre s'adresse aux <b>administrateurs</b>. Les écrans décrits ici n'apparaissent dans le menu que si vous avez ce rôle."
    :sections="sections"
    :prev="{ title: 'Chapitre 5 — Notifications, météo, événements', to: { name: 'docs-guide-suivi' } }"
    :next="{ title: 'Sommaire du guide', to: { name: 'docs-guide' } }"
  />
</template>

<script setup>
import DocPage from '../../components/DocPage.vue'

const sections = [
  {
    id: 'utilisateurs', t: 'La liste des adhérents',
    blocks: [
      { steps: ["Menu de gauche → section <b>Réglages</b> → <b>Utilisateurs</b>."] },
      { p: "Le tableau montre, pour chaque compte : le nom, l'<b>identifiant de connexion</b>, l'<b>adresse e-mail</b>, le téléphone, les <b>rôles</b> et l'état <b>actif / inactif</b>." },
      { img: 'g-utilisateurs.jpg', cap: "L'écran Utilisateurs." },
      { p: "La barre de <b>filtres</b> permet de chercher par nom, par rôle ou par état — pratique pour retrouver les comptes désactivés." },
      { h3: "Les boutons d'action, en bout de ligne" },
      { img: 'g-utilisateurs-boutons.jpg', cap: "Les trois boutons d'action (agrandis)." },
      { table: { head: ['Icône', 'Action'], rows: [
        ['✏️ <b>crayon</b>', "Modifier la fiche : nom, e-mail, téléphone, rôles, état actif."],
        ['🔑 <b>cadenas</b>', "Définir un nouveau mot de passe pour cette personne."],
        ['🗑️ <b>corbeille</b>', "Supprimer le compte — ou le désactiver, voir plus bas."],
      ] } },
    ],
  },
  {
    id: 'creer', t: 'Créer un compte',
    blocks: [
      { steps: [
        "Cliquez sur <b>Nouvel utilisateur</b>, en haut à droite.",
        "Remplissez le formulaire.",
        "Cliquez sur <b>Enregistrer</b>, puis communiquez à la personne son identifiant et son mot de passe.",
      ] },
      { img: 'g-utilisateur-form.jpg', cap: "Le formulaire d'un compte." },
      { table: { head: ['Champ', 'Ce qu\'il faut saisir'], rows: [
        ["<b>Nom d'utilisateur</b>", "L'<b>identifiant de connexion</b> : court, en minuscules, <b>sans arobase</b> (ex. <code>paulin</code>). Il ne pourra <b>plus être modifié</b> ensuite."],
        ['<b>Adresse e-mail</b>', "La <b>vraie</b> adresse. Elle sert au « mot de passe oublié » et aux envois. <b>C'est un champ différent de l'identifiant.</b>"],
        ['<b>Mot de passe</b>', "Provisoire : la personne le changera depuis son menu."],
        ['<b>Prénom</b>, <b>Nom</b>, <b>Téléphone</b>', 'Les coordonnées de l\'adhérent.'],
        ['<b>Rôles</b>', 'Un ou plusieurs. Sans rôle particulier, choisissez <i>Usager</i>.'],
        ['<b>Actif</b>', "Décoché, le compte existe mais ne peut plus se connecter."],
      ] } },
      { warn: "<b>Nom d'utilisateur ≠ adresse e-mail.</b> C'est la confusion la plus fréquente : l'identifiant sert à se connecter, l'adresse à recevoir les messages." },
    ],
  },
  {
    id: 'csv', t: 'Importer les adhérents par fichier CSV',
    blocks: [
      { p: "Pour créer plusieurs comptes d'un coup, par exemple au moment des adhésions. Un fichier CSV est un tableau enregistré en texte : Excel, LibreOffice Calc ou Google Sheets savent tous en produire." },
      { h3: 'La méthode la plus sûre : partir du modèle' },
      { steps: [
        "Sur l'écran <b>Utilisateurs</b>, cliquez sur <b>Modèle CSV</b> : un fichier <code>modele-adherents.csv</code> se télécharge, déjà rempli de trois exemples.",
        "Ouvrez-le dans votre tableur, <b>remplacez les lignes d'exemple</b> par vos adhérents — sans toucher à la première ligne, qui porte les noms de colonnes.",
        "Enregistrez <b>au format CSV</b> (et non <code>.xlsx</code>).",
        "Revenez sur l'écran <b>Utilisateurs</b>, cliquez sur <b>Import CSV</b> et choisissez votre fichier.",
      ] },
      { h3: 'Les colonnes attendues' },
      { p: "La <b>première ligne du fichier doit contenir les noms de colonnes</b>, écrits exactement comme ci-dessous (les majuscules et les espaces autour du nom sont tolérés). L'ordre des colonnes est libre ; seules <code>email</code> est obligatoire." },
      { table: { head: ['Colonne', 'Obligatoire', 'Contenu'], rows: [
        ['<code>email</code>', '<b>Oui</b>', "L'<b>identifiant de connexion</b>, pas l'adresse : court, en minuscules, sans arobase (ex. <code>paulin</code>). Doit être unique."],
        ['<code>first_name</code>', 'Non', 'Le prénom.'],
        ['<code>last_name</code>', 'Non', 'Le nom de famille.'],
        ['<code>contact_email</code>', 'Non', "La <b>vraie adresse e-mail</b> (ex. <code>paulin.durand@example.fr</code>). Doit être unique elle aussi. Indispensable pour le « mot de passe oublié »."],
        ['<code>phone</code>', 'Non', 'Le téléphone, tel quel.'],
        ['<code>roles</code>', 'Non', "Les rôles, séparés par une <b>barre verticale</b> <code>|</code>. Vide ⇒ <code>user</code>."],
      ] } },
      { warn: "La colonne s'appelle <code>email</code> mais contient l'<b>identifiant de connexion</b> ; c'est <code>contact_email</code> qui porte l'adresse. Ce nom de colonne est conservé pour rester compatible avec les fichiers déjà utilisés." },
      { h3: 'Les valeurs acceptées pour <code>roles</code>' },
      { table: { head: ['À écrire', 'Rôle'], rows: [
        ['<code>admin</code>', 'Administrateur'],
        ['<code>yard_manager</code>', 'Responsable de rucher'],
        ['<code>treasurer</code>', 'Trésorier'],
        ['<code>user</code>', 'Usager <i>(valeur par défaut)</i>'],
        ['<code>readonly</code>', 'Lecture seule'],
      ] } },
      { p: "Plusieurs rôles pour une même personne : <code>yard_manager|treasurer</code>, <b>sans espace</b> autour de la barre." },
      { h3: 'Exemple complet de fichier' },
      { code: `email;first_name;last_name;contact_email;phone;roles
paulin;Paulin;Durand;paulin.durand@example.fr;0612345678;admin
marie;Marie;Lefevre;marie.lefevre@example.fr;;user
claude;Claude;Martin;;;yard_manager|treasurer` },
      { p: "Une colonne peut rester vide : on laisse simplement <b>rien entre deux séparateurs</b> (ligne de Marie, sans téléphone)." },
      { h3: 'Séparateur et encodage' },
      { ul: [
        "Le séparateur est <b>détecté automatiquement</b> : point-virgule <code>;</code> (ce qu'écrit Excel en français), virgule <code>,</code> ou tabulation. Vous n'avez rien à régler.",
        "Le fichier doit être en <b>UTF-8</b> pour que les accents s'affichent correctement. Le modèle téléchargé l'est déjà ; dans LibreOffice, choisissez <i>Unicode (UTF-8)</i> à l'enregistrement.",
      ] },
      { h3: 'Les mots de passe provisoires' },
      { p: "Chaque compte créé reçoit un <b>mot de passe tiré au hasard</b>, différent pour chacun. Ils s'affichent dans un tableau <b>juste après l'import, une seule fois</b> : ils ne sont conservés en clair nulle part et personne, pas même un administrateur, ne peut les relire ensuite." },
      { steps: [
        "Après l'import, un bandeau vert liste les comptes créés avec leur mot de passe.",
        "Cliquez sur <b>Copier la liste</b> pour tout mettre dans le presse-papier, et collez-le dans un document ou un e-mail.",
        "Transmettez à chaque adhérent son identifiant et son mot de passe ; invitez-le à le changer à sa première connexion.",
      ] },
      { img: 'g-csv-resultat.jpg', cap: "Le résultat d'un import : trois comptes créés, avec leur mot de passe provisoire." },
      { tip: "Si l'adresse e-mail figure dans le fichier, l'adhérent n'a même pas besoin du mot de passe provisoire : il peut choisir le sien avec « Mot de passe oublié ? » dès l'écran de connexion." },
      { warn: "Ne fermez pas le bandeau avant d'avoir noté les mots de passe. S'il est perdu, il faut redéfinir les mots de passe un par un avec le bouton <b>cadenas</b>." },
      { h3: 'Ce que dit l\'application en cas de problème' },
      { table: { head: ['Message', 'Cause et solution'], rows: [
        ['<i>Colonne « email » absente…</i>', "La première ligne ne contient pas les noms de colonnes — souvent parce que le fichier commence directement par les données, ou qu'il a été enregistré en <code>.xlsx</code>. Repartez du <b>Modèle CSV</b>."],
        ['<i>Ligne 4 : paulin existe déjà</i>', "Un compte porte déjà cet identifiant. La ligne est <b>ignorée</b>, les autres sont bien importées."],
        ["<i>Ligne 7 : l'adresse … est déjà utilisée</i>", "Cette adresse e-mail est déjà rattachée à un autre compte."],
        ['<i>Ligne 9 : …</i> (autre message)', "Le plus souvent un rôle mal orthographié dans <code>roles</code>. Corrigez, et réimportez <b>uniquement</b> les lignes en erreur."],
      ] } },
      { tip: "L'import est <b>rejouable sans risque</b> : les comptes déjà présents sont signalés et sautés, jamais écrasés. On peut donc corriger le fichier et le réimporter entièrement." },
    ],
  },
  {
    id: 'supprimer', t: 'Supprimer ou désactiver un compte',
    blocks: [
      { p: "Un compte qui a saisi des visites, des traitements ou des écritures <b>ne peut pas être supprimé</b> : ces enregistrements font partie de l'historique de l'association et doivent conserver leur auteur." },
      { steps: [
        "Cliquez sur la <b>corbeille</b> en bout de ligne.",
        "L'application vérifie ce que ce compte a laissé et vous l'annonce — par exemple « 42 visites et 3 écritures de trésorerie ».",
        "S'il n'a rien laissé, cliquez sur <b>Supprimer</b> : la suppression est définitive.",
        "Sinon, cliquez sur <b>Désactiver le compte</b> : la personne ne peut plus se connecter, mais tout son historique reste en place et garde son nom.",
      ] },
      { note: "Un compte désactivé se retrouve à tout moment en filtrant sur l'état <b>Inactif</b>, et se réactive depuis sa fiche (interrupteur <b>Actif</b>)." },
    ],
  },
  {
    id: 'reglages', t: "Réglages de l'association",
    blocks: [
      { steps: ["Menu de gauche → section <b>Réglages</b> → <b>Configuration</b>."] },
      { img: 'g-reglages.jpg', cap: "L'écran de configuration." },
      { h3: 'Accès' },
      { ul: [
        "<b>Trésorerie visible par tous les membres</b> — ouvre l'écran en lecture à tous les adhérents.",
        "<b>Journal d'activité visible par tous</b> — même principe pour l'audit.",
      ] },
      { h3: 'Envoi des e-mails (SMTP)' },
      { p: "Sans ce réglage, l'application ne peut envoyer <b>ni le lien de réinitialisation de mot de passe, ni le récapitulatif</b>." },
      { steps: [
        "Renseignez le <b>serveur SMTP</b>, le <b>port</b> et le <b>chiffrement</b> fournis par votre hébergeur de messagerie.",
        "Saisissez l'<b>identifiant</b> et le <b>mot de passe</b> du compte d'envoi.",
        "Indiquez l'<b>adresse d'expédition</b> et l'<b>adresse de l'application</b> (elle sert à construire les liens contenus dans les e-mails).",
        "<b>Enregistrez</b>, puis utilisez <b>Message de test</b> pour envoyer un courriel à votre propre adresse et vérifier que tout passe.",
      ] },
      { h3: 'Récapitulatif hebdomadaire' },
      { p: "Un résumé de la semaine envoyé par e-mail : choisissez les <b>destinataires</b>, le <b>jour</b>, l'<b>heure</b>, puis activez <b>Envoi actif</b>." },
      { warn: "Avec Gmail ou une messagerie équipée de la double authentification, il faut créer un <b>mot de passe d'application</b> dédié : le mot de passe habituel du compte sera refusé." },
    ],
  },
  {
    id: 'journal', t: "Journal d'activité",
    blocks: [
      { p: "L'historique horodaté de toutes les actions : qui a créé, modifié ou supprimé quoi, et quand. Il sert à retrouver l'origine d'un changement — sans accuser personne, simplement pour comprendre." },
      { img: 'g-journal.jpg', cap: 'Le journal.' },
      { p: "La barre de <b>filtres</b> permet de restreindre par auteur, par type d'action ou par période. Le journal n'est <b>pas modifiable</b>, y compris par un administrateur." },
    ],
  },
]
</script>
