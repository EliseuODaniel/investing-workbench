import { describe, expect, it, vi } from 'vitest';
import { buildRunUrl, readRunIdFromUrl, syncRunIdInUrl } from './runPermalink';

describe('runPermalink', () => {
  it('builds a URL with the run query param', () => {
    const url = buildRunUrl('run_123', new URL('http://localhost:5173/app'));
    expect(url).toBe('http://localhost:5173/app?run=run_123');
  });

  it('reads the run query param', () => {
    const runId = readRunIdFromUrl(new URL('http://localhost:5173/app?run=run_456'));
    expect(runId).toBe('run_456');
  });

  it('syncs the run id in the browser URL', () => {
    const replaceState = vi.spyOn(window.history, 'replaceState').mockImplementation(() => {});

    syncRunIdInUrl('run_789', new URL('http://localhost:5173/app'));

    expect(replaceState).toHaveBeenCalledWith({}, '', '/app?run=run_789');
    replaceState.mockRestore();
  });
});
