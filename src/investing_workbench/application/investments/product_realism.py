"""Product realism metadata for didactic investment comparisons."""

from __future__ import annotations

from typing import Any

_SOURCE_KIND_LABELS = {
    "listed_security": "Ativo negociado na bolsa",
    "model_portfolio": "Carteira guiada",
    "custom_portfolio": "Carteira personalizada",
    "fixed_income_index": "Indice de renda fixa",
    "tesouro_direct_strategy": "Tesouro Direto simulado",
    "selic_proxy": "Proxy de caixa/SELIC",
    "rate_proxy": "Proxy de taxa",
    "inflation_proxy": "Proxy de inflacao",
}

_STATUS_LABELS = {
    "modeled": "modelado",
    "partial": "parcial",
    "not_modeled": "pendente",
}


def build_product_realism_metadata(
    *,
    results: list[dict[str, Any]],
    benchmarks: list[dict[str, Any]],
    fixed_income_backtest: dict[str, Any] | None,
    decision_profile: dict[str, Any],
) -> dict[str, Any]:
    """Describe how close the comparison is to an investable product experience."""

    rows = [*results, *benchmarks]
    source_kind_counts = _count_source_kinds(rows)
    source_kinds = set(source_kind_counts)
    has_listed = "listed_security" in source_kinds
    has_portfolio = bool({"model_portfolio", "custom_portfolio"} & source_kinds)
    has_fixed_income_index = "fixed_income_index" in source_kinds
    has_treasury = "tesouro_direct_strategy" in source_kinds
    has_proxy = bool({"selic_proxy", "rate_proxy", "inflation_proxy"} & source_kinds)
    has_taxed_rows = any(float(row.get("taxes_paid_total", 0.0) or 0.0) > 0 for row in rows)
    tax_treatment = (
        (fixed_income_backtest or {}).get("tax_treatment")
        or decision_profile.get("tax_view")
        or "gross"
    )
    liquidity_label = str(decision_profile.get("liquidity_need_label") or "nao informada")
    mark_to_market_label = str(
        decision_profile.get("mark_to_market_tolerance_label") or "nao informada"
    )
    investability_status = (
        "partial" if has_proxy or has_fixed_income_index or has_portfolio else "modeled"
    )
    tax_status = "partial" if has_treasury else "not_modeled"
    fee_status = "partial" if has_listed or has_treasury else "not_modeled"
    income_status = "partial" if has_listed or has_portfolio else "not_modeled"
    liquidity_status = "partial" if has_treasury else "not_modeled"
    mark_to_market_status = (
        "partial" if has_fixed_income_index or has_treasury or has_listed else "not_modeled"
    )
    retail_fixed_income_status = "partial"

    coverage = [
        {
            "dimension_id": "investable_product",
            "label": "Indice, proxy ou produto real",
            "status": investability_status,
            "status_label": _status_label(investability_status),
            "summary": _investability_summary(
                has_listed=has_listed,
                has_portfolio=has_portfolio,
                has_fixed_income_index=has_fixed_income_index,
                has_treasury=has_treasury,
                has_proxy=has_proxy,
            ),
            "current_scope": _labels_for_source_kinds(source_kind_counts),
            "limitations": (
                "A leitura ainda mistura ativos compraveis, indices, proxies e politicas de "
                "carteira. O payload identifica o tipo de evidencia para evitar falsa equivalencia."
            ),
            "next_step": (
                "Adicionar equivalentes investiveis para cada indice ou proxy relevante, "
                "como ETF, fundo, Tesouro Direto, CDB, LCI/LCA ou debenture."
            ),
        },
        {
            "dimension_id": "taxes",
            "label": "IR, IOF e leitura liquida",
            "status": tax_status,
            "status_label": _status_label(tax_status),
            "summary": (
                "Tesouro Direto ja pode estimar IR regressivo e IOF em resgates curtos; "
                "acoes, ETFs, FIIs, BDRs, CDBs, LCIs/LCAs e fundos ainda nao tem imposto "
                "individual completo."
            ),
            "current_scope": [
                (
                    "IR regressivo/IOF em estrategias de Tesouro Direto"
                    if has_treasury
                    else "sem ativo Tesouro Direto nesta comparacao"
                ),
                f"visao solicitada: {tax_treatment}",
                (
                    "impostos estimados apareceram nos resultados"
                    if has_taxed_rows
                    else "sem imposto estimado material nesta rodada"
                ),
            ],
            "limitations": (
                "Nao calcula DARF, compensacao de prejuizo, come-cotas, aliquotas especificas "
                "de renda variavel, isencoes de LCI/LCA ou regras de FIIs."
            ),
            "next_step": (
                "Criar uma camada tributaria por produto, incluindo equivalencia liquida "
                "CDB versus LCI/LCA e renda variavel com dividendos/JCP/FIIs."
            ),
        },
        {
            "dimension_id": "fees_and_spreads",
            "label": "Taxas, spreads e custos",
            "status": fee_status,
            "status_label": _status_label(fee_status),
            "summary": (
                "Precos historicos de ativos listados e Tesouro carregam parte da realidade de "
                "mercado, mas o simulador ainda nao explicita taxa de administracao, spread, "
                "corretagem, custodia ou tracking error."
            ),
            "current_scope": [
                "precos/cotacoes historicas quando disponiveis",
                "sem modelo explicito de spread de entrada e saida",
            ],
            "limitations": (
                "O resultado pode parecer mais limpo que a experiencia real do investidor em "
                "produtos com taxa, spread, baixa liquidez ou lote operacional."
            ),
            "next_step": (
                "Adicionar premissas editaveis de taxa, spread e tracking error por familia "
                "de produto."
            ),
        },
        {
            "dimension_id": "income_reinvestment",
            "label": "Dividendos, cupons e reinvestimento",
            "status": income_status,
            "status_label": _status_label(income_status),
            "summary": (
                "Series ajustadas aproximam retorno total de ativos listados; carteiras "
                "rebalanceadas reinvestem pelo proprio mecanismo de alocacao. O app ainda "
                "nao separa renda mensal, dividendos, JCP, cupons ou amortizacoes como fluxo."
            ),
            "current_scope": [
                (
                    "retorno total aproximado por serie ajustada"
                    if has_listed
                    else "sem ativo listado nesta comparacao"
                ),
                (
                    "rebalanceamento de carteiras"
                    if has_portfolio
                    else "sem carteira rebalanceada nesta comparacao"
                ),
            ],
            "limitations": (
                "Nao mostra calendario de renda nem imposto sobre distribuicoes. FIIs e acoes "
                "de dividendos ainda aparecem como patrimonio acumulado, nao como renda passiva."
            ),
            "next_step": (
                "Separar acumulacao de patrimonio e renda distribuida, com opcao de reinvestir "
                "ou consumir os proventos."
            ),
        },
        {
            "dimension_id": "liquidity_and_terms",
            "label": "Liquidez, vencimento e prazo",
            "status": liquidity_status,
            "status_label": _status_label(liquidity_status),
            "summary": (
                "Tesouro Direto considera vencimentos e troca de titulos nas estrategias. "
                "Acoes, ETFs, FIIs, CDBs, LCIs/LCAs e fundos ainda nao recebem restricoes "
                "explicitas de liquidez, carencia, volume ou prazo."
            ),
            "current_scope": [
                (
                    "vencimentos reais no Tesouro Direto"
                    if has_treasury
                    else "sem vencimentos reais nesta comparacao"
                ),
                f"necessidade de liquidez do perfil: {liquidity_label}",
            ],
            "limitations": (
                "Nao penaliza resgate antecipado de credito privado, baixa liquidez em FIIs/BDRs "
                "ou indisponibilidade de produto no varejo."
            ),
            "next_step": (
                "Adicionar restricoes de carencia, liquidez diaria/no vencimento, volume minimo "
                "e prazo recomendado por produto."
            ),
        },
        {
            "dimension_id": "mark_to_market",
            "label": "Marcacao a mercado",
            "status": mark_to_market_status,
            "status_label": _status_label(mark_to_market_status),
            "summary": (
                "Ativos listados, indices de duration e Tesouro Direto capturam oscilacao de "
                "precos. Proxies de taxa simples ainda nao sofrem marcacao a mercado real."
            ),
            "current_scope": [
                "drawdown e volatilidade historicos",
                f"tolerancia informada: {mark_to_market_label}",
            ],
            "limitations": (
                "Nao projeta cenarios futuros de abertura/fechamento de juros nem curva a termo "
                "para credito privado."
            ),
            "next_step": (
                "Criar cenarios didaticos de choque de juros e comparacao entre carregar ate "
                "o vencimento versus vender antes."
            ),
        },
        {
            "dimension_id": "retail_fixed_income",
            "label": "Renda fixa de varejo",
            "status": retail_fixed_income_status,
            "status_label": _status_label(retail_fixed_income_status),
            "summary": (
                "A prateleira real ja comeca pelo Tesouro Direto e por uma primeira tabela "
                "de equivalencia liquida entre CDB tributado e LCI/LCA isenta. Ainda faltam "
                "ofertas reais, debentures incentivadas, fundos DI e restricoes operacionais."
            ),
            "current_scope": [
                "equivalencia CDB versus LCI/LCA por prazo e IR regressivo",
                (
                    "Tesouro Direto com historico oficial"
                    if has_treasury
                    else "sem produto de varejo real nesta comparacao"
                ),
                (
                    "indices CDI/IDkA como referencia"
                    if has_fixed_income_index
                    else "sem indice ANBIMA nesta comparacao"
                ),
            ],
            "limitations": (
                "A equivalencia usa CDI de referencia e nao captura FGC, risco de credito, "
                "carencia, oferta real, liquidez secundaria ou aporte minimo."
            ),
            "next_step": (
                "Conectar presets de varejo com CDB % CDI, LCI/LCA, debentures incentivadas "
                "e fundos de renda fixa com taxas e liquidez editaveis."
            ),
        },
    ]

    return {
        "title": "Realismo do produto investivel",
        "plain_language_summary": (
            "Este bloco mostra onde a comparacao ja se aproxima de uma experiencia compravel "
            "e onde ela ainda e uma aproximacao didatica. Ele ajuda a evitar comparar indice, "
            "proxy, ETF, fundo, Tesouro e carteira como se fossem exatamente a mesma coisa."
        ),
        "product_types": [
            {
                "source_kind": source_kind,
                "label": _SOURCE_KIND_LABELS.get(
                    source_kind,
                    source_kind.replace("_", " ").title(),
                ),
                "count": count,
            }
            for source_kind, count in sorted(source_kind_counts.items())
        ],
        "coverage": coverage,
        "income_policy_examples": _build_income_policy_examples(rows),
        "next_methodology_steps": [
            "Separar retorno bruto, liquido e fluxo de renda distribuida.",
            (
                "Expandir a equivalencia liquida para ofertas editaveis de CDB, LCI/LCA "
                "e debentures incentivadas."
            ),
            "Mostrar taxa, spread, liquidez e prazo como premissas editaveis por produto.",
        ],
    }


