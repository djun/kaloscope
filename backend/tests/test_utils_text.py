"""Unit tests for text comparison utilities."""

from app.utils.text import natural_key


def test_natural_order():
    names = [
        "10.jpg",
        "2.jpg",
        "1.jpg",
        "01.jpg",
        "a10.jpg",
        "A2.jpg",
        "a2.jpg",
        "e\u03012.jpg",
        "é2.jpg",
    ]
    expected = [
        "01.jpg",
        "1.jpg",
        "2.jpg",
        "10.jpg",
        "A2.jpg",
        "a2.jpg",
        "a10.jpg",
        "e\u03012.jpg",
        "é2.jpg",
    ]

    assert sorted(names, key=natural_key) == expected
    assert sorted(reversed(names), key=natural_key) == expected
    assert natural_key("１.jpg")[0] == ("１.jpg",)
    assert natural_key("第十话")[0] == ("第十话",)
