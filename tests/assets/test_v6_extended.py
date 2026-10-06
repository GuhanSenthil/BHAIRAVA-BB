from pathlib import Path

from bhairava.assets import (
    Asset,
    AssetGraph,
    AssetRepository,
    AssetType,
    ScopeStatus,
    canonicalize,
    deduplicate,
    fingerprint,
    normalize_domain,
    normalize_url,
)

# ============================================================================
# NORMALIZER
# ============================================================================


def test_normalize_domain_lowercases():
    assert normalize_domain("Example.COM") == "example.com"


def test_normalize_domain_removes_trailing_dot():
    assert normalize_domain("Example.COM.") == "example.com"


def test_normalize_domain_preserves_subdomain():
    assert normalize_domain("API.Example.COM") == "api.example.com"


def test_normalize_domain_from_https_url():
    assert normalize_domain("HTTPS://Example.COM/") == "example.com"


def test_normalize_domain_from_http_url():
    assert normalize_domain("http://Example.COM/") == "example.com"


def test_normalize_domain_from_url_with_path():
    assert normalize_domain("https://API.Example.COM/login") == (
        "api.example.com"
    )


def test_normalize_url_lowercases_scheme_and_host():
    assert normalize_url("HTTPS://Example.COM/test") == (
        "https://example.com/test"
    )


def test_normalize_url_removes_default_https_port():
    assert normalize_url("https://example.com:443/login") == (
        "https://example.com/login"
    )


def test_normalize_url_removes_default_http_port():
    assert normalize_url("http://example.com:80/login") == (
        "http://example.com/login"
    )


def test_normalize_url_preserves_non_default_port():
    assert normalize_url("https://example.com:8443/login") == (
        "https://example.com:8443/login"
    )


def test_normalize_url_preserves_path():
    assert normalize_url("HTTPS://Example.COM/api/v1/users") == (
        "https://example.com/api/v1/users"
    )


def test_normalize_url_preserves_query():
    assert normalize_url("https://Example.COM/search?q=test") == (
        "https://example.com/search?q=test"
    )


def test_normalize_url_preserves_multiple_query_parameters():
    assert normalize_url(
        "https://Example.COM/search?q=test&page=2"
    ) == "https://example.com/search?q=test&page=2"


# ============================================================================
# CANONICALIZATION
# ============================================================================


def test_canonicalize_plain_domain():
    asset_type, value = canonicalize("example.com")

    assert asset_type == AssetType.DOMAIN
    assert value == "example.com"


def test_canonicalize_subdomain():
    asset_type, value = canonicalize("api.example.com")

    assert asset_type == AssetType.SUBDOMAIN
    assert value == "api.example.com"


def test_canonicalize_https_root_url():
    asset_type, value = canonicalize("https://example.com/")

    assert asset_type == AssetType.URL
    assert value == "https://example.com/"


def test_canonicalize_https_endpoint():
    asset_type, value = canonicalize("https://example.com/api")

    assert asset_type == AssetType.ENDPOINT
    assert value == "https://example.com/api"


def test_canonicalize_http_endpoint():
    asset_type, value = canonicalize("http://example.com/login")

    assert asset_type == AssetType.ENDPOINT
    assert value == "http://example.com/login"


def test_canonicalize_nested_subdomain():
    asset_type, value = canonicalize("dev.api.example.com")

    assert asset_type == AssetType.SUBDOMAIN
    assert value == "dev.api.example.com"


# ============================================================================
# ASSET MODEL
# ============================================================================


def test_asset_create_domain():
    asset = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "unit-test",
    )

    assert asset.asset_type == AssetType.DOMAIN
    assert asset.canonical_value == "example.com"
    assert asset.source == "unit-test"


def test_asset_create_subdomain():
    asset = Asset.create(
        AssetType.SUBDOMAIN,
        "api.example.com",
        "subfinder",
    )

    assert asset.asset_type == AssetType.SUBDOMAIN
    assert asset.canonical_value == "api.example.com"


def test_asset_create_url():
    asset = Asset.create(
        AssetType.URL,
        "https://example.com/",
        "httpx",
    )

    assert asset.asset_type == AssetType.URL
    assert asset.canonical_value == "https://example.com/"


def test_asset_create_endpoint():
    asset = Asset.create(
        AssetType.ENDPOINT,
        "https://example.com/api",
        "httpx",
    )

    assert asset.asset_type == AssetType.ENDPOINT
    assert asset.canonical_value == "https://example.com/api"


