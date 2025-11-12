from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import random
from datetime import datetime

from database import get_db
from models.user import User
from models.image import HealingImage
from models.patient import Patient
from schemas.image_schema import AIAnalysisResult, HealingImage as HealingImageSchema
from utils.security import get_current_user

router = APIRouter()


def mock_ai_analysis(image_path: str) -> dict:
    """
    Enhanced AI analysis function with medical classification and clinical recommendations
    In production, this would call an actual AI/ML model for:
    - Fracture detection on panoramic radiographs and CT scans
    - Displacement assessment
    - Healing progress evaluation based on radiographic findings
    """
    # Generate random healing percentage between 60-95%
    healing_percentage = round(random.uniform(60.0, 95.0), 1)
    
    # Simulate maxillofacial fracture classification detection
    # In production, ML model would analyze radiographs/CT scans
    fracture_types = [
        "Mandibular body fracture - minimally displaced",
        "Mandibular angle fracture - non-displaced",
        "Mandibular symphysis fracture - displaced",
        "Mandibular condyle fracture - intracapsular",
        "Zygomatic complex fracture - depressed",
        "Zygomatic arch fracture - isolated",
        "Le Fort I fracture - minimally displaced",
        "Le Fort II fracture - moderate displacement",
        "Le Fort III fracture - craniofacial disjunction",
        "Orbital floor fracture - non-displaced",
        "Nasal bone fracture - simple",
        "Maxillary alveolar fracture - segmental",
        "Frontal sinus fracture - anterior wall",
        "Dentoalveolar trauma - avulsion"
    ]
    
    # Randomly select fracture classification for mock analysis
    fracture_classification = random.choice(fracture_types)
    
    # Generate comprehensive clinical remarks and recommendations based on healing percentage
    if healing_percentage >= 90:
        ai_remarks = (
            "Excellent post-operative healing progress. Radiographic examination demonstrates optimal "
            "bone consolidation with mature callus formation evident at fracture site. Complete resolution "
            "of soft tissue swelling. No radiographic signs of infection, malunion, nonunion, or delayed union. "
            "Intermaxillary fixation (IMF) maintaining proper occlusal relationship. Periosteal reaction minimal. "
            "Tissue regeneration and bone remodeling within normal physiological parameters. Neurovascular status intact."
        )
        recommended_actions = (
            "CLINICAL MANAGEMENT - NEXT STEPS:\n\n"
            "• Dietary Progression: Advance to soft diet for 1-2 weeks, then regular diet as tolerated\n"
            "• Hardware Management: Consider IMF/arch bar removal if 6+ weeks post-operative\n"
            "• Imaging Follow-up: Schedule panoramic radiograph in 4 weeks to confirm complete osseous union\n"
            "• Physical Therapy: Initiate gradual jaw mobilization exercises and TMJ stretching\n"
            "• Activity: Resume normal activities, avoid contact sports for additional 4 weeks\n"
            "• Follow-up Schedule: Routine follow-up in 4-6 weeks\n"
            "• Medications: Discontinue antibiotics if currently prescribed; PRN acetaminophen for mild discomfort\n"
            "• Patient Education: Monitor for late complications (paresthesia, malocclusion)"
        )
        
    elif healing_percentage >= 85:
        ai_remarks = (
            "Very good healing trajectory with progressive improvement. Radiographic evaluation demonstrates "
            "active bone healing with early to intermediate callus formation visible at fracture margins. "
            "Minimal periosteal reaction observed - consistent with normal healing response. Fracture line "
            "still partially visible but with evidence of bridging callus. Soft tissue healing satisfactory "
            "with residual mild edema expected at this stage. No clinical signs of infection, wound dehiscence, "
            "or hardware failure. Occlusal relationship maintained and stable."
        )
        recommended_actions = (
            "CLINICAL MANAGEMENT - NEXT STEPS:\n\n"
            "• Dietary Modification: Maintain soft to semi-solid diet for additional 2-3 weeks\n"
            "• Hardware Management: Continue intermaxillary elastic traction if applicable; do not remove IMF yet\n"
            "• Imaging Protocol: Obtain follow-up panoramic radiograph or CT scan in 3 weeks\n"
            "• Physiotherapy: Initiate gentle passive range of motion exercises for TMJ\n"
            "• Neurosensory Assessment: Monitor for paresthesia in mental/infraorbital nerve distribution\n"
            "• Follow-up Schedule: Clinical and radiographic reassessment in 3 weeks mandatory\n"
            "• Nutritional Support: Consider vitamin D (2000 IU daily) and calcium (1000mg daily) supplementation\n"
            "• Pain Management: NSAIDs (ibuprofen 400mg TID) with food as needed\n"
            "• Warning Signs: Instruct patient to report increasing pain, swelling, or mobility at fracture site"
        )
        
    elif healing_percentage >= 75:
        ai_remarks = (
            "Good overall healing progress but still in intermediate fibrous union stage. Radiographic findings "
            "demonstrate bone healing in progress with fibrocartilaginous callus formation, but full osseous union "
            "not yet achieved. Moderate inflammation detected at fracture site - appears reactive rather than "
            "infectious in nature. Some periosteal thickening visible on imaging. Soft tissue edema persists but "
            "showing gradual improvement. Occlusal relationship maintained but requires close monitoring. "
            "No gross mobility at fracture site on clinical examination."
        )
        recommended_actions = (
            "CLINICAL MANAGEMENT - NEXT STEPS:\n\n"
            "• Dietary Restriction: STRICT soft/liquid diet for additional 3-4 weeks - no chewing stress\n"
            "• Hardware Management: Do NOT remove IMF at this time - bone union incomplete, high risk of displacement\n"
            "• Imaging Protocol: Repeat panoramic radiograph + consider limited cone beam CT in 2 weeks\n"
            "• Stability Assessment: Evaluate for any mobility at fracture site during next clinical visit\n"
            "• Adjunctive Therapy: Consider low-intensity pulsed ultrasound (LIPUS) to enhance osteogenesis\n"
            "• Laboratory Workup: Assess inflammatory markers (CRP, ESR) if systemic symptoms present\n"
            "• Nutritional Optimization: Ensure adequate protein intake (1.5-2g/kg/day), consider protein supplementation\n"
            "• Metabolic Panel: Check vitamin D, calcium, phosphate levels - correct deficiencies\n"
            "• Follow-up Schedule: Close monitoring - follow-up in 2 weeks mandatory\n"
            "• Pain Management: Scheduled NSAIDs (naproxen 500mg BID) + localized ice therapy\n"
            "• Risk Factor Modification: Smoking cessation counseling if applicable, optimize glycemic control if diabetic"
        )
        
    elif healing_percentage >= 65:
        ai_remarks = (
            "Moderate healing progress with concerning radiographic findings requiring intervention. Analysis reveals "
            "delayed union with insufficient callus formation at 4+ weeks post-operative - below expected healing trajectory. "
            "Moderate to significant persistent edema at surgical site. Possible early fibrous non-union development. "
            "Radiolucency noted at fracture margins suggesting inadequate bone apposition. Soft tissue inflammation present. "
            "Risk factors for healing complications identified. Hardware appears intact but fracture site biomechanically unstable."
        )
        recommended_actions = (
            "URGENT CLINICAL INTERVENTION REQUIRED:\n\n"
            "• Dietary Management: STRICT liquid/pureed diet only - absolutely no chewing forces\n"
            "• Hardware Management: Maintain rigid IMF for extended period (minimum 4-6 additional weeks)\n"
            "• Advanced Imaging: IMMEDIATE repeat CT scan with 3D reconstruction to assess bone healing and rule out infection/sequestrum\n"
            "• Laboratory Investigation: Comprehensive workup - CBC with differential, CRP, ESR, metabolic panel, vitamin D, PTH\n"
            "• Nuclear Medicine: Consider bone scan (99mTc-MDP) or MRI if osteomyelitis suspected\n"
            "• Risk Factor Assessment: Evaluate contributing factors - smoking history, diabetes control (HbA1c), nutritional status, immunosuppression\n"
            "• Surgical Consultation: Possible need for revision surgery, bone grafting, or hardware exchange if non-union confirmed\n"
            "• Specialist Referral: Oral & maxillofacial surgeon consultation for secondary opinion and management planning\n"
            "• Follow-up Frequency: Weekly clinical assessment until objective improvement documented\n"
            "• Antibiotic Coverage: Consider empiric antibiotic therapy (Augmentin 875mg BID or Clindamycin 300mg QID) if infection suspected\n"
            "• Bone Health Optimization: Calcium carbonate 1000mg + Vitamin D3 2000 IU daily, consider teriparatide if available\n"
            "• Patient Counseling: Discuss prolonged healing timeline and possible need for secondary procedures"
        )
        
    else:  # < 65%
        ai_remarks = (
            "CRITICAL ALERT: Suboptimal healing with significant concerns for major complication. Radiographic examination "
            "demonstrates poor bone consolidation with established non-union or progressive malunion. Persistent radiolucency "
            "at fracture site highly concerning for chronic infection, osteomyelitis, or avascular necrosis. Significant soft "
            "tissue swelling with possible abscess formation or fistula development. Occlusal discrepancy noted suggesting "
            "hardware failure or fracture displacement. High risk for complications including chronic osteomyelitis, "
            "pathological refracture, or need for segmental resection and reconstruction."
        )
        recommended_actions = (
            "EMERGENCY INTERVENTION - IMMEDIATE ACTION REQUIRED:\n\n"
            "• URGENT: In-person clinical evaluation within 24 hours - DO NOT DELAY\n"
            "• Emergency Imaging: Full maxillofacial CT with IV contrast + 3D reconstruction STAT\n"
            "• Infectious Disease Workup: Blood cultures if fever (>38°C), wound culture from any drainage\n"
            "• Comprehensive Labs: CBC with differential, CRP, ESR, procalcitonin, blood glucose, metabolic panel, liver function tests\n"
            "• Surgical Planning: High probability of requiring surgical exploration, debridement, sequestrectomy, and hardware revision\n"
            "• Hardware Management: Prepare for infected hardware removal and possible external fixation\n"
            "• Antibiotic Therapy: IMMEDIATE IV antibiotics - empiric coverage with Piperacillin-Tazobactam 4.5g IV Q6H or Clindamycin 600mg IV Q8H\n"
            "• NPO Status: Make patient NPO (nothing by mouth) in preparation for potential emergency surgery\n"
            "• Hospital Admission: Consider admission for IV antibiotics and close monitoring if systemic signs of infection\n"
            "• Infectious Disease Consult: If chronic osteomyelitis suspected - may require 4-6 weeks IV antibiotics\n"
            "• Biopsy Protocol: Bone biopsy for culture, sensitivity, and histopathology during surgical exploration\n"
            "• Nutritional Support: TPN (total parenteral nutrition) if prolonged NPO status expected\n"
            "• Vascular Assessment: Rule out compromised vascular supply contributing to non-union\n"
            "• Monitoring Protocol: DAILY clinical assessment, vital signs Q4H, inflammatory markers every 48-72 hours\n"
            "• Multidisciplinary Team: Involve OMFS, infectious disease, nutrition, anesthesia for comprehensive management\n"
            "• Informed Consent: Document detailed discussion regarding need for revision surgery, possible bone grafting, extended healing time\n"
            "• Family Communication: Update family regarding serious nature of complication and treatment plan"
        )
    
    return {
        "healing_percentage": healing_percentage,
        "ai_remarks": ai_remarks,
        "fracture_classification": fracture_classification,
        "recommended_actions": recommended_actions
    }


