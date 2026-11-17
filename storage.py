import csv
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "flashcards.csv"
FIELDNAMES = ["question", "answer"]

def load_cards():
    if not DATA_FILE.exists():
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)

            if reader.fieldnames != FIELDNAMES:
                print("Fehler: Die CSV braucht die Spalten 'question,answer'.")
                return []

            return list(reader)

    except PermissionError:
        print("Fehler: Kein Zugriff auf die Datei. Ist sie vielleicht in Excel offen?")
    except (csv.Error, UnicodeDecodeError):
        print("Fehler: Die CSV-Datei ist beschädigt oder hat ein falsches Format.")

    return []

def save_cards(cards):
    try:
        DATA_FILE.parent.mkdir(exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(cards)
        return True

    except PermissionError:
        print("Fehler: Speichern nicht möglich. Ist die Datei in Excel offen?")
        return False