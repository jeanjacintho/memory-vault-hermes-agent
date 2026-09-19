from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parent.parent

SKILLS = (
    "mv-ingest",
    "mv-recall",
    "mv-act",
    "mv-learn",
)


def deploy_hook():
    return (ROOT / "deploy-hook").read_text()


def test_soul_fits_hermes_context_file_limit():
    spec = importlib.util.spec_from_file_location(
        "soul_fits_context", ROOT / "checks" / "soul_fits_context.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    n, limit = module.check(ROOT)
    assert n <= limit
    assert limit == 40000


def test_deploy_hook_seeds_every_skill():
    text = deploy_hook()
    # The pt-* pattern: the seed rides a glob, and an empty match is a
    # broken checkout, not a silent pass. Which dirs exist is the other
    # tests' job (SKILLS above + test_skills_contract's discovery).
    assert "for dir in mv-*" in text
    assert 'no mv-* skill dirs -- broken checkout' in text


def test_shipped_skills_are_exactly_the_mv_dirs():
    # The shipped set is this tuple -- no stray mv-* dir, no missing one.
    globbed = sorted(p.name for p in ROOT.glob("mv-*") if p.is_dir())
    assert globbed == sorted(SKILLS)


def test_deploy_hook_seeds_skills_copy_if_absent():
    text = deploy_hook()
    # The agent's own edits are kept, never overwritten by a re-seed.
    assert "keeping agent-owned" in text
    # The staging shape an interrupted copy leaves behind is *.incoming.
    assert "dest.incoming" in text


def test_deploy_hook_publishes_soul_md_every_deploy():
    text = deploy_hook()
    assert "runtime/SOUL.md" in text
    assert "published SOUL.md" in text


def test_compose_yml_is_the_plow_agents_surface():
    # plow-agents' compose.example.yml: service `agent`, credential drop-in,
    # named home volume. compose.override.yml must not exist: Compose loads
    # that filename automatically and would start a second gateway.
    import re

    assert not (ROOT / "compose.override.yml").exists()
    text = (ROOT / "compose.yml").read_text()
    assert re.search(r"^  agent:", text, re.M)
    assert "build: ." in text
    assert "./plow-credentials:/var/lib/plow/credentials.host:ro" in text
    assert "agent-home:/var/lib/hermes" in text
    assert "AGENT_ID: memory-vault" in text
    assert "stop_grace_period: 35s" in text
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("-") and "skills" in stripped and "agent-home" not in stripped:
            raise AssertionError(f"skill mount in compose.yml: {stripped}")


def test_compose_yml_does_not_pin_a_model():
    text = (ROOT / "compose.yml").read_text()
    assert "HERMES_PROVIDER" not in text
    assert "HERMES_MODEL" not in text


def test_dockerfile_copies_every_mv_skill_outside_the_home():
    import re

    dockerfile = (ROOT / "Dockerfile").read_text()
    skills = sorted(p.parent.name for p in ROOT.glob("mv-*/SKILL.md"))
    missing = [name for name in skills if f"COPY {name}/" not in dockerfile]
    assert missing == [], f"in the tree but never copied into the image: {', '.join(missing)}"
    for name in skills:
        assert re.search(
            rf"^COPY\s+{re.escape(name)}/\s+/opt/hermes/skills/{re.escape(name)}/\s*$",
            dockerfile,
            re.MULTILINE,
        ), f"COPY {name}/ does not land at /opt/hermes/skills/{name}/"
        assert f"/var/lib/hermes/skills/{name}" not in dockerfile
    assert "COPY runtime/SOUL.md /var/lib/hermes/SOUL.md" in dockerfile
    assert "COPY runtime/SOUL.md /opt/hermes/plow-seed/SOUL.md" in dockerfile
    assert "COPY runtime/config.yaml /var/lib/hermes/config.yaml" in dockerfile
    assert "merge_mv_seed_config.py" in dockerfile
    assert "02-copy-plow-credentials" in dockerfile
    assert "interim_assistant_messages: false" in dockerfile
    assert "disabled_toolsets:" in dockerfile
    assert "context_file_max_chars: 40000" in dockerfile
    assert "anthropic/claude-sonnet-5" in dockerfile
    assert "moonshotai/kimi-k2.5" not in dockerfile
    assert "base-ef0019372ff8bca593611b31ebd2e08f9f1458ff" in dockerfile
    assert "image/s6-overlay" not in dockerfile
    assert "plow-credentials" in (ROOT / ".dockerignore").read_text()
    assert "plow-credentials" in (ROOT / ".gitignore").read_text()


def test_no_meal_planning_leftovers_remain():
    for name in ("fm-planner", "fm-shopping", "fm-homework", "fm-agenda", "fm-shared"):
        assert not (ROOT / name).exists(), f"{name} is a leftover of the pivoted domain"


def test_env_example_documents_the_dotenv_contract():
    text = (ROOT / ".env.example").read_text()
    for key in ("PLOW_HOME_CHANNEL", "DOMO_DEVICE_UID", "DOMO_MCP_TOKEN"):
        assert key in text, f".env.example does not document {key}"
    # Bare keys, no blank-value assignments: a present-but-empty key would
    # clobber a credential the container supplies (see the file's own comment).
    for line in text.splitlines():
        stripped = line.strip()
        for key in ("DOMO_DEVICE_UID", "DOMO_MCP_TOKEN"):
            if stripped == key:
                break
        else:
            if any(stripped.startswith(k + "=") for k in ("DOMO_DEVICE_UID", "DOMO_MCP_TOKEN")):
                raise AssertionError(f".env.example assigns a blank credential: {stripped!r}")


def test_descriptor_is_documented_in_env_example():
    example = (ROOT / ".env.example").read_text()
    assert "PLOW_HOME_CHANNEL=" in example


def test_readme_is_the_product():
    readme = (ROOT / "README.md").read_text()
    assert "Memory Vault" in readme
    assert "Share the link like a text to a friend" in readme
    assert "## Install" in readme
    assert "plow-agents mint ln_xxx" in readme
    assert "docker compose up --build -d" in readme
    assert "DELETES sessions and memory_store.db" in readme
    assert "not the repo `.env`" in readme
    assert "https://your-tutorial-url" not in readme


def test_skills_tsv_declares_no_connectors():
    # No connectors skill -- Latch is the only mcp_server (same shape the
    # sibling agents ship).
    content = (ROOT / "skills.tsv").read_text().strip()
    assert not content
