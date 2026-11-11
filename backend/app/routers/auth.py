from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import User, CommunityHelper
from backend.app.schemas import UserCreate, UserLogin, PasswordResetRequest, Token, UserOut, UserProfileUpdate
from backend.app.auth import verify_password, get_password_hash, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )
    if db.query(User).filter(User.phone == user_in.phone).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is already registered"
        )

    hashed_pw = get_password_hash(user_in.password)
    new_user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        phone=user_in.phone,
        hashed_password=hashed_pw,
        role=user_in.role or "user",
        address=user_in.address,
        emergency_notes=user_in.emergency_notes,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # If registered as helper, automatically create pending helper profile
    if new_user.role == "helper":
        helper_profile = CommunityHelper(
            user_id=new_user.id,
            neighbourhood="Central District",
            city="Bengaluru",
            verification_status="pending"
        )
        db.add(helper_profile)
        db.commit()

    access_token = create_access_token(data={"sub": str(new_user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": new_user
    }

@router.post("/login", response_model=Token)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_in.email).first()
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Compatible with OAuth2 standard form data (username=email)
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/reset-password")
def reset_password(reset_in: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == reset_in.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email not found"
        )
    user.hashed_password = get_password_hash(reset_in.new_password)
    db.commit()
    return {"status": "success", "message": "Password has been successfully updated"}

@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserOut)
def update_current_user(update_in: UserProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if update_in.full_name is not None:
        current_user.full_name = update_in.full_name
    if update_in.phone is not None:
        current_user.phone = update_in.phone
    if update_in.address is not None:
        current_user.address = update_in.address
    if update_in.emergency_notes is not None:
        current_user.emergency_notes = update_in.emergency_notes
    if update_in.battery_level is not None:
        current_user.battery_level = update_in.battery_level
    if update_in.network_status is not None:
        current_user.network_status = update_in.network_status

    db.commit()
    db.refresh(current_user)
    return current_user
