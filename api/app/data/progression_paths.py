"""
Curated Career Progression Paths
The FOB Platform

These are the hand-curated, data-backed career progression templates
for the most common veteran career transitions. Each path defines
the complete milestone journey from military role to target career.

This is our core value-add — not just raw API data, but realistic
progression sequences with tactical guidance at every step.

How to curate a bigger list of career paths per MOS:
  - Option 1: Add more MOS codes to existing paths (edit source_mos_codes).
  - Option 2: Add new path objects to CAREER_PROGRESSION_PATHS.
  See app/data/DATA_CURATION.md for structure, examples, and research tips.
"""

CAREER_PROGRESSION_PATHS = [
    
    # =========================================================================
    # PATH 1: INFANTRY / COMBAT ARMS → CYBERSECURITY
    # =========================================================================
    {
        "path_id": "combat_to_cybersec",
        "path_name": "Combat Arms → Cybersecurity Analyst",
        "source_mos_codes": ["11A", "11B", "11C", "11H", "11Z", "13B", "13F", "19D", "19K", "0311", "0313", "0321", "0331", "0341"],
        "source_branches": ["army", "marines"],
        "source_skill_tags": ["leadership", "security", "risk_assessment", "operations", "team_management"],
        "target_industry": "technology",
        "target_career_field": "cybersecurity",
        "target_soc_code": "15-1212.00",
        "total_timeline_months": 36,
        "difficulty_rating": 3,
        "demand_rating": 5,
        "salary_ceiling": 135000,
        "path_description": "Cybersecurity is one of the strongest career paths for combat arms veterans. Your security clearance, threat assessment mindset, and ability to operate under pressure translate directly. The field has a massive talent shortage — over 500,000 unfilled positions in the US — and employers actively seek veterans.",
        "military_advantage_summary": "Security clearance (worth $10-20K salary premium), threat assessment mindset, operations under pressure, team leadership, disciplined approach to procedures and protocols.",
        "common_pitfalls": [
            "Skipping Security+ and going straight for advanced certs — build the foundation first",
            "Targeting only defense contractors — the private sector often pays more",
            "Not leveraging your clearance while it is still active (it expires)",
            "Undervaluing your leadership experience on civilian resumes"
        ],
        "milestones": [
            {
                "milestone_id": "combat_cyber_m0",
                "phase": "origin",
                "sequence": 0,
                "title": "Combat Arms Service Member",
                "description": "Your current military role. Key transferable skills: security operations, threat assessment, team leadership, working under pressure, security clearance.",
                "timeline_start_months": 0,
                "timeline_end_months": 0,
                "duration_months": 0,
                "skills_from_military": [
                    "Security clearance (TS/SCI possible)",
                    "Threat assessment & risk analysis",
                    "Team leadership (fire team to platoon level)",
                    "Operations planning & execution",
                    "Communication under pressure",
                    "Attention to detail in high-stakes environments"
                ],
                "veteran_tip": "Start preparing 12+ months before separation. Your clearance is your biggest asset — use it before it lapses.",
                "military_advantage": "Your combat experience gives you a mindset that cybersecurity employers highly value: you understand real threats, not just theoretical ones."
            },
            {
                "milestone_id": "combat_cyber_m1",
                "phase": "preparation",
                "sequence": 1,
                "title": "Certification & Training Phase",
                "description": "Build your technical foundation. CompTIA Security+ is the gateway certification — it meets DoD 8570 requirements and is recognized across the industry. Pair this with a SkillBridge internship if available.",
                "timeline_start_months": 0,
                "timeline_end_months": 4,
                "duration_months": 4,
                "certifications": [
                    {
                        "name": "CompTIA Security+",
                        "issuing_body": "CompTIA",
                        "estimated_cost": 392.0,
                        "va_covered": True,
                        "estimated_weeks": 8,
                        "url": "https://www.comptia.org/certifications/security",
                        "prerequisite_certs": [],
                        "military_discount": True,
                        "voucher_available": True
                    },
                    {
                        "name": "CompTIA Network+",
                        "issuing_body": "CompTIA",
                        "estimated_cost": 358.0,
                        "va_covered": True,
                        "estimated_weeks": 6,
                        "url": "https://www.comptia.org/certifications/network",
                        "prerequisite_certs": [],
                        "military_discount": True,
                        "voucher_available": True
                    }
                ],
                "skillbridge_programs": [
                    {
                        "program_name": "Amazon AWS re/Start",
                        "company": "Amazon Web Services",
                        "duration_weeks": 12,
                        "url": "https://aws.amazon.com/training/restart/"
                    },
                    {
                        "program_name": "Palo Alto Networks Cybersecurity Academy",
                        "company": "Palo Alto Networks",
                        "duration_weeks": 16
                    },
                    {
                        "program_name": "Microsoft Software & Systems Academy (MSSA)",
                        "company": "Microsoft",
                        "duration_weeks": 17,
                        "url": "https://military.microsoft.com/mssa/"
                    }
                ],
                "education": [
                    {
                        "education_type": "bootcamp",
                        "field_of_study": "Cybersecurity Fundamentals",
                        "estimated_duration_months": 3,
                        "can_use_gi_bill": True,
                        "typical_cost_range": "$0 with VA/SkillBridge"
                    }
                ],
                "skills_required": [
                    {
                        "skill_name": "Networking fundamentals (TCP/IP, DNS, firewalls)",
                        "proficiency_needed": "intermediate",
                        "military_transferable": False,
                        "gap_closing_resource": "CompTIA Network+ study path"
                    },
                    {
                        "skill_name": "Operating system administration (Windows/Linux)",
                        "proficiency_needed": "beginner",
                        "military_transferable": False,
                        "gap_closing_resource": "Linux Academy free tier or TryHackMe"
                    },
                    {
                        "skill_name": "Security concepts & frameworks",
                        "proficiency_needed": "intermediate",
                        "military_transferable": True,
                        "gap_closing_resource": "Security+ covers this comprehensively"
                    }
                ],
                "advancement_criteria": [
                    "Pass CompTIA Security+ exam",
                    "Complete SkillBridge program (if available)",
                    "Build a home lab or complete TryHackMe/HackTheBox challenges",
                    "Update resume with civilian-translated skills"
                ],
                "veteran_tip": "SkillBridge lets you intern the last 6 months of service while getting full military pay. Apply early — slots fill fast. If SkillBridge isn't available, use TA (Tuition Assistance) for certs before separation.",
                "military_advantage": "Your security clearance alone can add $10-20K to starting salary compared to non-cleared candidates."
            },
            {
                "milestone_id": "combat_cyber_m2",
                "phase": "entry_role",
                "sequence": 2,
                "title": "SOC Analyst I / IT Security Specialist",
                "soc_code": "15-1212.00",
                "description": "Your first civilian cybersecurity role. Security Operations Center (SOC) Analyst Tier 1 is the most common entry point. You will monitor security alerts, triage incidents, and escalate threats — very similar to military watch operations.",
                "timeline_start_months": 4,
                "timeline_end_months": 16,
                "duration_months": 12,
                "salary_range_low": 55000,
                "salary_range_high": 78000,
                "salary_median": 65000,
                "employers": [
                    {
                        "company_name": "Booz Allen Hamilton",
                        "vet_status": "veteran_friendly",
                        "careers_url": "https://careers.boozallen.com",
                        "typical_roles": ["SOC Analyst", "Cybersecurity Analyst"],
                        "notes": "30%+ workforce is veterans. Dedicated military hiring program.",
                        "estimated_salary_range": "$60,000-$80,000"
                    },
                    {
                        "company_name": "USAA",
                        "vet_status": "veteran_friendly",
                        "careers_url": "https://www.usaajobs.com",
                        "typical_roles": ["Information Security Analyst", "SOC Analyst"],
                        "notes": "Mission-driven culture similar to military. Strong veteran community.",
                        "estimated_salary_range": "$58,000-$75,000"
                    },
                    {
                        "company_name": "Lockheed Martin",
                        "vet_status": "defense_contractor",
                        "careers_url": "https://www.lockheedmartinjobs.com",
                        "typical_roles": ["Cyber Security Analyst", "Security Operations Specialist"],
                        "notes": "Clearance required — direct advantage for veterans. Military Veteran Network.",
                        "estimated_salary_range": "$65,000-$85,000"
                    },
                    {
                        "company_name": "CrowdStrike",
                        "vet_status": "veteran_friendly",
                        "careers_url": "https://www.crowdstrike.com/careers/",
                        "typical_roles": ["SOC Analyst", "Threat Intelligence Analyst"],
                        "notes": "Fast-growing. Values military background in threat analysis.",
                        "estimated_salary_range": "$60,000-$80,000"
                    },
                    {
                        "company_name": "Leidos",
                        "vet_status": "defense_contractor",
                        "careers_url": "https://careers.leidos.com",
                        "typical_roles": ["Cybersecurity Analyst", "Security Engineer"],
                        "notes": "Major defense/intel contractor. Clearance holders prioritized.",
                        "estimated_salary_range": "$62,000-$82,000"
                    }
                ],
                "skills_required": [
                    {
                        "skill_name": "SIEM tools (Splunk, QRadar, or Sentinel)",
                        "proficiency_needed": "beginner",
                        "military_transferable": False,
                        "gap_closing_resource": "Splunk free training or TryHackMe SOC path"
                    },
                    {
                        "skill_name": "Incident response procedures",
                        "proficiency_needed": "intermediate",
                        "military_transferable": True,
                        "gap_closing_resource": "Military incident response experience directly transfers"
                    },
                    {
                        "skill_name": "Log analysis and threat hunting",
                        "proficiency_needed": "beginner",
                        "military_transferable": False,
                        "gap_closing_resource": "LetsDefend.io or CyberDefenders.org"
                    }
                ],
                "advancement_criteria": [
                    "12+ months of SOC operations experience",
                    "Pursue CySA+ or equivalent intermediate certification",
                    "Demonstrate ability to handle Tier 2 escalations independently",
                    "Build relationships with the incident response and engineering teams"
                ],
                "typical_time_to_advance": "12-18 months",
                "veteran_tip": "Don't get stuck in Tier 1 for too long. Volunteer for incident response and threat hunting projects to build your skills and visibility. Your leadership background means you can move up faster than most.",
                "military_advantage": "Watch operations, shift work discipline, escalation procedures — you already know this drill. Incident triage is just a different kind of threat assessment."
            },
            {
                "milestone_id": "combat_cyber_m3",
                "phase": "growth_role",
                "sequence": 3,
                "title": "Cybersecurity Analyst / Incident Responder",
                "soc_code": "15-1212.00",
                "description": "Mid-level role handling more complex threats, leading incident response, and beginning to specialize. This is where your military leadership experience starts creating real separation from peers.",
                "timeline_start_months": 16,
                "timeline_end_months": 30,
                "duration_months": 14,
                "salary_range_low": 78000,
                "salary_range_high": 105000,
                "salary_median": 90000,
                "certifications": [
                    {
                        "name": "CompTIA CySA+ (Cybersecurity Analyst)",
                        "issuing_body": "CompTIA",
                        "estimated_cost": 392.0,
                        "va_covered": True,
                        "estimated_weeks": 8,
                        "url": "https://www.comptia.org/certifications/cybersecurity-analyst",
                        "prerequisite_certs": ["CompTIA Security+"],
                        "military_discount": True,
                        "voucher_available": False
                    }
                ],
                "skills_required": [
                    {
                        "skill_name": "Advanced threat analysis and malware basics",
                        "proficiency_needed": "intermediate",
                        "military_transferable": False,
                        "gap_closing_resource": "SANS SEC504 or CySA+ study path"
                    },
                    {
                        "skill_name": "Scripting (Python or PowerShell)",
                        "proficiency_needed": "beginner",
                        "military_transferable": False,
                        "gap_closing_resource": "Automate the Boring Stuff with Python (free)"
                    },
                    {
                        "skill_name": "Vulnerability assessment and management",
                        "proficiency_needed": "intermediate",
                        "military_transferable": True,
                        "gap_closing_resource": "Translates from military vulnerability/risk assessment"
                    }
                ],
                "advancement_criteria": [
                    "Lead incident response for multiple significant events",
                    "Develop or improve SOC procedures and playbooks",
                    "Mentor junior analysts (leverage military leadership)",
                    "Begin specializing: threat intelligence, cloud security, or pen testing",
                    "Pursue advanced certification (CISSP, GIAC, or cloud security)"
                ],
                "typical_time_to_advance": "14-20 months",
                "veteran_tip": "This is where you start leading. Volunteer to write SOC playbooks, mentor new analysts, and present findings to management. These are the skills that get you promoted — not just technical ability.",
                "military_advantage": "Your ability to lead under pressure, brief leadership on situations, and create standard operating procedures is exactly what security teams need. Many civilian peers struggle with these soft skills."
            },
            {
                "milestone_id": "combat_cyber_m4",
                "phase": "target_role",
                "sequence": 4,
                "title": "Senior Security Analyst / Security Team Lead",
                "soc_code": "15-1212.00",
                "description": "Your target role. Senior-level cybersecurity position with team leadership responsibilities. You are setting strategy, managing incidents, and potentially leading a small team. This is where military leadership creates the biggest advantage.",
                "timeline_start_months": 30,
                "timeline_end_months": 42,
                "duration_months": 12,
                "salary_range_low": 100000,
                "salary_range_high": 140000,
                "salary_median": 118000,
                "certifications": [
                    {
                        "name": "CISSP (Certified Information Systems Security Professional)",
                        "issuing_body": "ISC2",
                        "estimated_cost": 749.0,
                        "va_covered": True,
                        "estimated_weeks": 12,
                        "url": "https://www.isc2.org/Certifications/CISSP",
                        "prerequisite_certs": [],
                        "military_discount": False,
                        "voucher_available": False
                    }
                ],
                "skills_required": [
                    {
                        "skill_name": "Security architecture and strategy",
                        "proficiency_needed": "advanced",
                        "military_transferable": True,
                        "gap_closing_resource": "CISSP domains cover this; military ops planning transfers"
                    },
                    {
                        "skill_name": "Team management and mentoring",
                        "proficiency_needed": "advanced",
                        "military_transferable": True,
                        "gap_closing_resource": "Direct transfer from military leadership"
                    },
                    {
                        "skill_name": "Risk management frameworks (NIST, ISO 27001)",
                        "proficiency_needed": "advanced",
                        "military_transferable": True,
                        "gap_closing_resource": "CISSP covers frameworks; military risk management directly applies"
                    },
                    {
                        "skill_name": "Executive communication and reporting",
                        "proficiency_needed": "advanced",
                        "military_transferable": True,
                        "gap_closing_resource": "Military briefing experience is directly applicable"
                    }
                ],
                "veteran_tip": "At this level, your military experience is your biggest differentiator. Many technically skilled analysts struggle with leadership, communication, and strategic thinking. You already have these. Lean into them.",
                "military_advantage": "Very few civilian-trained cybersecurity professionals have led teams under real pressure. Your ability to manage incidents calmly, brief executives clearly, and develop team members sets you apart significantly."
            }
        ],
        "alternative_paths": ["combat_to_project_mgmt", "combat_to_law_enforcement", "combat_to_intel_analyst"],
        "related_communities": ["vetsintech", "cybervets_usa", "hack_the_box_veterans"]
    },

    # =========================================================================
    # PATH 2: LOGISTICS / SUPPLY → SUPPLY CHAIN MANAGEMENT
    # =========================================================================
    {
        "path_id": "logistics_to_supply_chain",
        "path_name": "Military Logistics → Supply Chain Manager",
        "source_mos_codes": ["88M", "88N", "92A", "92F", "92Y", "92W", "3043", "3051", "3052", "3112", "LS", "SK", "AK", "PC"],
        "source_branches": ["army", "marines", "navy"],
        "source_skill_tags": ["logistics", "supply_chain", "inventory", "procurement", "distribution"],
        "target_industry": "logistics_supply_chain",
        "target_career_field": "supply_chain_management",
        "target_soc_code": "11-3071.00",
        "total_timeline_months": 30,
        "difficulty_rating": 2,
        "demand_rating": 4,
        "salary_ceiling": 125000,
        "path_description": "Military logistics is one of the most direct translations to civilian careers. You have managed supply chains under the most demanding conditions imaginable — the civilian sector needs exactly this. Supply chain disruptions since 2020 have made this expertise more valuable than ever.",
        "military_advantage_summary": "Direct experience managing complex supply chains, inventory systems, distribution networks, and procurement under austere conditions. Proven ability to solve logistics problems with limited resources.",
        "common_pitfalls": [
            "Not getting certified — CSCP or CPIM credentials are expected at senior levels",
            "Underestimating how much civilian supply chain relies on specific software (SAP, Oracle)",
            "Accepting roles below your capability — military logistics experience is often more advanced than civilian entry-level",
            "Not translating military logistics terminology to civilian equivalents"
        ],
        "milestones": [
            {
                "milestone_id": "logistics_sc_m0",
                "phase": "origin",
                "sequence": 0,
                "title": "Military Logistics Specialist",
                "description": "Your current role managing military supply chains, inventory, procurement, and distribution operations.",
                "timeline_start_months": 0,
                "timeline_end_months": 0,
                "duration_months": 0,
                "skills_from_military": [
                    "Inventory management and accountability",
                    "Supply chain operations (SARSS, GCSS-Army, or equivalent)",
                    "Procurement and contracting basics",
                    "Distribution and transportation coordination",
                    "Warehouse management",
                    "Demand forecasting under uncertainty"
                ],
                "veteran_tip": "Your military logistics experience is more valuable than you think. You have managed supply chains in environments most civilians cannot imagine. Document specific quantities, dollar values, and scope of what you managed.",
                "military_advantage": "You have done this job. The civilian version is the same mission with better tools and fewer constraints."
            },
            {
                "milestone_id": "logistics_sc_m1",
                "phase": "preparation",
                "sequence": 1,
                "title": "Certification & Software Training",
                "description": "Bridge the gap between military systems and civilian supply chain tools. Focus on industry-standard certifications and ERP software proficiency.",
                "timeline_start_months": 0,
                "timeline_end_months": 3,
                "duration_months": 3,
                "certifications": [
                    {
                        "name": "APICS CSCP (Certified Supply Chain Professional)",
                        "issuing_body": "ASCM (Association for Supply Chain Management)",
                        "estimated_cost": 2000.0,
                        "va_covered": True,
                        "estimated_weeks": 10,
                        "url": "https://www.ascm.org/learning/certification/cscp/",
                        "prerequisite_certs": [],
                        "military_discount": True,
                        "voucher_available": False
                    }
                ],
                "skillbridge_programs": [
                    {
                        "program_name": "Amazon Military Apprenticeship",
                        "company": "Amazon",
                        "duration_weeks": 12,
                        "url": "https://www.aboutamazon.com/news/workplace/amazon-military"
                    },
                    {
                        "program_name": "FedEx SkillBridge",
                        "company": "FedEx",
                        "duration_weeks": 12
                    }
                ],
                "skills_required": [
                    {
                        "skill_name": "SAP or Oracle ERP systems",
                        "proficiency_needed": "beginner",
                        "military_transferable": False,
                        "gap_closing_resource": "SAP Learning Hub (free tier) or LinkedIn Learning"
                    },
                    {
                        "skill_name": "Excel advanced (pivot tables, VLOOKUP, data analysis)",
                        "proficiency_needed": "intermediate",
                        "military_transferable": True,
                        "gap_closing_resource": "Excel skills from military reporting transfer well"
                    },
                    {
                        "skill_name": "Six Sigma / Lean basics",
                        "proficiency_needed": "beginner",
                        "military_transferable": True,
                        "gap_closing_resource": "Green Belt certification (often free through VA)"
                    }
                ],
                "advancement_criteria": [
                    "Complete CSCP or CPIM certification",
                    "Gain basic proficiency in one major ERP system",
                    "Translate all military experience into civilian terminology"
                ],
                "veteran_tip": "Many SkillBridge programs with Amazon, FedEx, and UPS are specifically designed for military logistics personnel. These often convert to full-time offers."
            },
            {
                "milestone_id": "logistics_sc_m2",
                "phase": "entry_role",
                "sequence": 2,
                "title": "Supply Chain Coordinator / Logistics Analyst",
                "soc_code": "13-1081.00",
                "description": "First civilian logistics role. Given your military experience, you may enter at a level above true entry-level. Focus on learning civilian tools and processes while leveraging your operational expertise.",
                "timeline_start_months": 3,
                "timeline_end_months": 15,
                "duration_months": 12,
                "salary_range_low": 50000,
                "salary_range_high": 72000,
                "salary_median": 60000,
                "employers": [
                    {
                        "company_name": "Amazon",
                        "vet_status": "veteran_friendly",
                        "careers_url": "https://www.amazon.jobs/en/military",
                        "typical_roles": ["Area Manager", "Operations Manager", "Supply Chain Analyst"],
                        "notes": "Massive veteran hiring. Military Leadership Development Program. Promotes fast.",
                        "estimated_salary_range": "$55,000-$75,000 + signing bonus"
                    },
                    {
                        "company_name": "FedEx",
                        "vet_status": "veteran_friendly",
                        "careers_url": "https://careers.fedex.com",
                        "typical_roles": ["Operations Coordinator", "Logistics Analyst"],
                        "notes": "Strong veteran culture. Military skills directly applicable.",
                        "estimated_salary_range": "$48,000-$65,000"
                    },
                    {
                        "company_name": "XPO Logistics",
                        "vet_status": "veteran_friendly",
                        "careers_url": "https://jobs.xpo.com",
                        "typical_roles": ["Supply Chain Analyst", "Operations Supervisor"],
                        "notes": "Growing company, lots of advancement opportunity.",
                        "estimated_salary_range": "$50,000-$68,000"
                    },
                    {
                        "company_name": "Defense Logistics Agency (DLA)",
                        "vet_status": "veteran_friendly",
                        "careers_url": "https://www.dla.mil/Careers/",
                        "typical_roles": ["Supply Chain Management Specialist", "Inventory Analyst"],
                        "notes": "Federal civilian role. Veterans preference in hiring. Familiar culture.",
                        "estimated_salary_range": "$55,000-$72,000 (GS-9 to GS-11)"
                    }
                ],
                "advancement_criteria": [
                    "Demonstrate proficiency in civilian ERP/WMS systems",
                    "Show measurable impact: cost reduction, efficiency improvement",
                    "Build cross-functional relationships outside your immediate team",
                    "Begin pursuing CPIM or advanced CSCP if not already certified"
                ],
                "typical_time_to_advance": "12-15 months",
                "veteran_tip": "Amazon and FedEx SkillBridge programs frequently convert to full-time operations management roles. If you go the SkillBridge route, your entry role may already be at this level or above.",
                "military_advantage": "You have managed inventory accountability for millions of dollars in equipment. Most civilian entry-level candidates have zero real-world logistics experience."
            },
            {
                "milestone_id": "logistics_sc_m3",
                "phase": "growth_role",
                "sequence": 3,
                "title": "Supply Chain Analyst / Operations Manager",
                "soc_code": "11-3071.00",
                "description": "Mid-level role with broader scope — managing teams, optimizing processes, and driving strategic improvements. Your military operations planning experience shines here.",
                "timeline_start_months": 15,
                "timeline_end_months": 24,
                "duration_months": 9,
                "salary_range_low": 72000,
                "salary_range_high": 95000,
                "salary_median": 82000,
                "certifications": [
                    {
                        "name": "Six Sigma Green Belt",
                        "issuing_body": "ASQ or equivalent",
                        "estimated_cost": 400.0,
                        "va_covered": True,
                        "estimated_weeks": 6,
                        "url": "https://asq.org/cert/six-sigma-green-belt",
                        "prerequisite_certs": [],
                        "military_discount": False,
                        "voucher_available": False
                    }
                ],
                "advancement_criteria": [
                    "Lead a process improvement project with measurable ROI",
                    "Manage a team of 3+ direct reports",
                    "Develop vendor relationships and negotiate contracts",
                    "Demonstrate strategic thinking beyond day-to-day operations"
                ],
                "typical_time_to_advance": "12-18 months",
                "veteran_tip": "This is where you start managing people again. Lean into it — your military leadership gives you a massive advantage over peers who have never led a team under real pressure."
            },
            {
                "milestone_id": "logistics_sc_m4",
                "phase": "target_role",
                "sequence": 4,
                "title": "Senior Supply Chain Manager",
                "soc_code": "11-3071.00",
                "description": "Your target. Senior leadership role overseeing supply chain strategy, multiple teams, and significant budget responsibility. At this level, you are making the decisions that drive operational efficiency across the organization.",
                "timeline_start_months": 24,
                "timeline_end_months": 36,
                "duration_months": 12,
                "salary_range_low": 95000,
                "salary_range_high": 130000,
                "salary_median": 110000,
                "veteran_tip": "At senior level, consider getting your MBA or MS in Supply Chain Management using remaining GI Bill benefits — it opens doors to director-level positions and can be done part-time while working.",
                "military_advantage": "Very few civilian supply chain managers have coordinated logistics across multiple theaters, managed crisis supply situations, or led large teams under high-stakes conditions. Your experience is genuinely rare in the civilian workforce."
            }
        ],
        "alternative_paths": ["logistics_to_project_mgmt", "logistics_to_procurement", "logistics_to_operations_director"],
        "related_communities": ["veterans_in_logistics", "ascm_veterans"]
    },

    # =========================================================================
    # PATH 3: SIGNAL / COMMS → IT / SYSTEMS ADMINISTRATION
    # =========================================================================
    {
        "path_id": "signal_to_it",
        "path_name": "Signal/Communications → IT Systems Administrator",
        "source_mos_codes": ["25A", "25B", "25D", "25F", "25N", "25Q", "25R", "25S", "25U", "0621", "0622", "0627", "0631", "0633", "0671", "IT", "CTN", "CTT", "1D7", "3D0", "3D1"],
        "source_branches": ["army", "marines", "navy", "air_force", "space_force"],
        "source_skill_tags": ["networking", "communications", "systems", "IT", "troubleshooting"],
        "target_industry": "technology",
        "target_career_field": "information_technology",
        "target_soc_code": "15-1244.00",
        "total_timeline_months": 30,
        "difficulty_rating": 1,
        "demand_rating": 4,
        "salary_ceiling": 120000,
        "path_description": "This is one of the most direct military-to-civilian translations. Signal and communications MOSs map almost 1:1 to civilian IT roles. You already have hands-on experience with networking, systems, and troubleshooting that many civilian IT professionals spend years building.",
        "military_advantage_summary": "Direct technical experience with networking, systems administration, and communications infrastructure. Security clearance. Experience maintaining critical systems with zero downtime tolerance.",
        "common_pitfalls": [
            "Settling for a help desk role when you are qualified for systems administration",
            "Not pursuing cloud certifications (AWS/Azure) early — the industry is shifting rapidly",
            "Ignoring the management track — your leadership skills can accelerate you past purely technical peers"
        ],
        "milestones": [
            {
                "milestone_id": "signal_it_m0",
                "phase": "origin",
                "sequence": 0,
                "title": "Signal / Communications Specialist",
                "description": "Your military IT and communications role. You have been doing civilian IT work in a military context.",
                "timeline_start_months": 0,
                "timeline_end_months": 0,
                "duration_months": 0,
                "skills_from_military": [
                    "Network configuration and troubleshooting",
                    "System administration (Windows/Linux)",
                    "Hardware installation and maintenance",
                    "Communications security (COMSEC)",
                    "Help desk and user support",
                    "Security clearance"
                ],
                "veteran_tip": "Document every system, network, and technology you have worked with. Be specific: number of users supported, network size, uptime percentages, incident response times.",
                "military_advantage": "You have maintained networks and systems where downtime was not an option. That mindset is worth more than most certifications."
            },
            {
                "milestone_id": "signal_it_m1",
                "phase": "preparation",
                "sequence": 1,
                "title": "Certification Alignment",
                "description": "You likely need fewer certifications than other paths since your experience is directly relevant. Focus on validating what you already know and adding cloud skills.",
                "timeline_start_months": 0,
                "timeline_end_months": 2,
                "duration_months": 2,
                "certifications": [
                    {
                        "name": "CompTIA A+ (if needed for resume)",
                        "issuing_body": "CompTIA",
                        "estimated_cost": 358.0,
                        "va_covered": True,
                        "estimated_weeks": 4,
                        "military_discount": True,
                        "voucher_available": True
                    },
                    {
                        "name": "AWS Cloud Practitioner",
                        "issuing_body": "Amazon Web Services",
                        "estimated_cost": 100.0,
                        "va_covered": True,
                        "estimated_weeks": 4,
                        "url": "https://aws.amazon.com/certification/certified-cloud-practitioner/",
                        "military_discount": True,
                        "voucher_available": True
                    }
                ],
                "advancement_criteria": [
                    "Validate existing skills with at least one industry certification",
                    "Complete AWS or Azure fundamentals course",
                    "Build civilian-formatted resume emphasizing IT experience"
                ],
                "veteran_tip": "Do not over-prepare. Your hands-on experience is more valuable than many certifications. Get Security+ if you do not have it (you may already from military), then focus on cloud skills."
            },
            {
                "milestone_id": "signal_it_m2",
                "phase": "entry_role",
                "sequence": 2,
                "title": "Systems Administrator / Network Administrator",
                "soc_code": "15-1244.00",
                "description": "Your entry point should be mid-level, not junior. Do not settle for a help desk role unless necessary. You have real systems experience that qualifies you for administration roles.",
                "timeline_start_months": 2,
                "timeline_end_months": 14,
                "duration_months": 12,
                "salary_range_low": 58000,
                "salary_range_high": 82000,
                "salary_median": 68000,
                "employers": [
                    {
                        "company_name": "General Dynamics IT (GDIT)",
                        "vet_status": "defense_contractor",
                        "careers_url": "https://www.gdit.com/careers/",
                        "typical_roles": ["Systems Administrator", "Network Engineer"],
                        "notes": "Defense contractor. Clearance required for many roles — direct advantage.",
                        "estimated_salary_range": "$65,000-$85,000"
                    },
                    {
                        "company_name": "ManTech International",
                        "vet_status": "defense_contractor",
                        "careers_url": "https://www.mantech.com/careers",
                        "typical_roles": ["IT Systems Admin", "Network Administrator"],
                        "notes": "Federal IT. Your military systems experience is directly applicable.",
                        "estimated_salary_range": "$60,000-$80,000"
                    },
                    {
                        "company_name": "Microsoft",
                        "vet_status": "veteran_friendly",
                        "careers_url": "https://careers.microsoft.com",
                        "typical_roles": ["Support Engineer", "Cloud Solutions Architect"],
                        "notes": "MSSA program can lead directly to roles. Strong veteran community.",
                        "estimated_salary_range": "$70,000-$95,000"
                    }
                ],
                "typical_time_to_advance": "12-15 months",
                "veteran_tip": "Target roles that require a security clearance — this is where your premium is. Defense contractors and federal IT shops will pay more and the culture will feel familiar."
            },
            {
                "milestone_id": "signal_it_m3",
                "phase": "growth_role",
                "sequence": 3,
                "title": "Senior Systems Administrator / Cloud Engineer",
                "soc_code": "15-1244.00",
                "description": "Mid-level role with specialization in cloud infrastructure or senior on-prem systems management. This is where you choose: stay technical or start moving toward management.",
                "timeline_start_months": 14,
                "timeline_end_months": 24,
                "duration_months": 10,
                "salary_range_low": 82000,
                "salary_range_high": 110000,
                "salary_median": 95000,
                "certifications": [
                    {
                        "name": "AWS Solutions Architect Associate",
                        "issuing_body": "Amazon Web Services",
                        "estimated_cost": 150.0,
                        "va_covered": True,
                        "estimated_weeks": 8,
                        "prerequisite_certs": ["AWS Cloud Practitioner"],
                        "military_discount": True,
                        "voucher_available": True
                    }
                ],
                "typical_time_to_advance": "10-14 months"
            },
            {
                "milestone_id": "signal_it_m4",
                "phase": "target_role",
                "sequence": 4,
                "title": "IT Manager / Infrastructure Lead",
                "soc_code": "11-3021.00",
                "description": "Target role combining technical expertise with team leadership. Managing IT teams, infrastructure strategy, and vendor relationships. Your military leadership experience is the differentiator.",
                "timeline_start_months": 24,
                "timeline_end_months": 36,
                "duration_months": 12,
                "salary_range_low": 100000,
                "salary_range_high": 130000,
                "salary_median": 112000,
                "veteran_tip": "At this level, your leadership experience matters more than your technical skills. You have managed teams, briefed commanders, and kept critical systems running. That is exactly what IT management requires.",
                "military_advantage": "Military signal leaders have managed larger, more complex, and more critical infrastructure than most civilian IT managers ever will. Your experience leading diverse technical teams under pressure is genuinely rare."
            }
        ],
        "alternative_paths": ["signal_to_cybersec", "signal_to_cloud_architect", "signal_to_devops"],
        "related_communities": ["vetsintech", "aws_veterans"]
    },

    # =========================================================================
    # PATH 4: MEDIC / CORPSMAN → HEALTHCARE
    # =========================================================================
    {
        "path_id": "medic_to_healthcare",
        "path_name": "Combat Medic / Corpsman → Healthcare Professional",
        "source_mos_codes": ["68A", "68B", "68C", "68D", "68E", "68G", "68K", "68M", "68P", "68Q", "68S", "68W", "68X", "8404", "HM", "4N0", "4N1", "4A0"],
        "source_branches": ["army", "navy", "air_force"],
        "source_skill_tags": ["medical", "emergency_care", "patient_care", "triage", "trauma"],
        "target_industry": "healthcare",
        "target_career_field": "nursing_healthcare",
        "target_soc_code": "29-1141.00",
        "total_timeline_months": 48,
        "difficulty_rating": 3,
        "demand_rating": 5,
        "salary_ceiling": 120000,
        "path_description": "Military medics and corpsmen have extensive patient care experience that translates well to civilian healthcare — but the path requires formal education that military training alone does not provide. The investment is worth it: healthcare has massive demand and job security.",
        "military_advantage_summary": "Extensive hands-on patient care under extreme conditions, trauma management, triage experience, ability to remain calm in emergencies, EMT-level certifications from service.",
        "common_pitfalls": [
            "Expecting military medical training to count for civilian licensure — it usually does not directly",
            "Not using GI Bill strategically — nursing programs are expensive, but GI Bill covers most",
            "Ignoring bridge programs designed specifically for military medics",
            "Undervaluing your trauma experience — it is genuinely rare among new civilian nurses"
        ],
        "milestones": [
            {
                "milestone_id": "medic_health_m0",
                "phase": "origin",
                "sequence": 0,
                "title": "Combat Medic / Hospital Corpsman",
                "description": "Your military medical role. You have more hands-on patient care experience than most nursing students — the challenge is getting civilian credentials to match.",
                "timeline_start_months": 0,
                "timeline_end_months": 0,
                "duration_months": 0,
                "skills_from_military": [
                    "Emergency trauma care",
                    "Patient assessment and triage",
                    "Medication administration",
                    "IV therapy and fluid management",
                    "Basic life support / Advanced life support",
                    "Medical documentation",
                    "Calm decision-making under extreme pressure"
                ],
                "veteran_tip": "Get your NREMT (National Registry of EMTs) certification validated before separation if possible. Many states recognize military medic training for EMT-B or EMT-P certification.",
                "military_advantage": "You have treated real patients in real emergencies. Most nursing students do not touch a patient until clinicals. Your experience is invaluable."
            },
            {
                "milestone_id": "medic_health_m1",
                "phase": "preparation",
                "sequence": 1,
                "title": "EMT Certification & Nursing Prerequisites",
                "description": "Validate your EMT certification for civilian use and begin nursing school prerequisites. Many community colleges offer accelerated prerequisite programs for veterans.",
                "timeline_start_months": 0,
                "timeline_end_months": 6,
                "duration_months": 6,
                "certifications": [
                    {
                        "name": "NREMT-B or NREMT-P (if not already held)",
                        "issuing_body": "National Registry of EMTs",
                        "estimated_cost": 110.0,
                        "va_covered": True,
                        "estimated_weeks": 2,
                        "url": "https://www.nremt.org/",
                        "military_discount": False,
                        "voucher_available": False
                    }
                ],
                "education": [
                    {
                        "education_type": "associate",
                        "field_of_study": "Nursing Prerequisites (Anatomy, Physiology, Microbiology)",
                        "estimated_duration_months": 6,
                        "can_use_gi_bill": True,
                        "typical_cost_range": "$0 with GI Bill at community college"
                    }
                ],
                "veteran_tip": "Work as an EMT or ER tech while completing prerequisites — it keeps your skills sharp, provides income, and strengthens your nursing school application.",
                "military_advantage": "Your clinical experience makes you a strong nursing school candidate. Admissions committees value real-world patient care experience."
            },
            {
                "milestone_id": "medic_health_m2",
                "phase": "entry_role",
                "sequence": 2,
                "title": "EMT / ER Technician (while pursuing nursing degree)",
                "soc_code": "29-2042.00",
                "description": "Work as an EMT or ER technician while completing your nursing degree. This provides income, keeps skills current, and builds civilian healthcare experience.",
                "timeline_start_months": 3,
                "timeline_end_months": 24,
                "duration_months": 21,
                "salary_range_low": 35000,
                "salary_range_high": 52000,
                "salary_median": 42000,
                "employers": [
                    {
                        "company_name": "VA Medical Centers",
                        "vet_status": "veteran_friendly",
                        "careers_url": "https://www.vacareers.va.gov/",
                        "typical_roles": ["Emergency Medical Technician", "Health Technician"],
                        "notes": "Veterans preference in hiring. Familiar culture. Tuition support.",
                        "estimated_salary_range": "$38,000-$50,000"
                    },
                    {
                        "company_name": "HCA Healthcare",
                        "vet_status": "veteran_friendly",
                        "careers_url": "https://careers.hcahealthcare.com",
                        "typical_roles": ["ER Tech", "Patient Care Tech"],
                        "notes": "Largest hospital system in US. Military friendly. Tuition reimbursement.",
                        "estimated_salary_range": "$35,000-$48,000"
                    }
                ],
                "education": [
                    {
                        "education_type": "associate",
                        "field_of_study": "Associate Degree in Nursing (ADN)",
                        "estimated_duration_months": 24,
                        "can_use_gi_bill": True,
                        "typical_cost_range": "$0 with GI Bill"
                    }
                ],
                "veteran_tip": "VA medical centers often have partnerships with nursing schools and can offer flexible scheduling for veteran employees pursuing degrees."
            },
            {
                "milestone_id": "medic_health_m3",
                "phase": "growth_role",
                "sequence": 3,
                "title": "Registered Nurse (RN) — Emergency / Critical Care",
                "soc_code": "29-1141.00",
                "description": "Your first RN role. Emergency and critical care nursing is a natural fit for military medics — your trauma experience is directly applicable.",
                "timeline_start_months": 24,
                "timeline_end_months": 36,
                "duration_months": 12,
                "salary_range_low": 62000,
                "salary_range_high": 90000,
                "salary_median": 75000,
                "certifications": [
                    {
                        "name": "NCLEX-RN",
                        "issuing_body": "NCSBN",
                        "estimated_cost": 200.0,
                        "va_covered": True,
                        "estimated_weeks": 4,
                        "url": "https://www.ncsbn.org/nclex.htm",
                        "prerequisite_certs": [],
                        "military_discount": False,
                        "voucher_available": False
                    }
                ],
                "typical_time_to_advance": "12-18 months",
                "veteran_tip": "Consider travel nursing after 1 year of experience — travel RNs can earn $80-120K and the lifestyle may appeal to veterans comfortable with relocation.",
                "military_advantage": "In the ER and ICU, your ability to stay calm under pressure, triage effectively, and make quick decisions sets you apart from nurses who trained only in clinical settings."
            },
            {
                "milestone_id": "medic_health_m4",
                "phase": "target_role",
                "sequence": 4,
                "title": "Senior RN / Charge Nurse / Nurse Practitioner Track",
                "soc_code": "29-1141.00",
                "description": "Senior nursing role with leadership responsibilities, or entry into advanced practice (NP/PA) track using remaining GI Bill benefits.",
                "timeline_start_months": 36,
                "timeline_end_months": 48,
                "duration_months": 12,
                "salary_range_low": 80000,
                "salary_range_high": 125000,
                "salary_median": 95000,
                "veteran_tip": "If you have GI Bill benefits remaining, consider a BSN-to-MSN bridge program for Nurse Practitioner. NPs earn $115-130K and have significant autonomy — similar to being the senior medic.",
                "military_advantage": "Charge nurses need leadership, crisis management, and the ability to direct a team under pressure. Sound familiar? Your military experience is exactly this."
            }
        ],
        "alternative_paths": ["medic_to_pa", "medic_to_healthcare_admin", "medic_to_emt_firefighter"],
        "related_communities": ["nurse_veterans", "va_medical_careers"]
    },

    # =========================================================================
    # PATH 5: INTELLIGENCE → DATA / BUSINESS ANALYTICS
    # =========================================================================
    {
        "path_id": "intel_to_data_analytics",
        "path_name": "Military Intelligence → Data Analyst / Business Intelligence",
        "source_mos_codes": ["35A", "35D", "35F", "35G", "35L", "35M", "35N", "35P", "35Q", "35S", "35T", "35Y", "0231", "0241", "0203", "0210", "0211", "0261", "IS", "CTI", "CTR", "1N0", "1N1", "1N2", "1N3", "1N4", "1N7", "14N"],
        "source_branches": ["army", "marines", "navy", "air_force", "space_force"],
        "source_skill_tags": ["analysis", "intelligence", "data", "pattern_recognition", "briefing", "research"],
        "target_industry": "technology",
        "target_career_field": "data_analytics",
        "target_soc_code": "15-2051.00",
        "total_timeline_months": 24,
        "difficulty_rating": 2,
        "demand_rating": 5,
        "salary_ceiling": 140000,
        "path_description": "Military intelligence analysts are already data analysts — you just need to translate the tools. You analyze large datasets, identify patterns, create briefings for decision-makers, and operate under time pressure. The civilian analytics field needs exactly this skillset, and it pays extremely well.",
        "military_advantage_summary": "Pattern recognition, analytical thinking, briefing complex findings to decision-makers, working with large datasets, security clearance, attention to detail under pressure.",
        "common_pitfalls": [
            "Thinking you need a masters degree — you do not for most data analyst roles",
            "Ignoring SQL and Python — these are table stakes for civilian analytics",
            "Not building a portfolio of civilian-relevant analytics projects",
            "Targeting only intelligence community roles when the private sector pays more"
        ],
        "milestones": [
            {
                "milestone_id": "intel_data_m0",
                "phase": "origin",
                "sequence": 0,
                "title": "Military Intelligence Analyst",
                "description": "Your current intelligence role. You already analyze data, find patterns, and brief leaders. The transition is about tools, not thinking.",
                "timeline_start_months": 0,
                "timeline_end_months": 0,
                "duration_months": 0,
                "skills_from_military": [
                    "Data analysis and pattern recognition",
                    "Intelligence preparation of the battlefield (analytical frameworks)",
                    "Briefing complex findings to senior leaders",
                    "Multi-source data fusion",
                    "Report writing and visualization",
                    "Security clearance (TS/SCI)",
                    "Working under tight deadlines"
                ],
                "veteran_tip": "Your analytical methodology transfers completely. The only gap is civilian tools: SQL, Python, Tableau. These can be learned in 3-4 months.",
                "military_advantage": "Most junior data analysts struggle with presenting findings to executives. You have been briefing commanders your entire career. This soft skill is enormously valuable."
            },
            {
                "milestone_id": "intel_data_m1",
                "phase": "preparation",
                "sequence": 1,
                "title": "Technical Skills Bridge",
                "description": "Learn the civilian data analytics toolkit: SQL for data querying, Python or R for analysis, and Tableau or Power BI for visualization. Your analytical thinking is already there — this is just learning new tools.",
                "timeline_start_months": 0,
                "timeline_end_months": 3,
                "duration_months": 3,
                "certifications": [
                    {
                        "name": "Google Data Analytics Certificate",
                        "issuing_body": "Google / Coursera",
                        "estimated_cost": 0.0,
                        "va_covered": True,
                        "estimated_weeks": 8,
                        "url": "https://grow.google/certificates/data-analytics/",
                        "military_discount": True,
                        "voucher_available": True
                    },
                    {
                        "name": "Tableau Desktop Specialist",
                        "issuing_body": "Salesforce/Tableau",
                        "estimated_cost": 100.0,
                        "va_covered": True,
                        "estimated_weeks": 4,
                        "url": "https://www.tableau.com/learn/certification",
                        "military_discount": True,
                        "voucher_available": False
                    }
                ],
                "skills_required": [
                    {
                        "skill_name": "SQL (querying databases)",
                        "proficiency_needed": "intermediate",
                        "military_transferable": False,
                        "gap_closing_resource": "Mode Analytics SQL tutorial or DataCamp (free for military)"
                    },
                    {
                        "skill_name": "Python for data analysis (pandas, matplotlib)",
                        "proficiency_needed": "beginner",
                        "military_transferable": False,
                        "gap_closing_resource": "DataCamp (free for military) or Kaggle Learn"
                    },
                    {
                        "skill_name": "Data visualization (Tableau or Power BI)",
                        "proficiency_needed": "intermediate",
                        "military_transferable": True,
                        "gap_closing_resource": "Your briefing and visualization skills transfer — learn the tool"
                    }
                ],
                "skillbridge_programs": [
                    {
                        "program_name": "Accenture Federal Services SkillBridge",
                        "company": "Accenture",
                        "duration_weeks": 12
                    },
                    {
                        "program_name": "Deloitte Military Transition Program",
                        "company": "Deloitte",
                        "duration_weeks": 16
                    }
                ],
                "veteran_tip": "DataCamp offers free subscriptions for military and veterans. Use it aggressively for SQL and Python. Build 2-3 portfolio projects using public datasets (Kaggle has great ones)."
            },
            {
                "milestone_id": "intel_data_m2",
                "phase": "entry_role",
                "sequence": 2,
                "title": "Data Analyst / Business Intelligence Analyst",
                "soc_code": "15-2051.00",
                "description": "First civilian analytics role. You should be able to enter at mid-level given your analytical background. Focus on learning domain-specific data (finance, marketing, operations) and building technical credibility.",
                "timeline_start_months": 3,
                "timeline_end_months": 15,
                "duration_months": 12,
                "salary_range_low": 60000,
                "salary_range_high": 85000,
                "salary_median": 72000,
                "employers": [
                    {
                        "company_name": "Deloitte",
                        "vet_status": "veteran_friendly",
                        "careers_url": "https://www2.deloitte.com/us/en/pages/careers/topics/military.html",
                        "typical_roles": ["Data Analyst", "Business Analyst", "Consulting Analyst"],
                        "notes": "CORE Leadership Program for veterans. Values intel background for consulting.",
                        "estimated_salary_range": "$65,000-$85,000"
                    },
                    {
                        "company_name": "Palantir Technologies",
                        "vet_status": "veteran_friendly",
                        "careers_url": "https://www.palantir.com/careers/",
                        "typical_roles": ["Forward Deployed Engineer", "Defense Analyst"],
                        "notes": "Founded to serve national security. Very military-friendly culture.",
                        "estimated_salary_range": "$80,000-$110,000"
                    },
                    {
                        "company_name": "CACI International",
                        "vet_status": "defense_contractor",
                        "careers_url": "https://careers.caci.com",
                        "typical_roles": ["Intelligence Analyst", "Data Analyst"],
                        "notes": "Defense/intel contractor. Clearance required. Familiar mission sets.",
                        "estimated_salary_range": "$65,000-$85,000"
                    },
                    {
                        "company_name": "Capital One",
                        "vet_status": "veteran_friendly",
                        "careers_url": "https://www.capitalonecareers.com/military",
                        "typical_roles": ["Data Analyst", "Business Analyst"],
                        "notes": "Strong data culture. Military transition program. McLean VA area.",
                        "estimated_salary_range": "$70,000-$90,000"
                    }
                ],
                "typical_time_to_advance": "12-15 months",
                "veteran_tip": "Do not limit yourself to defense contractors. Finance, tech, and consulting firms highly value the analytical rigor and clearance you bring. The pay is often significantly better in the private sector."
            },
            {
                "milestone_id": "intel_data_m3",
                "phase": "growth_role",
                "sequence": 3,
                "title": "Senior Data Analyst / Analytics Manager",
                "soc_code": "15-2051.00",
                "description": "Senior role leading analytics projects, mentoring junior analysts, and presenting insights to executives. This is where your intelligence briefing experience becomes your superpower.",
                "timeline_start_months": 15,
                "timeline_end_months": 24,
                "duration_months": 9,
                "salary_range_low": 90000,
                "salary_range_high": 120000,
                "salary_median": 105000,
                "typical_time_to_advance": "12-18 months"
            },
            {
                "milestone_id": "intel_data_m4",
                "phase": "target_role",
                "sequence": 4,
                "title": "Lead Data Analyst / Analytics Director / Data Science Track",
                "soc_code": "15-2051.00",
                "description": "Target role: leading analytics strategy, managing a team, or transitioning into data science. At this level, your combination of analytical depth and leadership experience puts you in a rare category.",
                "timeline_start_months": 24,
                "timeline_end_months": 36,
                "duration_months": 12,
                "salary_range_low": 115000,
                "salary_range_high": 150000,
                "salary_median": 130000,
                "veteran_tip": "If you want to go further into data science, consider a masters in Data Science or Statistics using remaining GI Bill benefits. But honestly, many senior analytics roles do not require it if you have the experience and portfolio.",
                "military_advantage": "Intelligence analysts who can also code, lead teams, and present to executives are extraordinarily rare. You are the unicorn that every analytics organization is looking for."
            }
        ],
        "alternative_paths": ["intel_to_cybersec", "intel_to_consulting", "intel_to_risk_analysis"],
        "related_communities": ["vetsintech", "intelligence_veterans_network"]
    }
]


