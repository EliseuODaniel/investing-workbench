import { useMemo, useState } from 'react';
import type { InvestmentCatalogPayload } from '../../types/api';

interface InvestmentOrganizerParityPanelProps {
  parity?: InvestmentCatalogPayload['investor_easy_parity'];
}

type OrganizerTab = 'summary' | 'calculators' | 'goals' | 'portfolio' | 'alerts' | 'report';

interface GoalItem {
  id: string;
  label: string;
  target: number;
  current: number;
  monthly: number;
  months: number;
}

interface PositionItem {
  id: string;
  ticker: string;
  assetClass: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
}

interface CalculatorInputs {
  principal: number;
  monthly: number;
  annualRate: number;
  years: number;
  target: number;
  inflation: number;
  monthlyIncome: number;
  dividendYield: number;
  expenses: number;
}

const tabs: Array<{ id: OrganizerTab; label: string }> = [
  { id: 'summary', label: 'Resumo' },
  { id: 'calculators', label: 'Calculadoras' },
  { id: 'goals', label: 'Metas' },
  { id: 'portfolio', label: 'Carteira' },
  { id: 'alerts', label: 'Alertas' },
  { id: 'report', label: 'Relatorio' },
];

const defaultInputs: CalculatorInputs = {
  principal: 10000,
  monthly: 1000,
  annualRate: 10,
  years: 10,
  target: 500000,
  inflation: 4,
  monthlyIncome: 5000,
  dividendYield: 8,
  expenses: 6000,
};

const defaultGoals: GoalItem[] = [
  {
    id: 'goal_reserve',
    label: 'Reserva de emergencia',
    target: 60000,
    current: 28000,
    monthly: 2500,
    months: 12,
  },
];

const defaultPositions: PositionItem[] = [
  {
    id: 'pos_selic',
    ticker: 'SELIC/CDI',
    assetClass: 'Renda fixa',
    quantity: 1,
    averagePrice: 32000,
    currentPrice: 32000,
  },
  {
    id: 'pos_fii',
    ticker: 'FIIs',
    assetClass: 'FIIs',
    quantity: 1,
    averagePrice: 18000,
    currentPrice: 18600,
  },
];

