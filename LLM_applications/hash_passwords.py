from streamlit_authenticator import Hasher

# Replace with your plaintext passwords to get their bcrypt hashes
plaintext_passwords = ["password", "admin123"]

if __name__ == "__main__":
    print(Hasher(plaintext_passwords).generate())
