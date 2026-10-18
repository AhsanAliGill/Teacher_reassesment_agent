import logging
from typing import Dict, List, Optional
from sqlmodel import Session, select
from fastapi import HTTPException, status

from ..db.session import get_db
from ..models.assessment import Assessment, Question

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_available_subjects(db: Session = None) -> List[str]:
    """
    Get a list of all available subject names in the database.
    
    Args:
        db: Database session (optional). If not provided, a new session will be created.
        
    Returns:
        List of subject names available in the database
    """
    try:
        # Create a new database session if not provided
        close_db = False
        if db is None:
            db = next(get_db())
            close_db = True
            
        # Query all distinct subject names
        statement = select(Assessment.subject_name).distinct()
        results = db.exec(statement).all()
        
        # Return the list of subject names
        return results
        
    except Exception as e:
        logger.error(f"Error retrieving available subjects: {str(e)}")
        return []
        
    finally:
        # Close the database session if we created it
        if close_db and db is not None:
            db.close()


def get_original_paper(subject_name: str) -> dict:
    """
    Tool to retrieve the original exam paper for a specific subject from the database.
    
    This is a synchronous wrapper around the async _get_original_paper function.
    """
    import asyncio
    import nest_asyncio
    
    # Apply nest_asyncio to allow running asyncio.run inside an existing event loop
    try:
        nest_asyncio.apply()
    except ImportError:
        logger.warning("nest_asyncio not installed. Async operations inside event loops may fail.")
    
    # Create a new event loop and run the async function
    try:
        return asyncio.run(_get_original_paper(subject_name))
    except RuntimeError as e:
        # If we're already in an event loop, use a different approach
        if "This event loop is already running" in str(e):
            try:
                # Try to get the current event loop
                loop = asyncio.get_event_loop()
                # Create a new task and run it to completion
                return loop.run_until_complete(_get_original_paper(subject_name))
            except Exception as inner_e:
                logger.error(f"Error running async function in existing event loop: {str(inner_e)}")
                # Fall back to dummy data
                return {
                    "message": "ERROR RETRIEVING PAPER",
                    "details": f"Error occurred while retrieving paper for '{subject_name}': {str(inner_e)}",
                    "questions": [
                        {"question": "Backpropagation and its purpose?", "marks": 10},
                        {"question": "Multiple linear regression differ from simple linear regression?", "marks": 10},
                        {"question": "Why fairness is important in data science?", "marks": 10},
                        {"question": "Considering data size, should we use Spark?", "marks": 10}
                    ]
                }
        else:
            # Re-raise other runtime errors
            raise

