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
    visible_in_catalog: bool = True
    rebalance_frequency: str | None = None
    implementation_note: str | None = None
    proxy_kind: str | None = None
    fixed_rate_annual: float | None = None
    spread_rate_annual: float | None = None
    components: tuple[tuple[str, float], ...] = ()
    notes: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["notes"] = list(self.notes)
        payload["components"] = [
            {"component_id": component_id, "weight": weight}
            for component_id, weight in self.components
        ]
        payload["product_profile"] = _build_instrument_product_profile(self)
        return payload


@dataclass(frozen=True)
class InvestmentPreset:
    """One beginner-friendly comparison preset."""

    preset_id: str
    label: str
    description: str
    asset_ids: tuple[str, ...]
    goal_label: str
    default_start_date: str | None = None
    default_end_date: str | None = None
    default_initial_capital: float | None = None
    default_monthly_contribution: float | None = None
    default_benchmark_ids: tuple[str, ...] | None = None
    default_fixed_income_study_mode: str | None = None
    default_fixed_income_tax_treatment: str | None = None
    default_fixed_income_window_frequency: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["asset_ids"] = list(self.asset_ids)
        payload["default_benchmark_ids"] = (
            list(self.default_benchmark_ids) if self.default_benchmark_ids is not None else None
        )
        return payload


CATEGORY_LABELS: dict[str, str] = {
    "guided_portfolios": "Carteiras guiadas",
    "custom_portfolios": "Carteiras personalizadas",
    "stocks_brazil": "Acoes brasileiras",
    "etfs_brazil": "ETFs de bolsa local",
    "international_b3": "Internacional pela B3",
    "fiis": "FIIs",
    "fixed_income_b3": "Renda fixa / juros na B3",
    "macro_proxies": "Caixa, inflacao e retorno real",
}

SOURCE_KIND_LABELS: dict[str, str] = {
    "listed_security": "Ativos negociados",
    "model_portfolio": "Carteiras guiadas",
    "fixed_income_index": "Indices de renda fixa",
    "tesouro_direct_strategy": "Tesouro Direto",
    "selic_proxy": "Proxy de caixa",
    "rate_proxy": "Proxy de taxa",
    "inflation_proxy": "Proxy de inflacao",
}


def _build_instrument_product_profile(instrument: InvestmentInstrument) -> dict[str, Any]:
    """Build product-level metadata for didactic catalog explanations."""

    if instrument.source_kind == "model_portfolio":
        return {
            "investment_type_label": "Carteira modelo",
            "liquidity_label": "Depende dos componentes e do rebalanceamento.",
            "tax_treatment_label": "Impostos tratados pelos produtos internos quando aplicavel.",
            "income_policy_label": "Renda e valorizacao sao agregadas no retorno total.",
            "fee_model_label": "Sem taxa propria; componentes podem ter custos e spreads.",
            "data_quality_label": "Backtest composto por historico dos componentes.",
            "investability_label": "Modelo replicavel manualmente, nao um produto unico.",
        }
    if instrument.source_kind == "tesouro_direct_strategy":
        return {
            "investment_type_label": "Tesouro Direto",
            "liquidity_label": "Liquidez diaria via Tesouro Direto, sujeita a calendario e preco.",
            "tax_treatment_label": "IR regressivo e IOF estimados na visao liquida.",
            "income_policy_label": (
                "Cupom e vencimentos sao aproximados pela estrategia de rolagem."
            ),
            "fee_model_label": "Nao inclui spread operacional ou eventuais custos de corretora.",
            "data_quality_label": "Historico oficial de precos e taxas do Tesouro Direto.",
            "investability_label": "Produto de varejo real, modelado por regra de rolagem.",
        }
    if instrument.source_kind == "fixed_income_index":
        return {
            "investment_type_label": "Indice de renda fixa",
            "liquidity_label": "Nao e produto negociavel diretamente.",
            "tax_treatment_label": (
                "Indice teorico bruto, salvo quando estudo aplicar visao liquida."
            ),
            "income_policy_label": "Retorno total do indice, sem fluxo de caixa individual.",
            "fee_model_label": "Sem taxa de produto; ETFs/fundos reais podem divergir.",
            "data_quality_label": "Serie historica de indice usada para metodologia.",
            "investability_label": "Referencia teorica, nao produto de prateleira.",
        }
    if instrument.source_kind in {"selic_proxy", "rate_proxy", "inflation_proxy"}:
        return {
            "investment_type_label": "Proxy macro",
            "liquidity_label": "Referencia didatica, nao produto compravel diretamente.",
            "tax_treatment_label": "Sem tributacao de produto modelada neste proxy.",
            "income_policy_label": "Acumulacao por taxa ou indice.",
            "fee_model_label": "Sem taxa de administracao ou spread.",
            "data_quality_label": "Serie macro transformada em curva comparativa.",
            "investability_label": "Proxy para decisao, nao instrumento investivel.",
        }
    if instrument.category_id == "fiis":
        return {
            "investment_type_label": "FII listado",
            "liquidity_label": "Negociado em bolsa; liquidez depende do fundo.",
            "tax_treatment_label": (
                "Rendimentos podem ser isentos; ganho de capital tem regras proprias."
            ),
            "income_policy_label": (
                "Cota ajustada aproxima retorno total, sem calendario mensal detalhado."
            ),
            "fee_model_label": (
                "Taxas do fundo ja afetam a cota; spread de negociacao nao modelado."
            ),
            "data_quality_label": "Serie ajustada em bolsa, sujeita a historico mais curto.",
            "investability_label": "Produto listado compravel na B3.",
        }
    if instrument.category_id == "international_b3":
        return {
            "investment_type_label": "ETF/BDR internacional pela B3",
            "liquidity_label": "Negociado em reais na B3; liquidez varia por produto.",
            "tax_treatment_label": "Tributacao de renda variavel local nao e modelada no catalogo.",
            "income_policy_label": "Serie ajustada aproxima dividendos/eventos no retorno total.",
            "fee_model_label": "Taxas do ETF/BDR e tracking error podem afetar o retorno.",
            "data_quality_label": (
                "Historico local em reais; pode ser mais curto que o ativo original."
            ),
            "investability_label": "Produto listado na B3 ou proxy local de exposicao global.",
        }
    if instrument.category_id == "fixed_income_b3":
        return {
            "investment_type_label": "ETF de renda fixa listado",
            "liquidity_label": "Negociado em bolsa; liquidez e spread variam por ETF.",
            "tax_treatment_label": "Imposto do produto listado nao e separado neste catalogo.",
            "income_policy_label": "Retorno total via cota ajustada, sem fluxo de cupons separado.",
            "fee_model_label": "Taxa do ETF e tracking error aparecem indiretamente na cota.",
            "data_quality_label": (
                "Historico de produto investivel, normalmente mais curto que indices."
            ),
            "investability_label": "Produto listado compravel na B3.",
        }
    return {
        "investment_type_label": "Acao listada",
        "liquidity_label": "Negociada em bolsa; liquidez depende do papel.",
        "tax_treatment_label": "Tributacao de renda variavel nao e aplicada no catalogo.",
        "income_policy_label": (
            "Serie ajustada aproxima dividendos, JCP e eventos no retorno total."
        ),
        "fee_model_label": "Corretagem, spread e emolumentos nao modelados.",
        "data_quality_label": "Historico ajustado de mercado.",
        "investability_label": "Ativo listado compravel na B3.",
    }


