import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import { SystemStatusPayload } from '../types/api';

export function useSystemStatus() {
  const [status, setStatus] = useState<SystemStatusPayload | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isCancelled = false;

    async function loadStatus() {
      try {
        const payload = await apiClient.getSystemStatus();
        if (!isCancelled) {
          setStatus(payload);
          setError(null);
        }
      } catch (loadError) {
        if (!isCancelled) {
          console.error('Failed to load system status:', loadError);
          setStatus(null);
          setError('Status unavailable');
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    loadStatus();
    const intervalId = window.setInterval(loadStatus, 15000);

    return () => {
      isCancelled = true;
      window.clearInterval(intervalId);
    };
  }, []);

  return {
    status,
    isLoading,
    error,
  };
}
