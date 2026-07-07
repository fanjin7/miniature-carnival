"""AI-education literature search and selection logic.

This module mirrors the ai-education-daily workflow in academic-daily-scholar:
- prepend AI-education priority queries to the normal search query list;
- keep a three-year search window through runtime configuration;
- filter papers by AI teaching, subject-specific AI integration, teacher literacy,
  teacher education/training, and digital-transformation teacher-role themes;
- rank selected papers by topic relevance first, not by publication date first.
"""

from __future__ import annotations

import logging
import re

import filter as paper_filter
import search as search_module
from config import AppConfig
from utils import Paper

AI_PRIORITY_SEARCH_QUERIES: tuple[str, ...] = (
    "artificial intelligence teaching education",
    "AI teaching education",
    "AI assisted teaching",
    "AI-assisted instruction education",
    "AI supported classroom teaching",
    "AI assisted learning education",
    "AI supported learning education",
    "generative AI teaching education",
    "ChatGPT teaching education",
    "large language models teaching education",
    "AI lesson planning teacher",
    "AI teaching design education",
    "AI curriculum education",
    "AI classroom assessment teacher",
    "AI assisted assessment education",
    "automated feedback education",
    "intelligent tutoring education",
    "adaptive learning education",
    "learning analytics education",
    "educational data mining",
    "artificial intelligence preschool education teaching",
    "AI early childhood education teaching",
    "generative AI early childhood education",
    "artificial intelligence kindergarten teaching",
    "AI kindergarten education",
    "artificial intelligence primary education teaching",
    "AI primary school teaching",
    "AI elementary education teaching",
    "AI elementary school learning",
    "artificial intelligence basic education teaching",
    "AI compulsory education teaching",
    "AI K-12 education teaching",
    "artificial intelligence junior high school teaching",
    "AI middle school teaching",
    "AI lower secondary education",
    "school education artificial intelligence teaching",
    "classroom teaching artificial intelligence school",
    "mathematics education artificial intelligence primary school",
    "mathematics teaching artificial intelligence elementary school",
    "mathematics learning artificial intelligence K-12",
    "math education generative AI school",
    "AI assisted mathematics teaching",
    "Chinese language education artificial intelligence",
    "Chinese language teaching artificial intelligence school",
    "Chinese writing instruction artificial intelligence",
    "language arts education artificial intelligence school",
    "native language education artificial intelligence",
    "first language writing instruction artificial intelligence",
    "reading education artificial intelligence school",
    "writing instruction artificial intelligence school",
    "English education artificial intelligence school",
    "English language teaching artificial intelligence",
    "EFL teaching artificial intelligence",
    "ESL teaching artificial intelligence",
    "AI assisted English learning school",
    "science education artificial intelligence primary school",
    "science teaching artificial intelligence middle school",
    "STEM education artificial intelligence school",
    "language education artificial intelligence primary school",
    "subject teaching artificial intelligence school education",
    "curriculum artificial intelligence basic education",
    "disciplinary teaching artificial intelligence education",
    "teacher digital literacy education",
    "teacher digital competence education",
    "teacher AI literacy education",
    "teacher artificial intelligence literacy education",
    "teacher intelligent literacy education",
    "teacher data literacy education",
    "teachers digital literacy artificial intelligence",
    "teachers digital competence artificial intelligence",
    "teachers data literacy digital education",
    "teacher digital literacy primary education",
    "teacher digital competence basic education",
    "teacher AI literacy school education",
    "teacher artificial intelligence literacy basic education",
    "teacher intelligent literacy school education",
    "teacher data literacy basic education",
    "primary school teacher digital literacy",
    "elementary teacher AI literacy",
    "middle school teacher data literacy",
    "preschool teacher digital competence",
    "teacher education artificial intelligence integration",
    "preservice teachers artificial intelligence education",
    "pre-service teachers AI integration teacher education",
    "in-service teachers artificial intelligence training",
    "teacher professional development artificial intelligence school",
    "teacher training generative AI education",
    "AI integration preservice teacher education",
    "AI integration in-service teacher professional development",
    "AI lesson planning teacher education",
    "AI classroom assessment teacher training",
    "educational digital transformation teaching change",
    "educational digital transformation basic education teacher role",
    "digital transformation school education teacher role",
    "educational digitalization teaching reform school teachers",
    "AI teaching reform basic education",
    "artificial intelligence teacher role school education",
    "digital education teacher role primary school",
    "technology integration teacher role basic education",
    "technology integration teaching education",
    "teacher agency artificial intelligence school education",
)


def configure_daily_search_queries() -> None:
    """Use the same priority-query composition as ai-education-daily."""

    search_module.SEARCH_QUERIES = tuple(dict.fromkeys(AI_PRIORITY_SEARCH_QUERIES + search_module.SEARCH_QUERIES))