_VIDEO_STOCK_SLEEVE: tuple[tuple[str, float], ...] = (
    ("ITUB4", 0.069942),
    ("BBSE3", 0.041908),
    ("TAEE11", 0.028035),
    ("SUZB3", 0.023121),
    ("FLRY3", 0.016185),
    ("SBSP3", 0.013873),
    ("VIVT3", 0.006936),
)


INSTRUMENTS: tuple[InvestmentInstrument, ...] = (
    InvestmentInstrument(
        instrument_id="SARDINHA40_ORIGINAL",
        label="Carteira 40+ (video original)",
        ticker=None,
        category_id="guided_portfolios",
        category_label=CATEGORY_LABELS["guided_portfolios"],
        description=(
            "Carteira-modelo inspirada no video do Investidor Sardinha " "para a faixa de 40+."
        ),
        rationale=(
            "Mistura preservacao, dividendos e exterior usando os exemplos internacionais citados "
            "no video."
        ),
        risk_label="Media",
        region_label="Brasil + exterior",
        source_kind="model_portfolio",
        listed_on_b3=False,
        rebalance_frequency="monthly",
        implementation_note=(
            "Usa ETFs globais do video para a sleeve internacional e renormaliza os pesos "
            "setoriais das acoes brasileiras, porque o detalhamento do video soma 69,2% e nao 100%."
        ),
        components=(
            ("IMAB11", 0.25),
            ("SELIC_PROXY", 0.15),
            ("IRFM11", 0.10),
            *_VIDEO_STOCK_SLEEVE,
            ("QUAL", 0.05),
            ("VEA", 0.05),
            ("IAU", 0.05),
            ("XLP", 0.05),
            ("HGLG11", 0.05),
            ("KNRI11", 0.05),
        ),
        notes=(
            "Bitcoin foi mencionado como opcional no video e ficou fora da simulacao-base.",
            (
                "A sleeve de acoes Brasil foi renormalizada dentro dos 20% "
                "porque o mapa setorial informado soma 69,2%."
            ),
        ),
    ),
    InvestmentInstrument(
        instrument_id="SARDINHA40_B3",
        label="Carteira 40+ (versao B3)",
        ticker=None,
        category_id="guided_portfolios",
        category_label=CATEGORY_LABELS["guided_portfolios"],
        description=(
            "Versao operacional na B3 da carteira 40+, com proxies locais "
            "e rebalanceamento mensal."
        ),
        rationale=(
            "Mantem a ideia central do video, mas substitui a sleeve internacional por proxies "
            "negociaveis na B3."
        ),
        risk_label="Media",
        region_label="Brasil + internacional via B3",
        source_kind="model_portfolio",
        listed_on_b3=True,
        rebalance_frequency="monthly",
        implementation_note=(
            "Usa BDRs/ETFs locais para qualidade, exterior desenvolvido, ouro e consumo basico. "
            "A proxy de consumo basico local tem historico mais curto."
        ),
        components=(
            ("IMAB11", 0.25),
            ("SELIC_PROXY", 0.15),
            ("IRFM11", 0.10),
            *_VIDEO_STOCK_SLEEVE,
            ("BQUA39", 0.05),
            ("ACWI11", 0.05),
            ("GOLD11", 0.05),
            ("BKXI39", 0.05),
            ("HGLG11", 0.05),
            ("KNRI11", 0.05),
        ),
        notes=(
            "Mantem a logica do video, mas com proxies B3 no lugar dos ETFs globais originais.",
            "BKXI39 e alguns BDRs de ETF podem empurrar o inicio efetivo da serie para frente.",
        ),
    ),
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
        instrument_id="BBSE3",
        label="BBSE3",
        ticker="BBSE3",
        category_id="stocks_brazil",
        category_label=CATEGORY_LABELS["stocks_brazil"],
        description="Seguradora listada usada como proxy do bloco de seguradoras do video.",
        rationale=(
            "Ajuda a representar a parte mais previsivel e pagadora de "
            "dividendos da bolsa local."
        ),
        risk_label="Media",
        region_label="Brasil",
    ),
    InvestmentInstrument(
        instrument_id="TAEE11",
        label="TAEE11",
        ticker="TAEE11",
        category_id="stocks_brazil",
        category_label=CATEGORY_LABELS["stocks_brazil"],
        description="Utility eletrica usada como proxy da sleeve de energia eletrica.",
        rationale="Representa um setor tradicionalmente defensivo e gerador de caixa.",
        risk_label="Media",
        region_label="Brasil",
    ),
    InvestmentInstrument(
        instrument_id="SUZB3",
        label="SUZB3",
        ticker="SUZB3",
        category_id="stocks_brazil",
        category_label=CATEGORY_LABELS["stocks_brazil"],
        description="Proxy local para papel e celulose dentro da carteira 40+.",
        rationale="Mantem a exposicao a um setor exportador e resiliente do mercado brasileiro.",
        risk_label="Media",
        region_label="Brasil",
    ),
    InvestmentInstrument(
        instrument_id="FLRY3",
        label="FLRY3",
        ticker="FLRY3",
        category_id="stocks_brazil",
        category_label=CATEGORY_LABELS["stocks_brazil"],
        description="Proxy de servicos medicos para a sleeve defensiva de saude.",
        rationale="Ajuda a capturar um setor perene sem recorrer a small caps.",
        risk_label="Media",
        region_label="Brasil",
    ),
    InvestmentInstrument(
        instrument_id="SBSP3",
        label="SBSP3",
        ticker="SBSP3",
        category_id="stocks_brazil",
        category_label=CATEGORY_LABELS["stocks_brazil"],
        description="Proxy de saneamento para a alocacao inspirada no video.",
        rationale="Representa um servico essencial com perfil mais previsivel.",
        risk_label="Media",
        region_label="Brasil",
    ),
    InvestmentInstrument(
        instrument_id="VIVT3",
        label="VIVT3",
        ticker="VIVT3",
        category_id="stocks_brazil",
        category_label=CATEGORY_LABELS["stocks_brazil"],
        description="Proxy de telecomunicações para completar a sleeve de acoes do video.",
        rationale="Ajuda a representar um setor mais defensivo e maduro da bolsa brasileira.",
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
        instrument_id="HASH11",
        label="HASH11",
        ticker="HASH11",
        category_id="etfs_brazil",
        category_label=CATEGORY_LABELS["etfs_brazil"],
        description="ETF local de criptoativos usado como comparativo de classe alternativa.",
        rationale=(
            "Ajuda a separar retorno de alto risco de uma alocacao diversificada tradicional."
        ),
        risk_label="Muito alta",
        region_label="Brasil",
        notes=(
            "Pode ter volatilidade muito superior a acoes, FIIs e renda fixa.",
            "Entra como comparativo educacional, nao como recomendacao de alocacao.",
        ),
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
        instrument_id="ACWI11",
        label="ACWI11",
        ticker="ACWI11",
        category_id="international_b3",
        category_label=CATEGORY_LABELS["international_b3"],
        description=(
            "ETF global negociado na B3, usado como proxy simples de " "exterior diversificado."
        ),
        rationale=(
            "Ajuda a aproximar a ideia de mercados desenvolvidos fora do "
            "Brasil com um ativo local."
        ),
        risk_label="Media",
        region_label="Internacional via B3",
    ),
    InvestmentInstrument(
        instrument_id="GOLD11",
        label="GOLD11",
        ticker="GOLD11",
        category_id="international_b3",
        category_label=CATEGORY_LABELS["international_b3"],
        description="ETF local de ouro, usado como ativo de protecao no lugar do IAU.",
        rationale="Mantem a funcao defensiva e anticrise mencionada no video.",
        risk_label="Media",
        region_label="Internacional via B3",
    ),
    InvestmentInstrument(
        instrument_id="BQUA39",
        label="BQUA39",
        ticker="BQUA39",
        category_id="international_b3",
        category_label=CATEGORY_LABELS["international_b3"],
        description="BDR de ETF de qualidade americana, proxy local para a ideia do SPHQ.",
        rationale="Aproxima a tese de empresas de alta qualidade negociadas fora do Brasil.",
        risk_label="Media",
        region_label="Internacional via B3",
    ),
    InvestmentInstrument(
        instrument_id="BKXI39",
        label="BKXI39",
        ticker="BKXI39",
        category_id="international_b3",
        category_label=CATEGORY_LABELS["international_b3"],
        description=(
            "BDR de ETF global de consumo basico, proxy local para a ideia " "defensiva do XLP."
        ),
        rationale=(
            "Representa a parte internacional de consumo essencial, ainda "
            "que com historico mais curto."
        ),
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
        instrument_id="TSLA34",
        label="TSLA34",
        ticker="TSLA34",
        category_id="international_b3",
        category_label=CATEGORY_LABELS["international_b3"],
        description="BDR de acao internacional de crescimento negociado em reais na B3.",
        rationale="Exemplo de BDR individual com risco idiossincratico elevado.",
        risk_label="Muito alta",
        region_label="Internacional via B3",
    ),
    InvestmentInstrument(
        instrument_id="AMZO34",
        label="AMZO34",
        ticker="AMZO34",
        category_id="international_b3",
        category_label=CATEGORY_LABELS["international_b3"],
        description="BDR de acao internacional de comercio digital e tecnologia.",
        rationale="Permite comparar uma big tech/consumo global contra ETFs amplos.",
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
        instrument_id="VISC11",
        label="VISC11",
        ticker="VISC11",
        category_id="fiis",
        category_label=CATEGORY_LABELS["fiis"],
        description="FII de shopping centers usado para comparar tijolo de consumo.",
        rationale="Complementa os FIIs logisticos e hibridos com uma tese imobiliaria diferente.",
        risk_label="Media",
        region_label="Brasil",
    ),
    InvestmentInstrument(
        instrument_id="KNCR11",
        label="KNCR11",
        ticker="KNCR11",
        category_id="fiis",
        category_label=CATEGORY_LABELS["fiis"],
        description="FII de papel indexado majoritariamente a credito imobiliario.",
        rationale="Ajuda a comparar renda recorrente de recebiveis contra tijolo e caixa.",
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
        instrument_id="IMBB11",
        label="IMBB11",
        ticker="IMBB11",
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description="ETF de renda fixa listado que replica o IMA-B amplo com titulos NTN-B.",
        rationale=(
            "Ajuda a comparar uma versao investivel de juros reais amplos "
            "contra indices e Tesouro."
        ),
        risk_label="Baixa a media",
        region_label="Brasil",
        notes=(
            "Replica o IMA-B amplo, com NTN-Bs de diferentes vencimentos.",
            "Pode divergir do indice teorico por taxa, spread e tracking error do ETF.",
        ),
    ),
    InvestmentInstrument(
        instrument_id="B5P211",
        label="B5P211",
        ticker="B5P211",
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description="ETF listado ligado ao IMA-B5 P2, concentrado em NTN-Bs mais curtas.",
        rationale="Aproxima uma aposta compravel em IPCA+ curto para comparar retorno real.",
        risk_label="Baixa a media",
        region_label="Brasil",
        available_since="2020-11-16",
        notes=(
            "Representa uma cesta listada de juros reais mais curtos do que o IMA-B amplo.",
            "Permite comparar uma exposicao IPCA+ compravel contra Tesouro e indices sinteticos.",
        ),
    ),
    InvestmentInstrument(
        instrument_id="B5MB11",
        label="B5MB11",
        ticker="B5MB11",
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description="ETF listado ligado ao IMA-B5+, com NTN-Bs longas e mais duration.",
        rationale=(
            "Mostra uma forma investivel de alongar juros reais e sentir "
            "mais marcacao a mercado."
        ),
        risk_label="Media a alta",
        region_label="Brasil",
        notes=(
            "Replica o IMA-B5+, concentrado em NTN-Bs com prazo superior a 5 anos.",
            "Tende a oscilar mais quando a taxa real abre ou fecha do que exposicoes mais curtas.",
        ),
    ),
    InvestmentInstrument(
        instrument_id="IRFM11",
        label="IRFM11",
        ticker="IRFM11",
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description="ETF de renda fixa local usado como proxy prefixada para a carteira 40+.",
        rationale="Ajuda a representar a parte prefixada do bloco de renda fixa.",
        risk_label="Baixa a media",
        region_label="Brasil",
    ),
    InvestmentInstrument(
        instrument_id="CDI_INDEX",
        label="CDI (indice historico)",
        ticker=None,
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description=(
            "Indice diario de CDI usado para reproduzir comparativos de renda fixa "
            "sem depender de um produto especifico."
        ),
        rationale=(
            "Funciona como referencia pos-fixada para medir se assumir duration "
            "realmente valeu a pena."
        ),
        risk_label="Baixa",
        region_label="Brasil",
        source_kind="fixed_income_index",
        listed_on_b3=False,
        uses_adjusted_close=False,
        available_since="2005-12-30",
        implementation_note=(
            "Usa a serie diaria do indice CDI como benchmark de carrego pos-fixado."
        ),
        notes=(
            "Nao representa um titulo individual; representa a referencia pos-fixada do periodo.",
        ),
    ),
    InvestmentInstrument(
        instrument_id="IDKA_PRE_1A",
        label="IDkA Pre 1A",
        ticker=None,
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description="Indice ANBIMA de duration constante para prefixados curtos, perto de 1 ano.",
        rationale="Ajuda a medir o carrego prefixado curto contra o pos-fixado.",
        risk_label="Baixa a media",
        region_label="Brasil",
        source_kind="fixed_income_index",
        listed_on_b3=False,
        uses_adjusted_close=False,
        available_since="2005-12-30",
    ),
    InvestmentInstrument(
        instrument_id="IDKA_PRE_2A",
        label="IDkA Pre 2A",
        ticker=None,
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description="Indice ANBIMA de duration constante para prefixados em torno de 2 anos.",
        rationale="Mostra o retorno adicional de alongar um pouco a duration prefixada.",
        risk_label="Media",
        region_label="Brasil",
        source_kind="fixed_income_index",
        listed_on_b3=False,
        uses_adjusted_close=False,
        available_since="2005-12-30",
    ),
    InvestmentInstrument(
        instrument_id="IDKA_PRE_3A",
        label="IDkA Pre 3A",
        ticker=None,
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description="Indice ANBIMA de duration constante para prefixados em torno de 3 anos.",
        rationale="Serve para comparar o miolo da curva prefixada com os extremos.",
        risk_label="Media",
        region_label="Brasil",
        source_kind="fixed_income_index",
        listed_on_b3=False,
        uses_adjusted_close=False,
        available_since="2005-12-30",
    ),
    InvestmentInstrument(
        instrument_id="IDKA_PRE_5A",
        label="IDkA Pre 5A",
        ticker=None,
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description="Indice ANBIMA de duration constante para prefixados longos, perto de 5 anos.",
        rationale="Ajuda a visualizar o premio e o risco de duration no prefixado longo.",
        risk_label="Media a alta",
        region_label="Brasil",
        source_kind="fixed_income_index",
        listed_on_b3=False,
        uses_adjusted_close=False,
        available_since="2005-12-30",
    ),
    InvestmentInstrument(
        instrument_id="IDKA_IPCA_2A",
        label="IDkA IPCA 2A",
        ticker=None,
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description="Indice ANBIMA de duration constante para IPCA+ curto, perto de 2 anos.",
        rationale="E a referencia mais consistente para buy and hold de juros reais curtos.",
        risk_label="Baixa a media",
        region_label="Brasil",
        source_kind="fixed_income_index",
        listed_on_b3=False,
        uses_adjusted_close=False,
        available_since="2005-12-30",
        implementation_note=(
            "Representa um indice de duration constante, nao a compra de um titulo isolado."
        ),
    ),
    InvestmentInstrument(
        instrument_id="IDKA_IPCA_3A",
        label="IDkA IPCA 3A",
        ticker=None,
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description="Indice ANBIMA de duration constante para IPCA+ em torno de 3 anos.",
        rationale="Ajuda a comparar o miolo da curva real com o curto e o longo.",
        risk_label="Media",
        region_label="Brasil",
        source_kind="fixed_income_index",
        listed_on_b3=False,
        uses_adjusted_close=False,
        available_since="2005-12-30",
    ),
    InvestmentInstrument(
        instrument_id="IDKA_IPCA_5A",
        label="IDkA IPCA 5A",
        ticker=None,
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description="Indice ANBIMA de duration constante para IPCA+ longo, perto de 5 anos.",
        rationale="Mostra quando alongar a duration real compensa em retorno e marcacao a mercado.",
        risk_label="Media a alta",
        region_label="Brasil",
        source_kind="fixed_income_index",
        listed_on_b3=False,
        uses_adjusted_close=False,
        available_since="2005-12-30",
    ),
    InvestmentInstrument(
        instrument_id="TD_SELIC",
        label="Tesouro Selic (rolagem oficial)",
        ticker=None,
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description=(
            "Estrategia de Tesouro Direto baseada no historico oficial de precos e taxas, "
            "sempre carregando um Tesouro Selic ofertado."
        ),
        rationale=(
            "Aproxima melhor a experiencia do investidor pessoa fisica "
            "do que um indice puro de CDI."
        ),
        risk_label="Baixa",
        region_label="Brasil",
        source_kind="tesouro_direct_strategy",
        listed_on_b3=False,
        uses_adjusted_close=False,
        available_since="2006-08-09",
        implementation_note=(
            "Usa o CSV diario oficial do Tesouro Direto e rola para o titulo disponivel "
            "mais curto quando o papel anterior deixa de ficar dentro da estrategia."
        ),
        notes=(
            "A marcacao a mercado usa precos do Tesouro Direto, nao um indice sintetico.",
            "A camada liquida estima IR regressivo e IOF para resgates inferiores a 30 dias.",
        ),
    ),
    InvestmentInstrument(
        instrument_id="TD_PREFIXADO_2A",
        label="Tesouro Prefixado 2A (rolagem oficial)",
        ticker=None,
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description=(
            "Estrategia de rolagem com Tesouro Prefixado usando titulos oficiais "
            "perto de 2 anos de vencimento."
        ),
        rationale="Mostra o prefixado curto com precos reais de varejo do Tesouro Direto.",
        risk_label="Media",
        region_label="Brasil",
        source_kind="tesouro_direct_strategy",
        listed_on_b3=False,
        uses_adjusted_close=False,
        available_since="2006-08-10",
    ),
    InvestmentInstrument(
        instrument_id="TD_PREFIXADO_3A",
        label="Tesouro Prefixado 3A (rolagem oficial)",
        ticker=None,
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description=(
            "Estrategia de rolagem com Tesouro Prefixado usando titulos oficiais "
            "perto de 3 anos de vencimento."
        ),
        rationale="Ajuda a enxergar o miolo da curva prefixada com produto real de prateleira.",
        risk_label="Media",
        region_label="Brasil",
        source_kind="tesouro_direct_strategy",
        listed_on_b3=False,
        uses_adjusted_close=False,
        available_since="2006-08-10",
    ),
    InvestmentInstrument(
        instrument_id="TD_PREFIXADO_5A",
        label="Tesouro Prefixado 5A (rolagem oficial)",
        ticker=None,
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description=(
            "Estrategia de rolagem com Tesouro Prefixado usando titulos oficiais "
            "perto de 5 anos de vencimento."
        ),
        rationale="Explicita o premio e o susto de duration longa com precos historicos reais.",
        risk_label="Media a alta",
        region_label="Brasil",
        source_kind="tesouro_direct_strategy",
        listed_on_b3=False,
        uses_adjusted_close=False,
        available_since="2006-08-10",
    ),
    InvestmentInstrument(
        instrument_id="TD_IPCA_2A",
        label="Tesouro IPCA+ 2A (rolagem oficial)",
        ticker=None,
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description=(
            "Estrategia de rolagem com Tesouro IPCA+ usando titulos oficiais "
            "perto de 2 anos de vencimento."
        ),
        rationale="Aproxima a experiencia real do investidor em juros reais curtos.",
        risk_label="Baixa a media",
        region_label="Brasil",
        source_kind="tesouro_direct_strategy",
        listed_on_b3=False,
        uses_adjusted_close=False,
        available_since="2006-08-10",
    ),
    InvestmentInstrument(
        instrument_id="TD_IPCA_3A",
        label="Tesouro IPCA+ 3A (rolagem oficial)",
        ticker=None,
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description=(
            "Estrategia de rolagem com Tesouro IPCA+ usando titulos oficiais "
            "perto de 3 anos de vencimento."
        ),
        rationale="Mostra o miolo da curva real com historico oficial de precos ao investidor.",
        risk_label="Media",
        region_label="Brasil",
        source_kind="tesouro_direct_strategy",
        listed_on_b3=False,
        uses_adjusted_close=False,
        available_since="2006-08-10",
    ),
    InvestmentInstrument(
        instrument_id="TD_IPCA_5A",
        label="Tesouro IPCA+ 5A (rolagem oficial)",
        ticker=None,
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description=(
            "Estrategia de rolagem com Tesouro IPCA+ usando titulos oficiais "
            "perto de 5 anos de vencimento."
        ),
        rationale="Deixa claro quanto a duration longa em IPCA+ agrega ou so amplia o susto.",
        risk_label="Media a alta",
        region_label="Brasil",
        source_kind="tesouro_direct_strategy",
        listed_on_b3=False,
        uses_adjusted_close=False,
        available_since="2006-08-10",
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
        proxy_kind="selic_daily",
        notes=("Modelo por taxa diaria, nao por cotacao secundaria de um titulo especifico.",),
    ),
    InvestmentInstrument(
        instrument_id="CDI_PROXY",
        label="CDI / taxa extramercado (proxy)",
        ticker=None,
        category_id="macro_proxies",
        category_label=CATEGORY_LABELS["macro_proxies"],
        description=(
            "Proxy didatico de caixa pos-fixado usando a taxa extramercado diaria "
            "derivada da SELIC."
        ),
        rationale=(
            "Ajuda a comparar a ideia de CDI/caixa contra bolsa, FIIs e juros reais "
            "sem exigir um produto especifico."
        ),
        risk_label="Baixa",
        region_label="Brasil",
        source_kind="rate_proxy",
        listed_on_b3=False,
        uses_adjusted_close=False,
        proxy_kind="cdi_like_daily",
        notes=("A taxa extramercado do BCB e tratada aqui como proxy simples de CDI/cash.",),
    ),
    InvestmentInstrument(
        instrument_id="IPCA_PROXY",
        label="IPCA / poder de compra",
        ticker=None,
        category_id="macro_proxies",
        category_label=CATEGORY_LABELS["macro_proxies"],
        description=(
            "Curva de inflacao acumulada para mostrar quanto o dinheiro precisaria render "
            "so para preservar poder de compra."
        ),
        rationale=(
            "Funciona como piso didatico de retorno real, deixando claro quando um "
            "investimento so parece bom no valor nominal."
        ),
        risk_label="Referencia",
        region_label="Brasil",
        source_kind="inflation_proxy",
        listed_on_b3=False,
        uses_adjusted_close=False,
        proxy_kind="ipca_monthly",
        notes=("Nao representa um ativo negociado; representa a inflacao oficial acumulada.",),
    ),
    InvestmentInstrument(
        instrument_id="PREFIXADO_11_PROXY",
        label="Prefixado 11% a.a. (proxy)",
        ticker=None,
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description=(
            "Proxy nominal de taxa fixa para comparar cenarios de renda fixa prefixada "
            "sem marcar um titulo especifico a mercado."
        ),
        rationale=(
            "Ajuda a visualizar quando uma taxa fixa simples teria sido suficiente "
            "contra caixa, inflacao e bolsa."
        ),
        risk_label="Baixa a media",
        region_label="Brasil",
        source_kind="rate_proxy",
        listed_on_b3=False,
        uses_adjusted_close=False,
        proxy_kind="fixed_rate",
        fixed_rate_annual=0.11,
        notes=(
            "Nao simula duration nem marcacao a mercado; apenas um rendimento nominal constante.",
        ),
    ),
    InvestmentInstrument(
        instrument_id="IPCA_PLUS_6_PROXY",
        label="IPCA+ 6% a.a. (proxy)",
        ticker=None,
        category_id="fixed_income_b3",
        category_label=CATEGORY_LABELS["fixed_income_b3"],
        description=(
            "Proxy de juros reais combinando inflacao IPCA com um premio real fixo " "de 6% ao ano."
        ),
        rationale=(
            "Serve como referencia didatica para comparar crescimento nominal e "
            "preservacao de poder de compra."
        ),
        risk_label="Baixa a media",
        region_label="Brasil",
        source_kind="rate_proxy",
        listed_on_b3=False,
        uses_adjusted_close=False,
        proxy_kind="ipca_plus",
        spread_rate_annual=0.06,
        notes=("Nao representa um titulo individual do Tesouro; representa uma taxa real-alvo.",),
    ),
    InvestmentInstrument(
        instrument_id="QUAL",
        label="QUAL (ETF original)",
        ticker="QUAL",
        category_id="international_b3",
        category_label=CATEGORY_LABELS["international_b3"],
        description="ETF americano de qualidade usado internamente na carteira original do video.",
        rationale="Mantem fidelidade metodologica ao exemplo internacional citado no video.",
        risk_label="Media",
        region_label="Exterior direto",
        listed_on_b3=False,
        visible_in_catalog=False,
    ),
    InvestmentInstrument(
        instrument_id="VEA",
        label="VEA (ETF original)",
        ticker="VEA",
        category_id="international_b3",
        category_label=CATEGORY_LABELS["international_b3"],
        description=(
            "ETF americano de mercados desenvolvidos fora dos EUA usado na " "carteira original."
        ),
        rationale="Mantem fidelidade ao bloco internacional ex-EUA descrito no video.",
        risk_label="Media",
        region_label="Exterior direto",
        listed_on_b3=False,
        visible_in_catalog=False,
    ),
    InvestmentInstrument(
        instrument_id="IAU",
        label="IAU (ETF original)",
        ticker="IAU",
        category_id="international_b3",
        category_label=CATEGORY_LABELS["international_b3"],
        description="ETF americano de ouro usado internamente na carteira original do video.",
        rationale="Mantem a protecao em ouro do desenho original.",
        risk_label="Media",
        region_label="Exterior direto",
        listed_on_b3=False,
        visible_in_catalog=False,
    ),
    InvestmentInstrument(
        instrument_id="XLP",
        label="XLP (ETF original)",
        ticker="XLP",
        category_id="international_b3",
        category_label=CATEGORY_LABELS["international_b3"],
        description=(
            "ETF americano de consumo basico usado internamente na carteira " "original do video."
        ),
        rationale="Mantem a sleeve defensiva de staples do desenho original.",
        risk_label="Media",
        region_label="Exterior direto",
        listed_on_b3=False,
        visible_in_catalog=False,
    ),
)


