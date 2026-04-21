import { ResearchWorkspacePayload, ResearchWorkspaceReportPayload } from '../types/api';

export interface ResearchWorkspaceNarrative {
  title: string;
  executiveSummary: string;
  highlights: string[];
  risks: string[];
  keyMetrics: Array<{
    label: string;
    value: string;
  }>;
  markdown: string;
  html: string;
}

export function buildResearchWorkspaceNarrative(
  workspace: ResearchWorkspacePayload
): ResearchWorkspaceNarrative {
  const selected = workspace.records.selected;
  const optimization = workspace.records.optimization;
  const walkforward = workspace.records.walkforward;
  const montecarlo = workspace.records.montecarlo;
  const anchorRun = workspace.records.anchor_run;

  const highlights = [
    `Primary focus: ${selected.experiment_type} ${selected.experiment_id}.`,
    optimization
      ? `Optimization context available with objective ${String(optimization.summary.objective ?? 'unknown')}.`
      : 'No optimization context selected.',
    walkforward
      ? `Walk-forward context available with ${String(walkforward.summary.window_count ?? 'unknown')} windows.`
      : 'No walk-forward context selected.',
    montecarlo
      ? `Monte Carlo context available with ${String(montecarlo.summary.simulation_count ?? 'unknown')} simulations.`
      : 'No Monte Carlo context selected.',
    anchorRun
      ? `Anchor run linked as ${anchorRun.experiment_id}.`
      : 'No anchor run linked for quick backtest inspection.',
  ];

  const risks = [
    ...collectWarnings(selected, 'Primary experiment'),
    ...collectWarnings(optimization, 'Optimization'),
    ...collectWarnings(walkforward, 'Walk-forward'),
    ...collectWarnings(montecarlo, 'Monte Carlo'),
  ];

  if (!walkforward) {
    risks.push('Out-of-sample validation is missing from this workspace.');
  }
  if (!montecarlo) {
    risks.push('Tail-risk or robustness analysis is missing from this workspace.');
  }
  if (!anchorRun) {
    risks.push('There is no anchor run saved for direct replay in the main results workspace.');
  }

  const executiveSummary = [
    `Workspace "${workspace.name}" centers on ${selected.experiment_type} ${selected.experiment_id}.`,
    optimization ? 'Optimization evidence is attached.' : 'Optimization evidence is absent.',
    walkforward ? 'Walk-forward evidence is attached.' : 'Walk-forward evidence is absent.',
    montecarlo ? 'Monte Carlo evidence is attached.' : 'Monte Carlo evidence is absent.',
  ].join(' ');

  const keyMetrics = buildKeyMetrics(workspace);
  const markdown = [
    `# ${workspace.name}`,
    '',
    executiveSummary,
    '',
    `Created at: ${workspace.created_at}`,
    `Workspace ID: ${workspace.workspace_id}`,
    workspace.notes ? `Notes: ${workspace.notes}` : null,
    '',
    '## Key Metrics',
    ...keyMetrics.map((item) => `- ${item.label}: ${item.value}`),
    '',
    '## Highlights',
    ...highlights.map((item) => `- ${item}`),
    '',
    '## Risks',
    ...(risks.length > 0
      ? risks.map((item) => `- ${item}`)
      : ['- No explicit risks or warnings were detected in the saved workspace.']),
  ]
    .filter((item): item is string => item !== null)
    .join('\n');

  const html = buildResearchWorkspaceHtml({
    workspace,
    executiveSummary,
    highlights,
    risks,
    keyMetrics,
  });

  return {
    title: workspace.name,
    executiveSummary,
    highlights,
    risks,
    keyMetrics,
    markdown,
    html,
  };
}

export function buildResearchWorkspaceNarrativeFromReport(
  report: ResearchWorkspaceReportPayload
): ResearchWorkspaceNarrative {
  return {
    title: report.title,
    executiveSummary: report.executive_summary,
    highlights: report.highlights,
    risks: report.risks,
    keyMetrics: report.key_metrics,
    markdown: report.markdown,
    html: report.html,
  };
}

function collectWarnings(
  record: ResearchWorkspacePayload['records'][keyof ResearchWorkspacePayload['records']] | undefined,
  label: string
): string[] {
  if (!record) {
    return [];
  }

  const warnings = record.summary?.warnings;
  if (!Array.isArray(warnings)) {
    return [];
  }

  return warnings
    .filter((warning): warning is string => typeof warning === 'string' && warning.length > 0)
    .map((warning) => `${label}: ${warning}`);
}