def select_daily_papers(
    papers: list[Paper],
    config: AppConfig,
    logger: logging.Logger,
    whitelist: paper_filter.SsciWhitelist | None = None,
    exclude_identities: set[str] | None = None,
    ignore_seen: bool = False,
) -> list[Paper]:
    """Filter topic papers and select by relevance rather than newest-first ranking."""

    whitelist = whitelist or paper_filter.load_ssci_whitelist(config.ssci_whitelist_path, logger)
    filtered: list[Paper] = []
    seen = set() if ignore_seen else paper_filter.load_seen_identities(config.seen_state_path)
    if exclude_identities:
        seen.update(exclude_identities)

    for paper in papers:
        ok, score, reasons = _prioritize_defined_scope(paper, whitelist, config.ssci_filter_mode)
        use_whitelist = config.ssci_filter_mode != "off" and whitelist.available
        paper.ssci_matched = whitelist.is_match(paper) if use_whitelist else False
        if paper.ssci_matched:
            whitelist.apply_metadata(paper)
        elif not use_whitelist:
            paper.ssci_matched = False
            paper.ssci_categories = []
            paper.impact_factor = ""
            paper.quartile = ""
            paper.citescore = ""
            paper.publisher = ""
        paper.filter_score = score
        paper.filter_reasons = reasons
        if ok and paper.identity not in seen:
            filtered.append(paper)

    filtered.sort(key=_relevance_sort_key, reverse=True)
    selected = filtered[: config.max_papers]
    logger.info(
        "AI专题相关度筛选完成 input=%s kept=%s selected=%s whitelist_available=%s mode=%s sort=relevance_first",
        len(papers),
        len(filtered),
        len(selected),
        whitelist.available,
        config.ssci_filter_mode,
    )
    return selected


