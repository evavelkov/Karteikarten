def start_flashcards():
    from storage import load_cards
    cards = load_cards()

    if not cards:
        print("Keine Flashcards gefunden. Bitte erstelle welche.")
        return

    for card in cards:
        print(f"Frage: {card['question']}")
        input("Drücke Enter, um die Antwort zu sehen...")
        print(f"Antwort: {card['answer']}\n")
        input("Drücke Enter, um zur nächsten Karte zu gehen...")