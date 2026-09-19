"""Tests for SEO Crawler (Phase 1 - Core Infrastructure)

Covers:
- URL discovery from registry
- URL deduplication
- URL normalization
- Canonical/hreflang extraction
- Indexability detection
- Domain boundary enforcement
- Crawl limits
"""

from pathlib import Path
from urllib.parse import urlparse

import pytest

from app.services.seo_crawler import (
    SeoSrawler,
    CrawlResult,
    CrawlConfig,
    URLNormalizer,
    RobotsParser,
)


# ── Test Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def crawler():
    """Create a crawler instance for testing."""
    return SeoSrawler(contracts_dir=Path("app/data/converters"))


@pytest.fixture
def config():
    """Create a test configuration."""
    return CrawlConfig(
        base_domain="converigo.com",
        max_urls=100,
        exclude_paths=["/api", "/admin"],
    )


# ── URL Normalization Tests ──────────────────────────────────────────────────────

def test_url_normalizer_removes_trailing_slash():
    """Verify trailing slash removal."""
    normalizer = URLNormalizer()
    assert normalizer.normalize("https://converigo.com/tools/") == "https://converigo.com/tools"
    assert normalizer.normalize("https://converigo.com/") == "https://converigo.com/"


def test_url_normalizer_sorts_params():
    """Verify query parameter sorting."""
    normalizer = URLNormalizer()
    url1 = normalizer.normalize("https://converigo.com/tools?q=pdf&a=1")
    url2 = normalizer.normalize("https://converigo.com/tools?a=1&q=pdf")
    assert url1 == url2


def test_url_normalizer_has_parameters():
    """Verify parameter detection."""
    normalizer = URLNormalizer()
    assert normalizer.has_parameters("https://converigo.com/?lang=en")
    assert not normalizer.has_parameters("https://converigo.com/tools/jpg-to-pdf")


def test_url_normalizer_get_domain():
    """Verify domain extraction."""
    normalizer = URLNormalizer()
    assert normalizer.get_domain("https://converigo.com/tools") == "converigo.com"
    assert normalizer.get_domain("http://example.com") == "example.com"

# ── Crawler Tests ──────────────────────────────────────────────────────

def test_crawler_discover_from_registry(crawler):
    """Verify URL discovery from registry."""
    urls = crawler.discover_from_registry()
    assert len(urls) > 0
    assert all("/tools/" in url for url in urls)


def test_crawler_deduplication(crawler):
    """Verify URL deduplication prevents duplicate requests."""
    urls = [
        "/tools/mp4-to-mp3",
        "/tools/mp4-to-mp3",
        "/tools/jpg-to-pdf",
        "/tools/mp4-to-mp3/",
    ]
    
    results = crawler.crawl(test_urls=urls)
    
    # Should only crawl unique URLs
    crawled_urls = [r.url for r in results]
    assert len(crawled_urls) <= 3  # At most 3 unique URLs


def test_crawler_url_normalization():
    """Verify URL normalization prevents duplicate requests."""
    normalizer = URLNormalizer()
    urls = [
        "/tools/page",
        "/tools/page/",
        "/tools/page?lang=en",
        "/tools/page?lang=en&a=1",
    ]
    
    normalized = set(normalizer.normalize(u) for u in urls)
    assert len(normalized) == 3  # Trailing slash normalized, params sorted, distinct query param sets preserved


def test_crawler_discovery_source(crawler):
    """Verify discovery source is recorded."""
    results = crawler.crawl(test_urls=["/tools/mp4-to-mp3"])
    assert len(results) > 0
    assert results[0].discovery_source in ["registry", "internal"]


def test_crawler_parameter_detection(crawler):
    """Verify parameter URLs are detected."""
    result = crawler._crawl_url("/tools/page?lang=en", "https://converigo.com")
    assert result.parameter_url is True
    
    result2 = crawler._crawl_url("/tools/page", "https://converigo.com")
    assert result2.parameter_url is False


def test_crawler_limit_enforcement(crawler):
    """Verify max_urls limit is respected."""
    test_urls = ["/tools/page" + str(i) for i in range(10)]
    crawler.config.max_urls = 5

    results = crawler.crawl(test_urls=test_urls)
    assert len(results) <= 5


# ── HTML Extraction Tests ──────────────────────────────────────────────────────

