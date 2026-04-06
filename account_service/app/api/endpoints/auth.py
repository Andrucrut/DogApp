from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.security import hash_password, create_access_token, create_refresh_token, verify_password, decode_token
from app.db.session import get_db
from app.db_crud.blacklist_crud import crud_blacklist
from app.db_crud.role_crud import crud_role
from app.db_crud.user_crud import crud_user
from app.models.user import User
from app.schemas.auth import TokenResponse, LoginRequest, RefreshRequest
from app.schemas.password import ResetPasswordSchema, ForgotPasswordSchema, ChangePasswordSchema
from app.schemas.user import CreateUserSchema

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer()


async def _get_or_create_role(db: AsyncSession, role_key: str):
    role = await crud_role.get_by_key(db, role_key)
    if role:
        return role
    role_name = "Owner" if role_key == "owner" else "Walker"
    return await crud_role.create(
        db,
        {
            "name": role_name,
            "key": role_key,
            "description": f"{role_name} role",
            "permissions": 0,
        },
    )


@router.post('/register')
async def register(schema: CreateUserSchema, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    existing = await crud_user.get_by_email_or_phone(db, email=schema.email,phone=schema.phone)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="user already exists")

    role = await _get_or_create_role(db, schema.role_key)

    data = schema.model_dump(
        exclude={"consent_personal_data", "consent_privacy_policy", "role_key"}
    )
    try:
        data["hashed_password"] = hash_password(data.pop("password") if "password" in data else "")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_password",
        )
    data["role_id"] = role.id
    user = await crud_user.create(db, data)
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login")
async def login(schema: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await crud_user.get_by_email_or_phone(db, email=schema.email, phone=schema.phone)
    if not user or not verify_password(schema.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user_blocked")

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh")
async def refresh(schema: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(schema.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token_invalid")

    await crud_blacklist.add(db, schema.refresh_token)
    user_id = payload.get("sub")
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    await crud_blacklist.add(db, credentials.credentials)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    schema: ChangePasswordSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(schema.old_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="wrong_password")

    await crud_user.update(db, current_user, {"hashed_password": hash_password(schema.password)})


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(schema: ForgotPasswordSchema, db: AsyncSession = Depends(get_db)):
    user = await crud_user.get_by_email(db, schema.email)
    if not user:
        return


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(schema: ResetPasswordSchema, db: AsyncSession = Depends(get_db)):
    payload = decode_token(schema.token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="token_invalid")

    user = await crud_user.get(db, payload.get("sub"))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")

    await crud_user.update(db, user, {"hashed_password": hash_password(schema.password)})