def _paper_text(paper: Paper) -> str:
    return " ".join(
        [
            paper.title,
            paper.abstract,
            paper.journal,
            " ".join(paper.concepts),
            " ".join(paper.keywords),
        ]
    ).lower()


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _has_ai_theme(text: str) -> bool:
    patterns = [
        r"\bartificial intelligence\b",
        r"\bgenerative ai\b",
        r"\bgenai\b",
        r"\bchatgpt\b",
        r"\blarge language model(s)?\b",
        r"\bllm(s)?\b",
        r"\bai\b",
        r"\bai-assisted\b",
        r"\bai supported\b",
        r"\bintelligent tutor(ing|s)?\b",
        r"\badaptive learning\b",
        r"\blearning analytics\b",
        r"\beducational data mining\b",
        r"\bautomated feedback\b",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def _has_preschool_primary_or_junior_stage(text: str) -> bool:
    stage_terms = (
        "preschool",
        "pre-school",
        "early childhood",
        "kindergarten",
        "primary education",
        "primary school",
        "elementary education",
        "elementary school",
        "basic education",
        "compulsory education",
        "k-12",
        "k12",
        "school education",
        "school teacher",
        "school teachers",
        "school student",
        "school students",
        "junior high",
        "middle school",
        "lower secondary",
        "children",
        "pupils",
    )
    return _contains_any(text, stage_terms)


def _has_teaching_related_theme(text: str) -> bool:
    teaching_terms = (
        "teaching",
        "instruction",
        "learning",
        "classroom",
        "lesson planning",
        "instructional design",
        "teaching design",
        "curriculum",
        "assessment",
        "feedback",
        "tutoring",
        "adaptive learning",
        "learning analytics",
        "educational data mining",
        "pedagogy",
        "pedagogical",
    )
    return _contains_any(text, teaching_terms)


def _has_ai_teaching_application(text: str) -> bool:
    return _has_ai_theme(text) and _has_teaching_related_theme(text)


def _has_subject_ai_theme(text: str) -> bool:
    subject_terms = (
        "mathematics",
        "math",
        "science",
        "stem",
        "language",
        "english",
        "efl",
        "esl",
        "reading",
        "writing",
        "literacy",
        "chinese language",
        "chinese writing",
        "language arts",
        "native language",
        "first language",
        "mother tongue",
        "curriculum",
        "subject teaching",
        "disciplinary",
    )
    return _has_ai_theme(text) and _contains_any(text, subject_terms)


def _has_teacher_literacy_theme(text: str) -> bool:
    literacy_terms = (
        "teacher digital literacy",
        "teacher digital competence",
        "teacher ai literacy",
        "teacher artificial intelligence literacy",
        "teacher intelligent literacy",
        "teacher data literacy",
        "teachers digital literacy",
        "teachers digital competence",
        "teachers ai literacy",
        "teachers data literacy",
        "digital literacy",
        "digital competence",
        "ai literacy",
        "artificial intelligence literacy",
        "intelligent literacy",
        "data literacy",
    )
    teacher_terms = ("teacher", "teachers", "educator", "educators")
    return _contains_any(text, literacy_terms) and _contains_any(text, teacher_terms)


def _has_teacher_education_ai_integration(text: str) -> bool:
    teacher_training_terms = (
        "teacher education",
        "preservice teacher",
        "pre-service teacher",
        "preservice teachers",
        "pre-service teachers",
        "in-service teacher",
        "inservice teacher",
        "in-service teachers",
        "inservice teachers",
        "teacher training",
        "teacher professional development",
        "professional development",
        "initial teacher education",
    )
    return _has_ai_theme(text) and _contains_any(text, teacher_training_terms)


def _has_digital_transformation_teacher_role(text: str) -> bool:
    transformation_terms = (
        "digital transformation",
        "educational digital transformation",
        "digitalization",
        "digitalisation",
        "digital education",
        "technology integration",
        "teaching reform",
        "teaching change",
        "pedagogical change",
        "teacher role",
        "teacher agency",
        "teacher identity",
    )
    teacher_or_teaching_terms = ("teacher", "teachers", "teaching", "classroom", "school")
    return _contains_any(text, transformation_terms) and _contains_any(text, teacher_or_teaching_terms)


def _is_high_school_only(text: str) -> bool:
    high_school_terms = ("high school", "senior high", "upper secondary")
    lower_stage_terms = (
        "middle school",
        "junior high",
        "lower secondary",
        "primary",
        "elementary",
        "preschool",
        "kindergarten",
        "k-12",
        "k12",
        "basic education",
        "compulsory education",
    )
    return _contains_any(text, high_school_terms) and not _contains_any(text, lower_stage_terms)


def _can_relax_original_stage_gate(reasons: list[str], text: str) -> bool:
    """Allow broad teaching or teacher-literacy papers blocked only by a missing stage term."""

    if "no_preschool_or_basic_education_stage" not in reasons:
        return False
    if any(reason.startswith("excluded:") or reason == "not_in_ssci_whitelist" for reason in reasons):
        return False
    return (
        _has_ai_teaching_application(text)
        or _has_subject_ai_theme(text)
        or _has_teacher_literacy_theme(text)
        or _has_teacher_education_ai_integration(text)
        or _has_digital_transformation_teacher_role(text)
    )


def _prioritize_defined_scope(paper: Paper, whitelist: paper_filter.SsciWhitelist, mode: str) -> tuple[bool, int, list[str]]:
    text = _paper_text(paper)
    ok, score, reasons = paper_filter._score_paper(paper, whitelist, mode)  # type: ignore[attr-defined]
    if not ok and not _can_relax_original_stage_gate(reasons, text):
        return ok, score, reasons
    if not ok:
        score = max(score, 0)
        reasons = [reason for reason in reasons if reason != "no_preschool_or_basic_education_stage"]

    stage_hit = _has_preschool_primary_or_junior_stage(text)
    teaching_related = _has_teaching_related_theme(text)
    ai_teaching = _has_ai_teaching_application(text)
    subject_ai = _has_subject_ai_theme(text)
    teacher_literacy = _has_teacher_literacy_theme(text)
    teacher_education_ai = _has_teacher_education_ai_integration(text)
    digital_transform = _has_digital_transformation_teacher_role(text)

    if _is_high_school_only(text) and not (teacher_education_ai or teacher_literacy or ai_teaching):
        return False, score - 20, reasons + ["scope:high_school_only"]

    topic_hits: list[str] = []
    if subject_ai:
        score += 50
        topic_hits.append("subject_ai_integration")
    if ai_teaching:
        score += 44
        topic_hits.append("ai_teaching_application")
    if teacher_literacy:
        score += 40
        topic_hits.append("teacher_digital_ai_data_literacy")
    if teacher_education_ai:
        score += 38
        topic_hits.append("teacher_education_ai_integration")
    if digital_transform:
        score += 30
        topic_hits.append("digital_transformation_teacher_role")
    if teaching_related:
        score += 16
        topic_hits.append("teaching_related")
    if stage_hit:
        score += 20
        topic_hits.append("preschool_primary_or_junior_stage")

    if not topic_hits:
        return False, score, reasons + ["scope:no_teaching_or_teacher_literacy_topic"]

    return True, score, reasons + [f"defined_scope:{hit}" for hit in topic_hits]


def _relevance_sort_key(paper: Paper) -> tuple[int, int, int, int, int, int, int, int, int]:
    """Rank papers mainly by relevance; publication date is only the final tie-breaker."""

    text = _paper_text(paper)
    return (
        paper.filter_score,
        int(_has_subject_ai_theme(text)),
        int(_has_ai_teaching_application(text)),
        int(_has_teacher_literacy_theme(text)),
        int(_has_teacher_education_ai_integration(text)),
        int(_has_digital_transformation_teacher_role(text)),
        int(_has_preschool_primary_or_junior_stage(text)),
        int(paper.ssci_matched),
        paper.published_date.toordinal() if paper.published_date else 0,
    )
