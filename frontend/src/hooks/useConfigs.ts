import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import { BacktestRequest, ConfigInfo } from '../types/api';

const DEFAULT_START_DATE = '2020-01-01';
const DEFAULT_INITIAL_CAPITAL = 30000;

function getToday(): string {
  return new Date().toISOString().split('T')[0];
}

export function useConfigs(onError?: (message: string) => void) {
  const [configs, setConfigs] = useState<ConfigInfo[]>([]);
  const [selectedConfig, setSelectedConfig] = useState<ConfigInfo | null>(null);
  const [backtestRequest, setBacktestRequest] = useState<BacktestRequest>({});

  useEffect(() => {
    async function loadConfigs() {
      try {
        const configsData = await apiClient.getConfigs();
        setConfigs(configsData);

        if (configsData.length > 0) {
          const defaultConfig = configsData[0];
          setSelectedConfig(defaultConfig);
          setBacktestRequest({
            config_path: defaultConfig.path,
            start_date: DEFAULT_START_DATE,
            end_date: getToday(),
            initial_capital: DEFAULT_INITIAL_CAPITAL,
          });
        }
      } catch (error) {
        console.error('Failed to load configs:', error);
        onError?.('Failed to load configuration files');
      }
    }

    loadConfigs();
  }, [onError]);

  const handleConfigChange = (config: ConfigInfo) => {
    setSelectedConfig(config);
    setBacktestRequest((currentRequest) => ({
      ...currentRequest,
      config_path: config.path,
      strategies: [],
      start_date: currentRequest.start_date || DEFAULT_START_DATE,
      end_date: currentRequest.end_date || getToday(),
      initial_capital: currentRequest.initial_capital || DEFAULT_INITIAL_CAPITAL,
    }));
  };

  const handleRequestChange = (updates: Partial<BacktestRequest>) => {
    setBacktestRequest((currentRequest) => ({ ...currentRequest, ...updates }));
  };

  return {
    configs,
    selectedConfig,
    backtestRequest,
    handleConfigChange,
    handleRequestChange,
  };
}
