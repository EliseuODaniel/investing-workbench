import axios from 'axios';
import { useEffect, useRef, useState } from 'react';
import { apiClient } from '../lib/api';
import { SystemStatusPayload } from '../types/api';

const buildStatusErrorMessage = (loadError: unknown): string => {
  if (axios.isAxiosError(loadError)) {
    if (loadError.response) {
      const detail =
        typeof loadError.response.data === 'string'
          ? loadError.response.data
          : loadError.response.data?.detail;
      return detail ? String(detail) : `Erro ${loadError.response.status} em /system/status`;
    }
    return loadError.message || 'Erro de rede ao consultar /system/status';
  }
  return loadError instanceof Error ? 'Status unavailable' : 'Status unavailable';
};

export function useSystemStatus() {
  const [status, setStatus] = useState<SystemStatusPayload | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isStale, setIsStale] = useState(false);
  const consecutiveFailures = useRef(0);
  const hasStatusSnapshot = useRef(false);

  useEffect(() => {
    let isCancelled = false;

    async function loadStatus() {
      try {
        const payload = await apiClient.getSystemStatus();
        if (!isCancelled) {
          setStatus(payload);
          setError(null);
          setIsStale(false);
          hasStatusSnapshot.current = true;
          consecutiveFailures.current = 0;
        }
      } catch (loadError) {
        if (!isCancelled) {
          console.error('Failed to load system status:', loadError);
          consecutiveFailures.current += 1;
          const statusErrorMessage = buildStatusErrorMessage(loadError);
          if (!hasStatusSnapshot.current) {
            setError(statusErrorMessage);
            setIsStale(false);
          } else if (hasStatusSnapshot.current && consecutiveFailures.current >= 2) {
            setIsStale(true);
            setError(null);
          }
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
    isStale,
    error,
  };
}
