"""
MOS/AFSC/Rating code → display title for career pathfinder dropdowns.
Built from progression_paths source_mos_codes; extended with common titles.
One-time scrape or manual curation can expand this; API always returns all known MOSs + paths.
"""

# From progression_paths we have these codes; titles from path context or standard lists
# Format: code -> title (short, for "11B — Infantry" style)
MOS_TITLES = {
    # Combat / Infantry (path: combat_to_cybersec)
    "11A": "Infantry Officer",
    "11B": "Infantryman",
    "11C": "Indirect Fire Infantryman",
    "11H": "Infantry Heavy Weapons",
    "11Z": "Infantry Senior Sergeant",
    "13B": "Cannon Crewmember",
    "13F": "Fire Support Specialist",
    "19D": "Cavalry Scout",
    "19K": "Armor Crewman",
    "0311": "Rifleman",
    "0313": "LAV Crewman",
    "0321": "Reconnaissance Man",
    "0331": "Machine Gunner",
    "0341": "Mortarman",
    # Logistics (path: logistics_to_supply_chain)
    "88M": "Motor Transport Operator",
    "88N": "Transportation Management Coordinator",
    "92A": "Automated Logistical Specialist",
    "92F": "Petroleum Supply Specialist",
    "92Y": "Unit Supply Specialist",
    "92W": "Water Treatment Specialist",
    "3043": "Supply Chain Specialist",
    "3051": "Warehouse Clerk",
    "3052": "Export Traffic Specialist",
    "3112": "Traffic Management Specialist",
    "LS": "Logistics Specialist",
    "SK": "Storekeeper",
    "AK": "Aviation Storekeeper",
    "PC": "Postal Clerk",
    # Signal / IT (path: signal_to_it)
    "25A": "Signal Officer",
    "25B": "IT Specialist",
    "25D": "Network Defender",
    "25F": "Network Switching Systems Operator",
    "25N": "Nodal Network Systems Operator",
    "25Q": "Multichannel Transmission Systems Operator",
    "25R": "Visual Information Equipment Operator",
    "25S": "Satellite Communications Operator",
    "25U": "Signal Support Systems Specialist",
    "0621": "Communications Technician",
    "0622": "Satellite Communications Technician",
    "0627": "Tactical Data Systems Specialist",
    "0631": "Network Administrator",
    "0633": "Data Network Specialist",
    "0671": "Data Systems Administrator",
    "IT": "Information Systems Technician",
    "CTN": "Cryptologic Technician - Networks",
    "CTT": "Cryptologic Technician - Technical",
    "1D7": "Cyber Systems Operations",
    "3D0": "Cyberspace Operations",
    "3D1": "Client Systems",
    # Medical (path: medic_to_healthcare)
    "68A": "Biomedical Equipment Specialist",
    "68B": "Orthopedic Specialist",
    "68C": "Practical Nursing Specialist",
    "68D": "Operating Room Specialist",
    "68E": "Dental Specialist",
    "68G": "Patient Administration Specialist",
    "68K": "Medical Laboratory Specialist",
    "68M": "Nutrition Care Specialist",
    "68P": "Radiology Specialist",
    "68Q": "Pharmacy Specialist",
    "68S": "Preventive Medicine Specialist",
    "68W": "Combat Medic",
    "68X": "Behavioral Health Specialist",
    "8404": "Hospital Corpsman",
    "HM": "Hospital Corpsman",
    "4N0": "Aerospace Medical Service",
    "4N1": "Surgical Service",
    "4A0": "Health Services Management",
    # Intelligence (path: intel_to_data_analytics)
    "35A": "Intelligence Officer",
    "35D": "All-Source Intelligence Officer",
    "35F": "Intelligence Analyst",
    "35G": "Geospatial Intelligence Imagery Analyst",
    "35L": "Counterintelligence Agent",
    "35M": "Human Intelligence Collector",
    "35N": "Signals Intelligence Analyst",
    "35P": "Cryptologic Linguist",
    "35Q": "Cryptologic Cyberspace Analyst",
    "35S": "Signals Collector Analyst",
    "35T": "Military Intelligence Systems Maintainer",
    "35Y": "Signals Intelligence Analyst",
    "0231": "Intelligence Specialist",
    "0241": "Imagery Analysis Specialist",
    "0203": "Intelligence Officer",
    "0210": "Human Source Intelligence",
    "0211": "Counterintelligence Specialist",
    "0261": "Geospatial Intelligence Specialist",
    "IS": "Intelligence Specialist",
    "CTI": "Cryptologic Technician - Interpretive",
    "CTR": "Cryptologic Technician - Collection",
    "1N0": "Operations Intelligence",
    "1N1": "Geospatial Intelligence",
    "1N2": "Signals Intelligence Analyst",
    "1N3": "Cryptologic Language Analyst",
    "1N4": "Fusion Analyst",
    "1N7": "Signals Intelligence Analyst",
    "14N": "Intelligence Officer",
}


def get_mos_title(code: str) -> str:
    """Return display title for an MOS/AFSC/Rating code."""
    if not code:
        return ""
    key = str(code).strip().upper()
    return MOS_TITLES.get(key) or f"MOS {key}"
