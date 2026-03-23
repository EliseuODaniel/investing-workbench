import React, { useState } from 'react';
import { Download, FileSpreadsheet, Image, FileText, Share, Copy } from 'lucide-react';

interface QuickActionsProps {
  strategies: string[];
  onDownloadCSV: (strategy: string) => void;
  onDownloadPNG: () => void;
  onDownloadHTML: () => void;
  onShareResults: () => void;
  onCopySummary: () => void;
  onCopyLink: () => void;
  onCaptureScreenshot: () => void;
}

const QuickActions: React.FC<QuickActionsProps> = ({
  strategies,
  onDownloadCSV,
  onDownloadPNG,
  onDownloadHTML,
  onShareResults,
  onCopySummary,
  onCopyLink,
  onCaptureScreenshot,
}) => {
  const [downloadMenuOpen, setDownloadMenuOpen] = useState(false);

  const handleDownloadCSV = (strategy: string) => {
    onDownloadCSV(strategy);
    setDownloadMenuOpen(false);
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 flex items-center">
          <Share className="h-4 w-4 mr-2" />
          Ações Rápidas
        </h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Download CSV - Dropdown */}
        <div className="relative">
          <button
            onClick={() => setDownloadMenuOpen(!downloadMenuOpen)}
            className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            <FileSpreadsheet className="h-4 w-4 mr-2" />
            Download CSV
            <svg className="h-4 w-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {downloadMenuOpen && (
            <div className="absolute z-10 mt-2 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
              <div className="p-2">
                <div className="px-3 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700">
                  Escolha a estratégia:
                </div>
                {strategies.map((strategy) => (
                  <button
                    key={strategy}
                    onClick={() => handleDownloadCSV(strategy)}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                  >
                    <FileSpreadsheet className="h-3 w-3 mr-2 inline text-gray-500" />
                    {strategy}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Download Chart */}
        <button
          onClick={onDownloadPNG}
          className="flex items-center justify-center px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors"
        >
          <Image className="h-4 w-4 mr-2" />
          Gráfico
        </button>

        {/* Download Report */}
        <button
          onClick={onDownloadHTML}
          className="flex items-center justify-center px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-lg transition-colors"
        >
          <FileText className="h-4 w-4 mr-2" />
          Relatório
        </button>

        {/* Copy Summary */}
        <button
          onClick={onCopySummary}
          className="flex items-center justify-center px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm font-medium rounded-lg transition-colors"
        >
          <Copy className="h-4 w-4 mr-2" />
          Copiar
        </button>
      </div>

      {/* Info */}
      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <div className="flex items-start">
          <Download className="h-4 w-4 mt-0.5 mr-2 text-blue-500 flex-shrink-0" />
          <div>
            <h4 className="text-xs font-medium text-blue-900 dark:text-blue-100 mb-1">
              Exportação de Dados
            </h4>
            <p className="text-xs text-blue-700 dark:text-blue-300">
              Exporte os resultados em diferentes formatos para análise posterior ou compartilhamento.
              CSV contém todos os trades, PNG gera imagem dos gráficos, e HTML cria um relatório completo.
            </p>
          </div>
        </div>
      </div>

      {/* Share Options */}
      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-2">
        <button
          onClick={onShareResults}
          className="flex items-center justify-center px-3 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs font-medium rounded transition-colors"
        >
          <Share className="h-3 w-3 mr-1" />
          Compartilhar Link
        </button>

        <button
          className="flex items-center justify-center px-3 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs font-medium rounded transition-colors"
        >
          <FileText className="h-3 w-3 mr-1" />
          Salvar Projeto
        </button>

        <button
          onClick={onCaptureScreenshot}
          className="flex items-center justify-center px-3 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs font-medium rounded transition-colors"
        >
          <Image className="h-3 w-3 mr-1" />
          Captura de Tela
        </button>

        <button
          onClick={onCopyLink}
          className="flex items-center justify-center px-3 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs font-medium rounded transition-colors"
        >
          <Copy className="h-3 w-3 mr-1" />
          Copiar URL
        </button>
      </div>
    </div>
  );
};

export default QuickActions;
