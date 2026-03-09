"""
Batch Career Graph Seeder

Uses Claude API to generate career path data for every MOS × target combination.
Output: JSON files for human review before database insertion.

Usage:
    python -m scripts.seed_career_graph --mos 25B --target cybersecurity-analyst
    python -m scripts.seed_career_graph --all    # generates for all MOS codes
"""

import json
import os
import anthropic
from pathlib import Path


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OUTPUT_DIR = Path(os.path.join(os.path.dirname(__file__), "seed_output"))


SYSTEM_PROMPT = """You are a career transition advisor for military veterans.
Generate career path data as structured JSON for database insertion.

For the given MOS (military role) and target civilian role, produce:

1. Required credentials (certifications, degrees, bootcamps, SkillBridge programs)
   - Include BOTH certification paths AND degree paths
   - Each credential needs: name, type, domain, provider, duration_months, cost_dollars (use integer without $), cost_note, difficulty, description
   - valid types: certification, degree_associate, degree_bachelors, degree_masters, degree_doctorate, bootcamp, skillbridge, trade_certificate
   
2. Intermediate roles (entry-level civilian jobs that lead to the target)
   - Each role needs: title, code (slug), level (entry/mid), industry, salary_low (integer), salary_high (integer), typical_experience_years, description
   
3. Stretch roles (1-2 roles beyond the target for growth)
   - Same fields as intermediate roles but level=senior or level=executive

4. Career edges connecting everything:
   - origin → credentials (which certs/degrees to pursue first)
   - credentials → more credentials (cert ladders, e.g., Security+ → CySA+)
   - credentials → entry roles (what each cert qualifies you for)
   - entry roles → target role (progression path)
   - target role → stretch roles (career growth)
   - degree → roles (direct qualification paths)
   
   Each edge needs: source (code of role or cred), target (code of role or cred), weight (10-30, higher = more common path), typical_months, description
   
5. Edge conditions:
   - Which edges require minimum education (e.g., degree path only if user has < bachelors)
   - Which edges require clearance

6. Employers for each role (4-5 companies, mark veteran-friendly ones)
   - Format: { role_code, employer_name, is_vet_friendly, location, note }

CRITICAL RULES:
- All salary data must be realistic 2025-2026 ranges from BLS/Glassdoor
- All certifications must be REAL certifications that actually exist
- All SkillBridge programs must be REAL DoD SkillBridge programs
- Cost data must be accurate (exam fees, tuition)
- Duration must be realistic study/program time
- The user's selected target role MUST be in the output, not replaced by a similar role

Respond with ONLY valid JSON, no markdown, no commentary."""


USER_PROMPT_TEMPLATE = """Generate career path data for:

Origin MOS: {mos_code} — {mos_title}
Target Role: {target_title} ({target_industry})
Veteran's typical profile: {experience_years} years experience, {education_level} education, may have security clearance

Output the JSON with these top-level keys:
- credentials: array of credential objects
- roles: array of role objects (entry + stretch, NOT the origin or target — those already exist)
- edges: array of edge objects
- employers: array of employer objects
- role_target_mapping: {{ relevance_score (0-1), is_featured (bool) }}
"""


def generate_path_data(mos_code, mos_title, target_code, target_title, target_industry):
    """Call Claude to generate career path data for one MOS → target combination."""
    
    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        return None
        
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    print(f"Generating data for {mos_code} -> {target_code}...")
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(
                mos_code=mos_code,
                mos_title=mos_title,
                target_title=target_title,
                target_industry=target_industry,
                experience_years="4-6",
                education_level="some college",
            )
        }]
    )
    
    # Parse response
    text = response.content[0].text.strip()
    # Remove markdown fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
        print("Raw response:")
        print(text)
        return None
    
    # Save for review
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{mos_code}_to_{target_code}.json"
    with open(output_file, "w") as f:
        json.dump({
            "origin": {"code": mos_code, "title": mos_title},
            "target": {"code": target_code, "title": target_title, "industry": target_industry},
            "generated_data": data,
            "status": "pending_review",
        }, f, indent=2)
    
    print(f"✓ Generated {mos_code} → {target_code} → {output_file}")
    return data


if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv
    
    # Try to load from the api/.env explicitly
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    
    # Make sure we re-check api key after load_dotenv
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--mos", required=True)
    parser.add_argument("--mos-title", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--target-title", required=True)
    parser.add_argument("--industry", default="technology")
    args = parser.parse_args()
    
    generate_path_data(args.mos, args.mos_title, args.target, args.target_title, args.industry)