PRESETS: tuple[InvestmentPreset, ...] = (
    InvestmentPreset(
        preset_id="fixed_income_ipca_vs_cdi",
        label="IPCA+ vs CDI (video)",
        description=("Reproduz o recorte do video com CDI e durations de 2, 3 e 5 anos em IPCA+."),
        asset_ids=("CDI_INDEX", "IDKA_IPCA_2A", "IDKA_IPCA_3A", "IDKA_IPCA_5A"),
        goal_label=(
            "Conferir se o IPCA+ venceu o pos-fixado no ciclo completo e em janelas menores."
        ),
        default_start_date="2005-12-30",
        default_end_date="2026-03-31",
        default_initial_capital=1000.0,
        default_monthly_contribution=0.0,
        default_benchmark_ids=(),
        default_fixed_income_study_mode="index_duration",
        default_fixed_income_tax_treatment="gross",
        default_fixed_income_window_frequency="monthly",
    ),
    InvestmentPreset(
        preset_id="fixed_income_full_cycle",
        label="Renda fixa por duration",
        description=(
            "Coloca lado a lado indices de duration constante "
            "e estrategias com Tesouro Direto real."
        ),
        asset_ids=(
            "CDI_INDEX",
            "IDKA_PRE_1A",
            "IDKA_PRE_2A",
            "IDKA_PRE_3A",
            "IDKA_PRE_5A",
            "IDKA_IPCA_2A",
            "IDKA_IPCA_3A",
            "IDKA_IPCA_5A",
            "TD_SELIC",
            "TD_PREFIXADO_2A",
            "TD_PREFIXADO_3A",
            "TD_PREFIXADO_5A",
            "TD_IPCA_2A",
            "TD_IPCA_3A",
            "TD_IPCA_5A",
        ),
        goal_label=(
            "Comparar a tese do video com a experiencia real do investidor em Tesouro Direto."
        ),
        default_start_date="2005-12-30",
        default_end_date="2026-03-31",
        default_initial_capital=1000.0,
        default_monthly_contribution=0.0,
        default_benchmark_ids=(),
        default_fixed_income_study_mode="both",
        default_fixed_income_tax_treatment="net",
        default_fixed_income_window_frequency="monthly",
    ),
    InvestmentPreset(
        preset_id="fixed_income_tesouro_real",
        label="Tesouro Direto real",
        description=(
            "Foca na experiencia do investidor pessoa fisica usando precos oficiais do Tesouro "
            "Direto, com versao bruta e liquida."
        ),
        asset_ids=(
            "CDI_INDEX",
            "TD_SELIC",
            "TD_PREFIXADO_2A",
            "TD_PREFIXADO_5A",
            "TD_IPCA_2A",
            "TD_IPCA_5A",
        ),
        goal_label=(
            "Descobrir qual escolha de renda fixa fez mais sentido na prateleira real do Tesouro."
        ),
        default_start_date="2006-08-10",
        default_end_date="2026-03-31",
        default_initial_capital=1000.0,
        default_monthly_contribution=0.0,
        default_benchmark_ids=(),
        default_fixed_income_study_mode="retail_treasury",
        default_fixed_income_tax_treatment="net",
        default_fixed_income_window_frequency="monthly",
    ),
    InvestmentPreset(
        preset_id="fixed_income_ntnb_etfs",
        label="ETFs NTN-B historicos",
        description=(
            "Coloca lado a lado ETFs compraveis de NTN-B na B3 para comparar retorno nominal "
            "e retorno real."
        ),
        asset_ids=("IMAB11", "IMBB11", "B5P211", "B5MB11"),
        goal_label=(
            "Descobrir como juros reais amplos, curtos e longos teriam rendido via ETFs listados."
        ),
        default_start_date="2020-11-16",
        default_end_date="2026-03-31",
        default_initial_capital=1000.0,
        default_monthly_contribution=0.0,
        default_benchmark_ids=("selic_cash",),
    ),
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
        asset_ids=("SELIC_PROXY", "CDI_PROXY", "IMAB11", "HGLG11", "MXRF11"),
        goal_label="Ver como renda fixa e FIIs se comportam lado a lado.",
    ),
    InvestmentPreset(
        preset_id="real_return",
        label="Retorno real",
        description="Compara caixa, inflacao e juros reais no mesmo fluxo de aportes.",
        asset_ids=(
            "IPCA_PROXY",
            "SELIC_PROXY",
            "CDI_PROXY",
            "IPCA_PLUS_6_PROXY",
            "IMAB11",
        ),
        goal_label=("Descobrir quem realmente preservou ou ampliou poder de compra no periodo."),
    ),
    InvestmentPreset(
        preset_id="global_b3",
        label="Global pela B3",
        description="Internacionalizacao por ETF e BDR, sem abrir conta fora.",
        asset_ids=("SELIC_PROXY", "IVVB11", "ACWI11", "AAPL34", "MSFT34", "GOGL34"),
        goal_label="Comparar acesso internacional amplo versus concentrado.",
    ),
    InvestmentPreset(
        preset_id="global_bdr_growth",
        label="BDRs de crescimento",
        description="Compara big techs e empresas globais acessiveis via BDR na B3.",
        asset_ids=("SELIC_PROXY", "IVVB11", "AAPL34", "MSFT34", "GOGL34", "AMZO34", "TSLA34"),
        goal_label="Separar diversificacao internacional ampla de concentracao em BDRs.",
    ),
    InvestmentPreset(
        preset_id="fii_income_ladder",
        label="FIIs por tipo",
        description="Compara FIIs logisticos, hibridos, shoppings e recebiveis.",
        asset_ids=("SELIC_PROXY", "HGLG11", "KNRI11", "XPLG11", "VISC11", "MXRF11", "KNCR11"),
        goal_label="Entender como diferentes tipos de FII aparecem em retorno, queda e renda.",
    ),
    InvestmentPreset(
        preset_id="risk_spectrum",
        label="Escada de risco",
        description="Coloca caixa, juros reais, bolsa, exterior, FIIs e cripto ETF lado a lado.",
        asset_ids=("SELIC_PROXY", "IMAB11", "BOVA11", "IVVB11", "HGLG11", "HASH11"),
        goal_label="Visualizar o preco de buscar mais retorno em classes mais volateis.",
    ),
    InvestmentPreset(
        preset_id="sardinha_40_plus",
        label="Carteira 40+ (video)",
        description=(
            "Simulacao pronta da alocacao apresentada no video para " "investidores acima dos 40."
        ),
        asset_ids=(
            "SARDINHA40_ORIGINAL",
            "SARDINHA40_B3",
            "SELIC_PROXY",
            "BOVA11",
            "IVVB11",
        ),
        goal_label=(
            "Comparar a alocacao do video com proxies locais, SELIC e bolsa ampla no mesmo "
            "fluxo de aportes."
        ),
    ),
    InvestmentPreset(
        preset_id="pre_retirement",
        label="Pre-aposentadoria",
        description="Mistura juros reais, caixa e renda recorrente para transicao de fase.",
        asset_ids=(
            "SELIC_PROXY",
            "IPCA_PLUS_6_PROXY",
            "IMAB11",
            "HGLG11",
            "KNRI11",
        ),
        goal_label=(
            "Comparar estabilidade, renda e preservacao de poder de compra perto da aposentadoria."
        ),
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

    from .investor_easy_parity import build_investor_easy_parity
    from .product_data_plan import build_product_data_plan

    visible_items = [item for item in INSTRUMENTS if item.visible_in_catalog]
    categories = [
        {
            "category_id": category_id,
            "label": label,
            "count": sum(1 for item in visible_items if item.category_id == category_id),
        }
        for category_id, label in CATEGORY_LABELS.items()
        if any(item.category_id == category_id for item in visible_items)
    ]
    return {
        "categories": categories,
        "instruments": [item.to_payload() for item in visible_items],
        "presets": [item.to_payload() for item in PRESETS],
        "benchmark_options": list(BENCHMARK_OPTIONS),
        "market_explorer": _build_market_explorer_payload(visible_items),
        "product_data_plan": build_product_data_plan(instruments=list(INSTRUMENTS)),
        "investor_easy_parity": build_investor_easy_parity(),
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
                "CDI, IPCA, prefixado e IPCA+ aparecem como proxies didaticos para "
                "comparacao, nao como titulos varejo especificos."
            ),
            (
                "Os indices historicos de CDI e IDkA permitem comparar duration de "
                "renda fixa com cotacao diaria e janelas moveis."
            ),
            (
                "As estrategias oficiais de Tesouro Direto usam o historico diario de "
                "precos e taxas do Tesouro Transparente para aproximar a experiencia de varejo."
            ),
            (
                "ETFs de NTN-B listados mostram uma experiencia investivel em bolsa, mas tem "
                "historico mais curto e podem divergir do indice ANBIMA por "
                "custos e tracking error."
            ),
            (
                "As carteiras guiadas usam rebalanceamento mensal e podem ter um "
                "inicio efetivo posterior ao pedido quando algum componente tem "
                "historico mais curto."
            ),
            (
                "Alguns ativos podem ter historico mais curto do que o periodo "
                "pedido. Nesses casos, a plataforma avisa e exclui o comparativo "
                "para manter justica."
            ),
        ],
    }


