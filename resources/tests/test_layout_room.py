# resources\tests\test_layout_room.py
"""Pruebas de la escalera de anchos `Room` del frontend."""

import pytest

from frontend.common import Room


@pytest.mark.parametrize(
    "width, expected",
    [
        (0, Room.TIGHT),
        (479, Room.TIGHT),
        (480, Room.SNUG),
        (649, Room.SNUG),
        (650, Room.ROOMY),
        (949, Room.ROOMY),
        (950, Room.WIDE),
        (1099, Room.WIDE),
        (1100, Room.VAST),
        (1279, Room.VAST),
        (1280, Room.HUGE),
        (4000, Room.HUGE),
    ],
)
def test_of_classifies_the_width_at_each_step_boundary(width, expected):
    assert Room.of(width) is expected


def test_fits_and_below_are_complementary_at_every_step():
    for width in (100, 480, 700, 950, 1100, 1500):
        room = Room.of(width)
        for step in Room:
            assert room.fits(step) is not room.below(step)


def test_a_wider_room_fits_every_lower_step():
    assert Room.of(1000).fits(Room.ROOMY)
    assert Room.of(1000).fits(Room.WIDE)
    assert not Room.of(1000).fits(Room.VAST)
