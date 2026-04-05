"""
Representative district data for 30 Indian districts across 10 states.

Sources:
  - Population & households: Census of India 2011 (censusindia.gov.in)
  - Vulnerable households (BPL/elderly/disabled): SECC 2011 estimates
  - Induction adoption rates: Estimated from Amazon India / Flipkart sales surge
    reports (2022-2024); metros 12-15%, tier-2 8-10%, others 4-7%
  - Black market indices: Estimated from historical LPG diversion data,
    district-level enforcement capacity, and urban/rural distribution density
  - Military / hospital zones: Based on known cantonment cities and
    district headquarters with major public hospitals

Each entry key meanings:
  daily_demand  = households / 45  (one LPG refill per 45 days on average)
                  before induction-stove adjustment
"""

DISTRICTS_DATA = [
    # ── Uttar Pradesh ──────────────────────────────────────────────────────────
    {
        "district_id": "D001", "name": "Lucknow", "state": "Uttar Pradesh",
        "population": 4589838, "households": 1019964,
        "vulnerable_households": 356987,
        "daily_demand": 22666,
        "black_market_index": 0.28, "induction_adoption_rate": 0.11,
        "military_priority": False, "hospital_zone": True,
    },
    {
        "district_id": "D002", "name": "Varanasi", "state": "Uttar Pradesh",
        "population": 3682194, "households": 818265,
        "vulnerable_households": 286393,
        "daily_demand": 18183,
        "black_market_index": 0.35, "induction_adoption_rate": 0.08,
        "military_priority": False, "hospital_zone": False,
    },
    {
        "district_id": "D003", "name": "Prayagraj", "state": "Uttar Pradesh",
        "population": 5954391, "households": 1323198,
        "vulnerable_households": 463119,
        "daily_demand": 29404,
        "black_market_index": 0.32, "induction_adoption_rate": 0.07,
        "military_priority": False, "hospital_zone": False,
    },
    {
        "district_id": "D004", "name": "Kanpur Nagar", "state": "Uttar Pradesh",
        "population": 4572951, "households": 1016211,
        "vulnerable_households": 355674,
        "daily_demand": 22583,
        "black_market_index": 0.30, "induction_adoption_rate": 0.09,
        "military_priority": True, "hospital_zone": False,
    },
    # ── Bihar ──────────────────────────────────────────────────────────────────
    {
        "district_id": "D005", "name": "Patna", "state": "Bihar",
        "population": 5838465, "households": 1297437,
        "vulnerable_households": 519015,
        "daily_demand": 28809,
        "black_market_index": 0.38, "induction_adoption_rate": 0.06,
        "military_priority": False, "hospital_zone": True,
    },
    {
        "district_id": "D006", "name": "Gaya", "state": "Bihar",
        "population": 4391418, "households": 976093,
        "vulnerable_households": 390437,
        "daily_demand": 21691,
        "black_market_index": 0.42, "induction_adoption_rate": 0.04,
        "military_priority": False, "hospital_zone": False,
    },
    {
        "district_id": "D007", "name": "Bhagalpur", "state": "Bihar",
        "population": 3037766, "households": 675059,
        "vulnerable_households": 270024,
        "daily_demand": 15001,
        "black_market_index": 0.40, "induction_adoption_rate": 0.04,
        "military_priority": False, "hospital_zone": False,
    },
    # ── Maharashtra ────────────────────────────────────────────────────────────
    {
        "district_id": "D008", "name": "Mumbai City", "state": "Maharashtra",
        "population": 3085411, "households": 685647,
        "vulnerable_households": 102847,
        "daily_demand": 15236,
        "black_market_index": 0.15, "induction_adoption_rate": 0.14,
        "military_priority": False, "hospital_zone": True,
    },
    {
        "district_id": "D009", "name": "Mumbai Suburban", "state": "Maharashtra",
        "population": 9356962, "households": 2079325,
        "vulnerable_households": 311899,
        "daily_demand": 46207,
        "black_market_index": 0.18, "induction_adoption_rate": 0.15,
        "military_priority": False, "hospital_zone": False,
    },
    {
        "district_id": "D010", "name": "Pune", "state": "Maharashtra",
        "population": 9429408, "households": 2095424,
        "vulnerable_households": 314314,
        "daily_demand": 46565,
        "black_market_index": 0.16, "induction_adoption_rate": 0.14,
        "military_priority": False, "hospital_zone": True,
    },
    {
        "district_id": "D011", "name": "Nagpur", "state": "Maharashtra",
        "population": 4653570, "households": 1034127,
        "vulnerable_households": 155119,
        "daily_demand": 22980,
        "black_market_index": 0.20, "induction_adoption_rate": 0.10,
        "military_priority": True, "hospital_zone": False,
    },
    {
        "district_id": "D012", "name": "Nashik", "state": "Maharashtra",
        "population": 6107187, "households": 1357153,
        "vulnerable_households": 203573,
        "daily_demand": 30159,
        "black_market_index": 0.22, "induction_adoption_rate": 0.09,
        "military_priority": False, "hospital_zone": False,
    },
    # ── Rajasthan ──────────────────────────────────────────────────────────────
    {
        "district_id": "D013", "name": "Jaipur", "state": "Rajasthan",
        "population": 6626178, "households": 1472484,
        "vulnerable_households": 441745,
        "daily_demand": 32722,
        "black_market_index": 0.28, "induction_adoption_rate": 0.10,
        "military_priority": False, "hospital_zone": True,
    },
    {
        "district_id": "D014", "name": "Jodhpur", "state": "Rajasthan",
        "population": 3687165, "households": 819370,
        "vulnerable_households": 245811,
        "daily_demand": 18208,
        "black_market_index": 0.32, "induction_adoption_rate": 0.07,
        "military_priority": True, "hospital_zone": False,
    },
    {
        "district_id": "D015", "name": "Kota", "state": "Rajasthan",
        "population": 1950491, "households": 433442,
        "vulnerable_households": 130033,
        "daily_demand": 9632,
        "black_market_index": 0.25, "induction_adoption_rate": 0.08,
        "military_priority": False, "hospital_zone": False,
    },
    # ── West Bengal ────────────────────────────────────────────────────────────
    {
        "district_id": "D016", "name": "Kolkata", "state": "West Bengal",
        "population": 4486679, "households": 997040,
        "vulnerable_households": 249260,
        "daily_demand": 22156,
        "black_market_index": 0.22, "induction_adoption_rate": 0.13,
        "military_priority": False, "hospital_zone": True,
    },
    {
        "district_id": "D017", "name": "Howrah", "state": "West Bengal",
        "population": 4850029, "households": 1077784,
        "vulnerable_households": 269446,
        "daily_demand": 23951,
        "black_market_index": 0.30, "induction_adoption_rate": 0.10,
        "military_priority": False, "hospital_zone": False,
    },
    {
        "district_id": "D018", "name": "Murshidabad", "state": "West Bengal",
        "population": 7103807, "households": 1578624,
        "vulnerable_households": 394656,
        "daily_demand": 35081,
        "black_market_index": 0.40, "induction_adoption_rate": 0.05,
        "military_priority": False, "hospital_zone": False,
    },
    # ── Madhya Pradesh ─────────────────────────────────────────────────────────
    {
        "district_id": "D019", "name": "Bhopal", "state": "Madhya Pradesh",
        "population": 2371061, "households": 526902,
        "vulnerable_households": 168609,
        "daily_demand": 11709,
        "black_market_index": 0.25, "induction_adoption_rate": 0.09,
        "military_priority": False, "hospital_zone": True,
    },
    {
        "district_id": "D020", "name": "Indore", "state": "Madhya Pradesh",
        "population": 3276697, "households": 727933,
        "vulnerable_households": 232938,
        "daily_demand": 16176,
        "black_market_index": 0.22, "induction_adoption_rate": 0.10,
        "military_priority": False, "hospital_zone": False,
    },
    {
        "district_id": "D021", "name": "Jabalpur", "state": "Madhya Pradesh",
        "population": 2460714, "households": 546825,
        "vulnerable_households": 174984,
        "daily_demand": 12152,
        "black_market_index": 0.28, "induction_adoption_rate": 0.07,
        "military_priority": True, "hospital_zone": False,
    },
    # ── Tamil Nadu ─────────────────────────────────────────────────────────────
    {
        "district_id": "D022", "name": "Chennai", "state": "Tamil Nadu",
        "population": 7088000, "households": 1575111,
        "vulnerable_households": 315022,
        "daily_demand": 35003,
        "black_market_index": 0.15, "induction_adoption_rate": 0.14,
        "military_priority": False, "hospital_zone": True,
    },
    {
        "district_id": "D023", "name": "Coimbatore", "state": "Tamil Nadu",
        "population": 3458045, "households": 768454,
        "vulnerable_households": 153691,
        "daily_demand": 17077,
        "black_market_index": 0.18, "induction_adoption_rate": 0.11,
        "military_priority": False, "hospital_zone": False,
    },
    {
        "district_id": "D024", "name": "Madurai", "state": "Tamil Nadu",
        "population": 3038252, "households": 675167,
        "vulnerable_households": 135033,
        "daily_demand": 15004,
        "black_market_index": 0.22, "induction_adoption_rate": 0.09,
        "military_priority": False, "hospital_zone": False,
    },
    # ── Karnataka ──────────────────────────────────────────────────────────────
    {
        "district_id": "D025", "name": "Bengaluru Urban", "state": "Karnataka",
        "population": 9621551, "households": 2138122,
        "vulnerable_households": 427624,
        "daily_demand": 47514,
        "black_market_index": 0.12, "induction_adoption_rate": 0.15,
        "military_priority": False, "hospital_zone": True,
    },
    {
        "district_id": "D026", "name": "Mysuru", "state": "Karnataka",
        "population": 3001127, "households": 666917,
        "vulnerable_households": 133383,
        "daily_demand": 14821,
        "black_market_index": 0.18, "induction_adoption_rate": 0.10,
        "military_priority": False, "hospital_zone": False,
    },
    {
        "district_id": "D027", "name": "Dharwad", "state": "Karnataka",
        "population": 1847023, "households": 410450,
        "vulnerable_households": 82090,
        "daily_demand": 9121,
        "black_market_index": 0.22, "induction_adoption_rate": 0.07,
        "military_priority": False, "hospital_zone": False,
    },
    # ── Gujarat ────────────────────────────────────────────────────────────────
    {
        "district_id": "D028", "name": "Ahmedabad", "state": "Gujarat",
        "population": 7208200, "households": 1601822,
        "vulnerable_households": 240273,
        "daily_demand": 35596,
        "black_market_index": 0.15, "induction_adoption_rate": 0.12,
        "military_priority": False, "hospital_zone": True,
    },
    {
        "district_id": "D029", "name": "Surat", "state": "Gujarat",
        "population": 6081322, "households": 1351405,
        "vulnerable_households": 202711,
        "daily_demand": 30031,
        "black_market_index": 0.16, "induction_adoption_rate": 0.13,
        "military_priority": False, "hospital_zone": False,
    },
    # ── Delhi ──────────────────────────────────────────────────────────────────
    {
        "district_id": "D030", "name": "New Delhi", "state": "Delhi",
        "population": 11007835, "households": 2446185,
        "vulnerable_households": 293542,
        "daily_demand": 54360,
        "black_market_index": 0.12, "induction_adoption_rate": 0.14,
        "military_priority": True, "hospital_zone": True,
    },
]