def test_asset_create_records_source():
    asset = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "subfinder",
    )

    assert "subfinder" in asset.source


def test_asset_create_records_technologies():
    asset = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "httpx",
        technologies=["nginx", "python"],
    )

    assert "nginx" in asset.technologies
    assert "python" in asset.technologies


def test_asset_create_scope_status():
    asset = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "unit-test",
        scope_status=ScopeStatus.IN_SCOPE,
    )

    assert asset.scope_status == ScopeStatus.IN_SCOPE


def test_asset_create_out_of_scope_status():
    asset = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "unit-test",
        scope_status=ScopeStatus.OUT_OF_SCOPE,
    )

    assert asset.scope_status == ScopeStatus.OUT_OF_SCOPE


def test_asset_create_parent_asset():
    parent = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "seed",
    )

    child = Asset.create(
        AssetType.SUBDOMAIN,
        "api.example.com",
        "subfinder",
        parent_asset_id=parent.asset_id,
    )

    assert child.parent_asset_id == parent.asset_id


# ============================================================================
# STABLE ASSET IDENTIFIERS
# ============================================================================


def test_asset_id_is_stable_for_same_domain():
    first = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "subfinder",
    )

    second = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "amass",
    )

    assert first.asset_id == second.asset_id


def test_asset_id_is_stable_for_case_variation():
    first = Asset.create(
        AssetType.DOMAIN,
        "Example.com",
        "subfinder",
    )

    second = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "amass",
    )

    assert first.asset_id == second.asset_id


def test_different_domains_have_different_asset_ids():
    first = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "subfinder",
    )

    second = Asset.create(
        AssetType.DOMAIN,
        "example.org",
        "subfinder",
    )

    assert first.asset_id != second.asset_id


def test_different_asset_types_have_distinct_ids():
    domain = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "unit-test",
    )

    url = Asset.create(
        AssetType.URL,
        "https://example.com/",
        "unit-test",
    )

    assert domain.asset_id != url.asset_id


# ============================================================================
# DEDUPLICATION
# ============================================================================


def test_deduplicate_empty_collection():
    assert deduplicate([]) == []


def test_deduplicate_single_asset():
    asset = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "subfinder",
    )

    result = deduplicate([asset])

    assert len(result) == 1
    assert result[0].asset_id == asset.asset_id


def test_deduplicate_same_asset():
    first = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "subfinder",
    )

    second = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "amass",
    )

    result = deduplicate([first, second])

    assert len(result) == 1


def test_deduplicate_merges_sources():
    first = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "subfinder",
    )

    second = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "amass",
    )

    result = deduplicate([first, second])

    assert len(result) == 1
    assert "subfinder" in result[0].source
    assert "amass" in result[0].source


def test_deduplicate_merges_technologies():
    first = Asset.create(
        AssetType.URL,
        "https://example.com/",
        "httpx",
        technologies=["nginx"],
    )

    second = Asset.create(
        AssetType.URL,
        "https://example.com/",
        "nuclei",
        technologies=["wordpress"],
    )

    result = deduplicate([first, second])

    assert len(result) == 1
    assert "nginx" in result[0].technologies
    assert "wordpress" in result[0].technologies


def test_deduplicate_keeps_distinct_domains():
    first = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "subfinder",
    )

    second = Asset.create(
        AssetType.DOMAIN,
        "example.org",
        "subfinder",
    )

    result = deduplicate([first, second])

    assert len(result) == 2


def test_deduplicate_keeps_distinct_subdomains():
    first = Asset.create(
        AssetType.SUBDOMAIN,
        "api.example.com",
        "subfinder",
    )

    second = Asset.create(
        AssetType.SUBDOMAIN,
        "admin.example.com",
        "subfinder",
    )

    result = deduplicate([first, second])

    assert len(result) == 2


def test_deduplicate_preserves_single_unique_asset():
    assets = [
        Asset.create(AssetType.DOMAIN, "example.com", "subfinder"),
        Asset.create(AssetType.DOMAIN, "api.example.com", "subfinder"),
        Asset.create(AssetType.DOMAIN, "admin.example.com", "subfinder"),
    ]

    result = deduplicate(assets)

    assert len(result) == 3


# ============================================================================
# FINGERPRINTING
# ============================================================================


def test_fingerprint_empty_observations():
    technologies = fingerprint()

    assert technologies == []


