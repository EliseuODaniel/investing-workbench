"""SELIC data management for real monthly interest rates."""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# SGS code for SELIC rate from Banco Central do Brasil
SELIC_SGS_CODE = 1178


def generate_fake_selic_data() -> pd.DataFrame:
    """Generate fake SELIC data for testing purposes.

    Returns:
        DataFrame with columns: year, month, rate
    """
    data = []

    # Generate data from 2020 to 2024 with realistic variations
    for year in range(2020, 2025):
        for month in range(1, 13):
            # Simulate realistic SELIC monthly rates (around 0.5-1.5% monthly)
            if year < 2021:
                # Lower rates (historic low)
                base_rate = 0.002  # ~0.2% monthly (~2.4% annual)
            elif year < 2023:
                # Medium rates
                base_rate = 0.008  # ~0.8% monthly (~10% annual)
            else:
                # Higher rates (recent)
                base_rate = 0.0108  # ~1.08% monthly (~13.8% annual)

            # Add some monthly variation
            variation = 0.0002 * (month % 3 - 1)  # Small variation
            rate = max(0.0001, base_rate + variation)  # Ensure positive

            data.append({
                'year': year,
                'month': month,
                'rate': rate
            })

    return pd.DataFrame(data)


def download_selic_data(start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
    """Download SELIC data from Banco Central do Brasil.

    Args:
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format

    Returns:
        DataFrame with columns: year, month, rate or None if download fails
    """
    try:
        # Try to import required libraries
        import bcb

        # Create SGS client
        sgs = bcb.sgs.SGS()

        # Download SELIC data
        logger.info(f"Downloading SELIC data (SGS {SELIC_SGS_CODE})...")
        raw_data = sgs.get_serie(SELIC_SGS_CODE, start=start_date, end=end_date)

        # Convert to monthly format
        monthly_data = []
        for date, rate in raw_data.items():
            # Convert annual rate to monthly rate
            monthly_rate = (1 + rate) ** (1/12) - 1

            monthly_data.append({
                'year': date.year,
                'month': date.month,
                'rate': monthly_rate
            })

        df = pd.DataFrame(monthly_data)
        logger.info(f"Downloaded {len(df)} monthly SELIC rates")

        return df

    except ImportError:
        logger.warning("bcb library not available. Install with: pip install bcb")
        return None
    except Exception as e:
        logger.error(f"Failed to download SELIC data: {e}")
        return None


def save_selic_data(df: pd.DataFrame, path: str) -> None:
    """Save SELIC data to CSV file.

    Args:
        df: DataFrame with SELIC data
        path: File path to save
    """
    # Ensure data directory exists
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    # Sort by year and month
    df = df.sort_values(['year', 'month']).reset_index(drop=True)

    # Save to CSV
    df.to_csv(path, index=False)
    logger.info(f"SELIC data saved to {path}")


def load_selic_data(path: str) -> Optional[pd.DataFrame]:
    """Load SELIC data from CSV file.

    Args:
        path: Path to CSV file

    Returns:
        DataFrame with SELIC data or None if file not found
    """
    try:
        if not Path(path).exists():
            logger.warning(f"SELIC file not found: {path}")
            return None

        df = pd.read_csv(path)

        # Validate required columns
        required_columns = ['year', 'month', 'rate']
        if not all(col in df.columns for col in required_columns):
            logger.error(f"SELIC file missing required columns: {required_columns}")
            return None

        # Convert data types
        df['year'] = df['year'].astype(int)
        df['month'] = df['month'].astype(int)
        df['rate'] = pd.to_numeric(df['rate'])

        logger.info(f"Loaded {len(df)} monthly SELIC rates from {path}")

        return df

    except Exception as e:
        logger.error(f"Error loading SELIC data from {path}: {e}")
        return None


def get_monthly_rate(selic_data: pd.DataFrame, year: int, month: int,
                    fallback_rate_annual: float = 0.13) -> float:
    """Get SELIC rate for a specific month/year with fallback.

    Args:
        selic_data: DataFrame with SELIC data
        year: Year
        month: Month (1-12)
        fallback_rate_annual: Annual fallback rate (default: 13%)

    Returns:
        Monthly SELIC rate as decimal
    """
    # Check if data is empty or None
    if selic_data is None or selic_data.empty:
        # Final fallback to configured annual rate converted to monthly
        monthly_fallback = (1 + fallback_rate_annual) ** (1/12) - 1
        logger.warning(f"No SELIC data available, using fallback monthly rate: {monthly_fallback:.6f}")
        return monthly_fallback

    # Try to find exact match
    mask = (selic_data['year'] == year) & (selic_data['month'] == month)
    matching_rows = selic_data[mask]

    if not matching_rows.empty:
        rate = matching_rows.iloc[0]['rate']
        logger.debug(f"Found SELIC rate for {year}-{month:02d}: {rate:.6f}")
        return rate

    # Fallback to last available rate
    last_rate = selic_data.iloc[-1]['rate']
    logger.warning(f"SELIC rate not found for {year}-{month:02d}, using last available: {last_rate:.6f}")
    return last_rate


def get_or_create_selic_data(path: str = "data/selic.csv",
                           use_download: bool = False,
                           start_date: str = None,
                           end_date: str = None,
                           fallback_rate_annual: float = 0.13) -> pd.DataFrame:
    """Get SELIC data, creating it if necessary.

    Args:
        path: Path to SELIC CSV file
        use_download: Whether to attempt downloading real data
        start_date: Start date for download
        end_date: End date for download
        fallback_rate_annual: Annual rate for fallback

    Returns:
        DataFrame with SELIC data
    """
    # Try to load existing data
    selic_data = load_selic_data(path)

    if selic_data is not None:
        return selic_data

    # Try to download real data
    if use_download:
        logger.info("Attempting to download real SELIC data...")
        selic_data = download_selic_data(start_date, end_date)

        if selic_data is not None:
            save_selic_data(selic_data, path)
            return selic_data

    # Generate fake data as last resort
    logger.info("Generating fake SELIC data for testing...")
    selic_data = generate_fake_selic_data()
    save_selic_data(selic_data, path)

    return selic_data


def validate_selic_data(df: pd.DataFrame) -> bool:
    """Validate SELIC data format and content.

    Args:
        df: DataFrame to validate

    Returns:
        True if valid, False otherwise
    """
    if df is None or df.empty:
        logger.error("SELIC data is empty")
        return False

    required_columns = ['year', 'month', 'rate']
    if not all(col in df.columns for col in required_columns):
        logger.error(f"Missing required columns: {required_columns}")
        return False

    # Check for valid date ranges
    if df['year'].min() < 2000 or df['year'].max() > 2100:
        logger.error(f"Invalid year range: {df['year'].min()} - {df['year'].max()}")
        return False

    if df['month'].min() < 1 or df['month'].max() > 12:
        logger.error(f"Invalid month range: {df['month'].min()} - {df['month'].max()}")
        return False

    # Check for valid rate ranges (should be positive and reasonable)
    if df['rate'].min() < 0 or df['rate'].max() > 0.05:  # Max ~5% monthly
        logger.error(f"Invalid rate range: {df['rate'].min():.6f} - {df['rate'].max():.6f}")
        return False

    logger.info("SELIC data validation passed")
    return True