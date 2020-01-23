import getpass

from flask_script import Command

from src.app.model import SimpleAuth, MIN_PASSWORD_LEN, LTMSDatabaseException


class CreateAdmin(Command):
    """
    create initial admin user
    """
    def run(self):  # pylint: disable=E0202,W0221
        """ invoked by the command """
        print("Creating a new admin user...")
        email = input("E-mail Address: ")
        password = getpass.getpass()
        confirm_password = getpass.getpass('Confirm: ')

        if not password == confirm_password:
            print("passwords do not match")
            return 1

        if len(password) < MIN_PASSWORD_LEN:
            print(
                f"Please use a password containing at least {MIN_PASSWORD_LEN} characters.")
            return 1
        else:
            try:
                SimpleAuth.create_admin(email, password)
            except LTMSDatabaseException as e:
                print(e)
                return 1
        return 0
