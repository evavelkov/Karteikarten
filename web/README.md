# Karteikarten – Webseite

Flask + SQLite. Kartensets enthalten Karten und können in Ordnern abgelegt werden.

## Starten

```
pip install flask
python web/app.py
```

Dann im Browser http://127.0.0.1:5000 öffnen.

Beim ersten Start wird `web/karteikarten.db` angelegt und die Vokabeln aus
`data/flashcards.csv` werden als Ordner „Französisch“ → Set „Grundwortschatz“ importiert.

## Seiten

- **Startseite** – Begrüßung, Auswahl zwischen *Ordner* und *Kartensets*
- **Ordner** – Übersicht; „+ Ordner erstellen“ öffnet ein Pop-up für Name und bestehende Sets
- **Ordner-Detail** – Sets im Ordner, „+ Neues Set“, „Sets hinzufügen“ (Pop-up), Set aus Ordner entfernen
- **Kartensets** – alle Sets; „+ Neues Set erstellen“ öffnet eine Seite für Name, Ordner und beliebig viele Karten
- **Set** – Karten hinzufügen, bearbeiten (Zeile anklicken), löschen; Set umbenennen oder verschieben
- **Lernen** – Karte umdrehen, „Gewusst“ / „Nochmal“, mischen, Seiten tauschen
  - Tasten: Leertaste = umdrehen, 1 = nochmal, 2 = gewusst

## Datenmodell

`folders` ← `card_sets.folder_id` (optional) ← `cards.set_id`

Ein Set liegt in höchstens einem Ordner. Wird ein Ordner gelöscht, bleiben seine Sets
erhalten. Wird ein Set gelöscht, werden seine Karten mitgelöscht.
