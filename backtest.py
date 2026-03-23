import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

class MartingaleBacktester:
    def __init__(self, symbol='BTC-BRL', start_capital=30000, base_bet=500, 
                 multiplier=2.0, drop_step=0.10, take_profit=0.15):
        """
        Configura os parâmetros da estratégia.
        symbol: Ticker do ativo (ex: BTC-BRL ou BTC-USD)
        start_capital: Capital total disponível
        base_bet: Valor da primeira entrada
        multiplier: Fator de multiplicação do Martingale (Geo. Progression)
        drop_step: % de queda para acionar nova camada (0.10 = 10%)
        take_profit: % de ganho sobre a CAMADA para vender (LIFO)
        """
        self.symbol = symbol
        self.capital = start_capital
        self.initial_capital = start_capital
        self.base_bet = base_bet
        self.multiplier = multiplier
        self.drop_step = drop_step
        self.take_profit = take_profit
        
        # Estado do Sistema
        self.cash = start_capital
        self.layers = [] # Lista de dicts: [{'price': float, 'btc_qty': float, 'cost': float}]
        self.history = []
        self.trade_log = []

    def fetch_data(self, period="1y"):
        print(f"Baixando dados para {self.symbol}...")
        self.df = yf.download(self.symbol, period=period, progress=False)
        # Limpeza básica
        self.df.dropna(inplace=True)
        print(f"Dados carregados: {len(self.df)} registros.")

    def run(self):
        # Loop dia a dia (Row-based iteration é necessária pois o estado depende do dia anterior)
        # Em produção/high-freq, vetorizaríamos isso, mas para backtest de swing trade, loop é mais legível.
        
        highest_price_seen = 0 # Para controle de referência inicial
        
        for date, row in self.df.iterrows():
            close_price = float(row['Close'])
            high_price = float(row['High'])
            low_price = float(row['Low'])
            
            action = "HOLD"
            
            # --- LÓGICA DE COMPRA (Martingale) ---
            # Se não tem posição, compra a base
            if not self.layers:
                # Compra inicial imediata no primeiro dia
                cost = self.base_bet
                qty = cost / close_price
                self.layers.append({'price': close_price, 'btc_qty': qty, 'cost': cost})
                self.cash -= cost
                self.trade_log.append((date, 'BUY_INIT', close_price, qty))
                last_buy_price = close_price
            else:
                last_buy_price = self.layers[-1]['price']
                
                # Verifica se caiu o suficiente para a próxima camada
                target_buy_price = last_buy_price * (1 - self.drop_step)
                
                # Se a MÍNIMA do dia foi menor que o alvo, executamos a compra
                if low_price <= target_buy_price:
                    # Calcula tamanho da aposta (Multiplicador ^ numero de camadas)
                    next_bet = self.base_bet * (self.multiplier ** len(self.layers))
                    
                    if self.cash >= next_bet:
                        # Executa compra no preço alvo (Limit Order simulada)
                        qty = next_bet / target_buy_price
                        self.layers.append({'price': target_buy_price, 'btc_qty': qty, 'cost': next_bet})
                        self.cash -= next_bet
                        self.trade_log.append((date, f'BUY_LAYER_{len(self.layers)}', target_buy_price, qty))
                        action = "BUY"
                    else:
                        print(f"ALERTA: Sem caixa para camada {len(self.layers)+1} em {date}")

            # --- LÓGICA DE VENDA (LIFO - Last In, First Out) ---
            # Verifica se a ÚLTIMA camada atingiu o alvo de lucro
            if self.layers:
                last_layer = self.layers[-1]
                target_sell_price = last_layer['price'] * (1 + self.take_profit)
                
                # Se a MÁXIMA do dia superou o alvo, vendemos SÓ a última camada
                if high_price >= target_sell_price:
                    revenue = last_layer['btc_qty'] * target_sell_price
                    profit = revenue - last_layer['cost']
                    
                    self.cash += revenue
                    self.layers.pop() # Remove a última camada
                    self.trade_log.append((date, 'SELL_LIFO', target_sell_price, profit))
                    action = "SELL"

            # --- Métrica de Patrimônio ---
            total_btc = sum(l['btc_qty'] for l in self.layers)
            equity = self.cash + (total_btc * close_price)
            
            self.history.append({
                'Date': date,
                'Equity': equity,
                'BTC_Held': total_btc,
                'Cash': self.cash,
                'Close': close_price
            })

    def plot_results(self):
        res_df = pd.DataFrame(self.history).set_index('Date')
        
        # Comparativo Buy & Hold (Se tivesse comprado 30k tudo no dia 1)
        initial_price = self.df.iloc[0]['Close']
        bh_qty = self.initial_capital / initial_price
        res_df['BuyHold'] = res_df['Close'] * bh_qty
        
        # Plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # Gráfico 1: Performance
        ax1.plot(res_df.index, res_df['Equity'], label='Estratégia Martingale', color='green', linewidth=2)
        ax1.plot(res_df.index, res_df['BuyHold'], label='Buy & Hold (100% alocado)', color='gray', linestyle='--', alpha=0.6)
        ax1.set_title(f'Backtest Martingale LIFO ({self.symbol})')
        ax1.set_ylabel('Patrimônio (R$)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Gráfico 2: Exposição e Drawdown
        ax2.plot(res_df.index, res_df['Cash'], label='Caixa Disponível', color='blue')
        ax2.set_ylabel('Caixa (R$)')
        ax2.fill_between(res_df.index, res_df['Cash'], alpha=0.1, color='blue')
        ax2.set_title('Gerenciamento de Caixa (Liquidez)')
        ax2.grid(True, alpha=0.3)
        
        plt.show()
        
        # Estatísticas Finais
        total_return = ((res_df['Equity'].iloc[-1] - self.initial_capital) / self.initial_capital) * 100
        bh_return = ((res_df['BuyHold'].iloc[-1] - self.initial_capital) / self.initial_capital) * 100
        
        print(f"--- RESULTADOS FINAIS ---")
        print(f"Retorno Estratégia: {total_return:.2f}%")
        print(f"Retorno Buy & Hold: {bh_return:.2f}%")
        print(f"Trades Executados: {len(self.trade_log)}")
        print(f"Camadas Atuais em Aberto: {len(self.layers)}")

# --- EXECUÇÃO ---
# Parâmetros ajustados para o cenário do usuário
bt = MartingaleBacktester(symbol='BTC-USD', start_capital=30000, base_bet=500, multiplier=2, drop_step=0.10, take_profit=0.15)
bt.fetch_data(period="2y") # Testando últimos 2 anos (pega 2023/2024 e um pouco de bear market)
bt.run()
bt.plot_results()