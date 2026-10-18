from fastapi import HTTPException, status
import os
import logging
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any
from ..services.reassesment_agent import create_workflow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def generate_evaluation_report(file_paths: List[str]) -> Dict[str, Any]:
    """
    Generate an evaluation report using the reassessment agent workflow.
    
    Args:
        file_paths: List of paths to the PDF files to process
        
    Returns:
        Dictionary containing the final evaluation report
    """
    try:
        # Create and run the workflow
        app = create_workflow()
        inputs = {"file_paths": file_paths}
        result = app.invoke(inputs)
        
        # Extract the final evaluation report
        if "final_evaluation_report" not in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate evaluation report"
            )
        
        return {
            "status": "success",
            "message": "Evaluation report generated successfully",
            "data": result["final_evaluation_report"]
        }
        
    except Exception as e:
        logger.error(f"Error generating evaluation report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating evaluation report: {str(e)}"
        )

async def generate_pdf_report(markdown_content: str) -> bytes:
    """
    Convert markdown content to PDF using reportlab.
    
    Args:
        markdown_content: The markdown content to convert to PDF
        
    Returns:
        PDF file as bytes
    """
    try:
        from io import BytesIO
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
        from reportlab.lib import colors
        
        # Convert markdown to HTML
        html_content = markdown.markdown(markdown_content)
        
        # Create a buffer for the PDF
        buffer = BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Add custom styles
        styles.add(ParagraphStyle(
            name='Heading1',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        ))
        
        styles.add(ParagraphStyle(
            name='Heading2',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.darkblue
        ))
        
        styles.add(ParagraphStyle(
            name='Normal',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=8
        ))
        
        # Split the HTML content into lines
        lines = html_content.split('\n')
        
        # Process the lines and create PDF elements
        elements = []
        
        # Add title
        elements.append(Paragraph("Student Evaluation Report", styles['Title']))
        elements.append(Spacer(1, 12))
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Process headings
            if line.startswith('<h1>'):
                text = line.replace('<h1>', '').replace('</h1>', '')
                elements.append(Paragraph(text, styles['Heading1']))
            elif line.startswith('<h2>'):
                text = line.replace('<h2>', '').replace('</h2>', '')
                elements.append(Paragraph(text, styles['Heading2']))
            elif line.startswith('<h3>'):
                text = line.replace('<h3>', '').replace('</h3>', '')
                elements.append(Paragraph(text, styles['Heading3']))
            elif line.startswith('<p>'):
                text = line.replace('<p>', '').replace('</p>', '')
                elements.append(Paragraph(text, styles['Normal']))
            elif line.startswith('<ul>'):
                # Skip the ul tag, will process li tags individually
                pass
            elif line.startswith('<li>'):
                text = '• ' + line.replace('<li>', '').replace('</li>', '')
                elements.append(Paragraph(text, styles['Normal']))
            elif line.startswith('<strong>'):
                text = line.replace('<strong>', '').replace('</strong>', '')
                elements.append(Paragraph(text, styles['Heading3']))
            else:
                # Default to normal paragraph
                elements.append(Paragraph(line, styles['Normal']))
            
            elements.append(Spacer(1, 6))
        
        # Build the PDF
        doc.build(elements)
        
        # Get the PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF report: {str(e)}"
        )