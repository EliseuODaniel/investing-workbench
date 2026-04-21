"""Narrative and report helpers for saved research workspaces."""

from __future__ import annotations

from typing import Any


def build_workspace_report(workspace: dict[str, Any]) -> dict[str, Any]:
    """Build a portable narrative/report payload for one saved workspace."""
    selected = workspace["records"]["selected"]
    optimization = workspace["records"].get("optimization")
    walkforward = workspace["records"].get("walkforward")
    montecarlo = workspace["records"].get("montecarlo")
    anchor_run = workspace["records"].get("anchor_run")

    highlights = [
        f"Primary focus: {selected['experiment_type']} {selected['experiment_id']}.",
        (
            "Optimization context available with objective "
            f"{_read_summary_value(optimization, 'objective', 'unknown')}."
            if optimization
            else "No optimization context selected."
        ),
        (
            "Walk-forward context available with "
            f"{_read_summary_value(walkforward, 'window_count', 'unknown')} windows."
            if walkforward
            else "No walk-forward context selected."
        ),
        (
            "Monte Carlo context available with "
            f"{_read_summary_value(montecarlo, 'simulation_count', 'unknown')} simulations."
            if montecarlo
            else "No Monte Carlo context selected."
        ),
        (
            f"Anchor run linked as {anchor_run['experiment_id']}."
            if anchor_run
            else "No anchor run linked for quick backtest inspection."
        ),
    ]

    risks = [
        *_collect_warnings(selected, "Primary experiment"),
        *_collect_warnings(optimization, "Optimization"),
        *_collect_warnings(walkforward, "Walk-forward"),
        *_collect_warnings(montecarlo, "Monte Carlo"),
    ]
    if not walkforward:
        risks.append("Out-of-sample validation is missing from this workspace.")
    if not montecarlo:
        risks.append("Tail-risk or robustness analysis is missing from this workspace.")
    if not anchor_run:
        risks.append(
            "There is no anchor run saved for direct replay in the main results workspace."
        )

    key_metrics_raw: list[tuple[str, str | None]] = [
        (
            "Primary Experiment",
            (
                f"{workspace['selected_experiment']['experiment_type']}:"
                f"{workspace['selected_experiment']['experiment_id']}"
            ),
        ),
        ("Strategy Count", str(len(selected.get("strategy_names", [])))),
        ("Optimization Objective", _read_summary_value(optimization, "objective")),
        (
            "Completed Trials",
            _summarize_pair(
                optimization,
                "completed_trial_count",
                "trial_count",
                "trials",
            ),
        ),
        ("Walk-Forward Windows", _read_summary_value(walkforward, "window_count")),
        (
            "Walk-Forward Split",
            _summarize_triple(
                walkforward,
                "train_window_days",
                "test_window_days",
                "step_days",
                "days",
            ),
        ),
        ("Monte Carlo Sims", _read_summary_value(montecarlo, "simulation_count")),
        ("Monte Carlo Method", _read_summary_value(montecarlo, "method")),
        ("Anchor Fingerprint", _read_summary_value(anchor_run, "data_fingerprint")),
    ]
    key_metrics: list[dict[str, str]] = []
    for label, value in key_metrics_raw:
        if value is not None:
            key_metrics.append({"label": label, "value": value})

    executive_summary = " ".join(
        [
            f'Workspace "{workspace["name"]}" centers on '
            f'{selected["experiment_type"]} {selected["experiment_id"]}.',
            (
                "Optimization evidence is attached."
                if optimization
                else "Optimization evidence is absent."
            ),
            (
                "Walk-forward evidence is attached."
                if walkforward
                else "Walk-forward evidence is absent."
            ),
            (
                "Monte Carlo evidence is attached."
                if montecarlo
                else "Monte Carlo evidence is absent."
            ),
        ]
    )

    markdown = "\n".join(
        line
        for line in [
            f"# {workspace['name']}",
            "",
            executive_summary,
            "",
            f"Created at: {workspace['created_at']}",
            f"Workspace ID: {workspace['workspace_id']}",
            f"Notes: {workspace['notes']}" if workspace.get("notes") else None,
            "",
            "## Key Metrics",
            *[f"- {metric['label']}: {metric['value']}" for metric in key_metrics],
            "",
            "## Highlights",
            *[f"- {item}" for item in highlights],
            "",
            "## Risks",
            *[
                f"- {item}"
                for item in (
                    risks
                    if risks
                    else ["No explicit risks or warnings were detected in the saved workspace."]
                )
            ],
        ]
        if line is not None
    )

    html = _build_html_report(
        workspace=workspace,
        executive_summary=executive_summary,
        key_metrics=key_metrics,
        highlights=highlights,
        risks=risks,
    )

    return {
        "title": workspace["name"],
        "executive_summary": executive_summary,
        "highlights": highlights,
        "risks": risks,
        "key_metrics": key_metrics,
        "markdown": markdown,
        "html": html,
    }


