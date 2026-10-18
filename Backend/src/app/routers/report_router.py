from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Response, Body
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List
import os
import io
from pydantic import BaseModel
from ..controllers.report_controller import generate_evaluation_report, generate_pdf_report
from ..db.session import get_db
from sqlalchemy.orm import Session

class FilePathsRequest(BaseModel):
    file_paths: List[str]

router = APIRouter(
    prefix="/api/reports",
    tags=["reports"],
    responses={404: {"description": "Not found"}},
) 

@router.post("/upload-files", response_model=Dict[str, Any])
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload PDF files for evaluation.
    
    This endpoint accepts multiple PDF file uploads and saves them to a temporary
    location for processing by the reassessment agent.
    """
    try:
        # Create a temporary directory for the uploaded files
        temp_dir = os.path.join(os.getcwd(), "uploads")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save the uploaded files
        file_paths = []
        for file in files:
            # Check file type
            if not file.filename.lower().endswith(".pdf"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} is not a PDF file"
                )
            
            # Save the file
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as f:
                f.write(await file.read())
            
            file_paths.append(file_path)
        
        return {
            "status": "success",
            "message": f"{len(file_paths)} files uploaded successfully",
            "data": {
                "file_paths": file_paths
            }
        }
        
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading files: {str(e)}"
        )


@router.post("/generate", response_model=Dict[str, Any])
async def generate_report(request: FilePathsRequest = Body(...)):
    """
    Generate an evaluation report from PDF files.
    
    This endpoint accepts a list of file paths to PDF files, processes them with the
    reassessment agent, and returns the evaluation report in markdown format.
    """
    try:
        # Generate the evaluation report
        result = await generate_evaluation_report(request.file_paths)
        
        return result
        
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )

@router.post("/generate-pdf", response_class=StreamingResponse)
async def generate_pdf(request: FilePathsRequest = Body(...)):
    """
    Generate an evaluation report from PDF files and return it as a PDF.
    
    This endpoint accepts a list of file paths to PDF files, processes them with the
    reassessment agent, and returns the evaluation report as a PDF file.
    """
    try:
        # Generate the evaluation report
        result = await generate_evaluation_report(request.file_paths)
        
        # Convert the markdown report to PDF
        pdf_content = await generate_pdf_report(result["data"])
        
        # Return the PDF as a streaming response
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=evaluation_report.pdf"
            }
        )
        
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF report: {str(e)}"
        )

@router.post("/upload-and-generate", response_model=Dict[str, Any])
async def upload_and_generate(files: List[UploadFile] = File(...)):
    """
    Upload PDF files and generate an evaluation report in a single request.
    
    This endpoint accepts multiple PDF file uploads, processes them with the
    reassessment agent, and returns the evaluation report in markdown format.
    """
    try:
        # Create a temporary directory for the uploaded files
        temp_dir = os.path.join(os.getcwd(), "uploads")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save the uploaded files
        file_paths = []
        for file in files:
            # Check file type
            if not file.filename.lower().endswith(".pdf"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} is not a PDF file"
                )
            
            # Save the file
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as f:
                f.write(await file.read())
            
            file_paths.append(file_path)
        
        # Generate the evaluation report
        result = await generate_evaluation_report(file_paths)
        
        return result
        
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )

@router.post("/upload-and-generate-pdf", response_class=StreamingResponse)
async def upload_and_generate_pdf(files: List[UploadFile] = File(...)):
    """
    Upload PDF files and generate an evaluation report as a PDF in a single request.
    
    This endpoint accepts multiple PDF file uploads, processes them with the
    reassessment agent, and returns the evaluation report as a PDF file.
    """
    try:
        # Create a temporary directory for the uploaded files
        temp_dir = os.path.join(os.getcwd(), "uploads")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save the uploaded files
        file_paths = []
        for file in files:
            # Check file type
            if not file.filename.lower().endswith(".pdf"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} is not a PDF file"
                )
            
            # Save the file
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as f:
                f.write(await file.read())
            
            file_paths.append(file_path)
        
        # Generate the evaluation report
        result = await generate_evaluation_report(file_paths)
        
        # Convert the markdown report to PDF
        pdf_content = await generate_pdf_report(result["data"])
        
        # Return the PDF as a streaming response
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=evaluation_report.pdf"
            }
        )
        
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF report: {str(e)}"
        )