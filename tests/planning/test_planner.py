from pathlib import Path

import yaml

from bhairava.planning import create_plan


def test_plan_generation(tmp_path: Path):
    config = tmp_path / "target.yaml"

    config.write_text(
        yaml.safe_dump(
            {
                "scope": {
                    "domains": ["authorized.example"],
                    "urls": ["https://authorized.example"],
                },
                "limits": {
                    "requests_per_second": 5,
                    "max_concurrency": 3,
                },
                "selected_tools": [
                    "subfinder",
                    "httpx",
                    "nuclei",
                ],
            }
        ),
        encoding="utf-8",
    )

    plan = create_plan(config)

    assert plan.target == "https://authorized.example"
    assert plan.requests_per_second == 5
    assert plan.max_concurrency == 3
    assert "scope" in plan.stages
    assert "correlation" in plan.stages
    assert plan.authorization_required is True


def test_plan_does_not_execute_network_operations(tmp_path: Path):
    config = tmp_path / "target.yaml"

    config.write_text(
        yaml.safe_dump(
            {
                "scope": {
                    "domains": ["authorized.example"],
                }
            }
        ),
        encoding="utf-8",
    )

    plan = create_plan(config)

    output = plan.render()

    assert "No network testing" in output
    assert "explicit authorization" in output
