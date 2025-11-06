from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from datetime import datetime

from database import get_db
from models.user import User
from models.image import HealingImage
from models.patient import Patient
from schemas.image_schema import HealingImage as HealingImageSchema
from utils.security import get_current_user
from config import UPLOAD_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS

router = APIRouter()

def save_upload_file(upload_file: UploadFile, patient_id: int) -> str:
    # Validate file extension
    file_ext = os.path.splitext(upload_file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {ALLOWED_EXTENSIONS}"
        )
    
    # Generate unique filename
    unique_filename = f"patient_{patient_id}_{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Ensure directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Save file
    with open(file_path, "wb") as f:
        content = upload_file.file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB"
            )
        f.write(content)
    
    return file_path

@router.post("/upload", response_model=HealingImageSchema, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    patient_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Verify access
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only upload images for yourself"
        )
    
    # Save file
    file_path = save_upload_file(file, patient_id)
    
    # Create database record
    new_image = HealingImage(
        patient_id=patient_id,
        image_path=file_path
    )
    
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    
    return new_image

@router.get("/patient/{patient_id}", response_model=List[HealingImageSchema])
def get_patient_images(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Verify access
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these images"
        )
    
    images = db.query(HealingImage).filter(
        HealingImage.patient_id == patient_id
    ).order_by(HealingImage.upload_date.desc()).all()
    
    return images

@router.get("/{image_id}", response_model=HealingImageSchema)
def get_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    image = db.query(HealingImage).filter(HealingImage.id == image_id).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Verify access
    patient = db.query(Patient).filter(Patient.id == image.patient_id).first()
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this image"
        )
    
    return image

@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    image = db.query(HealingImage).filter(HealingImage.id == image_id).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Verify access
    patient = db.query(Patient).filter(Patient.id == image.patient_id).first()
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this image"
        )
    
    # Delete file from disk
    if os.path.exists(image.image_path):
        os.remove(image.image_path)
    
    # Delete database record
    db.delete(image)
    db.commit()
    
    return None