from pyfiglet import Figlet
from start_flashcards import start_flashcards
#from create_flashcards import create_flashcards
#from edit_flashcards import edit_flashcards
#from delete_flashcards import delete_flashcards

f = Figlet(font='doom')

def menu(): 
    print(f.renderText('Menu'))

    while True:
        print("1. Start FlashCards")
        print("2. Create FlashCards")
        print("3. Edit FlashCards")
        print("4. Delete FlashCards")
        print("5. Exit")

        choice = input("Enter your choice (1-5): ")
        if choice == '1':
            start_flashcards()
        elif choice == '2':
            create_flashcards() 
        elif choice == '3':
            edit_flashcards()
        elif choice == '4': 
            delete_flashcards()
        elif choice == '5':
            print("Exiting the program.")
            print(f.renderText('Goodbye!'))
            break   
        else: 
            print("Invalid choice. Please try again.")
