import os
import re

default_teams = (
    "Atalanta",
    "Benevento",
    "Bologna",
    "Cagliari",
    "Como",
    "Cremonese",
    "Crotone",
    "Empoli",
    "Fiorentina",
    "Frosinone",
    "Genoa",
    "Inter",
    "Juventus",
    "Lazio",
    "Lecce",
    "Milan",
    "Monza",
    "Napoli",
    "Parma",
    "Pisa",
    "Roma",
    "Salernitana",
    "Sampdoria",
    "Sassuolo",
    "Spezia",
    "Torino",
    "Udinese",
    "Venezia",
    "Verona",
)


def get_teams():
    teams = os.environ.get("TEAMS")
    if teams is None or teams == "":
        return default_teams
    return teams.split(",")


teams_regex = re.compile(rf'({"|".join(get_teams())})\b')


default_blacklist = (
    "Youth",
    "Primavera",
    r"U\d+",
    "Inter Miami",
    "Inter Escaldes",
    "New England",
)


def get_blacklist():
    blacklist = os.environ.get("BLACKLIST")
    if blacklist is None or blacklist == "":
        return default_blacklist
    return blacklist.split(",")


blacklist_regex = re.compile(rf'({"|".join(get_blacklist())})\b')
