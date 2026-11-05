"""Add categories and product images

Revision ID: c8866b6ab3dc
Revises: 1fdff36ea460
Create Date: 2026-10-01 16:20:45.570881

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision = "c8866b6ab3dc"
down_revision = "1fdff36ea460"
branch_labels = None
depends_on = None


def upgrade():
    # ---------------------------------------------------------
    # 1. Create categories table
    # ---------------------------------------------------------
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("image", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # ---------------------------------------------------------
    # 2. Create product_images table
    # ---------------------------------------------------------
    op.create_table(
        "product_images",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),

        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_product_images_product_id",
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    # ---------------------------------------------------------
    # 3. Update products table
    # ---------------------------------------------------------
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('name', sa.String(length=255), nullable=True)
        )

        batch_op.add_column(
            sa.Column('thumbnail', sa.String(length=255), nullable=True)
        )

        batch_op.add_column(
            sa.Column('cost', sa.Numeric(precision=10, scale=2), nullable=True)
        )

        batch_op.add_column(
            sa.Column('category_id', sa.Integer(), nullable=True)
        )

        batch_op.alter_column(
            'price',
            existing_type=sa.NUMERIC(precision=10, scale=2),
            nullable=True
        )

        batch_op.alter_column(
            'title',
            existing_type=sa.VARCHAR(length=255),
            nullable=True
        )

        batch_op.alter_column(
            'type',
            existing_type=sa.VARCHAR(length=100),
            nullable=True
        )

        batch_op.create_foreign_key(
            'fk_products_category_id_categories',
            'categories',
            ['category_id'],
            ['id']
        )

        batch_op.drop_column('images')
        batch_op.drop_column('category')


def downgrade():

    # ---------------------------------------------------------
    # Restore old product columns
    # ---------------------------------------------------------
    with op.batch_alter_table("products", schema=None) as batch_op:

        batch_op.add_column(
            sa.Column(
                "category",
                sa.VARCHAR(length=100),
                nullable=True,
            )
        )

        batch_op.add_column(
            sa.Column(
                "images",
                sqlite.JSON(),
                nullable=True,
            )
        )

        batch_op.drop_constraint(
            "fk_products_category_id",
            type_="foreignkey",
        )

        batch_op.alter_column(
            "type",
            existing_type=sa.VARCHAR(length=100),
            nullable=False,
        )

        batch_op.alter_column(
            "title",
            existing_type=sa.VARCHAR(length=255),
            nullable=False,
        )

        batch_op.alter_column(
            "price",
            existing_type=sa.NUMERIC(
                precision=10,
                scale=2
            ),
            nullable=False,
        )

        batch_op.drop_column("category_id")
        batch_op.drop_column("cost")
        batch_op.drop_column("thumbnail")
        batch_op.drop_column("name")

    # ---------------------------------------------------------
    # Remove product_images and categories
    # ---------------------------------------------------------
    op.drop_table("product_images")
    op.drop_table("categories")