"""
Admin OAuth2 Router

OAuth2 email configuration, authorization flow, callback handling, and test email.
"""

import logging
import os
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import HTMLResponse

from ..services.email_service import get_email_service

logger = logging.getLogger("app.routers.admin_oauth")

router = APIRouter(prefix="/admin", tags=["admin-oauth"])


@router.get("/oauth2-status")
def get_oauth2_status(x_admin_email: str = Header(None)):  # type: ignore
    """Get OAuth2 configuration status (admin only)"""
    # Check admin access
    admin_emails = ["stuagano@gmail.com", "admin@wgp.com"]
    if not x_admin_email or x_admin_email not in admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        oauth2_service = get_email_service()
        status = oauth2_service.get_configuration_status()  # type: ignore
        return {"status": status}
    except Exception as e:
        logger.error(f"Error getting OAuth2 status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/oauth2-authorize")
def start_oauth2_authorization(request: dict[str, Any], x_admin_email: str = Header(None)):  # type: ignore
    """Start OAuth2 authorization flow (admin only)"""
    # Check admin access
    admin_emails = ["stuagano@gmail.com", "admin@wgp.com"]
    if not x_admin_email or x_admin_email not in admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        oauth2_service = get_email_service()

        # Set from_email and from_name if provided
        if request.get("from_email"):
            oauth2_service.from_email = request["from_email"]  # type: ignore
            os.environ["FROM_EMAIL"] = request["from_email"]
        if request.get("from_name"):
            oauth2_service.from_name = request["from_name"]  # type: ignore
            os.environ["FROM_NAME"] = request["from_name"]

        # Let the service auto-detect the correct redirect URI
        # The redirect URI should point to the backend API, not the frontend
        auth_url = oauth2_service.get_auth_url()  # type: ignore

        return {
            "auth_url": auth_url,
            "message": "Visit the auth_url to complete authorization",
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail="Gmail credentials file not found. Please upload your Gmail API credentials file first.",
        )
    except Exception as e:
        logger.error(f"Error starting OAuth2 authorization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/oauth2-callback")
def handle_oauth2_callback(code: str = Query(...), state: str = Query(None)):  # type: ignore
    """Handle OAuth2 callback from Google"""
    try:
        oauth2_service = get_email_service()
        success = oauth2_service.handle_oauth_callback(code)  # type: ignore

        if success:
            # Return HTML page that will close the window and notify the parent
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>OAuth2 Authorization Complete</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }
                    .container {
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
                        text-align: center;
                        max-width: 400px;
                    }
                    h1 {
                        color: #4CAF50;
                        margin-bottom: 20px;
                    }
                    p {
                        color: #666;
                        margin-bottom: 20px;
                    }
                    .spinner {
                        border: 3px solid #f3f3f3;
                        border-top: 3px solid #4CAF50;
                        border-radius: 50%;
                        width: 40px;
                        height: 40px;
                        animation: spin 1s linear infinite;
                        margin: 20px auto;
                    }
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅ Authorization Successful!</h1>
                    <p>OAuth2 authorization has been completed successfully.</p>
                    <div class="spinner"></div>
                    <p>This window will close automatically...</p>
                </div>
                <script>
                    // Notify parent window if it exists
                    if (window.opener) {
                        window.opener.postMessage({ type: 'oauth2-success' }, '*');
                    }
                    // Close window after 2 seconds
                    setTimeout(() => {
                        window.close();
                    }, 2000);
                </script>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content, status_code=200)
        # Return error HTML page
        html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>OAuth2 Authorization Failed</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%);
                    }
                    .container {
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
                        text-align: center;
                        max-width: 400px;
                    }
                    h1 {
                        color: #f44336;
                        margin-bottom: 20px;
                    }
                    p {
                        color: #666;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>❌ Authorization Failed</h1>
                    <p>Failed to complete OAuth2 authorization.</p>
                    <p>Please close this window and try again.</p>
                </div>
            </body>
            </html>
            """
        return HTMLResponse(content=html_content, status_code=400)

    except Exception as e:
        logger.error(f"Error handling OAuth2 callback: {e}")
        # Return error HTML page
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OAuth2 Error</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%);
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
                    text-align: center;
                    max-width: 400px;
                }}
                h1 {{
                    color: #f44336;
                    margin-bottom: 20px;
                }}
                p {{
                    color: #666;
                    margin-bottom: 10px;
                }}
                .error {{
                    background: #ffebee;
                    color: #c62828;
                    padding: 10px;
                    border-radius: 5px;
                    margin-top: 20px;
                    font-family: monospace;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>❌ OAuth2 Error</h1>
                <p>An error occurred during OAuth2 authorization.</p>
                <div class="error">{e!s}</div>
                <p>Please close this window and try again.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=500)


@router.post("/oauth2-test-email")
async def test_oauth2_email(request: dict[str, Any], x_admin_email: str = Header(None)):  # type: ignore
    """Send test email using OAuth2 (admin only)"""
    # Check admin access
    admin_emails = ["stuagano@gmail.com", "admin@wgp.com"]
    if not x_admin_email or x_admin_email not in admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        test_email = request.get("test_email")
        if not test_email:
            raise HTTPException(status_code=400, detail="Test email address required")

        oauth2_service = get_email_service()

        if not oauth2_service.is_configured:  # type: ignore
            raise HTTPException(
                status_code=400,
                detail="OAuth2 email service not configured. Please complete OAuth2 authorization first.",
            )

        success = oauth2_service.send_test_email(test_email, x_admin_email)

        if success:
            return {
                "status": "success",
                "message": f"Test email sent to {test_email} using OAuth2",
            }
        raise HTTPException(status_code=500, detail="Failed to send test email")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending OAuth2 test email: {e}")
        raise HTTPException(status_code=500, detail=str(e))
