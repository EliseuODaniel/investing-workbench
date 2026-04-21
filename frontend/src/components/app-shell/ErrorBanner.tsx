import { AlertCircle } from 'lucide-react';

interface ErrorBannerProps {
  error: string;
  dimmed?: boolean;
}

export default function ErrorBanner({ error, dimmed = false }: ErrorBannerProps) {
  return (
    <div
      className={`card mb-6 border-red-200 bg-red-50 ${
        dimmed ? 'dark:border-red-900 dark:bg-red-950/20' : ''
      }`}
    >
      <div className="flex items-center">
        <AlertCircle className="mr-2 h-5 w-5 text-red-600 dark:text-red-300" />
        <div>
          <h3 className="font-medium text-red-800 dark:text-red-200">Error</h3>
          <p className="mt-1 text-sm text-red-600 dark:text-red-300">{error}</p>
        </div>
      </div>
    </div>
  );
}
