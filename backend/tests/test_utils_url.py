"""Unit tests for URL query utilities."""

from app.utils.url import query_param


class TestQueryParam:
    def test_append_without_query(self):
        assert query_param("https://example.com/video", "lang=zh-CN") == (
            "https://example.com/video?lang=zh-CN"
        )

    def test_append_with_query(self):
        assert query_param("https://example.com/video?page=1", "lang=zh-CN") == (
            "https://example.com/video?page=1&lang=zh-CN"
        )

    def test_skip_existing_key(self):
        assert query_param("https://example.com/video?lang=en", "lang=zh-CN") == (
            "https://example.com/video?lang=en"
        )

    def test_keep_fragment(self):
        assert query_param("https://example.com/video#player", "lang=zh-CN") == (
            "https://example.com/video?lang=zh-CN#player"
        )

    def test_empty_url(self):
        assert query_param("", "lang=zh-CN") == ""

    def test_empty_param(self):
        assert (
            query_param("https://example.com/video", "") == "https://example.com/video"
        )

    def test_invalid_param(self):
        assert query_param("https://example.com/video", "lang") == (
            "https://example.com/video"
        )

    def test_empty_key(self):
        assert query_param("https://example.com/video", "=zh-CN") == (
            "https://example.com/video"
        )
