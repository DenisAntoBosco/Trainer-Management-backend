"""Initial migration - create all tables

Revision ID: 001
Revises: 
Create Date: 2024-12-30 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create enums using DO blocks to check existence
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE app_role AS ENUM ('admin', 'hr', 'project_manager', 'trainer');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE trainer_status AS ENUM ('available', 'partially_allocated', 'fully_allocated', 'on_leave');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE employment_type AS ENUM ('full-time', 'part-time', 'freelance', 'intern');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE experience_level AS ENUM ('junior', 'mid', 'senior');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE project_status AS ENUM ('active', 'upcoming', 'completed');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE engagement_status AS ENUM ('active', 'upcoming', 'completed');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE batch_status AS ENUM ('confirmed', 'pending', 'awaiting_confirmation');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE hr_request_status AS ENUM ('pending', 'in_progress', 'fulfilled');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE urgency_level AS ENUM ('critical', 'high', 'medium', 'low');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE attendance_status AS ENUM ('pending', 'present', 'absent', 'half_day');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create enum objects for table definitions
    app_role_enum = postgresql.ENUM('admin', 'hr', 'project_manager', 'trainer', name='app_role', create_type=False)
    trainer_status_enum = postgresql.ENUM('available', 'partially_allocated', 'fully_allocated', 'on_leave', name='trainer_status', create_type=False)
    employment_type_enum = postgresql.ENUM('full-time', 'part-time', 'freelance', 'intern', name='employment_type', create_type=False)
    experience_level_enum = postgresql.ENUM('junior', 'mid', 'senior', name='experience_level', create_type=False)
    project_status_enum = postgresql.ENUM('active', 'upcoming', 'completed', name='project_status', create_type=False)
    engagement_status_enum = postgresql.ENUM('active', 'upcoming', 'completed', name='engagement_status', create_type=False)
    batch_status_enum = postgresql.ENUM('confirmed', 'pending', 'awaiting_confirmation', name='batch_status', create_type=False)
    hr_request_status_enum = postgresql.ENUM('pending', 'in_progress', 'fulfilled', name='hr_request_status', create_type=False)
    urgency_level_enum = postgresql.ENUM('critical', 'high', 'medium', 'low', name='urgency_level', create_type=False)
    attendance_status_enum = postgresql.ENUM('pending', 'present', 'absent', 'half_day', name='attendance_status', create_type=False)

    # Create profiles table
    op.create_table('profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Create user_roles table
    op.create_table('user_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', app_role_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'role')
    )

    # Create trainers table
    op.create_table('trainers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('avatar', sa.Text(), nullable=True),
        sa.Column('expertise', postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column('status', trainer_status_enum, nullable=False),
        sa.Column('max_batches', sa.Integer(), nullable=False),
        sa.Column('current_batches', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('employment_type', employment_type_enum, nullable=False),
        sa.Column('experience_level', experience_level_enum, nullable=False),
        sa.Column('join_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create projects table
    op.create_table('projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('client_name', sa.Text(), nullable=False),
        sa.Column('primary_contact_name', sa.Text(), nullable=False),
        sa.Column('primary_contact_email', sa.Text(), nullable=False),
        sa.Column('primary_contact_phone', sa.Text(), nullable=False),
        sa.Column('project_type', postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', project_status_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create engagements table
    op.create_table('engagements',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('domain', sa.Text(), nullable=False),
        sa.Column('training_type', sa.Text(), nullable=False),
        sa.Column('total_students', sa.Integer(), nullable=False),
        sa.Column('students_per_batch', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('status', engagement_status_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create batches table
    op.create_table('batches',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('batch_number', sa.Integer(), nullable=False),
        sa.Column('students', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('status', batch_status_enum, nullable=False),
        sa.Column('trainer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('confirmed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['confirmed_by'], ['profiles.id'], ),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ),
        sa.ForeignKeyConstraint(['trainer_id'], ['trainers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create hr_requests table
    op.create_table('hr_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('domain', sa.Text(), nullable=False),
        sa.Column('trainers_needed', sa.Integer(), nullable=False),
        sa.Column('urgency', urgency_level_enum, nullable=False),
        sa.Column('status', hr_request_status_enum, nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['profiles.id'], ),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create trainer_attendance table
    op.create_table('trainer_attendance',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trainer_id', sa.Text(), nullable=False),
        sa.Column('trainer_name', sa.Text(), nullable=False),
        sa.Column('batch_id', sa.Text(), nullable=False),
        sa.Column('project_id', sa.Text(), nullable=False),
        sa.Column('engagement_id', sa.Text(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False, server_default=sa.text('CURRENT_DATE')),
        sa.Column('status', attendance_status_enum, nullable=False, server_default='pending'),
        sa.Column('punch_in', sa.DateTime(timezone=True), nullable=True),
        sa.Column('punch_out', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completion_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('trainer_id', 'batch_id', 'date')
    )

def downgrade() -> None:
    op.drop_table('trainer_attendance')
    op.drop_table('hr_requests')
    op.drop_table('batches')
    op.drop_table('engagements')
    op.drop_table('projects')
    op.drop_table('trainers')
    op.drop_table('user_roles')
    op.drop_table('profiles')
    
    # Drop enums
    postgresql.ENUM(name='attendance_status').drop(op.get_bind())
    postgresql.ENUM(name='urgency_level').drop(op.get_bind())
    postgresql.ENUM(name='hr_request_status').drop(op.get_bind())
    postgresql.ENUM(name='batch_status').drop(op.get_bind())
    postgresql.ENUM(name='engagement_status').drop(op.get_bind())
    postgresql.ENUM(name='project_status').drop(op.get_bind())
    postgresql.ENUM(name='experience_level').drop(op.get_bind())
    postgresql.ENUM(name='employment_type').drop(op.get_bind())
    postgresql.ENUM(name='trainer_status').drop(op.get_bind())
    postgresql.ENUM(name='app_role').drop(op.get_bind())