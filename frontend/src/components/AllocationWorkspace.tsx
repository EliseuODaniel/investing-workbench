import { ChangeEvent, useEffect, useState } from 'react';
import {
  Download,
  FolderOpen,
  Loader2,
  Plus,
  RefreshCw,
  Save,
  ShieldAlert,
  Trash2,
  Upload,
  Wand2,
} from 'lucide-react';
import SectionTabs from './app-shell/SectionTabs';
import { useAllocationWorkspaces } from '../hooks/useAllocationWorkspaces';
import { apiClient } from '../lib/api';
import {
  cn,
  downloadJSON,
  formatCurrency,
  formatDateTime,
  formatNumber,
  formatPercent,
} from '../lib/utils';
import {
  AllocationPlanRequestPayload,
  AllocationPlanResponsePayload,
  AllocationWorkspacePayload,
} from '../types/api';

type AllocationTab = 'planner' | 'saved';

type AllocationAssetDraft = {
  id: string;
  asset: string;
  quantity: string;
  price: string;
  targetWeight: string;
};

interface AllocationWorkspaceProps {
  onError: (message: string | null) => void;
}

const DEFAULT_CASH = '2000';
const DEFAULT_WEIGHT_TOLERANCE = '0.02';
const DEFAULT_MIN_TRADE_NOTIONAL = '250';
const DEFAULT_RESERVE_CASH = '500';

function makeDraftRow(overrides: Partial<AllocationAssetDraft> = {}): AllocationAssetDraft {
  return {
    id: `${Date.now()}_${Math.random().toString(16).slice(2)}`,
    asset: '',
    quantity: '',
    price: '',
    targetWeight: '',
    ...overrides,
  };
}

function buildExampleRows(): AllocationAssetDraft[] {
  return [
    makeDraftRow({ asset: 'BTC-BRL', quantity: '0.05', price: '60000', targetWeight: '0.5' }),
    makeDraftRow({ asset: 'ETH-USD', quantity: '2', price: '2000', targetWeight: '0.2' }),
    makeDraftRow({ asset: 'SPY', quantity: '0', price: '900', targetWeight: '0.1' }),
  ];
}

function parseNumber(value: string): number {
  if (!value.trim()) {
    return 0;
  }
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : 0;
}

function buildRequestFromDraft(params: {
  cash: string;
  rows: AllocationAssetDraft[];
  weightTolerance: string;
  minTradeNotional: string;
  reserveCash: string;
}): AllocationPlanRequestPayload {
  const normalizedRows = params.rows
    .map((row) => ({
      asset: row.asset.trim(),
      quantity: parseNumber(row.quantity),
      price: parseNumber(row.price),
      targetWeight: parseNumber(row.targetWeight),
    }))
    .filter((row) => row.asset || row.quantity > 0 || row.price > 0 || row.targetWeight > 0)
    .filter((row) => row.asset.length > 0);

  return {
    cash: parseNumber(params.cash),
    holdings: normalizedRows
      .filter((row) => row.quantity > 0)
      .map((row) => ({ asset: row.asset, quantity: row.quantity })),
    prices: Object.fromEntries(
      normalizedRows.filter((row) => row.price > 0).map((row) => [row.asset, row.price])
    ),
    targets: normalizedRows
      .filter((row) => row.targetWeight > 0)
      .map((row) => ({ asset: row.asset, target_weight: row.targetWeight })),
    weight_tolerance: parseNumber(params.weightTolerance),
    min_trade_notional: parseNumber(params.minTradeNotional),
    reserve_cash: parseNumber(params.reserveCash),
  };
}

function buildDraftRowsFromWorkspace(
  workspace: AllocationWorkspacePayload
): AllocationAssetDraft[] {
  const assetOrder = workspace.summary.assets.length
    ? workspace.summary.assets
    : Array.from(
        new Set([
          ...workspace.request.holdings.map((holding) => holding.asset),
          ...workspace.request.targets.map((target) => target.asset),
          ...Object.keys(workspace.request.prices),
        ])
      ).sort();

  return assetOrder.map((asset) => {
    const holding = workspace.request.holdings.find((item) => item.asset === asset);
    const target = workspace.request.targets.find((item) => item.asset === asset);
    return makeDraftRow({
      asset,
      quantity: holding ? String(holding.quantity) : '',
      price:
        workspace.request.prices[asset] !== undefined
          ? String(workspace.request.prices[asset])
          : '',
      targetWeight: target ? String(target.target_weight) : '',
    });
  });
}