function buildKeyMetrics(
  workspace: ResearchWorkspacePayload
): Array<{
  label: string;
  value: string;
}> {
  const metrics: Array<{ label: string; value: string | null | undefined }> = [
    {
      label: 'Primary Experiment',
      value: `${workspace.selected_experiment.experiment_type}:${workspace.selected_experiment.experiment_id}`,
    },
    {
      label: 'Strategy Count',
      value: String(workspace.records.selected.strategy_names.length),
    },
    {
      label: 'Optimization Objective',
      value: readSummaryValue(workspace.records.optimization?.summary, 'objective'),
    },
    {
      label: 'Completed Trials',
      value: summarizePair(
        workspace.records.optimization?.summary,
        'completed_trial_count',
        'trial_count',
        'trials'
      ),
    },
    {
      label: 'Walk-Forward Windows',
      value: readSummaryValue(workspace.records.walkforward?.summary, 'window_count'),
    },
    {
      label: 'Walk-Forward Split',
      value: summarizeTriple(
        workspace.records.walkforward?.summary,
        'train_window_days',
        'test_window_days',
        'step_days'
      ),
    },
    {
      label: 'Monte Carlo Sims',
      value: readSummaryValue(workspace.records.montecarlo?.summary, 'simulation_count'),
    },
    {
      label: 'Monte Carlo Method',
      value: readSummaryValue(workspace.records.montecarlo?.summary, 'method'),
    },
    {
      label: 'Anchor Fingerprint',
      value: readSummaryValue(workspace.records.anchor_run?.summary, 'data_fingerprint'),
    },
  ];

  return metrics
    .filter((item): item is { label: string; value: string } => Boolean(item.value))
    .map((item) => ({ label: item.label, value: item.value }));
}

function readSummaryValue(summary: Record<string, unknown> | null | undefined, key: string): string | null {
  const value = summary?.[key];
  if (value === null || value === undefined || value === '') {
    return null;
  }
  return String(value);
}

function summarizePair(
  summary: Record<string, unknown> | null | undefined,
  leftKey: string,
  rightKey: string,
  suffix: string
): string | null {
  const left = readSummaryValue(summary, leftKey);
  const right = readSummaryValue(summary, rightKey);
  if (!left || !right) {
    return null;
  }
  return `${left}/${right} ${suffix}`;
}

function summarizeTriple(
  summary: Record<string, unknown> | null | undefined,
  firstKey: string,
  secondKey: string,
  thirdKey: string
): string | null {
  const first = readSummaryValue(summary, firstKey);
  const second = readSummaryValue(summary, secondKey);
  const third = readSummaryValue(summary, thirdKey);
  if (!first || !second || !third) {
    return null;
  }
  return `${first}/${second}/${third} days`;
}

function buildResearchWorkspaceHtml({
  workspace,
  executiveSummary,
  highlights,
  risks,
  keyMetrics,
}: {
  workspace: ResearchWorkspacePayload;
  executiveSummary: string;
  highlights: string[];
  risks: string[];
  keyMetrics: Array<{ label: string; value: string }>;
}): string {
  const safeRisks =
    risks.length > 0 ? risks : ['No explicit risks or warnings were detected in this workspace.'];

  return `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${escapeHtml(workspace.name)}</title>
    <style>
      body { font-family: Georgia, "Times New Roman", serif; margin: 40px auto; max-width: 920px; color: #1f2937; background: #f8fafc; padding: 0 20px; }
      .hero { background: linear-gradient(135deg, #e0f2fe, #f8fafc); border: 1px solid #cbd5e1; border-radius: 20px; padding: 28px; }
      .eyebrow { font-size: 12px; text-transform: uppercase; letter-spacing: 0.12em; color: #475569; }
      h1, h2 { margin-bottom: 12px; }
      h1 { font-size: 32px; margin-top: 10px; }
      h2 { font-size: 18px; margin-top: 30px; }
      p, li { line-height: 1.7; }
      .meta { color: #64748b; font-size: 14px; }
      .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-top: 18px; }
      .card { background: #ffffff; border: 1px solid #dbe4ee; border-radius: 16px; padding: 16px; }
      .label { font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: #64748b; }
      .value { margin-top: 6px; font-weight: 700; word-break: break-word; }
      .section { background: #ffffff; border: 1px solid #dbe4ee; border-radius: 16px; padding: 22px; margin-top: 20px; }
      .notes { white-space: pre-wrap; }
    </style>
  </head>
  <body>
    <section class="hero">
      <div class="eyebrow">Research Workspace Report</div>
      <h1>${escapeHtml(workspace.name)}</h1>
      <div class="meta">Created at ${escapeHtml(workspace.created_at)} · Workspace ID ${escapeHtml(workspace.workspace_id)}</div>
      <p>${escapeHtml(executiveSummary)}</p>
    </section>
    <section class="section">
      <h2>Key Metrics</h2>
      <div class="grid">
        ${keyMetrics
          .map(
            (item) => `<div class="card"><div class="label">${escapeHtml(item.label)}</div><div class="value">${escapeHtml(item.value)}</div></div>`
          )
          .join('')}
      </div>
    </section>
    ${
      workspace.notes
        ? `<section class="section"><h2>Notes</h2><div class="notes">${escapeHtml(workspace.notes)}</div></section>`
        : ''
    }
    <section class="section">
      <h2>Highlights</h2>
      <ul>${highlights.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>
    </section>
    <section class="section">
      <h2>Risks</h2>
      <ul>${safeRisks.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>
    </section>
  </body>
</html>`;
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
