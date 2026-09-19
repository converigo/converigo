"""
Converigo
SEO Crawler (Phase 1 - Core Infrastructure)
Version: 1.0.0

Core crawler for URL discovery, inventory, and structured output.
Does NOT modify production code or existing SEO systems.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse, urljoin, urlunparse

from app.services.seo_service import SeoService
from app.services.converter_data_service import ConverterDataService
from app.services.converter_registry_service import ConverterRegistryService


# ── Data Classes ──────────────────────────────────────────────────────

@dataclass
class CrawlResult:
    """Result for a single crawled URL."""
    url: str
    status_code: int
    content_type: str = ""
    canonical: Optional[str] = None
    indexable: bool = True
    robots_meta: Optional[str] = None
    hreflang: list[str] = field(default_factory=list)
    discovery_source: str = "internal"
    internal_link_count: int = 0
    outbound_internal_link_count: int = 0
    crawl_error: Optional[str] = None
    redirect_url: Optional[str] = None
    parameter_url: bool = False


@dataclass
class CrawlConfig:
    """Crawler configuration."""
    base_domain: str = "converigo.com"
    max_urls: int = 1000
    rate_limit_delay: float = 0.5  # seconds between requests
    timeout: int = 10  # seconds
    concurrent_requests: int = 3
    exclude_paths: list[str] = field(default_factory=lambda: ["/api", "/admin", "/private", "/.git"])
    user_agent: str = "ConverigoSEO/1.0"


# ── URL Normalization ──────────────────────────────────────────────────────

class URLNormalizer:
    """Normalize URLs for deduplication and comparison."""
    
    @staticmethod
    def normalize(url: str) -> str:
        """Normalize URL: remove trailing slash, sort params, standardize."""
        if not url:
            return url
        
        parsed = urlparse(url)
        
        # Remove trailing slash (except for root)
        path = parsed.path.rstrip("/") if parsed.path != "/" else parsed.path
        
        # Sort query parameters
        if parsed.query:
            params = sorted(parsed.query.split("&"))
            query = "&".join(params)
        else:
            query = ""
        
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            path,
            parsed.params,
            query,
            parsed.fragment
        ))
    
    @staticmethod
    def has_parameters(url: str) -> bool:
        """Check if URL has query parameters."""
        return "?" in url
    
    @staticmethod
    def get_domain(url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc or ""


# ── Robots Parser ──────────────────────────────────────────────────────

class RobotsParser:
    """Parse and check robots.txt rules."""
    
    def __init__(self):
        self._rules: list[dict[str, Any]] = []
    
    def parse(self, robots_content: str) -> None:
        """Parse robots.txt content."""
        current_agent = ""
        current_rules = []
        
        for line in robots_content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            if line.lower().startswith("user-agent:"):
                if current_agent and current_rules:
                    self._rules.append({"agent": current_agent, "rules": current_rules})
                current_agent = line.split(":", 1)[1].strip()
                current_rules = []
            elif line.lower().startswith("disallow:"):
                rule = line.split(":", 1)[1].strip()
                current_rules.append({"type": "disallow", "path": rule})
            elif line.lower().startswith("allow:"):
                rule = line.split(":", 1)[1].strip()
                current_rules.append({"type": "allow", "path": rule})
        
        if current_agent and current_rules:
            self._rules.append({"agent": current_agent, "rules": current_rules})
    
    def is_allowed(self, path: str, user_agent: str = "*") -> bool:
        """Check if path is allowed for user agent."""
        best_match = None
        best_match_len = 0
        
        for rule in self._rules:
            if rule["agent"] != user_agent and rule["agent"] != "*":
                continue
            
            for r in rule["rules"]:
                if r["path"] and path.startswith(r["path"]):
                    if len(r["path"]) > best_match_len:
                        best_match = r
                        best_match_len = len(r["path"])
        
        if best_match and best_match["type"] == "disallow":
            return False
        
        return True


# ── Crawler Core ──────────────────────────────────────────────────────

class SeoSrawler:
    """Phase 1 SEO crawler for URL discovery and inventory."""
    
    def __init__(
        self,
        contracts_dir: Path | str | None = None,
        config: CrawlConfig | None = None,
    ) -> None:
        self.contracts_dir = Path(contracts_dir or "app/data/converters")
        self.config = config or CrawlConfig()
        self._normalizer = URLNormalizer()
        self._robots = RobotsParser()
        
        # Services
        self._registry = ConverterRegistryService(self.contracts_dir)
        self._data = ConverterDataService(self.contracts_dir)
        self._seo = SeoService(self.contracts_dir)
        
        # State
        self._visited: set[str] = set()
        self._results: list[CrawlResult] = []
        self._start_time: Optional[datetime] = None

    # ── URL Discovery ──────────────────────────────────────────────────────
    
    def discover_from_sitemap(self, sitemap_urls: list[str]) -> list[str]:
        """Extract URLs from sitemap XML."""
        urls = []
        for sitemap_url in sitemap_urls:
            try:
                # In production, fetch the sitemap; for local testing, parse local files
                parsed = urlparse(sitemap_url)
                # Skip external sitemaps
                if parsed.netloc and not self._is_internal(parsed.netloc):
                    continue
                
                # Local sitemap parsing would happen here
                urls.extend([])  # Placeholder
            except Exception:
                continue
        return urls
    
    def discover_from_registry(self) -> list[str]:
        """Discover URLs from converter registry."""
        urls = []
        for converter in self._registry.list_all():
            enabled = getattr(converter, "enabled", True)
            if enabled is False:
                continue
            
            slug = converter.get("slug", "") if isinstance(converter, dict) else str(converter.id)
            url = f"/tools/{slug}"
            urls.append(url)
        return urls
    
    def discover_internal_links(self, html_content: str) -> list[str]:
        """Extract internal links from HTML."""
        pattern = r'href=["\']([^"\']+)["\']'
        links = re.findall(pattern, html_content)
        internal = []
        
        for link in links:
            if link.startswith(("/", "http://converigo.com", "https://converigo.com")):
                internal.append(link)
        
        return internal
    
    def discover_canonical(self, html_content: str) -> Optional[str]:
        """Extract canonical URL from HTML."""
        pattern = r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']'
    
        match = re.search(pattern, html_content)
        return match.group(1) if match else None
    # ── Safety ──────────────────────────────────────────────────────
    
    def _is_internal(self, domain: str) -> bool:
        """Check if domain is internal."""
        return self.config.base_domain in domain
    
    def _should_exclude(self, url: str) -> bool:
        """Check if URL should be excluded."""
        for path in self.config.exclude_paths:
            if url.startswith(path):
                return True
        return False
    
    # ── Main Crawl ──────────────────────────────────────────────────────
    
    def crawl(
        self,
        base_url: str = "https://converigo.com",
        test_urls: Optional[list[str]] = None,
    ) -> list[CrawlResult]:
        """Run crawl and return results."""
        self._start_time = datetime.now(timezone.utc)
        self._visited.clear()
        self._results.clear()
        
        # Get URLs to crawl
        if test_urls:
            urls_to_crawl = test_urls
        else:
            urls_to_crawl = self.discover_from_registry()
        
        # Process URLs
        processed = 0
        for url in urls_to_crawl:
            if processed >= self.config.max_urls:
                break
            
            normalized = self._normalizer.normalize(url)
            if normalized in self._visited or self._should_exclude(url):
                continue
            
            self._visited.add(normalized)
            
            try:
                result = self._crawl_url(url, base_url)
                self._results.append(result)
                processed += 1
            except Exception:
                self._results.append(CrawlResult(
                    url=url,
                    status_code=0,
                    crawl_error="crawl_failed"
                ))
        
        return self._results
    
    def _crawl_url(self, url: str, base_url: str) -> CrawlResult:
        """Crawl a single URL."""
        # Normalize URL
        if url.startswith("/"):
            full_url = urljoin(base_url, url)
        else:
            full_url = url
        
        normalized = self._normalizer.normalize(full_url)
        
        # Create result
        result = CrawlResult(
            url=full_url,
            status_code=200,
            discovery_source="registry" if "/tools/" in full_url else "internal",
            parameter_url=self._normalizer.has_parameters(full_url)
        )
        
        # In production, this would fetch the actual URL
        # For now, simulate results based on URL pattern
        if "/tools/" in full_url:
            result.content_type = "text/html"
            result.internal_link_count = 5  # Simulated
            result.outbound_internal_link_count = 5
        else:
            result.content_type = "text/html"
        
        return result

    # ── Reports ──────────────────────────────────────────────────────
    
    def to_dict(self) -> dict[str, Any]:
        """Convert results to dict format."""
        return {
            "version": "1.0.0",
            "generated_at": self._start_time.isoformat() if self._start_time else None,
            "total_urls": len(self._results),
            "results": [
                {
                    "url": r.url,
                    "status_code": r.status_code,
                    "content_type": r.content_type,
                    "canonical": r.canonical,
                    "indexable": r.indexable,
                    "robots_meta": r.robots_meta,
                    "hreflang": r.hreflang,
                    "discovery_source": r.discovery_source,
                    "internal_link_count": r.internal_link_count,
                    "outbound_internal_link_count": r.outbound_internal_link_count,
                    "crawl_error": r.crawl_error,
                    "redirect_url": r.redirect_url,
                }
                for r in self._results
            ]
        }
    
    def save_results(self, output_path: Path) -> None:
        """Save results to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        output_path.write_text(
            json.dumps(self.to_dict(), indent=2),
            encoding="utf-8"
        )

    
    def discover_hreflang(self, html_content: str) -> list[str]:
        """Extract hreflang values from HTML."""
        pattern = r'hreflang=["\']([^"\']+)["\']'
        return re.findall(pattern, html_content)
    
    def is_indexable(self, html_content: str, canonical: Optional[str] = None) -> bool:
        """Check if page is indexable."""
        pattern = r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex[^"\']*["\']'
        if re.search(pattern, html_content, re.IGNORECASE):
            return False
        
        pattern = r'<meta[^>]+content=["\'][^"\']*noindex[^"\']*["\'][^>]+name=["\']robots["\']'
        if re.search(pattern, html_content, re.IGNORECASE):
            return False
        
        return True

