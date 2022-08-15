import os
import re

teams = os.environ.get("TEAMS")
if teams is None:
    teams = (
        "Milan",
        "Inter",
        "Internazionale",
        "Napoli",
        "Juve",
        "Juventus",
        "Roma",
        "Lazio",
        "Spezia",
        "Udinese",
        "Sampdoria",
        "Sassuolo",
        "Hellas",
        "Verona",
        "Parma",
        "Atalanta",
        "Torino",
        "Fiorentina",
        "Bologna",
        "Cremonese",
        "Empoli",
        "Lecce",
        "Monza",
        "Salernitana",
    )
else:
    teams = teams.split(",")
teams_regex = re.compile(rf'({"|".join(teams)})\b')


blacklist = os.environ.get("BLACKLIST")
if blacklist is None:
    blacklist = (
        "Youth",
        "Primavera",
        "U\d+",
        "Inter Miami",
        "Inter Escaldes",
        "New England",
    )
else:
    blacklist = blacklist.split(",")
blacklist_regex = re.compile(rf'({"|".join(blacklist)})\b')
