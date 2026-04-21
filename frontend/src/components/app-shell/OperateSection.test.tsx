import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import OperateSection from './OperateSection';

vi.mock('../BacktestForm', () => ({
  default: () => <div>backtest-form</div>,
}));

vi.mock('../DatasetManagerPanel', () => ({
  default: () => <div>dataset-manager</div>,
}));

vi.mock('../BacktestJobsPanel', () => ({
  default: () => <div>jobs-panel</div>,
}));

vi.mock('../BacktestResultsWorkspace', () => ({
  default: () => <div>results-workspace</div>,
}));

vi.mock('../InitialWorkspaceState', () => ({
  default: () => <div>initial-workspace</div>,
}));

vi.mock('../LoadingSpinner', () => ({
  default: ({ message }: { message: string }) => <div>{message}</div>,
}));

vi.mock('./SectionTabs', () => ({
  default: () => <div>section-tabs</div>,
}));

vi.mock('./ErrorBanner', () => ({
  default: ({ error }: { error: string }) => <div>{error}</div>,
}));

const baseProps = {
  simulateTabs: [{ id: 'configure', label: 'Configurar' }],
  simulateTab: 'configure',
  onSimulateTabChange: vi.fn(),
  backtestFormProps: {} as any,
  datasetManagerProps: {} as any,
  jobsPanelProps: {
    jobs: [],
    activeJob: null,
    isLoadingJobs: false,
    isCancellingJob: false,
    onOpenJob: vi.fn(),
    onResumeJob: vi.fn(),
    onCancelActiveJob: vi.fn(),
    onRefreshJobs: vi.fn(),
  },
  resultsWorkspaceProps: null,
  isBacktestBusy: false,
  loadingMessage: 'loading',
  workspaceState: 'idle' as const,
  error: null,
};

describe('OperateSection', () => {
  it('hides the jobs panel when only completed jobs exist', () => {
    render(
      <OperateSection
        {...baseProps}
        jobsPanelProps={{
          ...baseProps.jobsPanelProps,
          jobs: [
            {
              job_id: 'job_1',
              status: 'completed',
            },
          ] as any,
        }}
      />
    );

    expect(screen.queryByText('jobs-panel')).toBeNull();
  });

  it('shows the jobs panel when there is a failed job that needs attention', () => {
    render(
      <OperateSection
        {...baseProps}
        jobsPanelProps={{
          ...baseProps.jobsPanelProps,
          jobs: [
            {
              job_id: 'job_2',
              status: 'failed',
            },
          ] as any,
        }}
      />
    );

    expect(screen.getByText('jobs-panel')).toBeTruthy();
  });
});
