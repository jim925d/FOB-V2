import json
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add the app directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import (
    get_async_engine, get_async_session_factory, 
    Role, Credential, CareerEdge, RoleTargetMapping, RoleEmployer
)
from app.config import get_settings

async def insert_data_from_json(json_path: Path, session: AsyncSession):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if data.get("status") != "approved":
        print(f"Skipping {json_path.name} — status is not 'approved' (is '{data.get('status')}')")
        return
        
    print(f"Processing {json_path.name}...")
    
    origin_info = data["origin"]
    target_info = data["target"]
    gen_data = data["generated_data"]
    
    # 1. Ensure Origin Role exists
    origin = await get_or_create_role(session, origin_info["code"], origin_info["title"], "military")
    
    # 2. Ensure Target Role exists
    target = await get_or_create_role(session, target_info["code"], target_info["title"], "civilian", industry=target_info["industry"], level="mid")
    
    # 3. Create Credentials
    cred_map = {}
    for cred_data in gen_data.get("credentials", []):
        cred = Credential(
            code=cred_data.get("code", cred_data["name"].lower().replace(" ", "-")),
            name=cred_data["name"],
            type=cred_data["type"],
            domain=cred_data.get("domain"),
            provider=cred_data.get("provider"),
            duration_months=cred_data.get("duration_months"),
            cost_dollars=cred_data.get("cost_dollars"),
            cost_note=cred_data.get("cost_note"),
            difficulty=cred_data.get("difficulty"),
            description=cred_data.get("description")
        )
        session.add(cred)
        await session.flush()
        cred_map[cred.code] = cred.id
        
    # 4. Create Generated Roles
    role_map = {origin.code: origin.id, target.code: target.id}
    for role_data in gen_data.get("roles", []):
        r = Role(
            code=role_data["code"],
            title=role_data["title"],
            category="civilian",
            industry=role_data.get("industry", target.industry),
            level=role_data.get("level", "entry"),
            description=role_data.get("description"),
            salary_low=role_data.get("salary_low"),
            salary_high=role_data.get("salary_high"),
            typical_experience_years=role_data.get("typical_experience_years", 0)
        )
        session.add(r)
        await session.flush()
        role_map[r.code] = r.id
        
    # 5. Create Employers
    for emp_data in gen_data.get("employers", []):
        r_id = role_map.get(emp_data.get("role_code"))
        if not r_id:
            continue
        emp = RoleEmployer(
            role_id=r_id,
            employer_name=emp_data["employer_name"],
            is_vet_friendly=emp_data.get("is_vet_friendly", False),
            location=emp_data.get("location"),
            note=emp_data.get("note")
        )
        session.add(emp)
        
    # 6. Create Mapping
    mapping_data = gen_data.get("role_target_mapping", {})
    mapping = RoleTargetMapping(
        origin_role_id=origin.id,
        target_role_id=target.id,
        relevance_score=mapping_data.get("relevance_score", 0.9),
        is_featured=mapping_data.get("is_featured", True)
    )
    session.add(mapping)
    
    # 7. Create Edges
    for edge_data in gen_data.get("edges", []):
        src_code = edge_data["source"]
        tgt_code = edge_data["target"]
        
        src_r_id = role_map.get(src_code)
        src_c_id = cred_map.get(src_code)
        
        tgt_r_id = role_map.get(tgt_code)
        tgt_c_id = cred_map.get(tgt_code)
        
        if (not src_r_id and not src_c_id) or (not tgt_r_id and not tgt_c_id):
            print(f"  Warning: Skipping edge {src_code} -> {tgt_code} due to missing nodes")
            continue
            
        edge = CareerEdge(
            source_role_id=src_r_id,
            source_credential_id=src_c_id,
            target_role_id=tgt_r_id,
            target_credential_id=tgt_c_id,
            weight=edge_data.get("weight", 10),
            typical_months=edge_data.get("typical_months"),
            description=edge_data.get("description"),
            min_education=edge_data.get("min_education"),
            min_experience_years=edge_data.get("min_experience_years", 0),
            requires_clearance=edge_data.get("requires_clearance", False)
        )
        session.add(edge)
        
    await session.commit()
    print(f"✓ Inserted all data from {json_path.name} into database")


from sqlalchemy import select
async def get_or_create_role(session, code, title, category, industry=None, level="origin"):
    res = await session.execute(select(Role).where(Role.code == code))
    r = res.scalar_one_or_none()
    if r:
        return r
    r = Role(code=code, title=title, category=category, industry=industry, level=level)
    session.add(r)
    await session.flush()
    return r

async def main():
    load_dotenv()
    settings = get_settings()
    engine = get_async_engine(settings.database_url)
    session_factory = get_async_session_factory(engine)
    
    seed_dir = Path(os.path.join(os.path.dirname(__file__), "seed_output"))
    if not seed_dir.exists():
        print(f"No seed directory found at {seed_dir}")
        return
        
    json_files = list(seed_dir.glob("*.json"))
    if not json_files:
        print("No JSON files found to import.")
        return
        
    print(f"Found {len(json_files)} JSON files. Connecting to db...")
    
    async with session_factory() as session:
        for json_path in json_files:
            await insert_data_from_json(json_path, session)

if __name__ == "__main__":
    asyncio.run(main())
