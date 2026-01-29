import hashlib
import os
import sqlite3


class Database:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), "djambi.db")
        self.init_database()

    def init_database(self):
        """Initialise la base de données et crée les tables si elles n'existent pas"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Création de la table users
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    games_played INTEGER DEFAULT 0,
                    games_won INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.commit()

    def hash_password(self, password):
        """Hash le mot de passe avec SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username, password):
        """Crée un nouvel utilisateur"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                password_hash = self.hash_password(password)
                cursor.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password_hash),
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False  # L'utilisateur existe déjà

    def verify_user(self, username, password):
        """Vérifie les identifiants de l'utilisateur"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            password_hash = self.hash_password(password)
            cursor.execute(
                "SELECT id FROM users WHERE username = ? AND password_hash = ?",
                (username, password_hash),
            )
            return cursor.fetchone() is not None

    def update_stats(self, username, won=False):
        """Met à jour les statistiques de l'utilisateur"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET games_played = games_played + 1, games_won = games_won + ? WHERE username = ?",
                (1 if won else 0, username),
            )
            conn.commit()

    def get_user_stats(self, username):
        """Récupère les statistiques d'un utilisateur"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT games_played, games_won FROM users WHERE username = ?",
                (username,),
            )
            return cursor.fetchone()
