export function buildRunUrl(runId: string, currentUrl?: URL): string {
  const url = currentUrl ? new URL(currentUrl.toString()) : new URL(window.location.href);
  url.searchParams.set('run', runId);
  return url.toString();
}

export function readRunIdFromUrl(currentUrl?: URL): string | null {
  const url = currentUrl ? new URL(currentUrl.toString()) : new URL(window.location.href);
  return url.searchParams.get('run');
}

export function syncRunIdInUrl(runId: string | null, currentUrl?: URL): void {
  const url = currentUrl ? new URL(currentUrl.toString()) : new URL(window.location.href);

  if (runId) {
    url.searchParams.set('run', runId);
  } else {
    url.searchParams.delete('run');
  }

  window.history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`);
}
