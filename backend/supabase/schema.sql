-- Tenants (users/firms)
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Entities (partnerships/SPVs)
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    ein TEXT,
    business_activity_code TEXT,
    entity_type TEXT DEFAULT 'LLC',
    fiscal_year_end TEXT DEFAULT '12/31',
    address_street TEXT,
    address_city TEXT,
    address_state TEXT,
    address_zip TEXT,
    state_of_formation TEXT,
    date_business_started DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Partners/Members
CREATE TABLE partners (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    ssn_ein TEXT,
    address_street TEXT,
    address_city TEXT,
    address_state TEXT,
    address_zip TEXT,
    partner_type TEXT DEFAULT 'limited',
    ownership_pct NUMERIC(5,2) NOT NULL,
    profit_sharing_pct NUMERIC(5,2),
    loss_sharing_pct NUMERIC(5,2),
    is_managing_partner BOOLEAN DEFAULT FALSE,
    is_foreign_partner BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- QBO Connections
CREATE TABLE qbo_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    realm_id TEXT NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    token_expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Operating Agreements
CREATE TABLE operating_agreements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    file_url TEXT,
    extracted_data JSONB,
    confirmed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tax Returns
CREATE TABLE tax_returns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    tax_year INTEGER NOT NULL,
    status TEXT DEFAULT 'draft',
    qbo_data JSONB,
    mapped_data JSONB,
    mapping_overrides JSONB,
    generated_1065_url TEXT,
    generated_at TIMESTAMPTZ,
    reviewer_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(entity_id, tax_year)
);

-- K-1s
CREATE TABLE k1s (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tax_return_id UUID REFERENCES tax_returns(id) ON DELETE CASCADE,
    partner_id UUID REFERENCES partners(id) ON DELETE CASCADE,
    allocations JSONB,
    generated_pdf_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
