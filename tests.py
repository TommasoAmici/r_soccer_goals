import pytest

from main import Submission, is_video, matches_wanted_teams


@pytest.mark.parametrize(
    "input,expected",
    [
        (
            Submission(
                "yi4g0d",
                "streamja/best-goal",
                "Juventus 1-[2] Torino Belotti great goal",
                "",
            ),
            True,
        ),
        (
            Submission(
                "yi4g0d",
                "bongbong.com",
                "Juventus 1-[2] Torino Belotti great goal",
                "media",
            ),
            True,
        ),
        (
            Submission(
                "yi4g0d",
                "gazzetta.it",
                "Juventus Primavera [7]-2 Albinoleffe Dybala",
                "",
            ),
            False,
        ),
    ],
)
def test_is_video(input, expected):
    assert is_video(input) is expected


@pytest.mark.parametrize(
    "input,expected",
    [
        (
            Submission(
                "yi4g0d",
                "streamja/best-goal",
                "Juventus 1-[2] Torino Belotti great goal",
                "",
            ),
            True,
        ),
        (
            Submission(
                "yi4g0d",
                "gazzetta.it",
                "Juventus Primavera [7]-2 Albinoleffe Dybala",
                "",
            ),
            False,
        ),
    ],
)
def test_matches_wanted_teams(input, expected):
    assert matches_wanted_teams(input) is expected
