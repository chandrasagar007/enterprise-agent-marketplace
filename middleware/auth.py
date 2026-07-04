from fastapi import Header, HTTPException
from database.registry import TENANT_SUBSCRIPTIONS

def verify_api_key(x_api_key: str = Header(None)):
    """Validates global API access."""
    if x_api_key != "123456":
        raise HTTPException(status_code=401, detail="Invalid API Key")

def get_verified_tenant(x_tenant_id: str = Header(..., description="The organization ID")):
    """Validates the tenant exists and returns the ID for the endpoint to use."""
    if x_tenant_id not in TENANT_SUBSCRIPTIONS:
        raise HTTPException(
            status_code=403, 
            detail=f"Unauthorized: Tenant ID '{x_tenant_id}' is not registered."
        )
    return x_tenant_id