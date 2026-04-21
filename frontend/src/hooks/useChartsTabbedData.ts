import { useMemo } from 'react';
import { BenchmarkResult, StrategyResult } from '../types/api';
import {
  DrawdownChartPoint,
  EquityChartPoint,
  TradeScatterPoint,
} from '../components/charts-tabbed/types';

interface UseChartsTabbedDataOptions {
  results: Record<string, StrategyResult>;
  buyHoldEquity: StrategyResult['equity'];
  benchmarks?: Record<string, BenchmarkResult>;
  visibleStrategies: string[];
  visibleBenchmarks: string[];
}

export function useChartsTabbedData({
  results,
  buyHoldEquity,
  benchmarks,
  visibleStrategies,
  visibleBenchmarks,
}: UseChartsTabbedDataOptions) {
  const equityData = useMemo<EquityChartPoint[]>(() => {
    const allTimestamps = new Set<string>();

    Object.values(results).forEach((result) => {
      if (visibleStrategies.includes(result.strategy_name)) {
        result.equity.forEach((point) => {
          allTimestamps.add(point.timestamp);
        });
      }
    });

    if (visibleBenchmarks.includes('Buy & Hold')) {
      buyHoldEquity.forEach((point) => {
        allTimestamps.add(point.timestamp);
      });
    }

    if (benchmarks) {
      Object.entries(benchmarks).forEach(([name, benchmark]) => {
        if (visibleBenchmarks.includes(name)) {
          benchmark.equity.forEach((point) => {
            allTimestamps.add(point.timestamp);
          });
        }
      });
    }

    return Array.from(allTimestamps)
      .sort()
      .map((timestamp) => {
        const dataPoint: EquityChartPoint = {
          timestamp,
          date: new Date(timestamp).toLocaleDateString('pt-BR'),
        };

        Object.values(results).forEach((result) => {
          if (visibleStrategies.includes(result.strategy_name)) {
            const point = result.equity.find((item) => item.timestamp === timestamp);
            dataPoint[result.strategy_name] = point?.equity ?? null;
            dataPoint[`${result.strategy_name}_cash`] = point?.cash ?? null;
          }
        });

        if (visibleBenchmarks.includes('Buy & Hold')) {
          const point = buyHoldEquity.find((item) => item.timestamp === timestamp);
          dataPoint['Buy & Hold'] = point?.equity ?? null;
        }

        if (benchmarks) {
          Object.entries(benchmarks).forEach(([name, benchmark]) => {
            if (visibleBenchmarks.includes(name)) {
              const point = benchmark.equity.find((item) => item.timestamp === timestamp);
              dataPoint[name] = point?.equity ?? null;
            }
          });
        }

        return dataPoint;
      });
  }, [results, buyHoldEquity, benchmarks, visibleStrategies, visibleBenchmarks]);

  const drawdownData = useMemo<DrawdownChartPoint[]>(() => {
    return equityData.map((point, index) => {
      const dataPoint: DrawdownChartPoint = {
        timestamp: point.timestamp,
        date: point.date,
      };

      Object.keys(results).forEach((strategyName) => {
        if (!visibleStrategies.includes(strategyName)) {
          return;
        }

        const currentValue = point[strategyName];
        if (index === 0 || typeof currentValue !== 'number') {
          dataPoint[`${strategyName}_drawdown`] = 0;
          return;
        }

        const valuesUpToNow = equityData
          .slice(0, index + 1)
          .map((entry) => entry[strategyName])
          .filter((value): value is number => typeof value === 'number');

        if (valuesUpToNow.length === 0) {
          dataPoint[`${strategyName}_drawdown`] = 0;
          return;
        }

        const peak = Math.max(...valuesUpToNow);
        dataPoint[`${strategyName}_drawdown`] = ((currentValue - peak) / peak) * 100;
      });

      return dataPoint;
    });
  }, [equityData, results, visibleStrategies]);

  const tradesData = useMemo<TradeScatterPoint[]>(() => {
    const allTrades: TradeScatterPoint[] = [];

    Object.entries(results).forEach(([strategyName, result]) => {
      if (!visibleStrategies.includes(strategyName)) {
        return;
      }

      result.trades.forEach((trade) => {
        const equityPoint = result.equity.find((point) => point.timestamp === trade.timestamp);

        allTrades.push({
          timestamp: new Date(trade.timestamp),
          price: trade.price,
          action: trade.action,
          strategy: strategyName,
          pnl: trade.pnl ?? 0,
          layer: trade.layer ?? 0,
          equity: equityPoint?.equity ?? 0,
          color: trade.action === 'BUY' ? '#10b981' : '#ef4444',
        });
      });
    });

    return allTrades.sort((left, right) => left.timestamp.getTime() - right.timestamp.getTime());
  }, [results, visibleStrategies]);

  return {
    equityData,
    drawdownData,
    tradesData,
  };
}
