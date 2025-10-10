from __future__ import annotations
import re
from datetime import datetime, date


def ask_national_id() -> str:
    """Demande un identifiant national valide (AA12345)."""
    pattern = r"^[A-Z]{2}\d{5}$"
    while True:
        player_id = input("Identifiant national (2 lettres + 5 chiffres) : ").strip().upper()
        if re.match(pattern, player_id):
            return player_id
        print("Format invalide. L'identifiant doit comporter 2 lettres suivies de 5 chiffres (ex: AB12345).")


def ask_birthdate() -> str:
    """Demande une date de naissance valide (YYYY-MM-DD) et vérifie la majorité (18 ans ou plus)."""
    while True:
        birthdate_str = input("Date de naissance (YYYY-MM-DD) : ").strip()
        try:
            birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
        except Exception:
            print("Format invalide. Exemple attendu : 2000-05-21.")
            continue
        today = date.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        if age < 18:
            print(f"Le joueur doit être majeur (18 ans ou plus). Âge actuel : {age}.")
            continue
        return birthdate_str


def ask_tournament_dates() -> tuple[str, str]:
    """Demande deux dates valides (début et fin), avec fin strictement postérieure à début."""
    while True:
        start_str = input("Date de début (YYYY-MM-DD) : ").strip()
        if start_str == "":
            start_str = date.today().isoformat()
            print(f"Date de début par défaut : {start_str}")
        end_str = input("Date de fin (YYYY-MM-DD) : ").strip()
        if end_str == "":
            end_str = start_str
            print(f"Date de fin par défaut : {end_str}")
        try:
            start = datetime.strptime(start_str, "%Y-%m-%d").date()
            end = datetime.strptime(end_str, "%Y-%m-%d").date()
        except Exception:
            print("Format invalide. Exemple attendu : 2025-10-03.")
            continue
        if end <= start:
            print("La date de fin doit être identique ou postérieure à la date de début.")
            continue
        return start_str, end_str
