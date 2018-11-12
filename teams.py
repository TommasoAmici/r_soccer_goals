import re


teams = (
    "Milan",
    "Inter",
    "Internazionale",
    "Napoli",
    "Juve",
    "Juventus",
    "Roma",
    "Lazio",
    "Spal",
    "Udinese",
    "Sampdoria",
    "Sassuolo",
    "Empoli",
    "Cagliari",
    "Parma",
    "Frosinone",
    "Atalanta",
    "Chievo",
    "Genoa",
    "Torino",
    "Fiorentina",
    "Bologna",
)

teams_regex = [re.compile(r"({})\b".format(t)) for t in teams]