def _build_market_explorer_payload(
    visible_items: list[InvestmentInstrument],
) -> dict[str, Any]:
    """Build lightweight catalog facets inspired by market-list products."""

    return {
        "title": "Explorador de mercado",
        "plain_language_summary": (
            "Visao inicial do universo disponivel no Workbench por categoria, tipo de produto, "
            "risco e regiao. Rankings historicos completos entram em ciclos posteriores."
        ),
        "category_lists": [
            {
                "list_id": category_id,
                "label": label,
                "count": len(items),
                "sample_instrument_ids": [item.instrument_id for item in items[:6]],
                "sample_labels": [item.label for item in items[:6]],
            }
            for category_id, label, items in _group_catalog_items(
                visible_items,
                key=lambda item: item.category_id,
                label=lambda item: item.category_label,
            )
        ],
        "curated_lists": _build_curated_market_lists(visible_items),
        "product_type_facets": [
            {
                "source_kind": source_kind,
                "label": SOURCE_KIND_LABELS.get(source_kind, source_kind.replace("_", " ").title()),
                "count": len(items),
            }
            for source_kind, _label, items in _group_catalog_items(
                visible_items,
                key=lambda item: item.source_kind,
                label=lambda item: SOURCE_KIND_LABELS.get(
                    item.source_kind,
                    item.source_kind.replace("_", " ").title(),
                ),
            )
        ],
        "risk_facets": _count_facet(
            visible_items,
            facet_id="risk",
            key=lambda item: item.risk_label,
        ),
        "region_facets": _count_facet(
            visible_items,
            facet_id="region",
            key=lambda item: item.region_label,
        ),
        "product_data_filters": _build_product_data_filters(visible_items),
        "product_data_screeners": _build_product_data_screeners(visible_items),
        "product_data_rankings": _build_product_data_rankings(visible_items),
        "ranking_backlog": [
            {
                "ranking_id": "final_value",
                "label": "Valor final",
                "status": "available_in_market_rankings",
            },
            {
                "ranking_id": "drawdown",
                "label": "Quem caiu menos",
                "status": "available_in_market_rankings",
            },
            {
                "ranking_id": "real_cagr",
                "label": "Protecao contra inflacao",
                "status": "available_in_market_rankings",
            },
            {
                "ranking_id": "income_generation",
                "label": "Renda acumulada",
                "status": "available_in_result_stories",
            },
            {
                "ranking_id": "mark_to_market_stress",
                "label": "Marcação a mercado extrema",
                "status": "available_in_result_stories",
            },
            {
                "ranking_id": "best_profile_match",
                "label": "Melhor perfil de decisão",
                "status": "available_in_result_stories",
            },
            {
                "ranking_id": "guided_factor_score",
                "label": "Score fatorial guiado",
                "status": "available_in_market_rankings",
            },
            {
                "ranking_id": "momentum_beta_var",
                "label": "Momentum, beta e VaR",
                "status": "planned",
            },
        ],
    }


