"""Curated B3 investment catalog used by the didactic comparison workspace."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class InvestmentInstrument:
    """One investment option exposed by the comparison product."""

    instrument_id: str
    label: str
    ticker: str | None
    category_id: str
    category_label: str
    description: str
    rationale: str
    risk_label: str
    region_label: str
    source_kind: str = "listed_security"
    listed_on_b3: bool = True
    uses_adjusted_close: bool = True
    available_since: str | None = None
    notes: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["notes"] = list(self.notes)
        return payload


@dataclass(frozen=True)
class InvestmentPreset:
    """One beginner-friendly comparison preset."""

    preset_id: str
    label: str
    description: str
    asset_ids: tuple[str, ...]
    goal_label: str

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["asset_ids"] = list(self.asset_ids)
        return payload


CATEGORY_LABELS: dict[str, str] = {
    "stocks_brazil": "Acoes brasileiras",
    "etfs_brazil": "ETFs de bolsa local",
    "international_b3": "Internacional pela B3",
    "fiis": "FIIs",
    "fixed_income_b3": "Renda fixa / juros na B3",
}


INSTRUMENTS: tuple[InvestmentInstrument, ...] = (
    InvestmentInstrument(
        instrument_id="PETR4",
        label="PETR4",
        ticker="PETR4",
        category_id="stocks_brazil",
        category_label=CATEGORY_LABELS["stocks_brazil"],
        description="Acao liquida e representativa do setor de energia no Brasil.",
        rationale="Serve como exemplo de tese ciclica e fortemente ligada a commodities.",
        risk_label="Alta",
        region_label="Brasil",
    ),
    InvestmentInstrument(
        instrument_id="VALE3",
        label="VALE3",
        ticker="VALE3",
        category_id="stocks_brazil",
        category_label=CATEGORY_LABELS["stocks_brazil"],
        description="Acao blue chip de mineracao, muito usada como referencia setorial.",
        rationale="Ajuda a comparar uma tese de commodities contra renda e indice amplo.",
        risk_label="Alta",
        region_label="Brasil",
    ),
    InvestmentInstrument(
        instrument_id="ITUB4",
        label="ITUB4",
        ticker="ITUB4",
        category_id="stocks_brazil",
        category_label=CATEGORY_LABELS["stocks_brazil"],
        description="Banco grande, liquido e amplamente acompanhado pelo mercado.",
        rationale="Boa referencia para exposicao a bancos e lucro recorrente local.",
        risk_label="Media",
        region_label="Brasil",
    ),
    InvestmentInstrument(
        instrument_id="WEGE3",
        label="WEGE3",
        ticker="WEGE3",
        category_id="stocks_brazil",
        category_label=CATEGORY_LABELS["stocks_brazil"],
        description="Acao de crescimento conhecida por tendencia estrutural forte.",
        rationale="Ajuda a comparar um papel de qualidade com classes mais defensivas.",
        risk_label="Alta",
        region_label="Brasil",
    ),
    InvestmentInstrument(
        instrument_id="BOVA11",
        label="BOVA11",
        ticker="BOVA11",
        category_id="etfs_brazil",
        category_label=CATEGORY_LABELS["etfs_brazil"],
        description="ETF amplo de bolsa brasileira, usado como proxy simples do Ibovespa.",
        rationale="Funciona como benchmark acionario local e comparador de diversificacao.",
        risk_label="Media",
        region_label="Brasil",
    ),
    InvestmentInstrument(
        instrument_id="SMAL11",
        label="SMAL11",
        ticker="SMAL11",
        category_id="etfs_brazil",
        category_label=CATEGORY_LABELS["etfs_brazil"],
        description="ETF de small caps brasileiras.",
        rationale="Mostra uma cesta mais volatil de empresas locais menores.",
        risk_label="Alta",
        region_label="Brasil",
    ),
    InvestmentInstrument(
        instrument_id="DIVO11",
        label="DIVO11",
        ticker="DIVO11",
        category_id="etfs_brazil",
        category_label=CATEGORY_LABELS["etfs_brazil"],
        description="ETF focado em empresas brasileiras de perfil mais pagador de dividendos.",
        rationale="Ajuda a comparar uma cesta mais orientada a renda dentro da bolsa.",
        risk_label="Media",
        region_label="Brasil",
    ),
    InvestmentInstrument(
        instrument_id="IVVB11",
        label="IVVB11",
        ticker="IVVB11",
        category_id="international_b3",
        category_label=CATEGORY_LABELS["international_b3"],
        description="ETF internacional negociado na B3, ligado ao S&P 500.",
        rationale="Porta de entrada simples para bolsa americana via B3.",
        risk_label="Media",
        region_label="Internacional via B3",
    ),
    InvestmentInstrument(
        instrument_id="AAPL34",
        label="AAPL34",
        ticker="AAPL34",
        category_id="international_b3",
        category_label=CATEGORY_LABELS["international_b3"],
        description="BDR de acao internacional de tecnologia negociado em reais na B3.",
        rationale="Mostra como um BDR individual difere de um ETF internacional amplo.",
        risk_label="Alta",
        region_label="Internacional via B3",
    ),
    InvestmentInstrument(
        instrument_id="MSFT34",
        label="MSFT34",
        ticker="MSFT34",
        category_id="international_b3",
        category_label=CATEGORY_LABELS["international_b3"],
        description="BDR de acao internacional de tecnologia negociado na B3.",
        rationale="Exemplo adicional de diversificacao internacional por recibo.",
        risk_label="Alta",
        region_label="Internacional via B3",
    ),
    InvestmentInstrument(
        instrument_id="GOGL34",
        label="GOGL34",
        ticker="GOGL34",
        category_id="international_b3",
        category_label=CATEGORY_LABELS["international_b3"],
        description="BDR de tecnologia internacional com negociacao em reais na B3.",
        rationale="Permite comparar concentracao em big tech versus ETFs amplos.",
        risk_label="Alta",
        region_label="Internacional via B3",
    ),
    InvestmentInstrument(
        instrument_id="HGLG11",
        label="HGLG11",
        ticker="HGLG11",
        category_id="fiis",
        category_label=CATEGORY_LABELS["fiis"],
        description="FII de tijolo com foco logistica, muito acompanhado pelo mercado.",
        rationale="Serve como referencia de renda imobiliaria listada na bolsa.",
        risk_label="Media",
        region_label="Brasil",
    ),
    InvestmentInstrument(
        instrument_id="KNRI11",
        label="KNRI11",
        ticker="KNRI11",
        category_id="fiis",
        category_label=CATEGORY_LABELS["fiis"],
        description="FII diversificado entre lajes e logistica.",
        rationale="Ajuda a comparar um FII mais balanceado com foco em distribuicao.",
        risk_label="Media",
        region_label="Brasil",
    ),
    InvestmentInstrument(
        instrument_id="XPLG11",
        label="XPLG11",
        ticker="XPLG11",
        category_id="fiis",
        category_label=CATEGORY_LABELS["fiis"],
        description="FII logistico liquido e amplamente negociado.",
        rationale="Mostra outra exposicao imobiliaria listada com foco operacional.",
        risk_label="Media",
        region_label="Brasil",
    ),
    InvestmentInstrument(
        instrument_id="MXRF11",
        label="MXRF11",
        ticker="MXRF11",
        category_id="fiis",
        category_label=CATEGORY_LABELS["fiis"],
        description="FII de papel popular entre investidores de renda recorrente.",
        rationale="Ajuda a comparar um FII orientado a recebiveis contra tijolo e ETFs.",
        risk_label="Media",
        region_label="Brasil",
    ),
    InvestmentInstrument(
        instrument_id="IMAB11",
        label="IMAB11",
        ticker="IMAB11",
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description="ETF de renda fixa listado na B3, ligado a titulos publicos indexados.",
        rationale="Permite comparar uma exposicao de juros listada com classes de risco.",
        risk_label="Baixa a media",
        region_label="Brasil",
    ),
    InvestmentInstrument(
        instrument_id="SELIC_PROXY",
        label="Tesouro Selic (proxy)",
        ticker=None,
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description="Acumulacao por taxa SELIC diaria para representar caixa/Tesouro Selic via B3.",
        rationale="Serve como piso de comparacao e proxy simples de renda fixa liquida.",
        risk_label="Baixa",
        region_label="Brasil",
        source_kind="selic_proxy",
        listed_on_b3=False,
        uses_adjusted_close=False,
        notes=(
            "Modelo por taxa diaria, nao por cotacao secundaria de um titulo especifico.",
        ),
    ),
)


PRESETS: tuple[InvestmentPreset, ...] = (
    InvestmentPreset(
        preset_id="first_steps",
        label="Primeiros passos",
        description="Mistura simples entre caixa, bolsa local, exterior e renda imobiliaria.",
        asset_ids=("SELIC_PROXY", "BOVA11", "IVVB11", "HGLG11"),
        goal_label="Entender as grandes familias de investimento sem excesso de opcoes.",
    ),
    InvestmentPreset(
        preset_id="balanced_b3",
        label="Balanceado B3",
        description="Combina renda fixa, bolsa local, exterior via B3 e FIIs.",
        asset_ids=("SELIC_PROXY", "IMAB11", "BOVA11", "IVVB11", "HGLG11"),
        goal_label="Comparar estabilidade, crescimento e renda numa carteira educacional.",
    ),
    InvestmentPreset(
        preset_id="income_focus",
        label="Renda e defensividade",
        description="Olha primeiro para juros e distribuicao recorrente.",
        asset_ids=("SELIC_PROXY", "IMAB11", "HGLG11", "KNRI11", "MXRF11"),
        goal_label="Ver como renda fixa e FIIs se comportam lado a lado.",
    ),
    InvestmentPreset(
        preset_id="global_b3",
        label="Global pela B3",
        description="Internacionalizacao por ETF e BDR, sem abrir conta fora.",
        asset_ids=("SELIC_PROXY", "IVVB11", "AAPL34", "MSFT34", "GOGL34"),
        goal_label="Comparar acesso internacional amplo versus concentrado.",
    ),
)


BENCHMARK_OPTIONS: tuple[dict[str, Any], ...] = (
    {
        "benchmark_id": "selic_cash",
        "label": "SELIC / caixa",
        "description": "Referencia de juros diarios para comparar se o risco valeu a pena.",
    },
    {
        "benchmark_id": "bova11",
        "label": "BOVA11",
        "description": "Proxy simples de bolsa brasileira ampla.",
    },
)


def build_catalog_payload() -> dict[str, Any]:
    """Serialize the curated catalog for API/UI consumers."""
    categories = [
        {
            "category_id": category_id,
            "label": label,
            "count": sum(1 for item in INSTRUMENTS if item.category_id == category_id),
        }
        for category_id, label in CATEGORY_LABELS.items()
    ]
    return {
        "categories": categories,
        "instruments": [item.to_payload() for item in INSTRUMENTS],
        "presets": [item.to_payload() for item in PRESETS],
        "benchmark_options": list(BENCHMARK_OPTIONS),
        "notes": [
            (
                "Acoes, ETFs, FIIs e BDRs usam serie ajustada para aproximar "
                "rendimento total historico."
            ),
            (
                "O proxy de Tesouro Selic usa acumulacao por taxa diaria, sem "
                "simular um titulo individual de renda fixa."
            ),
            (
                "Alguns ativos podem ter historico mais curto do que o periodo "
                "pedido. Nesses casos, a plataforma avisa e exclui o comparativo "
                "para manter justica."
            ),
        ],
    }
