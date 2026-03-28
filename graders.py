from typing import Dict, Any, List
from environment.models import Action, Reward


def _keyword_match(text: str, keywords: List[str]) -> bool:
    """Check if any keyword appears in text (case-insensitive)."""
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def _issues_text(action: Action) -> str:
    """Flatten all issue fields into one searchable string."""
    parts = [action.summary]
    for issue in action.issues:
        parts.append(str(issue.get("type", "")))
        parts.append(str(issue.get("description", "")))
        parts.append(str(issue.get("line", "")))
        parts.append(str(issue.get("severity", "")))
    return " ".join(parts)


def grade(task_data: Dict[str, Any], action: Action) -> Reward:
    """
    Grade an agent's action against the ground truth issues.
    Returns a Reward with score 0.0–1.0 and detailed breakdown.
    """
    ground_truth: List[Dict[str, Any]] = task_data["ground_truth_issues"]
    full_text = _issues_text(action)

    # ── 1. Issue Detection Score (0.0–0.6) ──────────────────────────────
    detected = 0
    detection_feedback = []
    for gt_issue in ground_truth:
        found = _keyword_match(full_text, gt_issue["keywords"])
        if found:
            detected += 1
            detection_feedback.append(f"✅ Found: {gt_issue['type']} (line ~{gt_issue['line']})")
        else:
            detection_feedback.append(f"❌ Missed: {gt_issue['type']} (line ~{gt_issue['line']})")

    detection_score = (detected / len(ground_truth)) * 0.6

    # ── 2. Issue Count Score (0.0–0.15) ─────────────────────────────────
    # Reward having a reasonable number of issues reported
    n_issues = len(action.issues)
    expected = len(ground_truth)
    if n_issues == 0:
        count_score = 0.0
    elif n_issues >= expected:
        count_score = 0.15
    else:
        count_score = (n_issues / expected) * 0.15

    # ── 3. Approval Correctness (0.0–0.1) ────────────────────────────────
    expected_approved = task_data.get("approved_expected", False)
    approval_score = 0.1 if action.approved == expected_approved else 0.0

    # ── 4. Summary Quality (0.0–0.1) ─────────────────────────────────────
    summary_score = 0.0
    if len(action.summary) > 30:
        summary_score = 0.05
    if len(action.summary) > 80:
        summary_score = 0.1

    # ── 5. Severity Labels Present (0.0–0.05) ────────────────────────────
    severity_keywords = ["critical", "high", "medium", "low", "warning", "error", "info"]
    has_severity = any(
        _keyword_match(str(issue.get("severity", "")), severity_keywords)
        for issue in action.issues
    )
    severity_score = 0.05 if has_severity else 0.0

    # ── Final Score ───────────────────────────────────────────────────────
    total = detection_score + count_score + approval_score + summary_score + severity_score
    total = round(min(max(total, 0.0), 1.0), 4)

    # ── Partial Progress Reward shaping ──────────────────────────────────
    # Even 0 detections get a small signal if they submitted something
    if total == 0.0 and n_issues > 0:
        total = 0.02

    breakdown = {
        "issue_detection": round(detection_score, 4),
        "issue_count": round(count_score, 4),
        "approval_correctness": round(approval_score, 4),
        "summary_quality": round(summary_score, 4),
        "severity_labels": round(severity_score, 4),
    }

    feedback_lines = detection_feedback + [
        f"\nIssues reported: {n_issues} (expected ~{expected})",
        f"Approval: {'✅' if action.approved == expected_approved else '❌'} "
        f"(you said {'approved' if action.approved else 'rejected'}, "
        f"expected {'approved' if expected_approved else 'rejected'})",
        f"Total score: {total:.4f}"
    ]

    return Reward(
        score=total,
        breakdown=breakdown,
        feedback="\n".join(feedback_lines)
    )
