-- ============================================================
-- CORPORATE VETERAN ERGs — The FOB
-- Run this in Supabase SQL Editor (or any PostgreSQL client).
-- If you don't have a profiles table, remove or comment the
-- submitted_by REFERENCES line in erg_submissions and use
-- submitted_by UUID NULL without FK.
-- ============================================================

-- Helper: update updated_at on row change
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- CORPORATE VETERAN ERGs
-- ============================================================
CREATE TABLE IF NOT EXISTS public.corporate_ergs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    -- Company info
    company_name TEXT NOT NULL,
    erg_name TEXT,
    industry TEXT NOT NULL,
    company_size TEXT CHECK (company_size IN ('small', 'medium', 'large', 'enterprise')),

    -- ERG details
    description TEXT,
    offerings TEXT[] DEFAULT '{}',
    founded_year INTEGER,
    member_count INTEGER,

    -- Links
    careers_url TEXT,
    erg_url TEXT,
    company_website TEXT,
    contact_email TEXT,
    linkedin_url TEXT,

    -- Location
    headquarters_city TEXT,
    headquarters_state TEXT,

    -- Ratings and verification
    military_friendly_rating TEXT CHECK (military_friendly_rating IN (
        'top_employer', 'gold', 'silver', 'designated', 'military_friendly'
    )),
    has_skillbridge BOOLEAN DEFAULT false,
    verified BOOLEAN DEFAULT false,
    featured BOOLEAN DEFAULT false,

    -- Data provenance
    data_sources TEXT[] DEFAULT '{}',
    source_type TEXT DEFAULT 'scraped' CHECK (source_type IN ('seed_data', 'scraped', 'community_submitted', 'admin_curated')),
    submitted_by UUID NULL,
    -- If you have Supabase profiles: REFERENCES public.profiles(id)

    -- Timestamps
    scraped_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(company_name)
);

CREATE INDEX IF NOT EXISTS idx_ergs_industry ON public.corporate_ergs(industry);
CREATE INDEX IF NOT EXISTS idx_ergs_company_size ON public.corporate_ergs(company_size);
CREATE INDEX IF NOT EXISTS idx_ergs_verified ON public.corporate_ergs(verified);
CREATE INDEX IF NOT EXISTS idx_ergs_featured ON public.corporate_ergs(featured);
CREATE INDEX IF NOT EXISTS idx_ergs_offerings ON public.corporate_ergs USING GIN(offerings);
CREATE INDEX IF NOT EXISTS idx_ergs_rating ON public.corporate_ergs(military_friendly_rating);
CREATE INDEX IF NOT EXISTS idx_ergs_skillbridge ON public.corporate_ergs(has_skillbridge);
CREATE INDEX IF NOT EXISTS idx_ergs_source ON public.corporate_ergs(source_type);

CREATE INDEX IF NOT EXISTS idx_ergs_search ON public.corporate_ergs USING GIN(
    to_tsvector('english',
        COALESCE(company_name, '') || ' ' ||
        COALESCE(erg_name, '') || ' ' ||
        COALESCE(description, '') || ' ' ||
        COALESCE(industry, '')
    )
);

-- ============================================================
-- ERG SUBMISSION QUEUE (community submissions before approval)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.erg_submissions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    submitted_by UUID NULL,
    submitter_email TEXT NOT NULL,
    submitter_name TEXT,
    submitter_role TEXT,

    company_name TEXT NOT NULL,
    erg_name TEXT,
    industry TEXT,
    company_size TEXT,
    description TEXT,
    offerings TEXT[] DEFAULT '{}',
    founded_year INTEGER,
    member_count INTEGER,
    careers_url TEXT,
    erg_url TEXT,
    company_website TEXT,
    contact_email TEXT,
    linkedin_url TEXT,
    headquarters_city TEXT,
    headquarters_state TEXT,
    has_skillbridge BOOLEAN DEFAULT false,

    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'duplicate')),
    reviewer_notes TEXT,
    reviewed_at TIMESTAMPTZ,

    approved_erg_id UUID REFERENCES public.corporate_ergs(id),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_submissions_status ON public.erg_submissions(status);
CREATE INDEX IF NOT EXISTS idx_submissions_company ON public.erg_submissions(company_name);

-- ============================================================
-- ROW LEVEL SECURITY (Supabase: enable if using Supabase Auth)
-- ============================================================
-- ALTER TABLE public.corporate_ergs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.erg_submissions ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "ERGs are publicly readable" ON public.corporate_ergs FOR SELECT USING (true);
-- CREATE POLICY "Authenticated users can submit ERGs" ON public.erg_submissions FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);
-- CREATE POLICY "Users view own submissions" ON public.erg_submissions FOR SELECT USING (auth.uid() = submitted_by);

-- ============================================================
-- UPDATED_AT TRIGGER
-- ============================================================
DROP TRIGGER IF EXISTS update_ergs_timestamp ON public.corporate_ergs;
CREATE TRIGGER update_ergs_timestamp BEFORE UPDATE ON public.corporate_ergs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