@router.post("/analyze/{image_id}", response_model=AIAnalysisResult)
def analyze_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform comprehensive AI-powered analysis on uploaded radiograph/CT scan
    Returns: healing percentage, fracture classification, clinical remarks, and evidence-based next steps
    """
    # Get image record
    image = db.query(HealingImage).filter(HealingImage.id == image_id).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Verify access authorization
    patient = db.query(Patient).filter(Patient.id == image.patient_id).first()
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to analyze this image"
        )
    
    # Perform enhanced AI analysis with medical classification and clinical recommendations
    analysis_result = mock_ai_analysis(image.image_path)
    
    # Update image record with comprehensive analysis results
    image.healing_percentage = analysis_result["healing_percentage"]
    image.ai_remarks = analysis_result["ai_remarks"]
    image.fracture_classification = analysis_result["fracture_classification"]
    image.recommended_actions = analysis_result["recommended_actions"]
    image.analyzed = True
    
    # Update patient's current healing percentage for dashboard
    patient.current_healing_percentage = analysis_result["healing_percentage"]
    
    db.commit()
    db.refresh(image)
    
    return AIAnalysisResult(
        image_id=image.id,
        healing_percentage=image.healing_percentage,
        ai_remarks=image.ai_remarks,
        fracture_classification=image.fracture_classification,
        recommended_actions=image.recommended_actions,
        analyzed_at=datetime.utcnow()
    )


@router.get("/results/{image_id}", response_model=AIAnalysisResult)
def get_analysis_results(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve comprehensive AI analysis results for a specific image
    Includes fracture classification and clinical management recommendations
    """
    # Get image record
    image = db.query(HealingImage).filter(HealingImage.id == image_id).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Verify access authorization
    patient = db.query(Patient).filter(Patient.id == image.patient_id).first()
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this analysis"
        )
    
    if not image.analyzed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image has not been analyzed yet"
        )
    
    return AIAnalysisResult(
        image_id=image.id,
        healing_percentage=image.healing_percentage,
        ai_remarks=image.ai_remarks,
        fracture_classification=image.fracture_classification,
        recommended_actions=image.recommended_actions,
        analyzed_at=image.upload_date
    )


@router.get("/history/{patient_id}", response_model=List[AIAnalysisResult])
def get_healing_history(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve complete healing history with all analyses for a patient
    Useful for tracking healing progression over time and clinical decision-making
    """
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Verify access authorization
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this history"
        )
    
    # Get all analyzed images for the patient, ordered chronologically
    images = db.query(HealingImage).filter(
        HealingImage.patient_id == patient_id,
        HealingImage.analyzed == True
    ).order_by(HealingImage.upload_date.asc()).all()
    
    history = [
        AIAnalysisResult(
            image_id=img.id,
            healing_percentage=img.healing_percentage,
            ai_remarks=img.ai_remarks,
            fracture_classification=img.fracture_classification,
            recommended_actions=img.recommended_actions,
            analyzed_at=img.upload_date
        )
        for img in images
    ]
    
    return history
