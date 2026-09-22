-- ============================================================
-- Agreement Template Management System — DB Migration
-- Run this SQL against your database before starting the app
-- ============================================================

-- 1. Create enum types (PostgreSQL)
DO $$ BEGIN
    CREATE TYPE agreementtemplatetype AS ENUM ('rich_text', 'pdf_upload');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE agreementtemplatestatus AS ENUM ('active', 'draft', 'archived');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 2. Create agreement_templates table
CREATE TABLE IF NOT EXISTS agreement_templates (
    id                BIGSERIAL PRIMARY KEY,
    public_id         UUID         NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    name              VARCHAR(255) NOT NULL,
    version           VARCHAR(50)  NOT NULL DEFAULT '1.0',
    description       TEXT,
    template_type     agreementtemplatetype NOT NULL DEFAULT 'rich_text',
    status            agreementtemplatestatus NOT NULL DEFAULT 'draft',
    content_json      TEXT,        -- JSON array of {heading, body} clauses
    pdf_file_key      VARCHAR(500),-- Storage key for uploaded PDF
    is_default        BOOLEAN      NOT NULL DEFAULT FALSE,
    created_by        BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_agreement_templates_public_id  ON agreement_templates(public_id);
CREATE INDEX IF NOT EXISTS ix_agreement_templates_status     ON agreement_templates(status);
CREATE INDEX IF NOT EXISTS ix_agreement_templates_is_default ON agreement_templates(is_default);
CREATE INDEX IF NOT EXISTS ix_agreement_templates_type       ON agreement_templates(template_type);

-- 3. Add template_id FK to vendor_agreements
ALTER TABLE vendor_agreements
    ADD COLUMN IF NOT EXISTS template_id BIGINT REFERENCES agreement_templates(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_vendor_agreements_template_id ON vendor_agreements(template_id);

-- 4. Trigger to auto-update updated_at on agreement_templates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_agreement_templates_updated_at ON agreement_templates;
CREATE TRIGGER set_agreement_templates_updated_at
    BEFORE UPDATE ON agreement_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

