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


def test_normalize_domain():
    assert normalize_domain("HTTPS://WWW.Example.COM.") == "www.example.com"


def test_normalize_url():
    assert normalize_url("HTTPS://Example.COM:443/login?x=1") == (
        "https://example.com/login?x=1"
    )


def test_canonicalize_types():
    assert canonicalize("example.com")[0] == AssetType.DOMAIN
    assert canonicalize("api.example.com")[0] == AssetType.SUBDOMAIN
    assert canonicalize("https://example.com/")[0] == AssetType.URL
    assert canonicalize("https://example.com/api")[0] == AssetType.ENDPOINT


def test_stable_asset_id():
    first = Asset.create(AssetType.DOMAIN, "Example.com", "subfinder")
    second = Asset.create(AssetType.DOMAIN, "example.com", "amass")

    assert first.asset_id == second.asset_id


def test_deduplicate_merges_observations():
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
    assert result[0].technologies == ["nginx", "wordpress"]
    assert "nuclei" in result[0].source


def test_fingerprint():
    technologies = fingerprint(
        headers={
            "Server": "nginx/1.25",
            "X-Powered-By": "Express",
        },
        body="<html>wp-content react</html>",
        cookies={"PHPSESSID": "abc"},
    )

    assert "nginx" in technologies
    assert "express" in technologies
    assert "wordpress" in technologies
    assert "react" in technologies
    assert "php" in technologies


def test_asset_graph():
    root = Asset.create(AssetType.DOMAIN, "example.com", "seed")
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


def test_repository(tmp_path):
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
    assert loaded.scope_status == ScopeStatus.IN_SCOPE
    assert loaded.technologies == ["nginx"]


def test_repository_upsert_is_idempotent(tmp_path):
    database = tmp_path / "assets.db"

    asset = Asset.create(AssetType.DOMAIN, "example.com", "subfinder")

    repository = AssetRepository(database)
    repository.upsert(asset)
    repository.upsert(asset)

    assert len(repository.list()) == 1
