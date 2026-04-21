import { BarChart3, DollarSign, List, Play, TrendingUp } from 'lucide-react';

export default function InitialWorkspaceState() {
  return (
    <div className="space-y-6">
      <div className="card bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-200 dark:border-blue-800">
        <div className="text-center">
          <div className="mx-auto w-16 h-16 bg-blue-100 dark:bg-blue-800 rounded-full flex items-center justify-center mb-4">
            <BarChart3 className="h-8 w-8 text-blue-600 dark:text-blue-400" />
          </div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-3">
            Pronto para rodar sua primeira simulacao
          </h3>
          <p className="text-gray-600 dark:text-gray-300 mb-6 max-w-2xl mx-auto">
            Comece pelo painel da esquerda. Escolha uma configuracao, confirme o
            periodo e execute. O resultado aparece aqui, com comparacao e trilha de trades.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8 max-w-3xl mx-auto">
            <div className="flex flex-col items-center p-4 bg-white dark:bg-gray-800 rounded-lg border border-blue-200 dark:border-blue-700">
              <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mb-2">
                <span className="text-sm font-bold text-blue-600 dark:text-blue-400">1</span>
              </div>
              <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-1">
                Escolha
              </h4>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Defina a configuracao base do estudo
              </p>
            </div>
            <div className="flex flex-col items-center p-4 bg-white dark:bg-gray-800 rounded-lg border border-blue-200 dark:border-blue-700">
              <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mb-2">
                <span className="text-sm font-bold text-blue-600 dark:text-blue-400">2</span>
              </div>
              <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-1">
                Revise
              </h4>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Ajuste dados, periodo e capital
              </p>
            </div>
            <div className="flex flex-col items-center p-4 bg-white dark:bg-gray-800 rounded-lg border border-blue-200 dark:border-blue-700">
              <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mb-2">
                <span className="text-sm font-bold text-blue-600 dark:text-blue-400">3</span>
              </div>
              <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-1">
                Analise
              </h4>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Veja retorno, benchmark e trades
              </p>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-blue-200 dark:border-blue-700">
            <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Comece sua análise agora
            </h4>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
              Configure seus parâmetros no painel esquerdo e clique em "Executar Backtest"
            </p>
            <div className="flex items-center justify-center space-x-4">
              <div className="flex items-center text-sm text-gray-500">
                <Play className="h-4 w-4 mr-2" />
                Configure no painel lateral
              </div>
              <div className="text-gray-300">→</div>
              <div className="flex items-center text-sm text-gray-500">
                <BarChart3 className="h-4 w-4 mr-2" />
                Leia o resultado aqui
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Recursos Disponíveis
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <TrendingUp className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Multiplas estrategias
              </h4>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Compare diferentes abordagens com o mesmo conjunto de dados
              </p>
            </div>
          </div>
          <div className="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <BarChart3 className="h-5 w-5 text-blue-500 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Benchmarks
              </h4>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Entenda se a estrategia bateu referencias simples
              </p>
            </div>
          </div>
          <div className="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <DollarSign className="h-5 w-5 text-yellow-500 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Rendimento do Caixa
              </h4>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Considere o retorno do capital parado em caixa
              </p>
            </div>
          </div>
          <div className="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <List className="h-5 w-5 text-purple-500 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Analise detalhada
              </h4>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Leia metricas, trades e comparacoes sem sair da tela
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
