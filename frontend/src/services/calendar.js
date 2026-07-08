/**
 * Ajout au calendrier — compatible iOS (Apple Calendar), Android et Google Agenda.
 *
 * Les événements sont saisis en heure locale (« wall clock »). On les émet en
 * heure flottante (sans fuseau) : chaque agenda les interprète dans le fuseau
 * de l'appareil, ce qui correspond à l'heure saisie par l'administrateur.
 */

// Date JS → "YYYYMMDDTHHMMSS" (composantes locales, heure flottante)
function fmtLocal(d) {
  const p = (n) => String(n).padStart(2, '0')
  return (
    d.getFullYear() +
    p(d.getMonth() + 1) +
    p(d.getDate()) +
    'T' +
    p(d.getHours()) +
    p(d.getMinutes()) +
    p(d.getSeconds())
  )
}

// Fin par défaut : +2h si non renseignée.
function resolveEnd(startStr, endStr) {
  const start = new Date(startStr)
  const end = endStr ? new Date(endStr) : new Date(start.getTime() + 2 * 3600 * 1000)
  return { start, end }
}

function icsEscape(s) {
  return String(s || '')
    .replace(/\\/g, '\\\\')
    .replace(/;/g, '\\;')
    .replace(/,/g, '\\,')
    .replace(/\r?\n/g, '\\n')
}

/** Construit le contenu d'un fichier .ics pour un événement. */
export function buildICS(ev) {
  const { start, end } = resolveEnd(ev.start_at, ev.end_at)
  const stamp = fmtLocal(new Date())
  const uid = `rucher-event-${ev.id}-${stamp}@rucher`
  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Rucher Manager//FR',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'BEGIN:VEVENT',
    `UID:${uid}`,
    `DTSTAMP:${stamp}`,
    `DTSTART:${fmtLocal(start)}`,
    `DTEND:${fmtLocal(end)}`,
    `SUMMARY:${icsEscape(ev.title)}`,
    ev.description ? `DESCRIPTION:${icsEscape(ev.description)}` : null,
    ev.location ? `LOCATION:${icsEscape(ev.location)}` : null,
    'END:VEVENT',
    'END:VCALENDAR',
  ].filter(Boolean)
  return lines.join('\r\n')
}

/** Télécharge le .ics (Apple Calendar / Android / Outlook…). */
export function downloadICS(ev) {
  const blob = new Blob([buildICS(ev)], { type: 'text/calendar;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${(ev.title || 'evenement').replace(/[^\w\-]+/g, '_')}.ics`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

/** Lien « Ajouter à Google Agenda ». */
export function googleCalendarUrl(ev) {
  const { start, end } = resolveEnd(ev.start_at, ev.end_at)
  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text: ev.title || 'Événement',
    dates: `${fmtLocal(start)}/${fmtLocal(end)}`,
    details: ev.description || '',
    location: ev.location || '',
  })
  return `https://calendar.google.com/calendar/render?${params.toString()}`
}