def test_crawler_discover_internal_links(crawler):
    """Verify internal link extraction from HTML."""
    html = """
    <a href="/tools/mp4-to-mp3">MP3</a>
    <a href="/about">About</a>
    <a href="https://external.com">External</a>
    """
    links = crawler.discover_internal_links(html)
    assert "/tools/mp4-to-mp3" in links
    assert "/about" in links


def test_crawler_discover_canonical(crawler):
    """Verify canonical URL extraction."""
    html = '<link rel="canonical" href="https://converigo.com/tools/page">'
    canonical = crawler.discover_canonical(html)
    assert canonical == "https://converigo.com/tools/page"


def test_crawler_discover_hreflang(crawler):
    """Verify hreflang extraction."""
    html = """
    <link rel="alternate" hreflang="en" href="/page?lang=en">
    <link rel="alternate" hreflang="es" href="/page?lang=es">
    <link rel="alternate" hreflang="x-default" href="/page">
    """
    hreflangs = crawler.discover_hreflang(html)
    assert "en" in hreflangs
    assert "es" in hreflangs
    assert "x-default" in hreflangs


def test_crawler_is_indexable_true(crawler):
    """Verify indexable pages return True."""
    html = '<html><title>Test</title></html>'
    assert crawler.is_indexable(html) is True


def test_crawler_is_indexable_false(crawler):
    """Verify noindex pages return False."""
    html = '<meta name="robots" content="noindex">'
    assert crawler.is_indexable(html) is False
    
    html = '<meta content="noindex" name="robots">'
    assert crawler.is_indexable(html) is False


# ── Result Structure Tests ──────────────────────────────────────────────────────

def test_crawl_result_structure():
    """Verify CrawlResult has all required fields."""
    result = CrawlResult(
        url="https://converigo.com/tools/page",
        status_code=200,
    )
    
    assert result.url == "https://converigo.com/tools/page"
    assert result.status_code == 200
    assert isinstance(result.content_type, str)
    assert isinstance(result.canonical, type(None)) or isinstance(result.canonical, str)
    assert isinstance(result.indexable, bool)
    assert isinstance(result.hreflang, list)
    assert isinstance(result.discovery_source, str)
    assert isinstance(result.internal_link_count, int)
    assert isinstance(result.outbound_internal_link_count, int)
    assert isinstance(result.crawl_error, type(None)) or isinstance(result.crawl_error, str)


def test_crawler_to_dict(crawler):
    """Verify to_dict produces valid structure."""
    results = crawler.crawl(test_urls=["/tools/mp4-to-mp3"])
    data = crawler.to_dict()
    
    assert data["version"] == "1.0.0"
    assert "generated_at" in data
    assert data["total_urls"] >= 0
    assert "results" in data
    assert isinstance(data["results"], list)


def test_crawler_save_results(crawler, tmp_path):
    """Verify results can be saved to file."""
    crawler.crawl(test_urls=["/tools/mp4-to-mp3"])
    output_path = tmp_path / "crawl_results.json"
    crawler.save_results(output_path)
    
    assert output_path.exists()
    content = output_path.read_text()
    assert "version" in content
    assert "results" in content

    """Verify max_urls limit is respected."""
    test_urls = ["/tools/page" + str(i) for i in range(10)]
    crawler.config.max_urls = 5
    
    results = crawler.crawl(test_urls=test_urls)
    assert len(results) <= 5


def test_crawler_exclusion_paths(crawler):
    """Verify exclude_paths filter works."""
    crawler.config.exclude_paths = ["/tools/page"]
    results = crawler.crawl(test_urls=["/tools/page", "/tools/other"])
    
    assert all("page" not in r.url for r in results)



# ── Robots Parser Tests ──────────────────────────────────────────────────────

def test_robots_parser_parse():
    """Verify robots.txt parsing."""
    robots = RobotsParser()
    content = """User-agent: *
Disallow: /admin
Allow: /api"""
    robots.parse(content)
    
    # Should allow /api and disallow /admin
    assert robots.is_allowed("/tools/mp4-to-mp3")
    assert robots.is_allowed("/api/data")
    assert not robots.is_allowed("/admin/settings")


def test_robots_parser_default_allowed():
    """Verify default allow when no rules match."""
    robots = RobotsParser()
    robots.parse("User-agent: *\nDisallow: /admin")
    assert robots.is_allowed("/tools/page")
