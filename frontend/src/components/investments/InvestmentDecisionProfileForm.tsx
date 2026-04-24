import type { InvestmentDecisionProfilePayload } from '../../types/api';

interface InvestmentDecisionProfileFormProps {
  profile?: InvestmentDecisionProfilePayload;
  onChange: (profile: InvestmentDecisionProfilePayload) => void;
}

const DEFAULT_PROFILE: InvestmentDecisionProfilePayload = {
  objective: 'balanced',
  horizon_years: 5,
  liquidity_need: 'monthly',
  mark_to_market_tolerance: 'medium',
  tax_view: 'gross',
  monthly_income_target: 0,
};

export default function InvestmentDecisionProfileForm({
  profile,
  onChange,
}: InvestmentDecisionProfileFormProps) {
  const current = { ...DEFAULT_PROFILE, ...(profile ?? {}) };

  const updateProfile = <K extends keyof InvestmentDecisionProfilePayload>(
    key: K,
    value: InvestmentDecisionProfilePayload[K]
  ) => {
    onChange({ ...current, [key]: value });
  };

  return (
    <div className="rounded-2xl border border-sky-200 bg-sky-50/70 p-4 dark:border-sky-900/50 dark:bg-sky-950/20">
      <div className="text-sm font-semibold text-sky-950 dark:text-sky-100">
        Perfil da decisão
      </div>
      <p className="mt-2 text-sm leading-6 text-sky-900/90 dark:text-sky-100/90">
        Este bloco não muda o backtest histórico. Ele muda a forma como o resultado é explicado:
        o sistema ranqueia os cards conforme prazo, liquidez, tolerância e objetivo.
      </p>

      <div className="mt-4 grid gap-4 md:grid-cols-3">
        <label className="space-y-2 text-sm">
          <span className="font-medium text-gray-700 dark:text-gray-200">Objetivo principal</span>
          <select
            className="input-field"
            value={current.objective}
            onChange={(event) => updateProfile('objective', event.target.value)}
          >
            <option value="balanced">Equilibrar retorno e risco</option>
            <option value="reserve">Reserva e liquidez</option>
            <option value="real_return">Ganhar acima da inflação</option>
            <option value="income">Gerar renda</option>
            <option value="growth">Crescer patrimônio</option>
            <option value="retirement">Aposentadoria</option>
          </select>
        </label>

        <label className="space-y-2 text-sm">
          <span className="font-medium text-gray-700 dark:text-gray-200">Horizonte</span>
          <input
            className="input-field"
            type="number"
            min="1"
            max="40"
            value={current.horizon_years}
            onChange={(event) =>
              updateProfile('horizon_years', Math.max(1, Number(event.target.value) || 1))
            }
          />
        </label>

        <label className="space-y-2 text-sm">
          <span className="font-medium text-gray-700 dark:text-gray-200">Liquidez</span>
          <select
            className="input-field"
            value={current.liquidity_need}
            onChange={(event) => updateProfile('liquidity_need', event.target.value)}
          >
            <option value="daily">Posso precisar a qualquer momento</option>
            <option value="monthly">Posso esperar algumas semanas</option>
            <option value="long_term">Não preciso no curto prazo</option>
          </select>
        </label>

        <label className="space-y-2 text-sm">
          <span className="font-medium text-gray-700 dark:text-gray-200">
            Marcação a mercado
          </span>
          <select
            className="input-field"
            value={current.mark_to_market_tolerance}
            onChange={(event) => updateProfile('mark_to_market_tolerance', event.target.value)}
          >
            <option value="low">Quero pouco susto</option>
            <option value="medium">Aceito oscilações moderadas</option>
            <option value="high">Aceito oscilações fortes</option>
          </select>
        </label>

        <label className="space-y-2 text-sm">
          <span className="font-medium text-gray-700 dark:text-gray-200">Visão tributária</span>
          <select
            className="input-field"
            value={current.tax_view}
            onChange={(event) => updateProfile('tax_view', event.target.value)}
          >
            <option value="gross">Bruta</option>
            <option value="net">Líquida estimada</option>
            <option value="both">Bruta e líquida</option>
          </select>
        </label>

        <label className="space-y-2 text-sm">
          <span className="font-medium text-gray-700 dark:text-gray-200">
            Meta de renda mensal
          </span>
          <input
            className="input-field"
            type="number"
            min="0"
            step="100"
            value={current.monthly_income_target}
            onChange={(event) =>
              updateProfile(
                'monthly_income_target',
                Math.max(0, Number(event.target.value) || 0)
              )
            }
          />
        </label>
      </div>
    </div>
  );
}
