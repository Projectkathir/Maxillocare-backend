
"""
Gemini AI Service for Maxillocare Dental Image Analysis
Specialized for maxillofacial surgery follow-up and dental diagnostics
"""

import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL
from pathlib import Path
from typing import Dict, Optional
import logging
import json
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiAnalysisService:
    """
    Dental and maxillofacial image analysis using Google Gemini Vision API
    Supports: X-rays, CT scans, CBCT, intraoral photos, clinical images
    """
    
    def __init__(self):
        """Initialize Gemini client with API key validation"""
        if not GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError(
                "GEMINI_API_KEY is required. Please set it in Render environment variables or .env file"
            )
        
        # Configure Gemini with API key
        genai.configure(api_key=GEMINI_API_KEY)
        self.model_name = GEMINI_MODEL
        logger.info(f"✅ Gemini AI Service initialized with model: {self.model_name}")
    
    def analyze_dental_image(self, image_path: str) -> Dict:
        """
        Analyze dental/maxillofacial images using Gemini Vision API
        
        Args:
            image_path: Absolute or relative path to uploaded image file
            
        Returns:
            Dict containing:
                - healing_percentage (float): 0-100 healing progress
                - fracture_classification (str): Medical diagnosis
                - ai_remarks (str): Clinical observations
                - recommended_actions (str): Treatment recommendations
                
        Raises:
            FileNotFoundError: If image file doesn't exist
            Exception: For Gemini API errors
        """
        
        try:
            # Validate image file exists
            image_file = Path(image_path)
            if not image_file.exists():
                logger.error(f"❌ Image file not found: {image_path}")
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            logger.info(f"📤 Uploading image to Gemini: {image_file.name}")
            
            # Upload image to Gemini
            uploaded_file = genai.upload_file(path=str(image_file))
            logger.info(f"✅ Image uploaded successfully: {uploaded_file.name}")
            
            # Create specialized dental analysis prompt
            prompt = self._create_dental_prompt()
            
            # Initialize Gemini model
            model = genai.GenerativeModel(self.model_name)
            
            # Generate analysis
            logger.info("🔍 Generating AI analysis...")
            response = model.generate_content([uploaded_file, prompt])
            
            # Extract text from response
            analysis_text = response.text
            logger.info("✅ Analysis completed successfully")
            
            # Parse structured response
            result = self._parse_analysis_response(analysis_text)
            
            return result
            
        except FileNotFoundError:
            raise
            
        except Exception as e:
            logger.error(f"❌ Gemini API error: {str(e)}")
            raise Exception(f"AI analysis failed: {str(e)}")
    
    def _create_dental_prompt(self) -> str:
        """
        Create specialized prompt for dental/maxillofacial image analysis
        Optimized for Gemini Vision API
        """
        return """
You are an expert maxillofacial surgeon and dental radiologist with 20+ years of clinical experience.
Analyze this dental/oral image carefully and provide a detailed clinical assessment.

**Supported Image Types:** 
- Panoramic X-rays (OPG)
- CT scans (CBCT)
- Intraoral radiographs
- Clinical photographs
- Post-operative healing images

**CRITICAL INSTRUCTIONS:**
1. Provide response in EXACT JSON format below
2. Use precise medical terminology
3. Prioritize patient safety in recommendations
4. If image quality is poor, note it in clinical_notes

**REQUIRED JSON FORMAT:**
{
    "image_type": "panoramic_xray|ct_scan|cbct|clinical_photo|intraoral|unclear",
    "healing_percentage": 85.0,
    "primary_diagnosis": "Brief primary finding (max 100 chars)",
    "fracture_classification": "Specific classification OR 'No fracture detected' OR 'Not applicable'",
    "detailed_findings": [
        "Finding 1 with anatomical location",
        "Finding 2 with severity description",
        "Finding 3 with healing status (if post-op)"
    ],
    "severity": "normal|mild|moderate|severe|critical",
    "recommended_actions": [
        "Action 1 (specific and actionable)",
        "Action 2 (with timeframe if applicable)",
        "Action 3 (follow-up requirements)"
    ],
    "clinical_notes": "Additional observations, image quality notes, or differential diagnoses"
}

**Assessment Guidelines:**

For Trauma Cases:
- Classify fractures: Le Fort I/II/III, mandibular (body/angle/symphysis/condyle), zygomatic, orbital, maxillary
- Assess displacement: non-displaced, minimally displaced, significantly displaced
- Check for comminution, hardware placement (if post-op)

For Post-Operative Cases:
- Healing percentage: 0-30% (early), 31-60% (intermediate), 61-85% (good), 86-100% (complete)
- Bone union quality: no union, fibrous union, partial union, solid union
- Hardware status: intact, loosened, fractured, infection signs

For Dental Pathology:
- Caries extent and location
- Periodontal bone loss
- Impacted teeth positioning
- Periapical lesions
- TMJ abnormalities (if visible)

**Severity Classification:**
- Normal: No pathology detected
- Mild: Minor findings, routine follow-up
- Moderate: Requires treatment planning, 2-4 weeks follow-up
- Severe: Urgent intervention needed, 1 week follow-up
- Critical: Emergency care required, immediate evaluation

**Safety Priority:**
If uncertain about diagnosis, indicate "further clinical correlation required" in clinical_notes.
Always err on the side of caution in severity assessment.

Analyze the uploaded image now and provide your assessment in the exact JSON format above.
"""
    
    def _parse_analysis_response(self, analysis_text: str) -> Dict:
        """
        Parse Gemini response and extract structured data
        Handles both JSON and markdown-wrapped JSON responses
        
        Args:
            analysis_text: Raw text response from Gemini
            
        Returns:
            Formatted dict for database storage
        """
        
        try:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'``````', analysis_text, re.DOTALL)
            if json_match:
                analysis_json = json.loads(json_match.group(1))
            else:
                # Try direct JSON parse
                analysis_json = json.loads(analysis_text)
            
            # Validate and sanitize healing percentage
            healing_pct = float(analysis_json.get('healing_percentage', 50.0))
            healing_pct = max(0.0, min(100.0, healing_pct))  # Clamp to 0-100
            
            # Format detailed findings as bullet points
            findings = analysis_json.get('detailed_findings', ['Analysis completed'])
            findings_text = '\n'.join([f"• {finding}" for finding in findings[:5]])  # Limit to 5
            
            # Format recommended actions
            actions = analysis_json.get('recommended_actions', ['Routine follow-up recommended'])
            actions_text = '\n'.join([f"• {action}" for action in actions[:5]])
            
            # Compile AI remarks
            ai_remarks = f"""PRIMARY DIAGNOSIS: {analysis_json.get('primary_diagnosis', 'Assessment completed')}

SEVERITY: {analysis_json.get('severity', 'unknown').upper()}

KEY FINDINGS:
{findings_text}

CLINICAL NOTES:
{analysis_json.get('clinical_notes', 'No additional notes')}"""
            
            # Format result for database
            result = {
                'healing_percentage': healing_pct,
                'fracture_classification': analysis_json.get('fracture_classification', 'Analysis completed'),
                'ai_remarks': ai_remarks,
                'recommended_actions': actions_text
            }
            
            logger.info(f"📊 Parsed analysis - Healing: {healing_pct}%, Severity: {analysis_json.get('severity', 'N/A')}")
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ Failed to parse JSON response: {e}")
            # Fallback: use raw text as clinical remarks
            return {
                'healing_percentage': 50.0,
                'fracture_classification': 'Manual review required',
                'ai_remarks': f"AI Analysis Output:\n{analysis_text[:800]}",  # Truncate long responses
                'recommended_actions': '• Clinical evaluation recommended\n• Manual review of AI output required'
            }
        
        except Exception as e:
            logger.error(f"❌ Error parsing analysis: {e}")
            raise


# Singleton instance for reuse across requests
try:
    gemini_service = GeminiAnalysisService()
except ValueError as e:
    logger.error(f"❌ Failed to initialize Gemini service: {e}")
    gemini_service = None
