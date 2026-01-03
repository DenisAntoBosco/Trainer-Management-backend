"""Fix trainer table enum columns

Revision ID: 003
Revises: 002
Create Date: 2026-01-02 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Alter trainer status column to use enum
    op.execute("ALTER TABLE trainers ALTER COLUMN status TYPE trainer_status USING status::trainer_status")
    
    # Alter employment_type column to use enum
    op.execute("ALTER TABLE trainers ALTER COLUMN employment_type TYPE employment_type USING employment_type::employment_type")
    
    # Alter experience_level column to use enum
    op.execute("ALTER TABLE trainers ALTER COLUMN experience_level TYPE experience_level USING experience_level::experience_level")

def downgrade() -> None:
    # Revert to varchar
    op.execute("ALTER TABLE trainers ALTER COLUMN status TYPE VARCHAR(50)")
    op.execute("ALTER TABLE trainers ALTER COLUMN employment_type TYPE VARCHAR(50)")
    op.execute("ALTER TABLE trainers ALTER COLUMN experience_level TYPE VARCHAR(50)")