async def _get_original_paper(subject_name: str) -> dict:
    """
    Tool to retrieve the original exam paper for a specific subject from the database.
    
    This function queries the database for an assessment with the given subject name
    and returns its questions in a standardized format. If no assessment is found,
    or if an error occurs during database access, it falls back to returning
    predefined dummy data.

    Parameters:
        subject_name (str): The name of the subject to search for (e.g., "Data Science", "Machine Learning").
                           Case-sensitive and must match exactly with what's stored in the database.

    Returns:
        dict: A dictionary with the following structure:
            {
                "questions": [
                    {"question": "The full text of the question", "marks": 10},
                    {"question": "Another question", "marks": 15},
                    ...
                ]
            }
            Where each question is represented as a dictionary with:
            - "question": The text of the question (from question_text field)
            - "marks": The number of marks for the question (from marks field, converted to int)

    Database Details:
        - Queries the Assessment table filtered by subject_name
        - Accesses the related questions through the relationship
        - Maps question_text to "question" and marks to "marks" in the output
    
    Error Handling:
        - Returns dummy data if the subject is not found
        - Returns dummy data if any database error occurs
        - Logs appropriate warning/error messages
    
    Example:
        >>> get_original_paper("Data Science")
        {
            "questions": [
                {"question": "Explain neural networks", "marks": 10},
                {"question": "Describe decision trees", "marks": 5}
            ]
        }
    """
    print("✅ Tool has been invoked")
    
    try:
        # Get database session
        db = next(get_db())
        
        # Query the database for the assessment with the given subject name
        # Using case-insensitive comparison and improved fuzzy matching
        # First try exact match with ILIKE
        statement = select(Assessment).where(Assessment.subject_name.ilike(f"%{subject_name}%"))
        result = db.exec(statement).first()
        
        # If no result, try with more flexible matching by splitting the subject name
        if not result:
            # Split the subject name into parts and try to match any part
            parts = subject_name.split()
            for part in parts:
                if len(part) > 2:  # Only use parts with more than 2 characters to avoid matching too broadly
                    statement = select(Assessment).where(Assessment.subject_name.ilike(f"%{part}%"))
                    result = db.exec(statement).first()
                    if result:
                        logger.info(f"Found assessment using partial match '{part}' from '{subject_name}'")
                        break
        
        # Log the query result for debugging
        if result:
            logger.info(f"Found assessment for subject '{subject_name}' with ID: {result.id}")
            logger.info(f"Number of questions found: {len(result.questions)}")
        else:
            logger.warning(f"No assessment found for subject: '{subject_name}'")

        
        if not result:
            # If no assessment is found, return a more informative message
            logger.warning(f"No assessment found for subject: {subject_name}. Using dummy data.")
            return {
                "message": "NO ASSESSMENT FOUND",
                "details": f"Could not find an assessment matching '{subject_name}'. Please check the spelling or try with a different subject name.",
                "available_subjects": await get_available_subjects(db=db)
            }
        
        # Format the questions from the database
        try:
            # Check if questions exist
            if not result.questions:
                logger.warning(f"Assessment found for '{subject_name}', but it has no questions")
                # Return a more informative message if no questions are found
                return {
                    "message": "NO ASSESSMENT QUESTIONS FOUND",
                    "details": f"Assessment found for '{subject_name}', but it has no questions. Please check the assessment data.",
                    "available_subjects": await get_available_subjects(db=db)
                }
            
            # Process and format each question
            questions = []
            for q in result.questions:
                try:
                    # Convert marks to integer and handle potential conversion errors
                    marks = int(q.marks) if q.marks is not None else 0
                    
                    # Add formatted question to the list
                    questions.append({
                        "question": q.question_text,
                        "marks": marks
                    })
                    
                except (ValueError, TypeError) as e:
                    # Log error but continue processing other questions
                    logger.error(f"Error processing question {q.id}: {str(e)}")
            
            # Log success message
            logger.info(f"Successfully retrieved {len(questions)} questions for subject '{subject_name}'")
            
            # Return the formatted questions
            return {
                "questions": questions
            }
        except Exception as e:
            # Log the specific error when formatting questions
            logger.error(f"Error formatting questions: {str(e)}")
            # Return a more informative message
            return {
                "message": "ERROR FORMATTING QUESTIONS",
                "details": f"Error occurred while formatting questions for '{subject_name}': {str(e)}",
                "available_subjects": await get_available_subjects(db=db)
            }
        
    except Exception as e:
        # Log detailed error information
        logger.error(f"Error retrieving original paper for subject '{subject_name}': {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Return dummy data as fallback in case of error
        logger.info(f"Returning dummy data for subject '{subject_name}' due to error")
        return {
            "questions": [
                {"question": "Backpropagation and its purpose?", "marks": 10},
                {"question": "Multiple linear regression differ from simple linear regression?", "marks": 10},
                {"question": "Why fairness is important in data science?", "marks": 10},
                {"question": "Considering data size, should we use Spark?", "marks": 10}
            ]
        }
    finally:
        # Ensure proper cleanup of database resources
        try:
            if 'db' in locals() and db is not None:
                logger.debug("Closing database session")
                db.close()
                logger.debug("Database session closed successfully")
        except Exception as e:
            logger.error(f"Error closing database session: {str(e)}")
            # Don't re-raise the exception to avoid masking the original error