from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from .. import models, schemas, database
from .auth import get_current_user
import shutil
import os

router = APIRouter()

UPLOAD_ROOT = "onboardingdoc"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload")
def submit_onboarding(
    energy_pic: UploadFile = None,
    doc: UploadFile = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate types if files are provided
    if energy_pic and energy_pic.content_type.split("/")[0] != "image":
        raise HTTPException(400, "Energy source file must be an image")
    
    if doc and doc.content_type not in ["application/pdf", "image/jpeg", "image/png"]:
            raise HTTPException(400, "Document must be PDF or image")

    # Validate size if files are provided
    for file in [f for f in [energy_pic, doc] if f]:
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)
        if size > MAX_FILE_SIZE:
                raise HTTPException(400, "File too large (max 5MB)")

    # Prepare user-specific directory
    user_dir = os.path.join(UPLOAD_ROOT, str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)

    pic_path = None
    doc_path = None

    # Save files if provided
    if energy_pic:
        pic_ext = os.path.splitext(energy_pic.filename)[1]
        pic_filename = f"energy_source{pic_ext}"
        pic_path = os.path.join(user_dir, pic_filename)
        with open(pic_path, "wb") as buffer:
            shutil.copyfileobj(energy_pic.file, buffer)
    
    if doc:
        doc_ext = os.path.splitext(doc.filename)[1]
        doc_filename = f"supporting_doc{doc_ext}"
        doc_path = os.path.join(user_dir, doc_filename)
        with open(doc_path, "wb") as buffer:
            shutil.copyfileobj(doc.file, buffer)

    # Update user status
    if pic_path:
        current_user.energy_source_pic = pic_path
    if doc_path:
        current_user.supporting_doc = doc_path
        
    current_user.is_onboarded = True # Auto-approve for this demo
    db.commit()
    db.refresh(current_user)

    return {"status": "onboarding_complete", "user": current_user.email}
