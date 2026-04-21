import { useState } from 'react';
import { ResearchWorkspacePayload } from '../types/api';

export type PrimarySection = 'home' | 'investments' | 'simulate' | 'results' | 'advanced';
export type SimulateTab = 'configure' | 'datasets';
export type ResultsTab = 'history' | 'compare' | 'workspaces';
export type AdvancedTool =
  | 'allocation'
  | 'optimization'
  | 'research'
  | 'walkforward'
  | 'montecarlo'
  | 'pairs'
  | 'wege3'
  | 'drilldown';

interface UseAppShellStateOptions {
  runsCount: number;
  selectedRunCount: number;
  workspaceCount: number;
}

export function useAppShellState({
  runsCount,
  selectedRunCount,
  workspaceCount,
}: UseAppShellStateOptions) {
  const [workspaceToOpen, setWorkspaceToOpen] = useState<ResearchWorkspacePayload | null>(null);
  const [primarySection, setPrimarySection] = useState<PrimarySection>('home');
  const [simulateTab, setSimulateTab] = useState<SimulateTab>('configure');
  const [resultsTab, setResultsTab] = useState<ResultsTab>('history');
  const [advancedTool, setAdvancedTool] = useState<AdvancedTool>('pairs');

  const primaryTabs = [
    { id: 'home' as const, label: 'Inicio' },
    { id: 'investments' as const, label: 'Investimentos' },
    { id: 'simulate' as const, label: 'Simular' },
    { id: 'results' as const, label: 'Resultados', badge: runsCount },
    { id: 'advanced' as const, label: 'Avancado' },
  ];

  const simulateTabs = [
    { id: 'configure' as const, label: 'Backtest guiado' },
    { id: 'datasets' as const, label: 'Bases de dados' },
  ];

  const resultsTabs = [
    { id: 'history' as const, label: 'Recentes', badge: runsCount },
    { id: 'compare' as const, label: 'Comparar', badge: selectedRunCount },
    { id: 'workspaces' as const, label: 'Estudos salvos', badge: workspaceCount },
  ];

  const advancedTools = [
    { id: 'allocation' as const, label: 'Planejamento de carteira' },
    { id: 'optimization' as const, label: 'Optimization' },
    { id: 'research' as const, label: 'Pesquisa guiada' },
    { id: 'walkforward' as const, label: 'Walk-Forward' },
    { id: 'montecarlo' as const, label: 'Monte Carlo' },
    { id: 'pairs' as const, label: 'Pairs B3' },
    { id: 'wege3' as const, label: 'WEGE3 Regra A' },
    { id: 'drilldown' as const, label: 'Drilldown' },
  ];

  function openWorkspaceInResearch(workspacePayload: ResearchWorkspacePayload) {
    setWorkspaceToOpen(workspacePayload);
    setPrimarySection('advanced');
    setAdvancedTool('research');
  }

  function clearWorkspaceToOpen() {
    setWorkspaceToOpen(null);
  }

  return {
    workspaceToOpen,
    primarySection,
    simulateTab,
    resultsTab,
    advancedTool,
    primaryTabs,
    simulateTabs,
    resultsTabs,
    advancedTools,
    setPrimarySection,
    setSimulateTab,
    setResultsTab,
    setAdvancedTool,
    openWorkspaceInResearch,
    clearWorkspaceToOpen,
  };
}
