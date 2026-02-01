from fastapi import Header, HTTPException

async def verify_role(x_role: str = Header("public", alias="X-Role")):
    """
    Simulates RBAC. In real world, this would verify a JWT claim.
    For this demo, we trust the header.
    
    Roles:
    - doctor: Can seeing unmasked PII.
    - researcher: Can see system but masked.
    - public/other: Masked.
    """
    allowed_roles = ["doctor", "researcher", "public"]
    if x_role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Invalid Role")
    return x_role
