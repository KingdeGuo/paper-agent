"""Tests for citation service."""

import pytest
from paper_agent.backend.services.citation_service import (
    generate_citation_key, format_authors_for_bibtex, doc_to_bibtex,
    parse_bibtex, generate_bibliography, CITATION_STYLES,
)


class TestCitationKey:
    def test_single_author_with_year(self):
        key = generate_citation_key(["Smith"], 2024)
        assert key == "Smith2024"

    def test_two_authors(self):
        key = generate_citation_key(["Smith", "Johnson"], 2024)
        assert key == "SmithJohnson2024"

    def test_no_year(self):
        key = generate_citation_key(["Zhang"], None)
        assert key.startswith("Zhang")

    def test_no_authors(self):
        key = generate_citation_key(None, 2024)
        assert "2024" in key

    def test_author_with_unicode(self):
        key = generate_citation_key(["García"], 2024)
        assert key == "García2024"


class TestBibTeXGeneration:
    def test_simple_document(self):
        bibtex = doc_to_bibtex(
            doc_id="abc-123",
            title="Deep Learning",
            authors=["Goodfellow, Ian"],
            year=2016,
            key="Goodfellow2016",
        )
        assert "@article{Goodfellow2016" in bibtex
        assert "Deep Learning" in bibtex
        assert "Goodfellow, Ian" in bibtex
        assert "year = {2016}" in bibtex

    def test_with_doi(self):
        bibtex = doc_to_bibtex(
            doc_id="abc", title="Test", authors=["Author"],
            year=2024, doi="10.1234/test",
        )
        assert "doi = {10.1234/test}" in bibtex

    def test_with_all_fields(self):
        bibtex = doc_to_bibtex(
            doc_id="1", title="Full Paper", authors=["A, B", "C, D"],
            year=2023, journal="Nature", volume="600",
            number="2", pages="100-110", doi="10.xx/yy",
        )
        for field in ["title", "author", "year", "journal", "volume", "number", "pages", "doi"]:
            assert field in bibtex


class TestBibTeXParsing:
    def test_parse_single_entry(self):
        bib = """@article{Key2024,
  title = {{Test Title}},
  author = {{Smith, John}},
  year = {2024}
}"""
        entries = parse_bibtex(bib)
        assert len(entries) == 1
        assert entries[0]["key"] == "Key2024"
        assert entries[0]["fields"]["title"] == "Test Title"

    def test_parse_multiple_entries(self):
        bib = """@article{Key1, title = {{First}}, year = {2024}}
@inproceedings{Key2, title = {{Second}}, year = {2023}}"""
        entries = parse_bibtex(bib)
        assert len(entries) == 2
        assert entries[0]["type"] == "article"
        assert entries[1]["type"] == "inproceedings"


class TestBibliography:
    def test_apa_style(self):
        entries = [{"authors": ["Smith, J"], "year": 2024, "title": "Test Paper", "journal": "Nature"}]
        bib = generate_bibliography(entries, style="apa")
        assert len(bib) > 0
        assert "Smith" in bib

    def test_ieee_style(self):
        entries = [{"authors": ["Smith, J"], "year": 2024, "title": "Test"}]
        bib = generate_bibliography(entries, style="ieee")
        assert "[" in bib  # IEEE uses numbered references

    def test_empty_entries(self):
        bib = generate_bibliography([])
        assert bib == ""

    def test_multiple_entries_sorted(self):
        entries = [
            {"authors": ["Zhang, W"], "year": 2024, "title": "B"},
            {"authors": ["Adams, R"], "year": 2023, "title": "A"},
        ]
        bib = generate_bibliography(entries, sort="author")
        assert bib.index("Adams") < bib.index("Zhang")


class TestCitationStyles:
    def test_all_styles_defined(self):
        assert "apa" in CITATION_STYLES
        assert "mla" in CITATION_STYLES
        assert "chicago" in CITATION_STYLES
        assert "ieee" in CITATION_STYLES
        assert "harvard" in CITATION_STYLES
        assert len(CITATION_STYLES) >= 5

    def test_style_names_are_readable(self):
        for sid, info in CITATION_STYLES.items():
            assert "name" in info
            assert len(info["name"]) > 3
