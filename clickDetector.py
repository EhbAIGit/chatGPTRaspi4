from pynput import mouse

def on_move(x, y):
    print(f'Muis verplaatst naar ({x}, {y})')

def on_click(x, y, button, pressed):
    if pressed:
        print(f'Muisklik gedetecteerd op positie ({x}, {y}) met knop {button}')
    else:
        print(f'Muisknop losgelaten op positie ({x}, {y}) met knop {button}')

def on_scroll(x, y, dx, dy):
    print(f'Scrollen gedetecteerd op positie ({x}, {y}) met delta ({dx}, {dy})')

# Met de muis listener
with mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll) as listener:
    listener.join()
