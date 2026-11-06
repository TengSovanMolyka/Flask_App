"""Storefront product routes are defined in routes.front.home.

This module remains as a compatibility import so older imports do not
register a second set of /products and /product routes.
"""

from routes.front.home import front_bp

__all__ = ["front_bp"]