def _build_income_policy_examples(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    categories = {str(row.get("category_id") or "") for row in rows}
    source_kinds = {str(row.get("source_kind") or "") for row in rows}

    if "stocks_brazil" in categories or "listed_security" in source_kinds:
        examples.append(
            {
                "policy_id": "stocks_dividends_jcp",
                "label": "Acoes brasileiras: dividendos e JCP",
                "cashflow_treatment": (
                    "Series ajustadas aproximam retorno total, mas o app ainda nao separa "
                    "dividendos e JCP como caixa mensal."
                ),
                "tax_treatment": (
                    "Dividendos seguem leitura de isencao vigente para pessoa fisica; JCP "
                    "tem retencao na fonte e ainda nao e destacado no fluxo."
                ),
                "reinvestment_assumption": (
                    "O retorno ajustado se comporta como reinvestimento implicito, nao como "
                    "renda consumida pelo investidor."
                ),
                "user_decision": (
                    "Para objetivo de renda, comparar patrimonio final junto de um calendario "
                    "de proventos antes de tratar o ativo como pagador recorrente."
                ),
            }
        )

    if "fiis" in categories:
        examples.append(
            {
                "policy_id": "fiis_monthly_income",
                "label": "FIIs: rendimento recorrente",
                "cashflow_treatment": (
                    "FIIs entram pela cota ajustada e ainda nao mostram rendimento mensal "
                    "separado de valorizacao ou queda da cota."
                ),
                "tax_treatment": (
                    "Rendimentos de FIIs podem ser isentos para pessoa fisica quando as "
                    "condicoes legais sao atendidas; ganho de capital e tributado e ainda "
                    "nao e modelado individualmente."
                ),
                "reinvestment_assumption": (
                    "A comparacao atual aproxima acumulacao; falta alternar entre reinvestir "
                    "os rendimentos ou usa-los como renda passiva."
                ),
                "user_decision": (
                    "Para renda mensal, observar vacancia, tipo do FII, recorrencia de "
                    "distribuicao e risco de queda da cota, nao apenas yield historico."
                ),
            }
        )

    if "etfs" in categories:
        examples.append(
            {
                "policy_id": "etfs_total_return",
                "label": "ETFs: retorno da cota e custos do fundo",
                "cashflow_treatment": (
                    "ETFs sao lidos pela serie da cota; distribuicoes, quando existirem, "
                    "nao aparecem como fluxo de renda separado."
                ),
                "tax_treatment": (
                    "Imposto sobre venda e regras por tipo de ETF ainda nao entram em uma "
                    "camada tributaria especifica."
                ),
                "reinvestment_assumption": (
                    "O estudo prioriza retorno total aproximado e ainda nao destaca taxa de "
                    "administracao, tracking error ou spread de negociacao."
                ),
                "user_decision": (
                    "Usar ETFs como exposicao diversificada, comparando custo, liquidez e "
                    "aderencia ao indice antes de substituir por um indice teorico."
                ),
            }
        )

    if "tesouro_direct_strategy" in source_kinds:
        examples.append(
            {
                "policy_id": "treasury_cashflows",
                "label": "Tesouro Direto: vencimento, IR e venda antecipada",
                "cashflow_treatment": (
                    "Estrategias de Tesouro ja usam precos oficiais e estimativa de IR/IOF; "
                    "cupons semestrais ainda nao sao separados como renda recorrente."
                ),
                "tax_treatment": (
                    "IR regressivo e IOF de curto prazo entram nas simulacoes liquidas quando "
                    "a visao net/both e usada."
                ),
                "reinvestment_assumption": (
                    "A rolagem reinveste conforme a politica simulada; carregar ate vencimento "
                    "versus vender antes ainda deve ser lido pela marcacao a mercado."
                ),
                "user_decision": (
                    "Casar prazo do titulo com objetivo e tolerancia a oscilacao antes de "
                    "comparar apenas rentabilidade historica."
                ),
            }
        )

    if {"model_portfolio", "custom_portfolio"} & source_kinds:
        examples.append(
            {
                "policy_id": "portfolio_income_policy",
                "label": "Carteiras: renda dos componentes",
                "cashflow_treatment": (
                    "Carteiras mostram patrimonio consolidado; a renda distribuida por cada "
                    "componente ainda nao e quebrada em caixa versus reinvestimento."
                ),
                "tax_treatment": (
                    "Cada componente pode ter regra tributaria propria, ainda nao consolidada "
                    "em uma carteira liquida produto a produto."
                ),
                "reinvestment_assumption": (
                    "Rebalanceamento representa disciplina de alocacao, nao uma politica "
                    "explicita de saque ou consumo dos proventos."
                ),
                "user_decision": (
                    "Para renda passiva, definir antes se proventos serao reinvestidos, "
                    "sacados ou usados para rebalancear a carteira."
                ),
            }
        )

    return examples


def _count_source_kinds(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        source_kind = str(row.get("source_kind") or "unknown")
        counts[source_kind] = counts.get(source_kind, 0) + 1
    return counts


def _labels_for_source_kinds(source_kind_counts: dict[str, int]) -> list[str]:
    return [
        f"{_SOURCE_KIND_LABELS.get(source_kind, source_kind.replace('_', ' ').title())}: {count}"
        for source_kind, count in sorted(source_kind_counts.items())
    ]


def _status_label(status: str) -> str:
    return _STATUS_LABELS.get(status, status)


def _investability_summary(
    *,
    has_listed: bool,
    has_portfolio: bool,
    has_fixed_income_index: bool,
    has_treasury: bool,
    has_proxy: bool,
) -> str:
    parts: list[str] = []
    if has_listed:
        parts.append("ativos listados usam historico de mercado")
    if has_treasury:
        parts.append("Tesouro Direto usa precos oficiais")
    if has_fixed_income_index:
        parts.append("indices de renda fixa representam referencias metodologicas")
    if has_proxy:
        parts.append("proxies simplificam caixa, taxa ou inflacao")
    if has_portfolio:
        parts.append("carteiras representam politicas de alocacao")
    if not parts:
        return "A comparacao nao trouxe tipos suficientes para classificar investibilidade."
    return "Nesta rodada, " + "; ".join(parts) + "."
