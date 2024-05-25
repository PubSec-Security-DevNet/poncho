import bcrypt
import sys

def generatePassword(password):
    try:
        # Generate a salt and hash the password with bcrypt
        salt = bcrypt.gensalt()
        hashedPassword = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashedPassword.decode('utf-8')
    except Exception as e:
        print("Error generating hashed password:", e)
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <password>")
        sys.exit(1)

    password = sys.argv[1]
    hashedPassword = generatePassword(password)
    if hashedPassword:
        print("Hashed Password:", hashedPassword)