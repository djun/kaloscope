"""Unit tests for text utilities."""

import pytest

from app.utils.text import natural_key, truncate_utf8


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


@pytest.mark.parametrize(
    ("value", "limit", "marker", "expected"),
    [
        ("中文", 6, "…", "中文"),
        ("中文测试", 7, "…", "中…"),
        ("abcdef", 5, "...", "ab..."),
        ("中文", 4, "", "中"),
        ("中文", 2, "…", ""),
        ("abc", 0, "…", ""),
        ("", 0, "…", ""),
    ],
)
def test_truncate_utf8(value, limit, marker, expected):
    result = truncate_utf8(value, limit, marker=marker)

    assert result == expected
    assert len(result.encode()) <= limit


def test_truncate_negative():
    with pytest.raises(ValueError):
        truncate_utf8("text", -1)
