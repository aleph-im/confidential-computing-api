"""VM and firmware tables

Revision ID: bd55f8625e90
Revises: 
Create Date: 2022-08-19 15:04:28.380117

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "bd55f8625e90"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "firmware_info",
        sa.Column("api_major", sa.Integer(), nullable=False),
        sa.Column("api_minor", sa.Integer(), nullable=False),
        sa.Column("platform_state", sa.Integer(), nullable=False),
        sa.Column("owner", sa.Integer(), nullable=False),
        sa.Column("config", sa.Integer(), nullable=False),
        sa.Column("build", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("api_major"),
    )
    op.create_table(
        "vm_images",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column(
            "upload_datetime",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "vms",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("owner", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("image_id", sa.String(), nullable=True),
        sa.Column("number_of_cores", sa.Integer(), nullable=False),
        sa.Column("memory", sa.Integer(), nullable=False),
        sa.Column("sev_policy", sa.Integer(), nullable=True),
        sa.Column("ssh_port", sa.Integer(), nullable=True),
        sa.Column("qmp_port", sa.Integer(), nullable=True),
        sa.Column("pid", sa.Integer(), nullable=True),
        sa.Column(
            "creation_datetime",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ("image_id",),
            ["vm_images.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("vms")
    op.drop_table("vm_images")
    op.drop_table("firmware_info")
    # ### end Alembic commands ###
