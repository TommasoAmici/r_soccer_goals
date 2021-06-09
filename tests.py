from dataclasses import dataclass

import pytest

from .main import is_goal, is_video


@dataclass
class Post:
    title: str
    url: str

    def __init__(self, title: str, url: str):
        self.title = title
        self.url = url


def test_is_goal():
    p = Post("Juventus 1-[2] Torino Belotti great goal", "streamja/best-goal")
    assert is_goal(p) is True
    p = Post("Juventus Primavera [7]-2 Albinoleffe Dybala", "gazzetta.it")
    assert is_goal(p) is False


def test_is_video():
    p = Post("Juventus 1-[2] Torino Belotti great goal", "streamja/best-goal")
    assert is_video(p) is True
    p = Post("Juventus Primavera [7]-2 Albinoleffe Dybala", "gazzetta.it")
    assert is_video(p) is False