def _collect_warnings(record: dict[str, Any] | None, label: str) -> list[str]:
    if not record:
        return []
    warnings = record.get("summary", {}).get("warnings")
    if not isinstance(warnings, list):
        return []
    return [
        f"{label}: {warning}"
        for warning in warnings
        if isinstance(warning, str) and warning
    ]


def _read_summary_value(
    record: dict[str, Any] | None,
    key: str,
    default: str | None = None,
) -> str | None:
    if not record:
        return default
    value = record.get("summary", {}).get(key)
    if value in (None, ""):
        return default
    return str(value)


def _summarize_pair(
    record: dict[str, Any] | None,
    left_key: str,
    right_key: str,
    suffix: str,
) -> str | None:
    left = _read_summary_value(record, left_key)
    right = _read_summary_value(record, right_key)
    if not left or not right:
        return None
    return f"{left}/{right} {suffix}"


def _summarize_triple(
    record: dict[str, Any] | None,
    first_key: str,
    second_key: str,
    third_key: str,
    suffix: str,
) -> str | None:
    first = _read_summary_value(record, first_key)
    second = _read_summary_value(record, second_key)
    third = _read_summary_value(record, third_key)
    if not first or not second or not third:
        return None
    return f"{first}/{second}/{third} {suffix}"


def _build_html_report(
    *,
    workspace: dict[str, Any],
    executive_summary: str,
    key_metrics: list[dict[str, str]],
    highlights: list[str],
    risks: list[str],
) -> str:
    safe_risks = risks or ["No explicit risks or warnings were detected in this workspace."]
    notes = workspace.get("notes")
    key_metrics_html = "".join(
        (
            '<div class="card">'
            f'<div class="label">{_escape_html(metric["label"])}</div>'
            f'<div class="value">{_escape_html(metric["value"])}</div>'
            "</div>"
        )
        for metric in key_metrics
    )
    highlights_html = "".join(f"<li>{_escape_html(item)}</li>" for item in highlights)
    risks_html = "".join(f"<li>{_escape_html(item)}</li>" for item in safe_risks)
    notes_html = (
        '<section class="section"><h2>Notes</h2>'
        f'<div class="notes">{_escape_html(str(notes))}</div></section>'
        if notes
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{_escape_html(str(workspace["name"]))}</title>
    <style>
      body {{
        font-family: Georgia, "Times New Roman", serif;
        margin: 40px auto;
        max-width: 920px;
        color: #1f2937;
        background: #f8fafc;
        padding: 0 20px;
      }}
      .hero {{
        background: linear-gradient(135deg, #e0f2fe, #f8fafc);
        border: 1px solid #cbd5e1;
        border-radius: 20px;
        padding: 28px;
      }}
      .eyebrow {{
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #475569;
      }}
      h1, h2 {{ margin-bottom: 12px; }}
      h1 {{ font-size: 32px; margin-top: 10px; }}
      h2 {{ font-size: 18px; margin-top: 30px; }}
      p, li {{ line-height: 1.7; }}
      .meta {{ color: #64748b; font-size: 14px; }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;
        margin-top: 18px;
      }}
      .card {{
        background: #ffffff;
        border: 1px solid #dbe4ee;
        border-radius: 16px;
        padding: 16px;
      }}
      .label {{
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748b;
      }}
      .value {{ margin-top: 6px; font-weight: 700; word-break: break-word; }}
      .section {{
        background: #ffffff;
        border: 1px solid #dbe4ee;
        border-radius: 16px;
        padding: 22px;
        margin-top: 20px;
      }}
      .notes {{ white-space: pre-wrap; }}
    </style>
  </head>
  <body>
    <section class="hero">
      <div class="eyebrow">Research Workspace Report</div>
      <h1>{_escape_html(str(workspace["name"]))}</h1>
      <div class="meta">
        Created at {_escape_html(str(workspace["created_at"]))}
        · Workspace ID {_escape_html(str(workspace["workspace_id"]))}
      </div>
      <p>{_escape_html(executive_summary)}</p>
    </section>
    <section class="section">
      <h2>Key Metrics</h2>
      <div class="grid">{key_metrics_html}</div>
    </section>
    {notes_html}
    <section class="section">
      <h2>Highlights</h2>
      <ul>{highlights_html}</ul>
    </section>
    <section class="section">
      <h2>Risks</h2>
      <ul>{risks_html}</ul>
    </section>
  </body>
</html>"""


def _escape_html(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
