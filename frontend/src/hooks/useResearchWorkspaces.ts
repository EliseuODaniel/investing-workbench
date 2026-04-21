import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import { ResearchWorkspacePayload } from '../types/api';

export function useResearchWorkspaces(
  onError: (message: string | null) => void,
  refreshToken: number = 0
) {
  const [workspaces, setWorkspaces] = useState<ResearchWorkspacePayload[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.listResearchWorkspaces();
      setWorkspaces(response);
      onError(null);
    } catch (error: any) {
      onError(error.response?.data?.detail || 'Failed to load research workspaces');
    } finally {
      setIsLoading(false);
    }
  }, [onError]);

  useEffect(() => {
    refresh();
  }, [refresh, refreshToken]);

  return {
    workspaces,
    isLoading,
    refresh,
  };
}
