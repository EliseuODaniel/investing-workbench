# Cash Yield SELIC - Frontend Documentation

## Overview

This document describes the cash yield SELIC functionality implemented in the Investing Workbench frontend. This feature allows users to enable SELIC-based interest on uninvested cash during backtesting, providing more realistic returns for Brazilian investors.

For the `SELIC real mensal` mode, the backend derives an effective monthly rate
from the official daily SELIC series before applying it to cash. This prevents
the annualized BCB series from being capitalized as if it were already a
monthly return.

## Implementation Details

### UI Components

#### 1. BacktestForm Component
Located at: `src/components/BacktestForm.tsx`

**New Fields Added:**
- **Checkbox**: "Aplicar rendimento SELIC ao caixa"
- **Numeric Input**: "SELIC anual (%)" (0-50%, step 0.1)
- **Help Text**: "aplicado mensalmente sobre o caixa não investido"

**Validation:**
- SELIC rate: 0-50% range
- Default: 13.0% (converted to 0.13 decimal for API)
- Step: 0.1%

**Conditional Logic:**
- SELIC input only shows when checkbox is checked
- Clear visual feedback with help text

#### 2. MetricsCards Component
Located at: `src/components/MetricsCards.tsx`

**New Metric Display:**
- **Cash Yield Interest**: Only displayed when `total_interest_earned > 0`
- Uses trending up icon with success color
- Shows formatted currency value

#### 3. App Component (Results Display)
Located at: `src/App.tsx`

**Enhanced Results Section:**
- Shows cash yield configuration in backtest parameters
- Displays:
  - SELIC rate used (e.g., "13.00% annually")
  - Frequency: "Monthly compounding"
  - Applied to: "Uninvested cash only"

### API Integration

#### Type Definitions
Located at: `src/types/api.ts`

**Updates Made:**
```typescript
// Added to BacktestRequest interface
apply_cash_yield?: boolean;
selic_rate_annual?: number;

// Added to StrategyMetrics interface
total_interest_earned: number;

// Updated ConfigInfo interface
strategies: string[];
```

#### API Client
Located at: `src/lib/api.ts`

**Configuration:**
- Base URL configurable via VITE_API_BASE environment variable
- 5-minute timeout for long backtests
- Error handling and retry logic

## User Experience

### Usage Flow

1. **Configuration**: Navigate to the backtest form
2. **Enable Cash Yield**: Check "Aplicar rendimento SELIC ao caixa"
3. **Set Rate**: Adjust SELIC rate (default 13.0%)
4. **Run Backtest**: Execute with cash yield enabled
5. **View Results**:
   - See "Cash Yield Interest" in metrics cards
   - Review configuration in results summary

### Visual Examples

#### Form Section:
```
Cash Yield Configuration
┌─────────────────────────────────────────┐
│ ☑ Aplicar rendimento SELIC ao caixa      │
├─────────────────────────────────────────┤
│ SELIC anual (%)                         │
│ 13.0 ▼                                 │
│ (aplicado mensalmente sobre o caixa     │
│  não investido)                         │
│ Taxa SELIC anual padrão: 13.0%         │
└─────────────────────────────────────────┘
```

#### Results Section:
```
Backtest Parameters
├─────────────────────────────────────────┤
│ Cash Yield Enabled                       │
│ SELIC Rate: 13.00% annually             │
│ Frequency: Monthly compounding          │
│ Applied to: Uninvested cash only        │
└─────────────────────────────────────────┘
```

#### Metrics Card:
```
Cash Yield Interest
$35,339.12 ↑
```

## Technical Implementation

### State Management
- Form state managed by parent `App` component
- Cash yield state passed via props
- Real-time form validation

### Data Flow
1. User inputs cash yield parameters
2. Form data sent to `/backtest` API endpoint
3. Backend processes with SELIC cash yield
4. Response includes `total_interest_earned` per strategy
5. Frontend displays interest in metrics cards
6. Configuration shown in results summary

### Error Handling
- API errors displayed in error banner
- Form validation prevents invalid inputs
- Graceful fallback when interest is 0

## Testing

### Manual Testing
1. Enable cash yield checkbox
2. Verify SELIC input appears
3. Test range validation (0-50%)
4. Run backtest with cash yield
5. Confirm interest appears in results
6. Verify configuration display

### API Testing
Test payload:
```json
{
  "apply_cash_yield": true,
  "selic_rate_annual": 0.13,
  "config_path": "configs/martingale.yaml"
}
```

Expected response includes:
```json
{
  "results": {
    "strategy_name": {
      "metrics": {
        "total_interest_earned": 35339.12
      }
    }
  }
}
```

## Build & Deployment

### Build Process
```bash
cd frontend
npm run build  # Uses Vite, not TypeScript compiler
```

**Build Output:**
- `dist/index.html` - Main HTML file
- `dist/assets/` - CSS and JS bundles
- Successfully builds with warnings for large chunks

### Environment Variables
- `VITE_API_BASE`: Backend API URL (default: http://localhost:8001)
- Configure in `.env` file during deployment

## Browser Compatibility

- Modern browsers with ES6+ support
- Requires JavaScript enabled
- Responsive design for mobile and desktop
- Dark mode supported via Tailwind CSS

## Future Enhancements

### Potential Improvements
1. **Enhanced Visualization**: Add cash yield contribution charts
2. **Historical Rates**: Support for historical SELIC rates
3. **Advanced Options**: Support for different compounding frequencies
4. **Export Feature**: Include cash yield data in CSV exports
5. **Comparison Mode**: Compare strategies with/without cash yield

### Performance Considerations
- Large datasets may impact rendering performance
- Consider virtualization for extensive trade histories
- Optimize chart rendering for mobile devices

## Support

For issues or questions regarding the cash yield functionality:
1. Check browser console for errors
2. Verify backend API connectivity
3. Ensure SELIC rate is within valid range (0-50%)
4. Confirm cash yield is enabled in form

---

**Note**: This feature is designed specifically for Brazilian investors using SELIC as a benchmark for cash returns. The implementation maintains backward compatibility - existing functionality remains unchanged when cash yield is disabled.
