import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import { AllocationWorkspacePayload } from '../types/api';

export function useAllocationWorkspaces(onError: (message: string | null) => void) {
  const [workspaces, setWorkspaces] = useState<AllocationWorkspacePayload[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.listAllocationWorkspaces();
      setWorkspaces(response);
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to load allocation workspaces');
    } finally {
      setIsLoading(false);
    }
  }, [onError]);

  const deleteWorkspace = useCallback(
    async (workspaceId: string) => {
      try {
        await apiClient.deleteAllocationWorkspace(workspaceId);
        await refresh();
      } catch (error: any) {
        onError(error.response?.data?.detail || 'Failed to delete allocation workspace');
      }
    },
    [onError, refresh]
  );

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {
    workspaces,
    isLoading,
    refresh,
    deleteWorkspace,
    setWorkspaces,
  };
}
