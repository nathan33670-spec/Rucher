"""Journal des versions de l'application.

Source unique : c'est ce fichier qui alimente la page « Versions » de la
documentation **et** la notification envoyée aux adhérents lors d'une mise en
service. Ajouter une version ici suffit — au premier démarrage qui suit, tout
le monde reçoit la note de version.

Convention : la version la plus récente en tête.
"""

RELEASES = [
    {
        "version": "1.10.0",
        "date": "2026-09-16",
        "title": "Rapprochement bancaire",
        "highlights": [
            "Un onglet « Rapprochement » dans la trésorerie : on pointe les écritures retrouvées sur le relevé, on saisit le solde de la banque, et l'écart apparaît tout de suite.",
            "La validation est refusée tant qu'une écriture n'est pas pointée ou qu'un écart subsiste — un rapprochement validé avec un écart ne vaudrait rien.",
            "Les administrateurs sont notifiés sur leur téléphone dès qu'un mois est validé, avec le solde arrêté et le nom du valideur.",
            "Un mois validé est figé ; seul un administrateur peut le rouvrir, et cela prévient les autres.",
            "À partir du 5 de chaque mois, un rappel hebdomadaire signale au bureau que le mois précédent n'est pas rapproché. Un mois ancien oublié remonte toujours dans le suivi.",
        ],
    },
    {
        "version": "1.9.0",
        "date": "2026-09-15",
        "title": "La trésorerie se remplit depuis SumUp",
        "highlights": [
            "Un bouton « Synchroniser SumUp » récupère les encaissements par carte et les inscrit en recettes, les remboursements en dépenses.",
            "Les commissions prélevées par SumUp, les ajustements de solde et les retours de prélèvement remontent aussi tout seuls, en dépenses.",
            "Un remboursement figure des deux côtés chez SumUp — transactions et retenue sur virement — et n'est compté qu'une fois : les dépenses ne sont pas gonflées.",
            "Les achats réglés avec la carte du compte professionnel s'importent depuis l'export CSV du relevé : SumUp n'expose pas le compte pro par son API, c'est la seule voie possible.",
            "Les deux imports sont rejouables : chaque écriture garde la référence SumUp dont elle provient, rien n'est jamais créé en double.",
            "Les écritures venues de SumUp portent un repère dans la liste, pour les distinguer de la saisie à la main.",
        ],
    },
    {
        "version": "1.8.6",
        "date": "2026-09-14",
        "title": "Relancer une notification sur un événement",
        "highlights": [
            "Un bouton « Notifier » sur chaque événement envoie une nouvelle notification sur les téléphones, quand vous le décidez : la veille d'une sortie, ou pour un détail de dernière minute.",
            "Ouvert à l'organisateur de l'événement — même s'il n'est pas administrateur — et aux administrateurs.",
            "Un message libre peut accompagner la relance ; sinon la date, le lieu et l'invitation à répondre sont repris.",
            "La date du dernier envoi est rappelée avant de relancer, pour ne pas notifier deux fois la même chose.",
        ],
    },
    {
        "version": "1.8.5",
        "date": "2026-09-14",
        "title": "Signalement général, sans passer par une ruche",
        "highlights": [
            "Le bouton « Signaler » propose désormais deux types : sur une ruche, comme avant, ou général — clôture, accès, matériel commun, voisinage, point à passer au bureau.",
            "Un signalement général prévient les administrateurs et les responsables de rucher, et n'écrit rien dans l'historique d'une ruche.",
            "En désignant un rucher, les responsables de ses ruches sont prévenus en plus : ce sont eux qui sont sur place.",
        ],
    },
    {
        "version": "1.8.4",
        "date": "2026-09-14",
        "title": "Les e-mails partent sans réglage préalable",
        "highlights": [
            "L'envoi des identifiants et le « mot de passe oublié » ne réclament plus que l'adresse du site soit saisie dans la configuration : elle est déduite de l'adresse par laquelle vous consultez l'application.",
            "Le champ « Adresse de l'application » reste prioritaire s'il est rempli, et se propose désormais pré-rempli dans la configuration.",
        ],
    },
    {
        "version": "1.8.3",
        "date": "2026-09-14",
        "title": "Renuméroter les ruches devient possible",
        "highlights": [
            "Donner à une ruche un numéro déjà pris propose désormais d'échanger les deux numéros, au lieu de refuser sans issue.",
            "Renuméroter un rucher entier se fait ainsi de proche en proche, sans avoir à libérer un numéro au préalable — c'était impossible depuis que toutes les ruches portent un numéro.",
            "L'encadré annonce quelle ruche détient le numéro voulu et lequel elle recevra en échange.",
        ],
    },
    {
        "version": "1.8.2",
        "date": "2026-09-14",
        "title": "Le numéro de ruche s'affiche enfin partout",
        "highlights": [
            "Le numéro identifie désormais la ruche sur tous les écrans — plan, visite, historique, sanitaire, miellée — et le nom vient en complément : « 12 — La bleue ».",
            "Le numéro se modifiait déjà, mais le nom passait avant lui à l'affichage : la correction ne se voyait nulle part, on croyait la modification impossible.",
            "Toutes les ruches ont maintenant un numéro modifiable. Celles qui n'en avaient pas parce qu'elles portaient un numéro d'apiculteur le reprennent tel quel ; les autres reçoivent le premier numéro libre.",
            "Dans la fiche d'une ruche, le n° de ruche est passé en premier champ, devant le nom.",
        ],
    },
    {
        "version": "1.8.1",
        "date": "2026-09-14",
        "title": "Envoyer ses identifiants à un adhérent",
        "highlights": [
            "Un bouton « enveloppe » sur l'écran Utilisateurs envoie à un adhérent son nom d'utilisateur, un mot de passe et le lien de l'application, en une seule manipulation.",
            "Le mot de passe enregistré étant chiffré, l'e-mail contient un nouveau mot de passe provisoire : l'ancien cesse de fonctionner et la personne choisit le sien une fois connectée.",
            "Si le serveur de messagerie refuse le message, le compte garde son mot de passe : rien ne change tant que l'e-mail n'est pas parti.",
        ],
    },
    {
        "version": "1.8.0",
        "date": "2026-09-13",
        "title": "Documentation refaite en six chapitres",
        "highlights": [
            "Le guide de l'application est découpé en six chapitres illustrés, écrits pas à pas pour quelqu'un qui découvre l'outil : où cliquer, dans quel ordre, et ce que fait chaque champ.",
            "Le format du fichier CSV d'import des adhérents est enfin documenté, colonne par colonne, avec un exemple complet et la liste des messages d'erreur.",
            "L'écran Utilisateurs propose un bouton « Modèle CSV » : un fichier prêt à remplir, réimportable tel quel.",
            "Les comptes créés par import reçoivent chacun un mot de passe tiré au hasard, affiché une seule fois — ils partageaient auparavant le même mot de passe connu.",
        ],
    },
    {
        "version": "1.7.1",
        "date": "2026-09-13",
        "title": "Suppression de compte expliquée",
        "highlights": [
            "Supprimer un compte qui a saisi des données affichait une erreur technique ; l'application dit maintenant ce qui le retient et propose de désactiver le compte.",
            "Désactiver conserve tout l'historique de la personne et l'empêche simplement de se connecter.",
            "La liste des adhérents se filtre par nom, rôle ou état.",
        ],
    },
    {
        "version": "1.7.0",
        "date": "2026-09-13",
        "title": "Numéros de ruche libres et correction des visites",
        "highlights": [
            "Chaque ruche porte un numéro que vous choisissez, modifiable à tout moment — plus aucun numéro technique à l'écran.",
            "Chacun peut corriger ses propres visites depuis l'historique.",
            "Un administrateur peut corriger ou supprimer n'importe quelle visite ; la correction est inscrite au journal.",
        ],
    },
    {
        "version": "1.6.0",
        "date": "2026-09-13",
        "title": "Adresse e-mail et mot de passe oublié",
        "highlights": [
            "Chaque adhérent enregistre son adresse e-mail depuis « Mes coordonnées ».",
            "Un lien « Mot de passe oublié ? » permet de le réinitialiser soi-même : un e-mail arrive avec un lien valable une heure, utilisable une seule fois.",
            "Changer son mot de passe par ce lien déconnecte tous les autres appareils.",
        ],
    },
    {
        "version": "1.5.0",
        "date": "2026-09-05",
        "title": "Numéro de ruche et transhumance",
        "highlights": [
            "Chaque ruche a désormais son propre numéro, distinct du NAPI : un numéro déjà utilisé est refusé en indiquant quelle ruche le porte.",
            "Le NAPI reste le numéro d'apiculteur du propriétaire, commun à toutes ses ruches.",
            "Une ruche se déplace d'un rucher à un autre : elle emporte tout son historique, seule sa position sur le plan est à refaire.",
        ],
    },
    {
        "version": "1.4.0",
        "date": "2026-09-05",
        "title": "Notes de version, filtres et pertes de miel",
        "highlights": [
            "Une cloche en haut de l'écran rassemble toutes les notifications reçues, consultables à tout moment.",
            "Chaque nouvelle version de l'application est annoncée avec ses nouveautés.",
            "Les historiques (visites, sanitaire, trésorerie, journal) se filtrent : par ruche, par personne, par période.",
            "Le stock de miel se corrige à la main : fond de cuve, casse d'un pot, écart d'inventaire.",
        ],
    },
    {
        "version": "1.3.0",
        "date": "2026-09-05",
        "title": "Visite rapide pré-remplie",
        "highlights": [
            "La visite rapide repart des valeurs de la dernière visite : plus besoin de tout ressaisir.",
            "Un bandeau indique d'où viennent les valeurs et permet de repartir de zéro.",
        ],
    },
    {
        "version": "1.2.0",
        "date": "2026-09-05",
        "title": "Signalement, inventaire personnel et messages d'erreur",
        "highlights": [
            "Nouveau bouton « Signaler un problème » : les responsables de la ruche sont prévenus immédiatement.",
            "Chaque adhérent gère son propre matériel dans l'inventaire, invisible des autres.",
            "Chacun règle ses propres conditions météo de sortie.",
            "Compteur de cadres de corps dans la visite ; récolte et traitement se saisissent dans leurs rubriques dédiées.",
            "Les messages d'erreur expliquent enfin ce qui ne va pas.",
            "Notifications push réparées : elles ne pouvaient pas partir.",
        ],
    },
    {
        "version": "1.1.0",
        "date": "2026-09-04",
        "title": "Changement de rôle",
        "highlights": [
            "Un administrateur peut travailler « en usager » depuis la puce en haut à droite, pour éviter les fausses manœuvres.",
            "Le plan du rucher ne bouge plus en dehors du mode édition.",
        ],
    },
    {
        "version": "1.0.0",
        "date": "2026-08-01",
        "title": "Première mise en service",
        "highlights": [
            "Ruchers, ruches, visites de terrain hors connexion, inventaire, miellée, suivi sanitaire, trésorerie, météo et événements.",
        ],
    },
]

CURRENT_VERSION = RELEASES[0]["version"]


def latest() -> dict:
    return RELEASES[0]