export default function InvestmentOrganizerParityPanel({
  parity,
}: InvestmentOrganizerParityPanelProps) {
  const [activeTab, setActiveTab] = useState<OrganizerTab>('summary');
  const [inputs, setInputs] = useState<CalculatorInputs>(defaultInputs);
  const [goals, setGoals] = useState<GoalItem[]>(() =>
    readStoredList('investing-workbench-goals', defaultGoals)
  );
  const [positions, setPositions] = useState<PositionItem[]>(() =>
    readStoredList('investing-workbench-positions', defaultPositions)
  );

  const dashboard = useMemo(() => buildDashboard(goals, positions), [goals, positions]);
  const alerts = useMemo(() => buildAlerts(goals, positions), [goals, positions]);

  if (!parity) {
    return null;
  }

  function updateInput(field: keyof CalculatorInputs, value: number) {
    setInputs((current) => ({ ...current, [field]: value }));
  }

  function updateGoal(id: string, field: keyof GoalItem, value: string | number) {
    const next = goals.map((goal) => (goal.id === id ? { ...goal, [field]: value } : goal));
    setGoals(next);
    writeStoredList('investing-workbench-goals', next);
  }

  function updatePosition(id: string, field: keyof PositionItem, value: string | number) {
    const next = positions.map((position) =>
      position.id === id ? { ...position, [field]: value } : position
    );
    setPositions(next);
    writeStoredList('investing-workbench-positions', next);
  }

  function addGoal() {
    const next = [
      ...goals,
      {
        id: `goal_${Date.now()}`,
        label: 'Nova meta',
        target: 100000,
        current: 0,
        monthly: 1000,
        months: 36,
      },
    ];
    setGoals(next);
    writeStoredList('investing-workbench-goals', next);
  }

  function addPosition() {
    const next = [
      ...positions,
      {
        id: `pos_${Date.now()}`,
        ticker: 'NOVO',
        assetClass: 'Outros',
        quantity: 1,
        averagePrice: 1000,
        currentPrice: 1000,
      },
    ];
    setPositions(next);
    writeStoredList('investing-workbench-positions', next);
  }

  function exportHtmlReport() {
    const html = buildHtmlReport({ goals, positions, dashboard, alerts });
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'relatorio-investimentos.html';
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/60">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
            {parity.title}
          </div>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-gray-600 dark:text-gray-300">
            {parity.plain_language_summary}
          </p>
        </div>
        <div className="rounded-full border border-emerald-300 bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-100">
          {parity.available_calculator_count}/{parity.calculator_count} calculadoras
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`rounded-full border px-3 py-2 text-xs font-medium ${
              activeTab === tab.id
                ? 'border-blue-300 bg-blue-50 text-blue-800 dark:border-blue-700 dark:bg-blue-950/30 dark:text-blue-100'
                : 'border-gray-300 text-gray-600 dark:border-gray-700 dark:text-gray-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'summary' ? (
        <SummaryView parity={parity} dashboard={dashboard} />
      ) : null}

      {activeTab === 'calculators' ? (
        <CalculatorView parity={parity} inputs={inputs} onChange={updateInput} />
      ) : null}

      {activeTab === 'goals' ? (
        <GoalsView goals={goals} onAdd={addGoal} onChange={updateGoal} />
      ) : null}

      {activeTab === 'portfolio' ? (
        <PortfolioView positions={positions} onAdd={addPosition} onChange={updatePosition} />
      ) : null}

      {activeTab === 'alerts' ? <AlertsView alerts={alerts} /> : null}

      {activeTab === 'report' ? (
        <ReportView dashboard={dashboard} alerts={alerts} onExport={exportHtmlReport} />
      ) : null}
    </section>
  );
}

function SummaryView({
  parity,
  dashboard,
}: {
  parity: NonNullable<InvestmentCatalogPayload['investor_easy_parity']>;
  dashboard: ReturnType<typeof buildDashboard>;
}) {
  return (
    <div className="mt-5 space-y-5">
      <div className="grid gap-3 lg:grid-cols-4">
        <MetricCard label="Patrimonio acompanhado" value={formatCurrency(dashboard.totalValue)} />
        <MetricCard label="Metas ativas" value={String(dashboard.goalCount)} />
        <MetricCard label="Progresso medio" value={formatPercent(dashboard.averageGoalProgress)} />
        <MetricCard label="Aporte mensal planejado" value={formatCurrency(dashboard.monthlyPlanned)} />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <FeatureCoverage parity={parity} />
        <CalculatorCatalog parity={parity} />
      </div>

      {parity.remaining_gaps.length ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs leading-5 text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/20 dark:text-amber-100">
          Lacunas restantes: {parity.remaining_gaps.join(' · ')}
        </div>
      ) : null}
    </div>
  );
}

function CalculatorView({
  parity,
  inputs,
  onChange,
}: {
  parity: NonNullable<InvestmentCatalogPayload['investor_easy_parity']>;
  inputs: CalculatorInputs;
  onChange: (field: keyof CalculatorInputs, value: number) => void;
}) {
  const results = buildCalculatorResults(parity, inputs);
  return (
    <div className="mt-5 grid gap-4 xl:grid-cols-[320px_1fr]">
      <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-950/40">
        <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
          Premissas rápidas
        </div>
        <div className="mt-3 grid gap-3">
          <NumberInput label="Capital inicial" value={inputs.principal} onChange={(value) => onChange('principal', value)} />
          <NumberInput label="Aporte mensal" value={inputs.monthly} onChange={(value) => onChange('monthly', value)} />
          <NumberInput label="Taxa anual %" value={inputs.annualRate} onChange={(value) => onChange('annualRate', value)} />
          <NumberInput label="Prazo em anos" value={inputs.years} onChange={(value) => onChange('years', value)} />
          <NumberInput label="Meta patrimonial" value={inputs.target} onChange={(value) => onChange('target', value)} />
          <NumberInput label="Inflação anual %" value={inputs.inflation} onChange={(value) => onChange('inflation', value)} />
          <NumberInput label="Renda mensal alvo" value={inputs.monthlyIncome} onChange={(value) => onChange('monthlyIncome', value)} />
          <NumberInput label="Yield anual %" value={inputs.dividendYield} onChange={(value) => onChange('dividendYield', value)} />
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {results.map((result) => (
          <article
            key={result.calculator_id}
            className="rounded-xl border border-blue-200 bg-blue-50/70 p-4 dark:border-blue-900/50 dark:bg-blue-950/20"
          >
            <div className="text-sm font-semibold text-blue-950 dark:text-blue-100">
              {result.label}
            </div>
            <div className="mt-2 text-xl font-semibold text-blue-950 dark:text-blue-100">
              {result.displayValue}
            </div>
            <p className="mt-2 text-xs leading-5 text-blue-900/80 dark:text-blue-100/80">
              {result.explanation}
            </p>
          </article>
        ))}
      </div>
    </div>
  );
}

function GoalsView({
  goals,
  onAdd,
  onChange,
}: {
  goals: GoalItem[];
  onAdd: () => void;
  onChange: (id: string, field: keyof GoalItem, value: string | number) => void;
}) {
  return (
    <div className="mt-5 rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-950/40">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
          Metas financeiras persistentes
        </div>
        <button type="button" className="btn-secondary" onClick={onAdd}>
          Adicionar meta
        </button>
      </div>
      <div className="mt-4 grid gap-3 xl:grid-cols-2">
        {goals.map((goal) => {
          const progress = goal.target > 0 ? goal.current / goal.target : 0;
          const required = Math.max(goal.target - goal.current, 0) / Math.max(goal.months, 1);
          return (
            <article key={goal.id} className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900/60">
              <input
                value={goal.label}
                onChange={(event) => onChange(goal.id, 'label', event.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-950"
              />
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                <NumberInput label="Alvo" value={goal.target} onChange={(value) => onChange(goal.id, 'target', value)} />
                <NumberInput label="Atual" value={goal.current} onChange={(value) => onChange(goal.id, 'current', value)} />
                <NumberInput label="Aporte planejado" value={goal.monthly} onChange={(value) => onChange(goal.id, 'monthly', value)} />
                <NumberInput label="Meses restantes" value={goal.months} onChange={(value) => onChange(goal.id, 'months', value)} />
              </div>
              <div className="mt-3 text-xs text-gray-600 dark:text-gray-300">
                Progresso: {formatPercent(progress)} · aporte necessario: {formatCurrency(required)}
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}

function PortfolioView({
  positions,
  onAdd,
  onChange,
}: {
  positions: PositionItem[];
  onAdd: () => void;
  onChange: (id: string, field: keyof PositionItem, value: string | number) => void;
}) {
  return (
    <div className="mt-5 rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-950/40">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
          Carteira manual e preço médio
        </div>
        <button type="button" className="btn-secondary" onClick={onAdd}>
          Adicionar posição
        </button>
      </div>
      <div className="mt-4 grid gap-3">
        {positions.map((position) => {
          const invested = position.quantity * position.averagePrice;
          const current = position.quantity * position.currentPrice;
          const pnl = invested > 0 ? current / invested - 1 : 0;
          return (
            <article key={position.id} className="grid gap-2 rounded-xl border border-gray-200 bg-white p-4 text-xs dark:border-gray-800 dark:bg-gray-900/60 md:grid-cols-6">
              <TextInput label="Ticker" value={position.ticker} onChange={(value) => onChange(position.id, 'ticker', value)} />
              <TextInput label="Classe" value={position.assetClass} onChange={(value) => onChange(position.id, 'assetClass', value)} />
              <NumberInput label="Quantidade" value={position.quantity} onChange={(value) => onChange(position.id, 'quantity', value)} />
              <NumberInput label="Preço médio" value={position.averagePrice} onChange={(value) => onChange(position.id, 'averagePrice', value)} />
              <NumberInput label="Preço atual" value={position.currentPrice} onChange={(value) => onChange(position.id, 'currentPrice', value)} />
              <div className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 dark:border-gray-800 dark:bg-gray-950/40">
                <div className="text-[11px] text-gray-500">Resultado</div>
                <div className="mt-1 font-semibold text-gray-950 dark:text-gray-100">
                  {formatCurrency(current)} · {formatPercent(pnl)}
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}

function AlertsView({ alerts }: { alerts: string[] }) {
  return (
    <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-900/60 dark:bg-amber-950/20">
      <div className="text-sm font-semibold text-amber-950 dark:text-amber-100">
        Alertas pessoais
      </div>
      <div className="mt-3 space-y-2">
        {alerts.map((alert) => (
          <div key={alert} className="rounded-lg border border-amber-200 bg-white px-3 py-2 text-xs text-amber-900 dark:border-amber-800 dark:bg-gray-950/30 dark:text-amber-100">
            {alert}
          </div>
        ))}
      </div>
    </div>
  );
}

function ReportView({
  dashboard,
  alerts,
  onExport,
}: {
  dashboard: ReturnType<typeof buildDashboard>;
  alerts: string[];
  onExport: () => void;
}) {
  return (
    <div className="mt-5 rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-950/40">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
            Relatório mensal exportável
          </div>
          <p className="mt-1 text-xs text-gray-600 dark:text-gray-300">
            Gera HTML local com patrimônio, metas, carteira e alertas. PDF fica para impressão do navegador.
          </p>
        </div>
        <button type="button" className="btn-secondary" onClick={onExport}>
          Exportar HTML
        </button>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <MetricCard label="Patrimônio" value={formatCurrency(dashboard.totalValue)} />
        <MetricCard label="Metas" value={String(dashboard.goalCount)} />
        <MetricCard label="Alertas" value={String(alerts.length)} />
      </div>
    </div>
  );
}

function FeatureCoverage({
  parity,
}: {
  parity: NonNullable<InvestmentCatalogPayload['investor_easy_parity']>;
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-950/40">
      <div className="text-sm font-semibold text-gray-950 dark:text-gray-100">
        Funcionalidades comparadas
      </div>
      <div className="mt-3 space-y-2">
        {parity.feature_coverage.map((feature) => (
          <div key={feature.feature_id} className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs dark:border-gray-800 dark:bg-gray-900/60">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="font-semibold text-gray-950 dark:text-gray-100">
                {feature.label}
              </span>
              <StatusLabel status={feature.local_status} />
            </div>
            <p className="mt-1 leading-5 text-gray-600 dark:text-gray-300">
              {feature.local_surface}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

function CalculatorCatalog({
  parity,
}: {
  parity: NonNullable<InvestmentCatalogPayload['investor_easy_parity']>;
}) {
  return (
    <div className="rounded-xl border border-blue-200 bg-blue-50/70 p-4 dark:border-blue-900/50 dark:bg-blue-950/20">
      <div className="text-sm font-semibold text-blue-950 dark:text-blue-100">
        15 calculadoras educativas
      </div>
      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        {parity.calculator_suite.map((calculator) => (
          <div key={calculator.calculator_id} className="rounded-lg border border-blue-200 bg-white px-3 py-2 text-xs dark:border-blue-800 dark:bg-gray-950/30">
            <div className="font-semibold text-blue-950 dark:text-blue-100">
              {calculator.label}
            </div>
            <div className="mt-1 text-[11px] text-blue-900/75 dark:text-blue-100/75">
              {calculator.tier} · {calculator.formula_family}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function NumberInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="text-xs text-gray-600 dark:text-gray-300">
      {label}
      <input
        type="number"
        value={Number.isFinite(value) ? value : 0}
        onChange={(event) => onChange(Number(event.target.value))}
        className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-950 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
      />
    </label>
  );
}

function TextInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="text-xs text-gray-600 dark:text-gray-300">
      {label}
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-950 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
      />
    </label>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-950/40">
      <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
      <div className="mt-1 text-lg font-semibold text-gray-950 dark:text-gray-100">{value}</div>
    </div>
  );
}

function StatusLabel({ status }: { status: string }) {
  const label =
    status === 'available'
      ? 'coberto'
      : status === 'partial'
        ? 'parcial'
        : status === 'not_applicable_local_first'
          ? 'local-first'
          : 'pendente';
  return (
    <span className="rounded-full border border-gray-300 px-2 py-1 text-[11px] text-gray-600 dark:border-gray-700 dark:text-gray-300">
      {label}
    </span>
  );
}

function buildDashboard(goals: GoalItem[], positions: PositionItem[]) {
  const totalValue = positions.reduce(
    (total, item) => total + item.quantity * item.currentPrice,
    0
  );
  const monthlyPlanned = goals.reduce((total, goal) => total + goal.monthly, 0);
  const averageGoalProgress =
    goals.length === 0
      ? 0
      : goals.reduce((total, goal) => total + goal.current / Math.max(goal.target, 1), 0) /
        goals.length;
  return {
    totalValue,
    monthlyPlanned,
    averageGoalProgress,
    goalCount: goals.length,
  };
}

function buildAlerts(goals: GoalItem[], positions: PositionItem[]) {
  const alerts: string[] = [];
  for (const goal of goals) {
    const required = Math.max(goal.target - goal.current, 0) / Math.max(goal.months, 1);
    if (goal.monthly < required) {
      alerts.push(`${goal.label}: aporte planejado abaixo do necessario.`);
    }
  }
  const total = positions.reduce((sum, item) => sum + item.quantity * item.currentPrice, 0);
  const byClass = positions.reduce<Record<string, number>>((acc, item) => {
    acc[item.assetClass] = (acc[item.assetClass] ?? 0) + item.quantity * item.currentPrice;
    return acc;
  }, {});
  for (const [assetClass, value] of Object.entries(byClass)) {
    if (total > 0 && value / total > 0.6) {
      alerts.push(`${assetClass}: concentração acima de 60% da carteira manual.`);
    }
  }
  return alerts.length ? alerts : ['Nenhum alerta pessoal relevante com as premissas atuais.'];
}

function buildCalculatorResults(
  parity: NonNullable<InvestmentCatalogPayload['investor_easy_parity']>,
  inputs: CalculatorInputs
) {
  const monthlyRate = (inputs.annualRate / 100) / 12;
  const months = Math.max(1, Math.round(inputs.years * 12));
  const futureValue =
    inputs.principal * (1 + monthlyRate) ** months +
    inputs.monthly * (((1 + monthlyRate) ** months - 1) / Math.max(monthlyRate, 0.000001));
  const realRate = ((1 + inputs.annualRate / 100) / (1 + inputs.inflation / 100) - 1) * 100;
  const incomeCapital = inputs.dividendYield > 0
    ? (inputs.monthlyIncome * 12) / (inputs.dividendYield / 100)
    : 0;

  return parity.calculator_suite.map((calculator) => {
    const value = calculatorValue(calculator.calculator_id, {
      ...inputs,
      months,
      futureValue,
      realRate,
      incomeCapital,
    });
    return {
      ...calculator,
      displayValue: value.kind === 'percent' ? formatPercent(value.value) : formatCurrency(value.value),
      explanation: calculator.local_surface,
    };
  });
}

function calculatorValue(
  calculatorId: string,
  values: CalculatorInputs & {
    months: number;
    futureValue: number;
    realRate: number;
    incomeCapital: number;
  }
) {
  const remaining = Math.max(values.target - values.principal, 0);
  const monthlyRequired = remaining / Math.max(values.months, 1);
  const invested = values.principal + values.monthly * values.months;
  const allocationBase = values.futureValue / 4;
  const map: Record<string, { value: number; kind?: 'currency' | 'percent' }> = {
    compound_interest: { value: values.futureValue },
    monthly_contribution_target: { value: monthlyRequired },
    future_value_with_contributions: { value: values.futureValue },
    real_return_after_inflation: { value: values.realRate / 100, kind: 'percent' },
    emergency_reserve: { value: values.expenses * 6 },
    passive_income_target: { value: values.incomeCapital },
    dividend_yield_income: { value: values.principal * (values.dividendYield / 100) / 12 },
    retirement_number: { value: values.monthlyIncome * 12 * 25 },
    safe_withdrawal: { value: values.principal * 0.04 / 12 },
    portfolio_rebalance: { value: allocationBase },
    asset_allocation: { value: allocationBase },
    average_price: { value: values.principal / 100 },
    accumulated_return: { value: invested > 0 ? values.futureValue / invested - 1 : 0, kind: 'percent' },
    net_fixed_income_equivalence: { value: values.annualRate * 0.85 / 100, kind: 'percent' },
    financial_independence: { value: values.expenses * 12 * 25 },
  };
  return map[calculatorId] ?? { value: values.futureValue };
}

function buildHtmlReport({
  goals,
  positions,
  dashboard,
  alerts,
}: {
  goals: GoalItem[];
  positions: PositionItem[];
  dashboard: ReturnType<typeof buildDashboard>;
  alerts: string[];
}) {
  return `<!doctype html>
<html lang="pt-BR">
<meta charset="utf-8" />
<title>Relatorio mensal de investimentos</title>
<body>
<h1>Relatorio mensal de investimentos</h1>
<p>Patrimonio acompanhado: ${formatCurrency(dashboard.totalValue)}</p>
<p>Progresso medio das metas: ${formatPercent(dashboard.averageGoalProgress)}</p>
<h2>Metas</h2>
<ul>${goals.map((goal) => `<li>${goal.label}: ${formatCurrency(goal.current)} de ${formatCurrency(goal.target)}</li>`).join('')}</ul>
<h2>Carteira</h2>
<ul>${positions.map((item) => `<li>${item.ticker}: ${formatCurrency(item.quantity * item.currentPrice)}</li>`).join('')}</ul>
<h2>Alertas</h2>
<ul>${alerts.map((alert) => `<li>${alert}</li>`).join('')}</ul>
</body>
</html>`;
}

function readStoredList<T>(key: string, fallback: T[]): T[] {
  if (typeof window === 'undefined') {
    return fallback;
  }
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function writeStoredList<T>(key: string, value: T[]) {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.setItem(key, JSON.stringify(value));
}

function formatCurrency(value: number) {
  return value.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 0,
  });
}

function formatPercent(value: number) {
  return value.toLocaleString('pt-BR', {
    style: 'percent',
    maximumFractionDigits: 1,
  });
}
