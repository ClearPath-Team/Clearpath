"""Canonical deterministic accessibility issue taxonomy.

Classification is functional, not a medical diagnosis or a WCAG conformance verdict.
Unknown axe rules are safely assigned to structure_navigation.
"""
from worker.engine.recommendations import RECOMMENDATIONS, EN_RECOMMENDATIONS

CATEGORY_LABELS = {
    "visual_contrast": {"en": "Contrast & Visual", "ro": "Contrast și lizibilitate"},
    "screen_reader": {"en": "Screen Reader & Semantics", "ro": "Cititoare de ecran și ARIA"},
    "motor_keyboard": {"en": "Keyboard & Motor Access", "ro": "Navigare tastatură și motor"},
    "structure_navigation": {"en": "Page Structure & Orientation", "ro": "Structură și repere de pagină"},
}
WCAG_PRINCIPLES = ("perceivable", "operable", "understandable", "robust")
DEFAULT_CATEGORY = "structure_navigation"

RULE_CATEGORIES = {
    "color-contrast": "visual_contrast", "link-in-text-block": "visual_contrast",
    "keyboard-trap": "motor_keyboard", "nested-interactive": "motor_keyboard",
    "aria-hidden-focus": "motor_keyboard", "scrollable-region-focusable": "motor_keyboard",
    "accesskeys": "motor_keyboard",
    "image-alt": "screen_reader", "input-image-alt": "screen_reader",
    "button-name": "screen_reader", "link-name": "screen_reader",
    "label": "screen_reader", "select-name": "screen_reader",
    "frame-title": "screen_reader", "duplicate-id-aria": "screen_reader",
    "aria-valid-attr": "screen_reader", "aria-valid-attr-value": "screen_reader",
    "aria-required-attr": "screen_reader", "aria-required-children": "screen_reader",
    "aria-required-parent": "screen_reader", "aria-allowed-attr": "screen_reader",
    "aria-allowed-role": "screen_reader", "aria-command-name": "screen_reader",
    "aria-dialog-name": "screen_reader", "aria-input-field-name": "screen_reader",
    "aria-meter-name": "screen_reader", "aria-progressbar-name": "screen_reader",
    "aria-toggle-field-name": "screen_reader", "aria-tooltip-name": "screen_reader",
    "aria-treeitem-name": "screen_reader", "aria-hidden-body": "screen_reader",
    "aria-roles": "screen_reader", "aria-deprecated-role": "screen_reader",
    "role-img-alt": "screen_reader", "svg-img-alt": "screen_reader",
    "object-alt": "screen_reader", "input-button-name": "screen_reader",
    "form-field-multiple-labels": "screen_reader", "autocomplete-valid": "screen_reader",
    "landmark-one-main": "structure_navigation", "region": "structure_navigation",
    "page-has-heading-one": "structure_navigation", "heading-order": "structure_navigation",
    "empty-heading": "structure_navigation", "html-has-lang": "structure_navigation",
    "html-lang-valid": "structure_navigation", "html-xml-lang-mismatch": "structure_navigation",
    "document-title": "structure_navigation", "list": "structure_navigation",
    "listitem": "structure_navigation", "dlitem": "structure_navigation",
    "definition-list": "structure_navigation", "landmark-unique": "structure_navigation",
    "landmark-complementary-is-top-level": "structure_navigation",
    "landmark-main-is-top-level": "structure_navigation", "landmark-no-duplicate-banner": "structure_navigation",
    "landmark-no-duplicate-contentinfo": "structure_navigation",
    "meta-viewport": "structure_navigation", "meta-refresh": "structure_navigation",
    "bypass": "motor_keyboard", "tabindex": "motor_keyboard",
    "target-size": "motor_keyboard", "focus-order-semantics": "motor_keyboard",
    "audio-caption": "visual_contrast", "video-caption": "visual_contrast",
}

# POUR is intentionally a single primary principle per finding. Context-specific
# mappings can vary; these deterministic choices are not legal WCAG conformance claims.
RULE_PRINCIPLES = {
    "keyboard-trap": "operable", "nested-interactive": "operable",
    "aria-hidden-focus": "operable", "scrollable-region-focusable": "operable",
    "accesskeys": "operable", "bypass": "operable", "tabindex": "operable",
    "target-size": "operable", "focus-order-semantics": "operable",
    "html-has-lang": "understandable", "html-lang-valid": "understandable",
    "html-xml-lang-mismatch": "understandable",
    "aria-valid-attr": "robust", "aria-valid-attr-value": "robust",
    "aria-roles": "robust", "duplicate-id-aria": "robust",
    "aria-required-attr": "robust", "aria-required-children": "robust",
    "aria-required-parent": "robust", "aria-allowed-attr": "robust",
    "aria-allowed-role": "robust",
}


def classify_issue(rule: str) -> dict:
    """Return a new independent taxonomy payload for any axe or custom rule."""
    rule = rule or ""
    category = RULE_CATEGORIES.get(rule)
    if category is None and rule.startswith("aria-"):
        category = "screen_reader"
    category = category or DEFAULT_CATEGORY
    principle = RULE_PRINCIPLES.get(rule)
    if principle is None:
        principle = {
            "visual_contrast": "perceivable",
            "screen_reader": "robust",
            "motor_keyboard": "operable",
            "structure_navigation": "perceivable",
        }[category]
    return {
        "category": category,
        "category_label": dict(CATEGORY_LABELS[category]),
        "wcag_principle": principle,
    }


def enrich_issue(issue: dict) -> dict:
    """Reclassify from rule, ignoring possibly stale caller-supplied taxonomy."""
    return {**issue, **classify_issue(issue.get("rule", ""))}


def category_counts(issues: list[dict]) -> dict[str, int]:
    counts = {key: 0 for key in CATEGORY_LABELS}
    for issue in issues:
        counts[classify_issue(issue.get("rule", ""))["category"]] += 1
    return counts


assert set(RECOMMENDATIONS).issubset(RULE_CATEGORIES)
assert set(EN_RECOMMENDATIONS).issubset(RULE_CATEGORIES)
