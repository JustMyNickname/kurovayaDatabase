import gui
from werkzeug.security import generate_password_hash, check_password_hash  # For password hashing

def main():
    app = gui.App()
    app.mainloop()

if __name__ == '__main__':
    main()
