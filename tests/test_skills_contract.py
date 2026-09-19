from pathlib import Path

import pytest

# A skill is any top-level folder with a SKILL.md -- no shared name prefix
# (the fm-* convention was specific to the meal-planning domain this
# project pivoted away from).
ROOT = Path(__file__).resolve().parent.parent
SKILL_DIRS = sorted(
    p.name
    for p in ROOT.iterdir()
    if p.is_dir() and not p.name.startswith(".") and (p / "SKILL.md").is_file()
)


@pytest.mark.parametrize("skill", SKILL_DIRS)
def test_every_skill_has_a_skill_md(skill):
    assert (ROOT / skill / "SKILL.md").is_file()


@pytest.mark.parametrize("skill", SKILL_DIRS)
def test_every_skill_md_frontmatter_names_itself(skill):
    text = (ROOT / skill / "SKILL.md").read_text()
    frontmatter = text.split("---")[1] if text.startswith("---") else ""
    assert f"name: {skill}" in frontmatter


@pytest.mark.parametrize("skill", SKILL_DIRS)
def test_every_skill_md_description_says_when_to_use_it(skill):
    text = (ROOT / skill / "SKILL.md").read_text()
    frontmatter = text.split("---")[1] if text.startswith("---") else ""
    assert "Use when" in frontmatter


# The closed relation vocabulary of the memory graph: every relation the
# vault names, as a relacao:* tag. The ingest skill defines them; the
# consult and learn skills must handle them.
RELATION_TAGS = (
    "relacao:recomendou",
    "relacao:localizado_em",
    "relacao:culinaria",
    "relacao:foi_com",
    "relacao:quer_visitar",
    "relacao:vai_para",
    "relacao:presente_para",
    "relacao:usa_ingrediente",
)


def test_ingest_skill_defines_the_relation_vocabulary():
    text = (ROOT / "mv-ingest" / "SKILL.md").read_text()
    for tag in RELATION_TAGS:
        assert tag in text, f"mv-ingest does not define {tag}"


def test_ingest_skill_routes_profile_away_from_fact_store():
    text = (ROOT / "mv-ingest" / "SKILL.md").read_text()
    assert "Durable facts about the owner" in text
    assert "never fact_store" in text
    assert "Which store" in text
    assert "`memory` tool to `USER.md`" in text


def test_ingest_skill_updates_a_changed_person_plan_in_place():
    text = (ROOT / "mv-ingest" / "SKILL.md").read_text()
    assert "the newer statement is the current truth" in text


def test_ingest_skill_resolves_stated_times_to_absolute_dates():
    text = (ROOT / "mv-ingest" / "SKILL.md").read_text()
    assert "resolved to the absolute date" in text


def test_ingest_skill_tags_bare_personal_events_as_diario():
    text = (ROOT / "mv-ingest" / "SKILL.md").read_text()
    assert "`diario`" in text


def test_consult_skill_answers_connection_questions_from_relation_tags():
    text = (ROOT / "mv-recall" / "SKILL.md").read_text()
    assert "relacao:*" in text


def test_consult_skill_answers_temporal_recaps_chronologically():
    text = (ROOT / "mv-recall" / "SKILL.md").read_text()
    assert "A temporal recap" in text


def test_ingest_skill_skips_a_stuck_post_and_continues():
    text = (ROOT / "mv-ingest" / "SKILL.md").read_text()
    assert "one `plow_browser_open` per link" in text
    assert "do not retry that URL" in text
    assert "não deu pra ler este:" in text
    assert "Never open two Latch sessions at once" in text


def test_ingest_skill_resurfaces_only_when_it_earns_it():
    text = (ROOT / "mv-ingest" / "SKILL.md").read_text()
    assert "Silence is the default; a resurface is\nthe exception." in text
    assert "≥14 days" in text
    assert "≥7 days" in text
    assert "never claim\n    anything was or wasn't done about it" in text
    assert "🧠-marked" in text


def test_consult_skill_resurfaces_from_cited_facts_only():
    text = (ROOT / "mv-recall" / "SKILL.md").read_text()
    assert "Below threshold,\nsilence." in text
    assert "`skill_view(name=\"mv-act\")`" in text
    assert "on a turn that\nhands off to `mv-act`" in text
    assert "on a temporal recap" in text
    assert "already surfaced the same connection" in text
    assert "🧠 line" in text


def test_consult_skill_widens_a_thin_probe_before_search():
    text = (ROOT / "mv-recall" / "SKILL.md").read_text()
    assert '`fact_store(action="related"' in text
    assert "`limit=25`" in text


def test_learn_skill_preserves_relation_tags_on_update():
    text = (ROOT / "mv-learn" / "SKILL.md").read_text()
    assert "including the `relacao:*` tags" in text


def test_act_skill_does_not_default_to_run_command():
    text = (ROOT / "mv-act" / "SKILL.md").read_text()
    assert "Always the `mcp__latch` tools" not in text
    assert "Do not reach for\n  `plow_run_command`" in text