def test_fingerprint_nginx_server():
    technologies = fingerprint(
        headers={
            "Server": "nginx/1.25",
        },
    )

    assert "nginx" in technologies


def test_fingerprint_express():
    technologies = fingerprint(
        headers={
            "X-Powered-By": "Express",
        },
    )

    assert "express" in technologies


def test_fingerprint_wordpress_body():
    technologies = fingerprint(
        body="<html><body>/wp-content/themes/test</body></html>",
    )

    assert "wordpress" in technologies


def test_fingerprint_react_body():
    technologies = fingerprint(
        body="<html><script>React.createElement()</script></html>",
    )

    assert "react" in technologies


def test_fingerprint_php_cookie():
    technologies = fingerprint(
        cookies={
            "PHPSESSID": "abc123",
        },
    )

    assert "php" in technologies


def test_fingerprint_combines_multiple_sources():
    technologies = fingerprint(
        headers={
            "Server": "nginx/1.25",
            "X-Powered-By": "Express",
        },
        body="<html>wp-content react</html>",
        cookies={
            "PHPSESSID": "abc",
        },
    )

    assert "nginx" in technologies
    assert "express" in technologies
    assert "wordpress" in technologies
    assert "react" in technologies
    assert "php" in technologies


def test_fingerprint_does_not_duplicate_technologies():
    technologies = fingerprint(
        headers={
            "Server": "nginx/1.25",
        },
        body="nginx nginx nginx",
    )

    assert technologies.count("nginx") == 1


# ============================================================================
# ASSET GRAPH
# ============================================================================


def test_graph_starts_empty():
    graph = AssetGraph()

    assert len(graph) == 0
    assert graph.roots() == []


def test_graph_adds_root():
    root = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "seed",
    )

    graph = AssetGraph()
    graph.add(root)

    assert len(graph) == 1
    assert graph.roots() == [root]


def test_graph_adds_child():
    root = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "seed",
    )

    child = Asset.create(
        AssetType.SUBDOMAIN,
        "api.example.com",
        "subfinder",
        parent_asset_id=root.asset_id,
    )

    graph = AssetGraph()
    graph.add(root)
    graph.add(child)

    assert len(graph) == 2
    assert graph.roots() == [root]
    assert graph.children(root.asset_id) == [child]


def test_graph_supports_multiple_children():
    root = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "seed",
    )

    api = Asset.create(
        AssetType.SUBDOMAIN,
        "api.example.com",
        "subfinder",
        parent_asset_id=root.asset_id,
    )

    admin = Asset.create(
        AssetType.SUBDOMAIN,
        "admin.example.com",
        "subfinder",
        parent_asset_id=root.asset_id,
    )

    graph = AssetGraph()

    graph.add(root)
    graph.add(api)
    graph.add(admin)

    children = graph.children(root.asset_id)

    assert len(children) == 2
    assert api in children
    assert admin in children


def test_graph_supports_multiple_roots():
    first = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "seed",
    )

    second = Asset.create(
        AssetType.DOMAIN,
        "example.org",
        "seed",
    )

    graph = AssetGraph()

    graph.add(first)
    graph.add(second)

    roots = graph.roots()

    assert len(roots) == 2
    assert first in roots
    assert second in roots


def test_graph_unknown_parent_is_not_root():
    child = Asset.create(
        AssetType.SUBDOMAIN,
        "api.example.com",
        "subfinder",
        parent_asset_id="missing-parent",
    )

    graph = AssetGraph()
    graph.add(child)

    assert len(graph) == 1
    assert graph.roots() == []


def test_graph_children_unknown_asset():
    graph = AssetGraph()

    assert graph.children("missing-asset") == []


# ============================================================================
# REPOSITORY
# ============================================================================


def test_repository_round_trip(tmp_path: Path):
    database = tmp_path / "assets.db"

    asset = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "subfinder",
        scope_status=ScopeStatus.IN_SCOPE,
        technologies=["nginx"],
    )

    repository = AssetRepository(database)
    repository.upsert(asset)

    loaded = repository.get(asset.asset_id)

    assert loaded is not None
    assert loaded.asset_id == asset.asset_id
    assert loaded.asset_type == AssetType.DOMAIN
    assert loaded.canonical_value == "example.com"
    assert loaded.scope_status == ScopeStatus.IN_SCOPE
    assert loaded.technologies == ["nginx"]


