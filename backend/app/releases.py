"""Journal des versions de l'application.

Source unique : c'est ce fichier qui alimente la page « Versions » de la
documentation **et** la notification envoyée aux adhérents lors d'une mise en
service. Ajouter une version ici suffit — au premier démarrage qui suit, tout
le monde reçoit la note de version.

Convention : la version la plus récente en tête.
"""

RELEASES = [
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
