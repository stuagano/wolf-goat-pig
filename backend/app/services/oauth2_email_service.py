"""
This module is deprecated and will be removed in a future version.
Please use the unified EmailService from `backend.app.services.email_service`.
"""

import logging
from .email_service import get_email_service

logger = logging.getLogger(__name__)

logger.warning(
    "The `oauth2_email_service` module is deprecated. "
    "Please update your code to use the unified `get_email_service()`."
)

# For backwards compatibility, provide the service, but it's now the unified one.
# This avoids breaking existing imports immediately.
def get_oauth2_email_service():
    """
    DEPRECATED: Returns the unified email service.
    """
    logger.warning("Call to deprecated function `get_oauth2_email_service`.")
    return get_email_service()