def test_repository_round_trip_out_of_scope(tmp_path: Path):
    database = tmp_path / "assets.db"

    asset = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "unit-test",
        scope_status=ScopeStatus.OUT_OF_SCOPE,
    )

    repository = AssetRepository(database)
    repository.upsert(asset)

    loaded = repository.get(asset.asset_id)

    assert loaded is not None
    assert loaded.scope_status == ScopeStatus.OUT_OF_SCOPE


def test_repository_round_trip_subdomain(tmp_path: Path):
    database = tmp_path / "assets.db"

    asset = Asset.create(
        AssetType.SUBDOMAIN,
        "api.example.com",
        "subfinder",
    )

    repository = AssetRepository(database)
    repository.upsert(asset)

    loaded = repository.get(asset.asset_id)

    assert loaded is not None
    assert loaded.asset_type == AssetType.SUBDOMAIN
    assert loaded.canonical_value == "api.example.com"


def test_repository_round_trip_url(tmp_path: Path):
    database = tmp_path / "assets.db"

    asset = Asset.create(
        AssetType.URL,
        "https://example.com/",
        "httpx",
    )

    repository = AssetRepository(database)
    repository.upsert(asset)

    loaded = repository.get(asset.asset_id)

    assert loaded is not None
    assert loaded.asset_type == AssetType.URL
    assert loaded.canonical_value == "https://example.com/"


def test_repository_round_trip_endpoint(tmp_path: Path):
    database = tmp_path / "assets.db"

    asset = Asset.create(
        AssetType.ENDPOINT,
        "https://example.com/api",
        "httpx",
    )

    repository = AssetRepository(database)
    repository.upsert(asset)

    loaded = repository.get(asset.asset_id)

    assert loaded is not None
    assert loaded.asset_type == AssetType.ENDPOINT
    assert loaded.canonical_value == "https://example.com/api"


def test_repository_preserves_source(tmp_path: Path):
    database = tmp_path / "assets.db"

    asset = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "subfinder",
    )

    repository = AssetRepository(database)
    repository.upsert(asset)

    loaded = repository.get(asset.asset_id)

    assert loaded is not None
    assert "subfinder" in loaded.source


def test_repository_preserves_parent(tmp_path: Path):
    database = tmp_path / "assets.db"

    parent = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "seed",
    )

    child = Asset.create(
        AssetType.SUBDOMAIN,
        "api.example.com",
        "subfinder",
        parent_asset_id=parent.asset_id,
    )

    repository = AssetRepository(database)

    repository.upsert(parent)
    repository.upsert(child)

    loaded = repository.get(child.asset_id)

    assert loaded is not None
    assert loaded.parent_asset_id == parent.asset_id


def test_repository_list_empty(tmp_path: Path):
    database = tmp_path / "assets.db"

    repository = AssetRepository(database)

    assert repository.list() == []


def test_repository_list_multiple_assets(tmp_path: Path):
    database = tmp_path / "assets.db"

    first = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "subfinder",
    )

    second = Asset.create(
        AssetType.SUBDOMAIN,
        "api.example.com",
        "subfinder",
    )

    repository = AssetRepository(database)

    repository.upsert(first)
    repository.upsert(second)

    assets = repository.list()

    assert len(assets) == 2

    asset_ids = {asset.asset_id for asset in assets}

    assert first.asset_id in asset_ids
    assert second.asset_id in asset_ids


def test_repository_get_missing_asset(tmp_path: Path):
    database = tmp_path / "assets.db"

    repository = AssetRepository(database)

    assert repository.get("asset_missing") is None


def test_repository_upsert_is_idempotent(tmp_path: Path):
    database = tmp_path / "assets.db"

    asset = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "subfinder",
    )

    repository = AssetRepository(database)

    repository.upsert(asset)
    repository.upsert(asset)

    assert len(repository.list()) == 1


def test_repository_upsert_updates_existing_asset(tmp_path: Path):
    database = tmp_path / "assets.db"

    first = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "subfinder",
        technologies=["nginx"],
    )

    second = Asset.create(
        AssetType.DOMAIN,
        "example.com",
        "amass",
        technologies=["python"],
    )

    assert first.asset_id == second.asset_id

    repository = AssetRepository(database)

    repository.upsert(first)
    repository.upsert(second)

    assets = repository.list()

    assert len(assets) == 1


