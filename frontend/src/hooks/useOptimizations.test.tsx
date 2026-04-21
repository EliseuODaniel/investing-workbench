import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../lib/api';
import { useOptimizations } from './useOptimizations';

describe('useOptimizations', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('clears a transient optimization loading error after a successful refresh', async () => {
    const onError = vi.fn();

    vi.mocked(apiClient.listOptimizations)
      .mockRejectedValueOnce({
        response: {
          data: {
            detail: 'Failed to load persisted optimizations',
          },
        },
      })
      .mockResolvedValueOnce([]);

    const { result } = renderHook(() =>
      useOptimizations('configs/test.yaml', ['Simple Martingale'], onError)
    );

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith('Failed to load persisted optimizations');
    });

    await act(async () => {
      await result.current.refreshOptimizations();
    });

    expect(apiClient.listOptimizations).toHaveBeenCalledTimes(2);
    expect(onError).toHaveBeenLastCalledWith(null);
  });
});
