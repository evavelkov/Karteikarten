from pyfiglet import Figlet

from _menu import menu

f = Figlet(font='doom')

def  StartFlashCards():
    print(f.renderText('FlashCards'))
    menu()
    

