from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import engine, SessionLocal
from . import models, schemas, auth
from .auth import get_current_user
from fastapi.security import OAuth2PasswordRequestForm

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Job Application Tracker API",
    docs_url="/docs",
    redoc_url="/redoc"
)


def get_db():
    db = SessionLocal()   # ✅ create session
    try:
        yield db
    finally:
        db.close()        # ✅ now close exists


@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    hashed = auth.hash_password(user.password)
    db_user = models.User(email=user.email, password=hashed)
    db.add(db_user)
    db.commit()
    return {"message":"User registered succesfully"}

@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    db_user = (
        db.query(models.User)
        .filter(models.User.email == form_data.username)
        .first()
    )

    if not db_user or not auth.verify_password(
        form_data.password, db_user.password
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth.create_access_token({"user_id": db_user.id})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/jobs")
def add_job(
    job: schemas.JobCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_job = models.job(**job.dict(), user_id=user_id)
    db.add(new_job)
    db.commit()
    return {"message": "Job added successfully"}


@app.get("/jobs")
def get_jobs(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(models.job).filter(models.job.user_id == user_id).all()
