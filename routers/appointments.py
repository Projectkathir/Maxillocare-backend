from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
from models.user import User
from models.appointment import Appointment
from models.patient import Patient
from schemas.appointment_schema import (
    AppointmentCreate,
    AppointmentUpdate,
    Appointment as AppointmentSchema
)
from utils.security import get_current_user

router = APIRouter()

# -------------------------------------------
# Create Appointment
# -------------------------------------------
@router.post("/", response_model=AppointmentSchema, status_code=status.HTTP_201_CREATED)
def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == appointment_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    # Verify doctor exists
    doctor = db.query(User).filter(
        User.id == appointment_data.doctor_id,
        User.role == "doctor"
    ).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    # If patient is creating, ensure they're booking for themselves
    if current_user.role == "patient":
        if patient.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only book appointments for yourself"
            )
        # Patients cannot set appointment status during booking
        # REMOVED BUGGY LINE: if appointment_data.status is not None:
        # AppointmentCreate doesn't have 'status' field, so we don't check it
        # Status will default to "pending" in the database model

    # Create new appointment - status will default to "pending" from model
    new_appointment = Appointment(
        patient_id=appointment_data.patient_id,
        doctor_id=appointment_data.doctor_id,
        appointment_date=appointment_data.appointment_date,
        notes=appointment_data.notes
        # status will automatically be set to "pending" by the model default
    )
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)

    return new_appointment

# -------------------------------------------
# Delete Appointment
# -------------------------------------------
@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    # Verify access
    if current_user.role == "doctor":
        if appointment.doctor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this appointment"
            )
    else:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient or appointment.patient_id != patient.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this appointment"
            )

    db.delete(appointment)
    db.commit()

    return None

# -------------------------------------------
# Get All Appointments
# -------------------------------------------
@router.get("/", response_model=List[AppointmentSchema])
def get_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "doctor":
        # Doctors see all their appointments
        appointments = db.query(Appointment).filter(
            Appointment.doctor_id == current_user.id
        ).all()
    else:
        # Patients see their own appointments
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient:
            return []
        appointments = db.query(Appointment).filter(
            Appointment.patient_id == patient.id
        ).all()

    return appointments

# -------------------------------------------
# Get Appointment by ID
# -------------------------------------------
@router.get("/{appointment_id}", response_model=AppointmentSchema)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    # Verify access
    if current_user.role == "doctor":
        if appointment.doctor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this appointment"
            )
    else:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient or appointment.patient_id != patient.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this appointment"
            )

    return appointment

# -------------------------------------------
# Update Appointment
# -------------------------------------------
@router.put("/{appointment_id}", response_model=AppointmentSchema)
def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    # Role-based update logic
    if current_user.role == "doctor":
        if appointment.doctor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this appointment"
            )
    else:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient or appointment.patient_id != patient.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this appointment"
            )

    # Update fields
    for key, value in appointment_data.dict(exclude_unset=True).items():
        setattr(appointment, key, value)

    db.commit()
    db.refresh(appointment)

    return appointment
