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
    "Spezia",
    "Udinese",
    "Sampdoria",
    "Sassuolo",
    "Hellas",
    "Verona",
    "Cagliari",
    "Parma",
    "Benevento",
    "Atalanta",
    "Crotone",
    "Genoa",
    "Torino",
    "Fiorentina",
    "Bologna",
)

teams_regex = [re.compile(r"({})\b".format(t)) for t in teams]
