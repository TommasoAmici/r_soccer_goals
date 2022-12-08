import pytest

from main import Submission


@pytest.mark.parametrize(
    "submission,expected",
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
def test_is_video(submission: Submission, expected):
    assert submission.is_video() is expected


@pytest.mark.parametrize(
    "submission,expected",
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
def test_matches_wanted_teams(submission: Submission, expected):
    assert submission.matches_wanted_teams() is expected
