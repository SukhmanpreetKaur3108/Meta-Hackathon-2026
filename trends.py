"""
Optional: fetch real induction-stove adoption signals via Google Trends (pytrends).

Reported facts this module contextualises:
  - Amazon India: induction stove sales jumped 30x during LPG supply crisis
  - Flipkart:     4x demand surge in induction stoves
  - Blinkit / Zepto / Swiggy Instamart: sold out in major metros

Usage:
    from lpg_crisis_env.trends import update_adoption_rates
    districts = update_adoption_rates(districts)

pytrends is the unofficial Google Trends API (no API key required).
Falls back gracefully if the network is unavailable or pytrends is not installed.

Install: pip install pytrends
"""
from __future__ import annotations

import logging
from typing import List

logger = logging.getLogger(__name__)

# Baseline adoption rates by state tier used when trends unavailable
_TIER_DEFAULTS = {
    "metro": 0.13,    # Mumbai, Delhi, Bengaluru, Chennai, Kolkata, Hyderabad
    "tier2": 0.09,    # Ahmedabad, Surat, Jaipur, Pune, Nagpur, Indore
    "others": 0.05,
}

_METRO_STATES = {"Delhi", "Maharashtra", "Karnataka", "Tamil Nadu", "West Bengal"}
_TIER2_STATES = {"Gujarat", "Rajasthan", "Madhya Pradesh"}


def _tier_for_state(state: str) -> str:
    if state in _METRO_STATES:
        return "metro"
    if state in _TIER2_STATES:
        return "tier2"
    return "others"


def _fetch_trends_scores() -> dict[str, float] | None:
    """
    Returns a dict mapping Indian state names → normalised adoption boost (0-1),
    or None if pytrends is unavailable / the request fails.
    """
    try:
        from pytrends.request import TrendReq  # type: ignore
    except ImportError:
        logger.warning("pytrends not installed — using static adoption rates.")
        return None

    try:
        pt = TrendReq(hl="en-IN", tz=330, timeout=(10, 25))
        pt.build_payload(
            kw_list=["induction stove", "induction cooktop"],
            geo="IN",
            timeframe="today 12-m",
        )
        df = pt.interest_by_region(resolution="REGION", inc_low_vol=True)
        if df is None or df.empty:
            return None
        # Normalise to [0, 1]
        max_val = df.max().max()
        if max_val == 0:
            return None
        scores: dict[str, float] = {}
        for idx, row in df.iterrows():
            state = str(idx)
            scores[state] = float(row.mean()) / float(max_val)
        return scores
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("pytrends request failed (%s) — using static rates.", exc)
        return None


def update_adoption_rates(districts: list) -> list:
    """
    Update induction_adoption_rate for each DistrictState using Google Trends data.
    The trend score scales the baseline by up to 2x (trend_score blended at 50%).

    Args:
        districts: list of DistrictState objects (or raw dicts with 'state' key)

    Returns:
        The same list with updated induction_adoption_rate values.
    """
    trends = _fetch_trends_scores()

    for d in districts:
        # Works for both DistrictState objects and plain dicts
        state_name = d.state if hasattr(d, "state") else d["state"]
        tier = _tier_for_state(state_name)
        baseline = _TIER_DEFAULTS[tier]

        if trends is not None:
            # Partial match: Google Trends uses full state names
            matched = next(
                (v for k, v in trends.items() if state_name.lower() in k.lower()),
                None,
            )
            if matched is not None:
                # Blend: 50% baseline + 50% trend-boosted
                boosted = min(0.30, baseline * (1 + matched))
                new_rate = 0.50 * baseline + 0.50 * boosted
            else:
                new_rate = baseline
        else:
            new_rate = baseline

        if hasattr(d, "induction_adoption_rate"):
            d.induction_adoption_rate = round(new_rate, 4)
        else:
            d["induction_adoption_rate"] = round(new_rate, 4)

    return districts
