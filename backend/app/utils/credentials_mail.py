"""E-mail d'envoi des identifiants à un adhérent.

Le mot de passe stocké est une empreinte Argon2 : il est **impossible** de
relire celui que la personne avait choisi. Envoyer « son » mot de passe veut
donc nécessairement dire en tirer un nouveau et le lui transmettre — c'est ce
que fait cet e-mail, avec le lien de l'application pour qu'elle n'ait rien à
chercher.

Le message reste volontairement court : un identifiant, un mot de passe, un
bouton. C'est ce qu'on relit sur un téléphone, debout, entre deux ruches.
"""

from app.models.user import User


def build_email(user: User, password: str, app_url: str) -> tuple[str, str, str]:
    """(sujet, html, texte) du message contenant les identifiants."""
    who = (user.first_name or "").strip() or user.email
    link = (app_url or "").rstrip("/")
    connexion = f"{link}/login"

    subject = "Rucher Manager — vos identifiants de connexion"
    html = (
        '<div style="font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;'
        'max-width:520px;margin:0 auto;padding:24px;color:#2B2520;">'
        '<div style="text-align:center;font-size:30px;">🐝</div>'
        f'<h2 style="text-align:center;font-size:19px;">Bonjour {who},</h2>'
        '<p style="line-height:1.6;">Voici vos identifiants pour vous connecter '
        'à Rucher Manager, l\'application de suivi des ruches de l\'association.</p>'
        '<table style="width:100%;border-collapse:collapse;margin:20px 0;'
        'background:#FBF7F0;border-radius:10px;">'
        '<tr><td style="padding:12px 16px;color:#6B5F52;font-size:14px;">'
        'Nom d\'utilisateur</td>'
        f'<td style="padding:12px 16px;font-weight:700;font-family:monospace;">'
        f'{user.email}</td></tr>'
        '<tr><td style="padding:12px 16px;color:#6B5F52;font-size:14px;">'
        'Mot de passe</td>'
        f'<td style="padding:12px 16px;font-weight:700;font-family:monospace;">'
        f'{password}</td></tr></table>'
        '<p style="text-align:center;margin:28px 0;">'
        f'<a href="{connexion}" style="background:#B8860B;color:#fff;'
        'text-decoration:none;padding:13px 26px;border-radius:8px;'
        'display:inline-block;font-weight:600;">Ouvrir l\'application</a></p>'
        '<p style="line-height:1.6;font-size:14px;color:#4E443A;">'
        'Ce mot de passe est <b>provisoire</b> : une fois connecté, cliquez sur '
        'votre prénom en haut à droite, puis sur « Changer mon mot de passe ».</p>'
        '<p style="line-height:1.6;font-size:14px;color:#4E443A;">'
        'Sur téléphone, vous pouvez installer l\'application sur votre écran '
        'd\'accueil : elle s\'ouvre alors en plein écran et fonctionne même sans '
        'réseau au rucher.</p>'
        '<p style="font-size:12px;color:#8A7F72;word-break:break-all;">'
        f'Si le bouton ne fonctionne pas, copiez cette adresse : {connexion}</p>'
        '</div>'
    )
    text = (
        f"Bonjour {who},\n\n"
        "Voici vos identifiants pour vous connecter à Rucher Manager,\n"
        "l'application de suivi des ruches de l'association.\n\n"
        f"  Nom d'utilisateur : {user.email}\n"
        f"  Mot de passe      : {password}\n\n"
        f"Adresse de l'application : {connexion}\n\n"
        "Ce mot de passe est provisoire : une fois connecté, cliquez sur votre\n"
        "prénom en haut à droite, puis sur « Changer mon mot de passe ».\n\n"
        "Sur téléphone, vous pouvez installer l'application sur votre écran\n"
        "d'accueil : elle s'ouvre alors en plein écran et fonctionne même sans\n"
        "réseau au rucher.\n"
    )
    return subject, html, text
