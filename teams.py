import os
import re

default_teams = (
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