def _build_product_data_filters(
    visible_items: list[InvestmentInstrument],
) -> list[dict[str, Any]]:
    from .product_data_connectors import load_cached_source_rows

    rows = load_cached_source_rows(source_id="b3_fii_listed")
    by_ticker = {row["ticker"].upper(): row for row in rows if row.get("ticker")}
    fii_items = [
        item
        for item in visible_items
        if item.category_id == "fiis" and item.ticker and item.ticker.upper() in by_ticker
    ]
    if not fii_items:
        return []

    segment_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    liquidity_counts: dict[str, int] = {}
    income_focus_counts: dict[str, int] = {}
    for item in fii_items:
        row = by_ticker[str(item.ticker).upper()]
        segment = row.get("segmento") or "Nao informado"
        status = row.get("status_listagem") or "Nao informado"
        liquidity = row.get("liquidity_label") or "Nao informado"
        income_focus = row.get("income_focus") or "Nao informado"
        segment_counts[segment] = segment_counts.get(segment, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1
        liquidity_counts[liquidity] = liquidity_counts.get(liquidity, 0) + 1
        income_focus_counts[income_focus] = income_focus_counts.get(income_focus, 0) + 1
    return [
        {
            "filter_id": "fii_segment",
            "label": "Segmento de FII",
            "source_id": "b3_fii_listed",
            "status": "available",
            "options": [
                {"value": segment, "label": segment, "count": count}
                for segment, count in sorted(segment_counts.items())
            ],
        },
        {
            "filter_id": "fii_listing_status",
            "label": "Status de listagem",
            "source_id": "b3_fii_listed",
            "status": "available",
            "options": [
                {"value": status, "label": status, "count": count}
                for status, count in sorted(status_counts.items())
            ],
        },
        {
            "filter_id": "fii_liquidity",
            "label": "Liquidez estimada",
            "source_id": "b3_fii_listed",
            "status": "available",
            "options": [
                {"value": liquidity, "label": liquidity, "count": count}
                for liquidity, count in sorted(liquidity_counts.items())
            ],
        },
        {
            "filter_id": "fii_income_focus",
            "label": "Tipo de renda",
            "source_id": "b3_fii_listed",
            "status": "available",
            "options": [
                {"value": focus, "label": focus, "count": count}
                for focus, count in sorted(income_focus_counts.items())
            ],
        },
    ]


def _build_product_data_screeners(
    visible_items: list[InvestmentInstrument],
) -> list[dict[str, Any]]:
    from .product_data_connectors import load_cached_source_rows

    rows = load_cached_source_rows(source_id="b3_fii_listed")
    by_ticker = {row["ticker"].upper(): row for row in rows if row.get("ticker")}
    matched_rows = [
        {
            "instrument_id": item.instrument_id,
            "label": item.label,
            "ticker": item.ticker,
            "segment": by_ticker[str(item.ticker).upper()].get("segmento"),
            "listing_status": by_ticker[str(item.ticker).upper()].get("status_listagem"),
            "yield_12m_pct": _float_or_none(
                by_ticker[str(item.ticker).upper()].get("yield_12m_pct")
            ),
            "liquidity_label": by_ticker[str(item.ticker).upper()].get("liquidity_label"),
            "income_focus": by_ticker[str(item.ticker).upper()].get("income_focus"),
            "data_quality_score": _float_or_none(
                by_ticker[str(item.ticker).upper()].get("data_quality_score")
            ),
        }
        for item in visible_items
        if item.category_id == "fiis" and item.ticker and item.ticker.upper() in by_ticker
    ]
    if not matched_rows:
        return []
    return [
        {
            "screener_id": "fii_listed_metadata",
            "label": "FIIs com metadados B3 em cache",
            "source_id": "b3_fii_listed",
            "status": "available",
            "methodology": (
                "Lista FIIs do catalogo que encontraram ticker no cache local da fonte B3."
            ),
            "rows": matched_rows,
        }
    ]


def _build_product_data_rankings(
    visible_items: list[InvestmentInstrument],
) -> list[dict[str, Any]]:
    screeners = _build_product_data_screeners(visible_items)
    if not screeners:
        return []
    quality_rows = [
        {
            "rank": index + 1,
            "instrument_id": row["instrument_id"],
            "label": row["label"],
            "score": round(row.get("data_quality_score") or 0.5, 2),
            "reason": (
                "Ticker presente no cache B3 de FIIs, status de listagem disponivel "
                "e campos de perfil preenchidos."
            ),
        }
        for index, row in enumerate(
            sorted(
                screeners[0]["rows"],
                key=lambda item: item.get("data_quality_score") or 0.0,
                reverse=True,
            )
        )
    ]
    income_rows = [
        {
            "rank": index + 1,
            "instrument_id": row["instrument_id"],
            "label": row["label"],
            "score": _fii_income_quality_score(row),
            "reason": _fii_income_quality_reason(row),
        }
        for index, row in enumerate(
            sorted(
                screeners[0]["rows"],
                key=_fii_income_quality_score,
                reverse=True,
            )
        )
    ]
    return [
        {
            "ranking_id": "fii_data_quality",
            "label": "Qualidade de dado FII",
            "source_id": "b3_fii_listed",
            "status": "available",
            "methodology": (
                "Ranking por completude e confianca dos metadados FII disponiveis no cache local."
            ),
            "rows": quality_rows,
        },
        {
            "ranking_id": "fii_income_quality",
            "label": "Renda FII com qualidade",
            "source_id": "b3_fii_listed",
            "status": "available_seed",
            "methodology": (
                "Score didatico combina yield 12m, liquidez qualitativa e qualidade do dado. "
                "Quando a fonte esta em fallback, use como triagem inicial, nao recomendacao."
            ),
            "rows": income_rows,
        },
    ]


def _float_or_none(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def _fii_income_quality_score(row: dict[str, Any]) -> float:
    yield_pct = row.get("yield_12m_pct") or 0.0
    data_quality = row.get("data_quality_score") or 0.5
    liquidity_multiplier = {
        "Alta": 1.0,
        "Media": 0.85,
        "Baixa": 0.65,
    }.get(str(row.get("liquidity_label") or ""), 0.55)
    return round(float(yield_pct) * float(data_quality) * liquidity_multiplier, 2)


def _fii_income_quality_reason(row: dict[str, Any]) -> str:
    yield_pct = row.get("yield_12m_pct")
    liquidity = row.get("liquidity_label") or "liquidez nao informada"
    focus = row.get("income_focus") or "foco de renda nao informado"
    if yield_pct is None:
        return f"{focus}; {liquidity}; yield 12m ausente no cache."
    return f"{focus}; {liquidity}; yield 12m aproximado de {yield_pct:.1f}% no cache."


def _build_curated_market_lists(
    visible_items: list[InvestmentInstrument],
) -> list[dict[str, Any]]:
    by_id = {item.instrument_id: item for item in visible_items}
    definitions = (
        {
            "list_id": "monthly_income_candidates",
            "label": "Candidatos a renda mensal",
            "description": "FIIs e juros usados para estudar renda recorrente e estabilidade.",
            "instrument_ids": (
                "SELIC_PROXY",
                "CDI_PROXY",
                "HGLG11",
                "KNRI11",
                "VISC11",
                "MXRF11",
                "KNCR11",
            ),
        },
        {
            "list_id": "fii_segments",
            "label": "FIIs por segmento",
            "description": "Tijolo logistico, hibrido, shopping e papel no mesmo recorte.",
            "instrument_ids": ("HGLG11", "KNRI11", "XPLG11", "VISC11", "MXRF11", "KNCR11"),
        },
        {
            "list_id": "global_b3_access",
            "label": "Exterior via B3",
            "description": "ETFs amplos, ouro, qualidade global e BDRs individuais.",
            "instrument_ids": (
                "IVVB11",
                "ACWI11",
                "GOLD11",
                "BQUA39",
                "AAPL34",
                "MSFT34",
                "GOGL34",
                "AMZO34",
                "TSLA34",
            ),
        },
        {
            "list_id": "ntnb_investable",
            "label": "NTN-B investivel",
            "description": "ETFs de juros reais compraveis na B3, com diferentes durations.",
            "instrument_ids": ("IMAB11", "IMBB11", "B5P211", "B5MB11"),
        },
        {
            "list_id": "retail_treasury_real",
            "label": "Tesouro Direto real",
            "description": "Estrategias oficiais de Tesouro para comparar prateleira de varejo.",
            "instrument_ids": (
                "TD_SELIC",
                "TD_PREFIXADO_2A",
                "TD_PREFIXADO_5A",
                "TD_IPCA_2A",
                "TD_IPCA_5A",
            ),
        },
        {
            "list_id": "risk_ladder",
            "label": "Escada de risco",
            "description": "Do caixa a cripto ETF para enxergar retorno, volatilidade e queda.",
            "instrument_ids": ("SELIC_PROXY", "IMAB11", "BOVA11", "IVVB11", "HGLG11", "HASH11"),
        },
    )
    lists: list[dict[str, Any]] = []
    for definition in definitions:
        items = [by_id[item_id] for item_id in definition["instrument_ids"] if item_id in by_id]
        lists.append(
            {
                "list_id": definition["list_id"],
                "label": definition["label"],
                "description": definition["description"],
                "count": len(items),
                "instrument_ids": [item.instrument_id for item in items],
                "sample_labels": [item.label for item in items[:8]],
                "risk_labels": sorted({item.risk_label for item in items}),
            }
        )
    return lists


def _group_catalog_items(
    items: list[InvestmentInstrument],
    *,
    key: Any,
    label: Any,
) -> list[tuple[str, str, list[InvestmentInstrument]]]:
    grouped: dict[str, tuple[str, list[InvestmentInstrument]]] = {}
    for item in items:
        group_key = str(key(item))
        group_label, group_items = grouped.setdefault(group_key, (str(label(item)), []))
        grouped[group_key] = (group_label, [*group_items, item])
    return [
        (group_key, group_label, group_items)
        for group_key, (group_label, group_items) in sorted(grouped.items())
    ]


def _count_facet(
    items: list[InvestmentInstrument],
    *,
    facet_id: str,
    key: Any,
) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for item in items:
        facet_value = str(key(item))
        counts[facet_value] = counts.get(facet_value, 0) + 1
    return [
        {"facet_id": facet_id, "label": label, "count": count}
        for label, count in sorted(counts.items(), key=lambda row: (-row[1], row[0]))
    ]