# ============================================================================
# V6 INTEGRATION-STYLE TEST
# ============================================================================


def test_v6_asset_lifecycle_end_to_end(tmp_path: Path):
    """
    Exercise the complete V6 asset flow:

        input
          ↓
        canonicalization
          ↓
        Asset creation
          ↓
        deduplication
          ↓
        fingerprinting
          ↓
        graph
          ↓
        repository
    """

    # 1. Canonicalize discovery inputs.
    domain_type, domain_value = canonicalize("example.com")
    subdomain_type, subdomain_value = canonicalize("api.example.com")
    url_type, url_value = canonicalize("https://example.com/")
    endpoint_type, endpoint_value = canonicalize("https://example.com/api")

    assert domain_type == AssetType.DOMAIN
    assert domain_value == "example.com"

    assert subdomain_type == AssetType.SUBDOMAIN
    assert subdomain_value == "api.example.com"

    assert url_type == AssetType.URL
    assert url_value == "https://example.com/"

    assert endpoint_type == AssetType.ENDPOINT
    assert endpoint_value == "https://example.com/api"

    # 2. Create root and discovered assets.
    root = Asset.create(
        AssetType.DOMAIN,
        domain_value,
        "seed",
        scope_status=ScopeStatus.IN_SCOPE,
    )

    api = Asset.create(
        AssetType.SUBDOMAIN,
        subdomain_value,
        "subfinder",
        scope_status=ScopeStatus.IN_SCOPE,
        parent_asset_id=root.asset_id,
    )

    url = Asset.create(
        AssetType.URL,
        url_value,
        "httpx",
        scope_status=ScopeStatus.IN_SCOPE,
        parent_asset_id=root.asset_id,
        technologies=["nginx"],
    )

    endpoint = Asset.create(
        AssetType.ENDPOINT,
        endpoint_value,
        "httpx",
        scope_status=ScopeStatus.IN_SCOPE,
        parent_asset_id=url.asset_id,
    )

    # 3. Fingerprint an HTTP observation.
    technologies = fingerprint(
        headers={
            "Server": "nginx/1.25",
            "X-Powered-By": "Express",
        },
        body="<html>wp-content react</html>",
        cookies={
            "PHPSESSID": "abc",
        },
    )

    assert "nginx" in technologies
    assert "express" in technologies
    assert "wordpress" in technologies
    assert "react" in technologies
    assert "php" in technologies

    # 4. Add technologies discovered by fingerprinting.
    fingerprinted_url = Asset.create(
        AssetType.URL,
        url_value,
        "fingerprint",
        scope_status=ScopeStatus.IN_SCOPE,
        parent_asset_id=root.asset_id,
        technologies=technologies,
    )

    # 5. Deduplicate the two observations of the same URL.
    unique_assets = deduplicate(
        [
            url,
            fingerprinted_url,
        ]
    )

    assert len(unique_assets) == 1
    assert "nginx" in unique_assets[0].technologies
    assert "express" in unique_assets[0].technologies
    assert "wordpress" in unique_assets[0].technologies
    assert "react" in unique_assets[0].technologies
    assert "php" in unique_assets[0].technologies

    # 6. Build the asset graph.
    graph = AssetGraph()

    graph.add(root)
    graph.add(api)
    graph.add(url)
    graph.add(endpoint)

    assert len(graph) == 4
    assert graph.roots() == [root]
    assert api in graph.children(root.asset_id)
    assert url in graph.children(root.asset_id)
    assert endpoint in graph.children(url.asset_id)

    # 7. Persist the V6 asset model.
    database = tmp_path / "v6-integration.db"
    repository = AssetRepository(database)

    repository.upsert(root)
    repository.upsert(api)
    repository.upsert(url)
    repository.upsert(endpoint)

    # 8. Verify persistence.
    assert len(repository.list()) == 4

    loaded_root = repository.get(root.asset_id)
    loaded_api = repository.get(api.asset_id)
    loaded_url = repository.get(url.asset_id)
    loaded_endpoint = repository.get(endpoint.asset_id)

    assert loaded_root is not None
    assert loaded_api is not None
    assert loaded_url is not None
    assert loaded_endpoint is not None

    assert loaded_root.scope_status == ScopeStatus.IN_SCOPE
    assert loaded_api.parent_asset_id == root.asset_id
    assert loaded_url.parent_asset_id == root.asset_id
    assert loaded_endpoint.parent_asset_id == url.asset_id