function actionTone(action: AllocationPlanResponsePayload['actions'][number]['action']): string {
  if (action === 'buy') {
    return 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300';
  }
  if (action === 'sell') {
    return 'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300';
  }
  return 'border-gray-200 bg-gray-50 text-gray-700 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300';
}

export default function AllocationWorkspace({ onError }: AllocationWorkspaceProps) {
  const [activeTab, setActiveTab] = useState<AllocationTab>('planner');
  const [rows, setRows] = useState<AllocationAssetDraft[]>([makeDraftRow()]);
  const [cash, setCash] = useState(DEFAULT_CASH);
  const [weightTolerance, setWeightTolerance] = useState(DEFAULT_WEIGHT_TOLERANCE);
  const [minTradeNotional, setMinTradeNotional] = useState(DEFAULT_MIN_TRADE_NOTIONAL);
  const [reserveCash, setReserveCash] = useState(DEFAULT_RESERVE_CASH);
  const [workspaceName, setWorkspaceName] = useState('');
  const [workspaceNotes, setWorkspaceNotes] = useState('');
  const [plan, setPlan] = useState<AllocationPlanResponsePayload | null>(null);
  const [isPlanning, setIsPlanning] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(null);
  const { workspaces, isLoading, refresh, deleteWorkspace } = useAllocationWorkspaces(onError);

  const tabs = [
    { id: 'planner' as const, label: 'Planner' },
    { id: 'saved' as const, label: 'Salvos', badge: workspaces.length },
  ];

  const sanitizedRequest = buildRequestFromDraft({
    cash,
    rows,
    weightTolerance,
    minTradeNotional,
    reserveCash,
  });

  const draftTargetWeight = sanitizedRequest.targets.reduce(
    (sum, target) => sum + target.target_weight,
    0
  );
  const draftInvestedValue = rows.reduce(
    (sum, row) => sum + parseNumber(row.quantity) * parseNumber(row.price),
    0
  );
  const draftEquity = parseNumber(cash) + draftInvestedValue;
  const selectedWorkspace =
    workspaces.find((workspace) => workspace.workspace_id === selectedWorkspaceId) ?? null;

  useEffect(() => {
    if (!workspaces.length) {
      setSelectedWorkspaceId(null);
      return;
    }

    setSelectedWorkspaceId((current) => {
      if (current && workspaces.some((workspace) => workspace.workspace_id === current)) {
        return current;
      }
      return workspaces[0]?.workspace_id ?? null;
    });
  }, [workspaces]);

  function updateRow(id: string, field: keyof Omit<AllocationAssetDraft, 'id'>, value: string) {
    setRows((current) =>
      current.map((row) => (row.id === id ? { ...row, [field]: value } : row))
    );
  }

  function addRow() {
    setRows((current) => [...current, makeDraftRow()]);
  }

  function removeRow(id: string) {
    setRows((current) => (current.length > 1 ? current.filter((row) => row.id !== id) : current));
  }

  function resetDraft() {
    setRows([makeDraftRow()]);
    setCash(DEFAULT_CASH);
    setWeightTolerance(DEFAULT_WEIGHT_TOLERANCE);
    setMinTradeNotional(DEFAULT_MIN_TRADE_NOTIONAL);
    setReserveCash(DEFAULT_RESERVE_CASH);
    setWorkspaceName('');
    setWorkspaceNotes('');
    setPlan(null);
    onError(null);
  }

  function loadExample() {
    setRows(buildExampleRows());
    setCash(DEFAULT_CASH);
    setWeightTolerance(DEFAULT_WEIGHT_TOLERANCE);
    setMinTradeNotional(DEFAULT_MIN_TRADE_NOTIONAL);
    setReserveCash(DEFAULT_RESERVE_CASH);
    setPlan(null);
    onError(null);
  }

  async function planRebalance() {
    setIsPlanning(true);
    try {
      const response = await apiClient.buildAllocationPlan(sanitizedRequest);
      setPlan(response);
      onError(null);
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to build allocation plan');
    } finally {
      setIsPlanning(false);
    }
  }

  async function saveWorkspace() {
    if (!plan) {
      onError('Build a rebalance plan before saving a workspace');
      return;
    }

    setIsSaving(true);
    try {
      const workspace = await apiClient.saveAllocationWorkspace({
        name: workspaceName || undefined,
        notes: workspaceNotes || undefined,
        request: sanitizedRequest,
      });
      await refresh();
      setSelectedWorkspaceId(workspace.workspace_id);
      setActiveTab('saved');
      onError(null);
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to save allocation workspace');
    } finally {
      setIsSaving(false);
    }
  }

  function loadWorkspaceIntoPlanner(workspace: AllocationWorkspacePayload) {
    setRows(buildDraftRowsFromWorkspace(workspace));
    setCash(String(workspace.request.cash));
    setWeightTolerance(String(workspace.request.weight_tolerance ?? 0));
    setMinTradeNotional(String(workspace.request.min_trade_notional ?? 0));
    setReserveCash(String(workspace.request.reserve_cash ?? 0));
    setWorkspaceName(workspace.name);
    setWorkspaceNotes(workspace.notes ?? '');
    setPlan(workspace.plan);
    setActiveTab('planner');
    onError(null);
  }

  async function importWorkspace(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setIsImporting(true);
    try {
      const payload = JSON.parse(await file.text());
      const workspace = await apiClient.importAllocationWorkspace({ payload });
      await refresh();
      setSelectedWorkspaceId(workspace.workspace_id);
      onError(null);
    } catch (error: any) {
      onError(error.response?.data?.detail || error?.message || 'Failed to import allocation workspace');
    } finally {
      event.target.value = '';
      setIsImporting(false);
    }
  }

  async function removeWorkspace(workspaceId: string) {
    if (!window.confirm('Excluir workspace salvo? Esta acao nao pode ser desfeita.')) {
      return;
    }

    await deleteWorkspace(workspaceId);
    if (selectedWorkspaceId === workspaceId) {
      setSelectedWorkspaceId(null);
    }
    onError(null);
  }

  return (
    <div className="space-y-6">
      <div className="card bg-gradient-to-br from-emerald-50 via-white to-cyan-50 dark:from-emerald-950/20 dark:via-gray-800 dark:to-cyan-950/20">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Allocation Workspace
            </h2>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Monte um retrato atual da carteira, defina pesos-alvo e gere um plano de
              rebalanceamento com cash floor, tolerancia e filtro minimo de notional.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void refresh()}
              className="inline-flex items-center rounded-md border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Atualizar
            </button>
            <button
              type="button"
              onClick={loadExample}
              className="inline-flex items-center rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700 transition-colors hover:bg-emerald-100 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-200 dark:hover:bg-emerald-900/40"
            >
              <Wand2 className="mr-2 h-4 w-4" />
              Carregar Exemplo
            </button>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-4">
          <div className="rounded-lg border border-white/70 bg-white/80 px-4 py-3 dark:border-gray-700 dark:bg-gray-900/40">
            <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Equity Draft
            </div>
            <div className="mt-2 text-lg font-semibold text-gray-900 dark:text-gray-100">
              {formatCurrency(draftEquity)}
            </div>
          </div>
          <div className="rounded-lg border border-white/70 bg-white/80 px-4 py-3 dark:border-gray-700 dark:bg-gray-900/40">
            <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Cash Atual
            </div>
            <div className="mt-2 text-lg font-semibold text-gray-900 dark:text-gray-100">
              {formatCurrency(parseNumber(cash))}
            </div>
          </div>
          <div className="rounded-lg border border-white/70 bg-white/80 px-4 py-3 dark:border-gray-700 dark:bg-gray-900/40">
            <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Peso-Alvo Somado
            </div>
            <div className="mt-2 text-lg font-semibold text-gray-900 dark:text-gray-100">
              {formatPercent(draftTargetWeight)}
            </div>
          </div>
          <div className="rounded-lg border border-white/70 bg-white/80 px-4 py-3 dark:border-gray-700 dark:bg-gray-900/40">
            <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Workspaces Salvos
            </div>
            <div className="mt-2 text-lg font-semibold text-gray-900 dark:text-gray-100">
              {workspaces.length}
            </div>
          </div>
        </div>

        <div className="mt-4">
          <SectionTabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
        </div>
      </div>

      {activeTab === 'planner' && (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <div className="card space-y-6">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                  Draft da Carteira
                </h3>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  Cada linha combina ativo, quantidade atual, preco e peso desejado.
                </p>
              </div>
              <button
                type="button"
                onClick={resetDraft}
                className="inline-flex items-center rounded-md border border-gray-200 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Limpar
              </button>
            </div>

            <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-900/40">
                  <tr className="text-left text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    <th className="px-4 py-3">Ativo</th>
                    <th className="px-4 py-3">Quantidade</th>
                    <th className="px-4 py-3">Preco</th>
                    <th className="px-4 py-3">Peso-Alvo</th>
                    <th className="px-4 py-3 text-right">Acao</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
                  {rows.map((row) => (
                    <tr key={row.id}>
                      <td className="px-4 py-3">
                        <input
                          value={row.asset}
                          onChange={(event) => updateRow(row.id, 'asset', event.target.value)}
                          className="form-input"
                          placeholder="BTC-BRL"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          value={row.quantity}
                          onChange={(event) => updateRow(row.id, 'quantity', event.target.value)}
                          className="form-input"
                          inputMode="decimal"
                          placeholder="0.0"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          value={row.price}
                          onChange={(event) => updateRow(row.id, 'price', event.target.value)}
                          className="form-input"
                          inputMode="decimal"
                          placeholder="0.0"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          value={row.targetWeight}
                          onChange={(event) => updateRow(row.id, 'targetWeight', event.target.value)}
                          className="form-input"
                          inputMode="decimal"
                          placeholder="0.25"
                        />
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          type="button"
                          onClick={() => removeRow(row.id)}
                          className="inline-flex items-center rounded-md border border-gray-200 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
                          disabled={rows.length === 1}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <button
              type="button"
              onClick={addRow}
              className="inline-flex items-center rounded-md border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
            >
              <Plus className="mr-2 h-4 w-4" />
              Adicionar Ativo
            </button>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <label className="space-y-2">
                <span className="form-label">Cash Atual</span>
                <input value={cash} onChange={(event) => setCash(event.target.value)} className="form-input" inputMode="decimal" />
              </label>
              <label className="space-y-2">
                <span className="form-label">Cash de Reserva</span>
                <input
                  value={reserveCash}
                  onChange={(event) => setReserveCash(event.target.value)}
                  className="form-input"
                  inputMode="decimal"
                />
              </label>
              <label className="space-y-2">
                <span className="form-label">Tolerancia de Peso</span>
                <input
                  value={weightTolerance}
                  onChange={(event) => setWeightTolerance(event.target.value)}
                  className="form-input"
                  inputMode="decimal"
                />
              </label>
              <label className="space-y-2">
                <span className="form-label">Notional Minimo</span>
                <input
                  value={minTradeNotional}
                  onChange={(event) => setMinTradeNotional(event.target.value)}
                  className="form-input"
                  inputMode="decimal"
                />
              </label>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <label className="space-y-2">
                <span className="form-label">Nome do Workspace</span>
                <input
                  value={workspaceName}
                  onChange={(event) => setWorkspaceName(event.target.value)}
                  className="form-input"
                  placeholder="Carteira defensiva abril"
                />
              </label>
              <label className="space-y-2 md:col-span-1">
                <span className="form-label">Notas</span>
                <textarea
                  value={workspaceNotes}
                  onChange={(event) => setWorkspaceNotes(event.target.value)}
                  className="form-input min-h-[96px]"
                  placeholder="Premissas, restricoes e contexto do rebalanceamento"
                />
              </label>
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => void planRebalance()}
                className="inline-flex items-center rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-gray-800 disabled:opacity-60 dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-gray-200"
                disabled={isPlanning}
              >
                {isPlanning ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <ShieldAlert className="mr-2 h-4 w-4" />
                )}
                Planejar Rebalanceamento
              </button>
              <button
                type="button"
                onClick={() => void saveWorkspace()}
                className="inline-flex items-center rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-700 transition-colors hover:bg-emerald-100 disabled:opacity-60 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-200 dark:hover:bg-emerald-900/40"
                disabled={!plan || isSaving}
              >
                {isSaving ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Save className="mr-2 h-4 w-4" />
                )}
                Salvar Workspace
              </button>
            </div>

            {draftTargetWeight > 1 && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">
                Os pesos-alvo somam {formatPercent(draftTargetWeight)}. O backend rejeita valores acima de 100%.
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div className="card">
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                Resumo do Plano
              </h3>
              {plan ? (
                <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                  <MetricCard label="Equity Total" value={formatCurrency(plan.total_equity)} />
                  <MetricCard label="Turnover" value={formatCurrency(plan.turnover_notional)} />
                  <MetricCard label="Cash Atual" value={formatCurrency(plan.current_cash)} />
                  <MetricCard label="Cash Projetado" value={formatCurrency(plan.projected_cash)} />
                  <MetricCard label="Cash Target" value={formatPercent(plan.target_cash_weight)} />
                  <MetricCard label="Drift Maximo" value={formatPercent(plan.max_abs_drift_weight)} />
                </div>
              ) : (
                <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">
                  O resultado aparece aqui depois que o planner calcula as acoes por ativo.
                </p>
              )}
            </div>

            <div className="card">
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                Acoes Recomendadas
              </h3>
              {plan ? (
                <div className="mt-4 space-y-3">
                  {plan.actions.map((action) => (
                    <div
                      key={`${action.asset}_${action.action}`}
                      className="rounded-lg border border-gray-200 px-4 py-3 dark:border-gray-700"
                    >
                      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-gray-900 dark:text-gray-100">
                              {action.asset}
                            </span>
                            <span
                              className={cn(
                                'rounded-full border px-2 py-1 text-xs font-semibold uppercase tracking-wide',
                                actionTone(action.action)
                              )}
                            >
                              {action.action}
                            </span>
                          </div>
                          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                            {action.reason}
                          </p>
                        </div>
                        <div className="grid grid-cols-2 gap-3 text-sm text-gray-600 dark:text-gray-300">
                          <div>
                            <div className="text-xs uppercase tracking-wide text-gray-400">Qtd Delta</div>
                            <div className="mt-1 font-medium">{formatNumber(action.quantity_delta, 4)}</div>
                          </div>
                          <div>
                            <div className="text-xs uppercase tracking-wide text-gray-400">Notional</div>
                            <div className="mt-1 font-medium">{formatCurrency(action.notional_delta)}</div>
                          </div>
                          <div>
                            <div className="text-xs uppercase tracking-wide text-gray-400">Peso Atual</div>
                            <div className="mt-1 font-medium">{formatPercent(action.current_weight)}</div>
                          </div>
                          <div>
                            <div className="text-xs uppercase tracking-wide text-gray-400">Peso-Alvo</div>
                            <div className="mt-1 font-medium">{formatPercent(action.target_weight)}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">
                  Nenhuma acao calculada ainda.
                </p>
              )}
            </div>

            {plan?.warnings.length ? (
              <div className="card border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/20">
                <h3 className="text-base font-semibold text-amber-900 dark:text-amber-100">
                  Alertas do Plano
                </h3>
                <ul className="mt-3 space-y-2 text-sm text-amber-800 dark:text-amber-200">
                  {plan.warnings.map((warning) => (
                    <li key={warning}>{warning}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        </div>
      )}

      {activeTab === 'saved' && (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[360px_1fr]">
          <div className="card">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                  Workspaces Salvos
                </h3>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  Reabra planos, exporte JSON e recarregue um draft no planner.
                </p>
              </div>
              <label className="inline-flex cursor-pointer items-center rounded-md border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800">
                {isImporting ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Upload className="mr-2 h-4 w-4" />
                )}
                Importar
                <input type="file" accept="application/json" className="hidden" onChange={importWorkspace} />
              </label>
            </div>

            <div className="mt-4 space-y-3">
              {isLoading && (
                <div className="rounded-lg border border-gray-200 px-4 py-3 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
                  Carregando workspaces...
                </div>
              )}

              {!isLoading && workspaces.length === 0 && (
                <div className="rounded-lg border border-dashed border-gray-300 px-4 py-6 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
                  Nenhum allocation workspace salvo ainda.
                </div>
              )}

              {workspaces.map((workspace) => (
                <div
                  key={workspace.workspace_id}
                  className={cn(
                    'w-full rounded-lg border p-4 transition-colors',
                    selectedWorkspaceId === workspace.workspace_id
                      ? 'border-gray-900 bg-gray-900 text-white dark:border-gray-100 dark:bg-gray-100 dark:text-gray-900'
                      : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700'
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <button
                      type="button"
                      onClick={() => setSelectedWorkspaceId(workspace.workspace_id)}
                      className="w-full text-left"
                    >
                      <div className="font-medium">{workspace.name}</div>
                      <div className="mt-1 text-xs opacity-80">
                        {formatDateTime(workspace.created_at)}
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2 text-xs">
                        <span className="rounded-full bg-black/10 px-2 py-1 dark:bg-white/10">
                          {workspace.summary.asset_count} ativos
                        </span>
                        <span className="rounded-full bg-black/10 px-2 py-1 dark:bg-white/10">
                          turnover {formatPercent(workspace.summary.turnover_ratio)}
                        </span>
                        <span className="rounded-full bg-black/10 px-2 py-1 dark:bg-white/10">
                          {workspace.summary.buy_count} buy / {workspace.summary.sell_count} sell
                        </span>
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => void removeWorkspace(workspace.workspace_id)}
                      className="inline-flex items-center rounded-md border border-transparent px-2 py-1 text-xs text-red-600 transition-colors hover:border-red-200 hover:bg-red-50 dark:text-red-300 dark:hover:bg-red-900/20"
                      title="Excluir workspace"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            {selectedWorkspace ? (
              <div className="space-y-5">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                      {selectedWorkspace.name}
                    </h3>
                    <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                      {selectedWorkspace.workspace_id} · criado em {formatDateTime(selectedWorkspace.created_at)}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => loadWorkspaceIntoPlanner(selectedWorkspace)}
                      className="inline-flex items-center rounded-md border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
                    >
                      <FolderOpen className="mr-2 h-4 w-4" />
                      Abrir no Planner
                    </button>
                    <button
                      type="button"
                      onClick={() => downloadJSON(selectedWorkspace, `${selectedWorkspace.workspace_id}.json`)}
                      className="inline-flex items-center rounded-md border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
                    >
                      <Download className="mr-2 h-4 w-4" />
                      Exportar JSON
                    </button>
                  </div>
                </div>

                {selectedWorkspace.notes && (
                  <div className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700 dark:border-gray-700 dark:bg-gray-900/40 dark:text-gray-300">
                    {selectedWorkspace.notes}
                  </div>
                )}

                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                  <MetricCard
                    label="Equity"
                    value={formatCurrency(selectedWorkspace.summary.total_equity)}
                  />
                  <MetricCard
                    label="Turnover"
                    value={formatCurrency(selectedWorkspace.summary.turnover_notional)}
                  />
                  <MetricCard
                    label="Cash Projetado"
                    value={formatCurrency(selectedWorkspace.summary.projected_cash)}
                  />
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="rounded-lg border border-gray-200 px-4 py-4 dark:border-gray-700">
                    <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      Resumo
                    </div>
                    <dl className="mt-3 space-y-3 text-sm">
                      <DetailRow label="Ativos" value={selectedWorkspace.summary.assets.join(', ') || 'n/a'} />
                      <DetailRow label="Buy / Sell / Hold" value={`${selectedWorkspace.summary.buy_count} / ${selectedWorkspace.summary.sell_count} / ${selectedWorkspace.summary.hold_count}`} />
                      <DetailRow label="Cash Atual" value={formatPercent(selectedWorkspace.summary.current_cash_weight)} />
                      <DetailRow label="Cash Alvo" value={formatPercent(selectedWorkspace.summary.target_cash_weight)} />
                      <DetailRow label="Cash Reserva" value={formatCurrency(selectedWorkspace.summary.reserve_cash)} />
                      <DetailRow label="Drift Maximo" value={formatPercent(selectedWorkspace.summary.max_abs_drift_weight)} />
                    </dl>
                  </div>

                  <div className="rounded-lg border border-gray-200 px-4 py-4 dark:border-gray-700">
                    <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      Ultimo Plano
                    </div>
                    <div className="mt-3 space-y-2">
                      {selectedWorkspace.plan.actions.map((action) => (
                        <div
                          key={`${selectedWorkspace.workspace_id}_${action.asset}_${action.action}`}
                          className="flex items-center justify-between rounded-lg border border-gray-200 px-3 py-2 text-sm dark:border-gray-700"
                        >
                          <div>
                            <div className="font-medium text-gray-900 dark:text-gray-100">
                              {action.asset}
                            </div>
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              {action.reason}
                            </div>
                          </div>
                          <div className="text-right">
                            <span
                              className={cn(
                                'rounded-full border px-2 py-1 text-xs font-semibold uppercase tracking-wide',
                                actionTone(action.action)
                              )}
                            >
                              {action.action}
                            </span>
                            <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                              {formatCurrency(action.notional_delta)}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-lg border border-dashed border-gray-300 px-6 py-10 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
                Selecione um workspace salvo para inspecionar o plano de rebalanceamento.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-gray-200 px-4 py-3 dark:border-gray-700">
      <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
        {label}
      </div>
      <div className="mt-2 text-lg font-semibold text-gray-900 dark:text-gray-100">
        {value}
      </div>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <dt className="text-gray-500 dark:text-gray-400">{label}</dt>
      <dd className="text-right font-medium text-gray-900 dark:text-gray-100">{value}</dd>
    </div>
  );
}
