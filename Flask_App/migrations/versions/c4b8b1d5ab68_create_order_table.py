"""create order table

Revision ID: c4b8b1d5ab68
Revises: 3646e9c82f64
"""

from alembic import op
import sqlalchemy as sa


revision = "c4b8b1d5ab68"
down_revision = "3646e9c82f64"
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "order",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.String(length=100), unique=True, nullable=False),

        sa.Column("user_id", sa.Integer(), nullable=False),

        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=128), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),

        sa.Column("payment_method", sa.String(length=50), nullable=False),

        sa.Column("subtotal", sa.Float(), nullable=False, default=0),
        sa.Column("shipping", sa.Float(), nullable=False, default=0),
        sa.Column("total", sa.Float(), nullable=False, default=0),

        sa.Column("status", sa.String(length=50), nullable=False, default="Pending"),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp()
        ),

        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"]
        )
    )


def downgrade():

    op.drop_table("order")