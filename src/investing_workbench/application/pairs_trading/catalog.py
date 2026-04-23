"""Curated B3 universe presets for pairs-trading research."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PairsUniversePreset:
    """Static metadata for a curated B3 universe preset."""

    preset_id: str
    label: str
    description: str
    universe_kind: str
    history_mode: str
    benchmark_tickers: tuple[str, ...]
    tickers: tuple[str, ...]


CURATED_B3_IBOV_PROXY = (
    "PETR4",
    "PETR3",
    "VALE3",
    "ITUB4",
    "BBDC4",
    "BBAS3",
    "ABEV3",
    "WEGE3",
    "RENT3",
    "LREN3",
    "SUZB3",
    "PRIO3",
    "GGBR4",
    "CSNA3",
    "ELET3",
    "ENEV3",
    "RADL3",
    "RAIL3",
    "JBSS3",
    "CMIG4",
)

CURATED_B3_DOMESTIC = (
    "ITUB4",
    "BBDC4",
    "BBAS3",
    "RADL3",
    "LREN3",
    "RENT3",
    "ENEV3",
    "CMIG4",
    "WEGE3",
    "RAIL3",
)

CURATED_B3_COMMODITIES = (
    "PETR4",
    "PETR3",
    "PRIO3",
    "VALE3",
    "GGBR4",
    "CSNA3",
    "SUZB3",
    "JBSS3",
)

CURATED_B3_BANKS_CORE = (
    "ITUB4",
    "BBDC4",
    "BBAS3",
    "SANB11",
    "ITSA4",
)

CURATED_B3_OIL_GAS_CORE = (
    "PETR4",
    "PETR3",
    "PRIO3",
)

CURATED_B3_METALS_CORE = (
    "VALE3",
    "GGBR4",
    "CSNA3",
    "BRAP4",
)

CURATED_B3_CONSUMER_DOMESTIC_CORE = (
    "RENT3",
    "LREN3",
    "RADL3",
    "ABEV3",
    "WEGE3",
    "RAIL3",
)

SECTOR_MAP: dict[str, str] = {
    "PETR4": "oil_gas",
    "PETR3": "oil_gas",
    "PRIO3": "oil_gas",
    "ITUB4": "banks",
    "BBDC4": "banks",
    "BBAS3": "banks",
    "VALE3": "metals_mining",
    "GGBR4": "metals_mining",
    "CSNA3": "metals_mining",
    "CMIN3": "metals_mining",
    "SUZB3": "pulp_paper",
    "ABEV3": "consumer_defensive",
    "RADL3": "consumer_defensive",
    "ASAI3": "consumer_defensive",
    "LREN3": "consumer_discretionary",
    "MGLU3": "consumer_discretionary",
    "RENT3": "consumer_discretionary",
    "ENEV3": "utilities",
    "CMIG4": "utilities",
    "CPFE3": "utilities",
    "CPLE6": "utilities",
    "EGIE3": "utilities",
    "EQTL3": "utilities",
    "SBSP3": "utilities",
    "TAEE11": "utilities",
    "ISAE4": "utilities",
    "ENGI11": "utilities",
    "WEGE3": "industrials",
    "RAIL3": "industrials",
    "ELET3": "utilities",
    "JBSS3": "protein",
    "BRFS3": "protein",
    "MRFG3": "protein",
    "BRAP4": "metals_mining",
    "BRKM5": "materials",
    "BBSE3": "insurance",
    "BPAC11": "financial_services",
    "CXSE3": "insurance",
    "SANB11": "banks",
    "ITSA4": "holding_financials",
    "B3SA3": "exchange_financials",
    "VIVT3": "telecom",
    "TIMS3": "telecom",
    "RDOR3": "healthcare",
    "HAPV3": "healthcare",
    "HYPE3": "healthcare",
    "CYRE3": "real_estate",
    "DIRR3": "real_estate",
    "CURY3": "real_estate",
    "MULT3": "real_estate",
    "CCRO3": "transportation",
    "MOTV3": "transportation",
    "UGPA3": "fuel_distribution",
    "VBBR3": "fuel_distribution",
    "KLBN11": "pulp_paper",
    "EMBR3": "industrials",
    "TOTS3": "technology",
    "LWSA3": "technology",
    "SMFT3": "consumer_services",
    "PSSA3": "insurance",
    "SLCE3": "agribusiness",
    "COGN3": "education",
    "YDUQ3": "education",
    "IRBR3": "insurance",
    "IGTI11": "real_estate",
    "BOVA11": "benchmark_etf",
}

SECTOR_RATIONALE: dict[str, str] = {
    "oil_gas": "Mesma cadeia de oleo e gas, com drivers macro e de commodity parecidos.",
    "banks": "Bancos domesticos com sensibilidade semelhante a juros e credito.",
    "metals_mining": "Mineracao e aco expostos ao mesmo ciclo de commodities metalicas.",
    "materials": "Materiais basicos com drivers parecidos de insumos e ciclo industrial.",
    "pulp_paper": "Celulose e papel; grupo mais isolado, util para pares idiossincraticos.",
    "consumer_defensive": ("Consumo defensivo domestico, com drivers locais de renda e juros."),
    "consumer_discretionary": (
        "Consumo discricionario domestico, sensivel a renda, juros e credito."
    ),
    "utilities": "Utilities/energia com sensibilidade a juros, regulacao e ciclo domestico.",
    "industrials": "Industria e logistica com drivers domesticos e ciclicidade parecida.",
    "protein": "Proteina animal, mais exportadora, com dinamica propria dentro do universo.",
    "insurance": "Seguradoras e seguridade com drivers de juros, sinistralidade e credito.",
    "financial_services": "Servicos financeiros e investment banking com drivers de mercado.",
    "holding_financials": "Holdings financeiras com sensibilidade ao setor bancario domestico.",
    "exchange_financials": "Infraestrutura de mercado e bolsa, ligada ao volume de negociacao.",
    "telecom": "Telecom domestica defensiva, com receita recorrente e drivers regulados.",
    "healthcare": "Saude listada, com drivers de sinistralidade, regulacao e renda.",
    "real_estate": "Construcao e shopping, sensiveis a juros reais e ciclo domestico.",
    "transportation": "Concessoes, rodovias e mobilidade com drivers de demanda local.",
    "fuel_distribution": "Distribuicao de combustiveis ligada ao ciclo local e petroleo.",
    "technology": "Tecnologia e software listados, expostos a crescimento e juros.",
    "consumer_services": "Servicos ao consumidor com sensibilidade a renda e emprego.",
    "agribusiness": "Agribusiness com drivers de commodities agricolas e exportacao.",
    "education": "Educacao listada com dinamica regulatoria e ciclo de renda domestica.",
    "benchmark_etf": "ETF usado apenas como benchmark, nao como par de negociacao.",
}

UNIVERSE_PRESETS: dict[str, PairsUniversePreset] = {
    "ibov_proxy": PairsUniversePreset(
        preset_id="ibov_proxy",
        label="IBOV Proxy",
        description=(
            "Proxy curado com blue chips e nomes liquidos da B3 usados como universo "
            "base de pairs trading."
        ),
        universe_kind="b3_ibov_proxy",
        history_mode="curated_proxy",
        benchmark_tickers=("BOVA11.SA", "^BVSP"),
        tickers=CURATED_B3_IBOV_PROXY,
    ),
    "ibov_domestic": PairsUniversePreset(
        preset_id="ibov_domestic",
        label="IBOV Domestic",
        description=(
            "Subset focado em bancos, varejo, utilities e industria domestica para "
            "pares mais conectados ao ciclo local."
        ),
        universe_kind="b3_ibov_proxy",
        history_mode="curated_proxy",
        benchmark_tickers=("BOVA11.SA", "^BVSP"),
        tickers=CURATED_B3_DOMESTIC,
    ),
    "ibov_commodities": PairsUniversePreset(
        preset_id="ibov_commodities",
        label="IBOV Commodities",
        description=(
            "Subset de commodities e exportadoras para explorar pares entre petroleo, "
            "mineracao, aco, celulose e proteina."
        ),
        universe_kind="b3_ibov_proxy",
        history_mode="curated_proxy",
        benchmark_tickers=("BOVA11.SA", "^BVSP"),
        tickers=CURATED_B3_COMMODITIES,
    ),
    "ibov_historical": PairsUniversePreset(
        preset_id="ibov_historical",
        label="IBOV Official History",
        description=(
            "Snapshot oficial do Ibovespa resolvido a partir do BDI da B3 para a data "
            "informada em as_of_date ou, na ausencia dela, para start_date."
        ),
        universe_kind="b3_ibov_official",
        history_mode="official_b3_bdi",
        benchmark_tickers=("BOVA11.SA", "^BVSP"),
        tickers=(),
    ),
    "banks_core": PairsUniversePreset(
        preset_id="banks_core",
        label="Banks Core",
        description=(
            "Banco e holdings financeiras mais líquidas da B3 para pairs domésticos "
            "com racional micro mais direto."
        ),
        universe_kind="b3_sector_core",
        history_mode="curated_proxy",
        benchmark_tickers=("BOVA11.SA", "^BVSP"),
        tickers=CURATED_B3_BANKS_CORE,
    ),
    "oil_gas_core": PairsUniversePreset(
        preset_id="oil_gas_core",
        label="Oil & Gas Core",
        description=(
            "Classe de ações e produtores de óleo/gás da B3 para spreads mais econômicos."
        ),
        universe_kind="b3_sector_core",
        history_mode="curated_proxy",
        benchmark_tickers=("BOVA11.SA", "^BVSP"),
        tickers=CURATED_B3_OIL_GAS_CORE,
    ),
    "metals_core": PairsUniversePreset(
        preset_id="metals_core",
        label="Metals & Mining Core",
        description=(
            "Mineradoras e siderúrgicas líquidas da B3 para testar spreads de commodities."
        ),
        universe_kind="b3_sector_core",
        history_mode="curated_proxy",
        benchmark_tickers=("BOVA11.SA", "^BVSP"),
        tickers=CURATED_B3_METALS_CORE,
    ),
    "consumer_domestic_core": PairsUniversePreset(
        preset_id="consumer_domestic_core",
        label="Consumer Domestic Core",
        description=(
            "Consumo discricionário e defensivo doméstico com liquidez suficiente "
            "para research de pairs."
        ),
        universe_kind="b3_sector_core",
        history_mode="curated_proxy",
        benchmark_tickers=("BOVA11.SA", "^BVSP"),
        tickers=CURATED_B3_CONSUMER_DOMESTIC_CORE,
    ),
}


def list_universe_presets() -> list[dict[str, object]]:
    """Return curated preset metadata in a JSON-friendly structure."""
    payload: list[dict[str, object]] = []
    for preset in UNIVERSE_PRESETS.values():
        payload.append(
            {
                "preset_id": preset.preset_id,
                "label": preset.label,
                "description": preset.description,
                "universe_kind": preset.universe_kind,
                "history_mode": preset.history_mode,
                "benchmark_tickers": list(preset.benchmark_tickers),
                "tickers": list(preset.tickers),
                "ticker_count": len(preset.tickers),
            }
        )
    return payload


def resolve_preset_tickers(preset_id: str) -> tuple[str, ...]:
    """Return the curated tickers for one known preset."""
    if preset_id not in UNIVERSE_PRESETS:
        available = ", ".join(sorted(UNIVERSE_PRESETS))
        raise ValueError(
            f"Unknown pairs universe preset '{preset_id}'. Available presets: {available}"
        )
    return UNIVERSE_PRESETS[preset_id].tickers


def resolve_preset_metadata(preset_id: str) -> PairsUniversePreset:
    """Return metadata for one known preset."""
    if preset_id not in UNIVERSE_PRESETS:
        available = ", ".join(sorted(UNIVERSE_PRESETS))
        raise ValueError(
            f"Unknown pairs universe preset '{preset_id}'. Available presets: {available}"
        )
    return UNIVERSE_PRESETS[preset_id]