# =============================================================================
# INDEX: Path lookup helpers
# =============================================================================

# Quick lookup by MOS code
MOS_TO_PATHS = {}
for path in CAREER_PROGRESSION_PATHS:
    for mos in path["source_mos_codes"]:
        if mos not in MOS_TO_PATHS:
            MOS_TO_PATHS[mos] = []
        MOS_TO_PATHS[mos].append(path["path_id"])

# Quick lookup by target industry
INDUSTRY_TO_PATHS = {}
for path in CAREER_PROGRESSION_PATHS:
    industry = path["target_industry"]
    if industry not in INDUSTRY_TO_PATHS:
        INDUSTRY_TO_PATHS[industry] = []
    INDUSTRY_TO_PATHS[industry].append(path["path_id"])

# Quick lookup by path_id
PATH_BY_ID = {path["path_id"]: path for path in CAREER_PROGRESSION_PATHS}


# Summary for quick reference
PATH_SUMMARY = [
    {
        "path_id": p["path_id"],
        "path_name": p["path_name"],
        "source_mos_codes": p["source_mos_codes"],
        "target_industry": p["target_industry"],
        "difficulty_rating": p["difficulty_rating"],
        "demand_rating": p["demand_rating"],
        "total_timeline_months": p["total_timeline_months"],
        "salary_ceiling": p["salary_ceiling"]
    }
    for p in CAREER_PROGRESSION_PATHS
]
