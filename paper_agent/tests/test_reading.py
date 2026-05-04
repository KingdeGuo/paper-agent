"""Tests for reading service."""

import pytest
from paper_agent.backend.api.routes.reading import READING_STATUSES


class TestReadingStatuses:
    def test_statuses_defined(self):
        assert len(READING_STATUSES) == 5
        assert "to_read" in READING_STATUSES
        assert "reading" in READING_STATUSES
        assert "read" in READING_STATUSES
        assert "skipped" in READING_STATUSES
        assert "reference" in READING_STATUSES

    def test_no_duplicates(self):
        assert len(READING_STATUSES) == len(set(READING_STATUSES))
