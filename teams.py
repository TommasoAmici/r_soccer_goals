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
    "SPAL",
    "Udinese",
    "Sampdoria",
    "Sassuolo",
    "Hellas",
    "Verona",
    "Cagliari",
    "Parma",
    "Lecce",
    "Atalanta",
    "Brescia",
    "Genoa",
    "Torino",
    "Fiorentina",
    "Bologna",
)

teams_regex = [re.compile(r"({})\b".format(t)) for t in teams]
