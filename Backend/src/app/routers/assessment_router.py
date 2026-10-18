import os
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from typing import Dict, Any
from ..controllers.gemini_controller import process_with_gemini
from ..db.session import get_db
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/api/assessments",
    tags=["assessments"],
    responses={404: {"description": "Not found"}},
) 

@router.post("/process-file", response_model=Dict[str, Any])
async def process_assessment_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Process an assessment file and extract structured information using Gemini.
    
    This endpoint accepts a file upload, processes it with Gemini, and returns
    the extracted subject name, questions, and marks.
    
    Supported file types: .txt, .pdf, .docx
    """
    # Check file type
    allowed_extensions = {".jpg", ".jpeg", ".png"}
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed types: {', '.join(sorted(allowed_extensions))}"
        )
    
    try:
        # Process the file with Gemini
        result = await process_with_gemini(file, db)
        
        # Validate the response structure
        if not all(key in result for key in ["subject_name", "questions"]):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected response format from Gemini"
            )
            
        return {
            "status": "success",
            "message": "File processed successfully",
            "data": result
        }
        
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )
