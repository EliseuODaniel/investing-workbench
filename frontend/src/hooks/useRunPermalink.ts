import { useCallback, useEffect, useRef } from 'react';
import { buildRunUrl, readRunIdFromUrl, syncRunIdInUrl } from '../lib/runPermalink';

interface UseRunPermalinkOptions {
  isReady: boolean;
  onLoadRun: (runId: string) => Promise<void>;
  onError?: (message: string) => void;
}

export function useRunPermalink({
  isReady,
  onLoadRun,
  onError,
}: UseRunPermalinkOptions) {
  const hasLoadedFromUrl = useRef(false);

  useEffect(() => {
    if (!isReady || hasLoadedFromUrl.current) {
      return;
    }

    hasLoadedFromUrl.current = true;
    const runId = readRunIdFromUrl();
    if (!runId) {
      return;
    }

    onLoadRun(runId).catch((error) => {
      console.error('Failed to hydrate run from URL:', error);
      onError?.('Failed to load run from shared URL');
    });
  }, [isReady, onError, onLoadRun]);

  const updatePermalink = useCallback((runId: string | null) => {
    syncRunIdInUrl(runId);
  }, []);

  const copyRunUrl = useCallback(
    async (runId: string) => {
      const url = buildRunUrl(runId);
      await navigator.clipboard.writeText(url);
      return url;
    },
    []
  );

  const shareRunUrl = useCallback(
    async (runId: string) => {
      const url = buildRunUrl(runId);
      if (navigator.share) {
        await navigator.share({
          title: 'Investing Workbench',
          text: `Confira este run persistido: ${runId}`,
          url,
        });
      } else {
        await navigator.clipboard.writeText(url);
      }
      return url;
    },
    []
  );

  return {
    updatePermalink,
    copyRunUrl,
    shareRunUrl,
  };
}
