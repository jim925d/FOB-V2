-- ════════════════════════════════════════════════════════════
-- CAREER GRAPH SCHEMA
-- Replaces AI-per-request generation with queryable graph
-- ════════════════════════════════════════════════════════════

-- ── Roles (military + civilian at all levels) ──
CREATE TABLE roles (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(20) UNIQUE,          -- MOS code (11B, 25B) or slug (cybersecurity-analyst)
    title           VARCHAR(255) NOT NULL,
    category        VARCHAR(50) NOT NULL,        -- 'military' or 'civilian'
    branch          VARCHAR(50),                 -- army, navy, marines, air_force, space_force, coast_guard, NULL for civilian
    industry        VARCHAR(100),                -- technology, healthcare, finance, government, trades, etc.
    level           VARCHAR(30) NOT NULL,        -- origin, entry, mid, senior, executive
    description     TEXT,
    salary_low      INTEGER,                     -- annual, in dollars
    salary_high     INTEGER,
    typical_experience_years  INTEGER DEFAULT 0,  -- years typically needed to reach this role
    clearance_helpful BOOLEAN DEFAULT false,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_roles_category ON roles(category);
CREATE INDEX idx_roles_branch ON roles(branch);
CREATE INDEX idx_roles_industry ON roles(industry);
CREATE INDEX idx_roles_level ON roles(level);

-- ── Credentials (certs, degrees, bootcamps, SkillBridge programs) ──
CREATE TABLE credentials (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(50) UNIQUE,          -- sec-plus, bs-cybersecurity, sb-amazon-restart
    name            VARCHAR(255) NOT NULL,
    type            VARCHAR(30) NOT NULL,        -- certification, degree_associate, degree_bachelors,
                                                 -- degree_masters, degree_doctorate, bootcamp,
                                                 -- skillbridge, trade_certificate
    domain          VARCHAR(100),                -- IT/Cyber, Project Management, Healthcare, Trades, etc.
    provider        VARCHAR(255),                -- CompTIA, WGU, Amazon, Microsoft, IBEW, etc.
    duration_months DECIMAL(4,1),                -- 2.0 for a cert, 24.0 for a BS, 6.0 for SkillBridge
    cost_dollars    INTEGER,                     -- exam/tuition cost
    cost_note       VARCHAR(255),                -- "GI Bill Ch. 33 covers", "Free (military)", "VET TEC eligible"
    difficulty      VARCHAR(20),                 -- entry, moderate, intermediate, advanced, expert
    description     TEXT,
    url             VARCHAR(500),                -- link to program/cert page
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_credentials_type ON credentials(type);
CREATE INDEX idx_credentials_domain ON credentials(domain);

-- ── Role Transferable Skills (what a military role teaches) ──
CREATE TABLE role_skills (
    id              SERIAL PRIMARY KEY,
    role_id         INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    skill_name      VARCHAR(255) NOT NULL,       -- "Network Administration", "Team Leadership", etc.
    skill_category  VARCHAR(100),                -- technical, leadership, operations, analytical
    relevance       VARCHAR(20) DEFAULT 'high',  -- high, medium, low
    UNIQUE(role_id, skill_name)
);

-- ── Credential Prerequisites (what you need before earning a credential) ──
CREATE TABLE credential_prereqs (
    id                  SERIAL PRIMARY KEY,
    credential_id       INTEGER REFERENCES credentials(id) ON DELETE CASCADE,
    prereq_credential_id INTEGER REFERENCES credentials(id) ON DELETE CASCADE,  -- NULL if prereq is education level
    prereq_education    VARCHAR(30),             -- min education: high_school, some_college, associate, bachelors, masters
    prereq_experience_years INTEGER,             -- min years of experience in related field
    is_required         BOOLEAN DEFAULT false,   -- true = hard requirement, false = recommended
    note                VARCHAR(255),            -- "Security+ recommended but not required"
    UNIQUE(credential_id, prereq_credential_id)
);

-- ── Career Edges (the graph connections) ──
-- Each row is a directed edge: "from X, you can reach Y"
-- X and Y can be roles OR credentials (one of each pair is NULL)
CREATE TABLE career_edges (
    id              SERIAL PRIMARY KEY,
    
    -- Source (exactly one must be set)
    source_role_id       INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    source_credential_id INTEGER REFERENCES credentials(id) ON DELETE CASCADE,
    
    -- Target (exactly one must be set)
    target_role_id       INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    target_credential_id INTEGER REFERENCES credentials(id) ON DELETE CASCADE,
    
    -- Edge metadata
    weight          INTEGER DEFAULT 10,          -- relative importance (higher = thicker Sankey band)
    typical_months  INTEGER,                     -- how long this transition typically takes
    description     TEXT,                        -- "Security+ qualifies you for SOC Analyst positions"
    path_tags       TEXT[],                      -- ['cyber', 'fast-track'] — for grouping paths
    
    -- Conditions for when this edge applies
    min_education        VARCHAR(30),            -- edge only valid if user has at least this education
    max_education        VARCHAR(30),            -- edge only valid if user has at most this (for degree paths)
    min_experience_years INTEGER DEFAULT 0,
    requires_clearance   BOOLEAN DEFAULT false,
    
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure exactly one source and one target
    CONSTRAINT chk_source CHECK (
        (source_role_id IS NOT NULL AND source_credential_id IS NULL) OR
        (source_role_id IS NULL AND source_credential_id IS NOT NULL)
    ),
    CONSTRAINT chk_target CHECK (
        (target_role_id IS NOT NULL AND target_credential_id IS NULL) OR
        (target_role_id IS NULL AND target_credential_id IS NOT NULL)
    )
);

CREATE INDEX idx_edges_source_role ON career_edges(source_role_id) WHERE source_role_id IS NOT NULL;
CREATE INDEX idx_edges_source_cred ON career_edges(source_credential_id) WHERE source_credential_id IS NOT NULL;
CREATE INDEX idx_edges_target_role ON career_edges(target_role_id) WHERE target_role_id IS NOT NULL;
CREATE INDEX idx_edges_target_cred ON career_edges(target_credential_id) WHERE target_credential_id IS NOT NULL;
CREATE INDEX idx_edges_tags ON career_edges USING gin(path_tags);

-- ── Role-to-Target Mappings (which targets are valid for which origins) ──
-- Pre-computed: "if you're a 25B, these are the target roles we have paths for"
CREATE TABLE role_target_mappings (
    id              SERIAL PRIMARY KEY,
    origin_role_id  INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    target_role_id  INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    relevance_score DECIMAL(3,2) DEFAULT 0.5,    -- 0.0 to 1.0, how relevant this target is for this origin
    is_featured     BOOLEAN DEFAULT false,       -- show in "recommended targets" for this MOS
    UNIQUE(origin_role_id, target_role_id)
);

CREATE INDEX idx_rtm_origin ON role_target_mappings(origin_role_id);

-- ── Employers (companies that hire for specific roles) ──
CREATE TABLE role_employers (
    id              SERIAL PRIMARY KEY,
    role_id         INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    employer_name   VARCHAR(255) NOT NULL,
    is_vet_friendly BOOLEAN DEFAULT false,
    location        VARCHAR(255),                -- "Arlington, VA" or "Remote"
    note            VARCHAR(255),                -- "Has veteran ERG", "SkillBridge partner"
    UNIQUE(role_id, employer_name)
);

-- ── Audit / Review Status ──
CREATE TABLE data_review_log (
    id              SERIAL PRIMARY KEY,
    table_name      VARCHAR(50) NOT NULL,
    record_id       INTEGER NOT NULL,
    status          VARCHAR(20) DEFAULT 'pending',  -- pending, approved, rejected, needs_edit
    reviewer        VARCHAR(100),
    notes           TEXT,
    reviewed_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Views for common queries ──

-- All valid targets for a given origin role
CREATE VIEW v_origin_targets AS
SELECT 
    r_origin.code AS origin_code,
    r_origin.title AS origin_title,
    r_target.code AS target_code,
    r_target.title AS target_title,
    r_target.industry,
    r_target.salary_low,
    r_target.salary_high,
    rtm.relevance_score,
    rtm.is_featured
FROM role_target_mappings rtm
JOIN roles r_origin ON r_origin.id = rtm.origin_role_id
JOIN roles r_target ON r_target.id = rtm.target_role_id
WHERE r_origin.is_active AND r_target.is_active;

-- All edges with resolved names
CREATE VIEW v_career_edges AS
SELECT 
    ce.id,
    COALESCE(sr.title, sc.name) AS source_name,
    COALESCE(sr.code, sc.code) AS source_code,
    CASE WHEN sr.id IS NOT NULL THEN 'role' ELSE 'credential' END AS source_type,
    COALESCE(tr.title, tc.name) AS target_name,
    COALESCE(tr.code, tc.code) AS target_code,
    CASE WHEN tr.id IS NOT NULL THEN 'role' ELSE 'credential' END AS target_type,
    ce.weight,
    ce.typical_months,
    ce.description,
    ce.path_tags,
    ce.min_education,
    ce.min_experience_years
FROM career_edges ce
LEFT JOIN roles sr ON sr.id = ce.source_role_id
LEFT JOIN credentials sc ON sc.id = ce.source_credential_id
LEFT JOIN roles tr ON tr.id = ce.target_role_id
LEFT JOIN credentials tc ON tc.id = ce.target_credential_id
WHERE ce.is_active;
