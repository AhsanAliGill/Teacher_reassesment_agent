from fastapi import HTTPException, UploadFile, status, Depends
from typing import Dict, List, Optional, Any
import os
import logging
import json
import pathlib
import re
import io
# src/app/controllers/gemini_controller.py
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from sqlalchemy.orm import Session

# Document processing libraries
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document
except ImportError:
    Document = None 

# Import database and models
from ..db.session import get_db
from ..models.assessment import Assessment, Question, AssessmentCreate, QuestionCreate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash')  # or 'gemini-pro', etc.

MODEL_NAME = "gemini-2.5-flash"


def extract_content_from_file(file: UploadFile) -> bytes:
    """Extract bytes from an uploaded file."""
    try:
        content = file.file.read()
        return content
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading file: {str(e)}"
        )

def extract_text_from_pdf(content: bytes) -> str:
    """Extract text from PDF content."""
    if PyPDF2 is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PyPDF2 library not installed. Please install it to process PDF files."
        )
    
    try:
        pdf_file = io.BytesIO(content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing PDF file: {str(e)}"
        )

def extract_text_from_docx(content: bytes) -> str:
    """Extract text from DOCX content."""
    if Document is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="python-docx library not installed. Please install it to process DOCX files."
        )
    
    try:
        docx_file = io.BytesIO(content)
        doc = Document(docx_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing DOCX file: {str(e)}"
        )

async def process_with_gemini(file: UploadFile, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Process the uploaded file with Gemini, extract information, and save to database.
    Args:
        file: The uploaded file to process
        db: Database session
    Returns:
        Dict containing the saved assessment data
    """
    try:
        content = extract_content_from_file(file)
        file_extension = os.path.splitext(file.filename)[1].lower()
        image_extensions = {".jpg", ".jpeg", ".png"}
        document_extensions = {'.pdf', '.docx', '.txt'}

        if file_extension in image_extensions:
            # For images, send as a part (if supported by Gemini API)
            prompt = (
                "Analyze the following image and extract the following information in JSON format: "
                "Return ONLY a valid JSON object with the following structure: "
                '{"subject_name": ..., "questions": [{"question_text": ..., "marks": ...}]}. '
                "Do not include any explanation or extra text."
            )
            response = model.generate_content(
                [prompt, {"mime_type": file.content_type, "data": content}],
                generation_config=GenerationConfig(
                    temperature=0.3,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2048,
                )
            )
        elif file_extension in document_extensions:
            # Extract text based on file type
            if file_extension == '.pdf':
                decoded_content = extract_text_from_pdf(content)
            elif file_extension == '.docx':
                decoded_content = extract_text_from_docx(content)
            elif file_extension == '.txt':
                try:
                    decoded_content = content.decode('utf-8')
                except Exception:
                    decoded_content = content.decode('latin1')  # fallback
            else:
                # Fallback for other text-based files
                try:
                    decoded_content = content.decode('utf-8')
                except Exception:
                    decoded_content = content.decode('latin1')  # fallback
            
            prompt = (
                "Analyze the following content and extract assessment information in JSON format. "
                "You MUST provide a subject_name - if you cannot determine the subject from the content, "
                "infer it from the filename or content context, or use 'General Assessment' as fallback. "
                "Extract all questions with their marks/points. "
                "Return ONLY a valid JSON object with this exact structure: "
                '{"subject_name": "Subject Name Here", "questions": [{"question_text": "Question text", "marks": 5}]}. '
                "Do not include any explanation or extra text.\n\nContent to analyze:\n" + decoded_content
            )
            response = model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    temperature=0.3,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2048,
                )
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_extension}. Supported types: {', '.join(sorted(image_extensions | document_extensions))}"
            )

        # Parse the response
        try:
            raw_text = response.text.strip()
            logger.info(f"Raw Gemini response: {raw_text}")
            
            # Remove code block markers if present
            if raw_text.startswith("```"):
                # Remove the first line (```json or ```)
                raw_text = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text)
                # Remove the last line if it's ```
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3].strip()
            
            logger.info(f"Cleaned response for JSON parsing: {raw_text}")
            result = json.loads(raw_text)
            logger.info(f"Parsed JSON result: {result}")
            # Create and save the assessment to database
            # Ensure subject_name is never None or empty
            subject_name = result.get("subject_name")
            if not subject_name or subject_name.strip() == "":
                # Try to infer subject from filename
                filename_without_ext = os.path.splitext(file.filename)[0]
                if filename_without_ext:
                    subject_name = filename_without_ext.replace("-", " ").replace("_", " ").title()
                else:
                    subject_name = "Unknown Subject"
                logger.warning(f"Subject name not found in Gemini response, using filename-based fallback: {subject_name}")
            
            assessment_data = {
                "subject_name": subject_name,
                "file_name": file.filename,
                "questions": [
                    {"question_text": q["question_text"], "marks": float(q.get("marks", 0))}
                    for q in result.get("questions", [])
                ]
            }
            return await save_assessment(assessment_data, db)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            logger.error(f"Response content: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error parsing the response from Gemini. Raw response: {response.text}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in process_with_gemini: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )

async def save_assessment(assessment_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Save assessment data to the database.
    
    Args:
        assessment_data: Dictionary containing assessment data
        db: Database session
        
    Returns:
        Dictionary containing the saved assessment data
    """
    try:
        # Create questions
        questions = [
            Question(
                question_text=q["question_text"],
                marks=q["marks"]
            )
            for q in assessment_data["questions"]
        ]
        
        # Create assessment
        assessment = Assessment(
            subject_name=assessment_data["subject_name"],
            file_name=assessment_data.get("file_name"),
            questions=questions
        )
        
        # Save to database
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        
        # Prepare response
        return {
            "id": assessment.id,
            "subject_name": assessment.subject_name,
            "file_name": assessment.file_name,
            "created_at": assessment.created_at.isoformat(),
            "questions": [
                {
                    "id": q.id,
                    "question_text": q.question_text,
                    "marks": q.marks,
                    "created_at": q.created_at.isoformat()
                }
                for q in assessment.questions
            ]
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving assessment to database: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error saving assessment to database"
        )
