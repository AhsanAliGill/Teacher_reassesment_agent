from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END, START
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
import mimetypes
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import PromptTemplate
import pathlib
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt import ToolNode
from ..services.tool import get_original_paper
import json
import os
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash') 

# Define Pydantic models for structured output
class QuestionAnswer(BaseModel):
    question: str
    answer: str

class StudentResponse(BaseModel):
    student_name: str
    registration_no: str
    Subject: str
    questions: List[QuestionAnswer]

# Define the state structure
class AgentState(TypedDict):
    """State for the PDF extraction and evaluation workflow."""
    file_paths: List[str]
    gemini_responses: List[str]
    extracted_info: List[Dict[str, Any]]
    evaluation_report: List[Dict[str, Any]]
    evaluation_report_2: List[Dict[str, Any]]
    final_evaluation_report: List[Dict[str, Any]]
    original_questions: Dict[str, Any]
    messages: List[Any] # Use List[Any] to accommodate different message types
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",  # Use gemini-pro, not gemini-2.0-flash
    google_api_key="AIzaSyA4KHeA3EBHS31MYWqai5k-zi6hy9Y50Pk"  # Use env or actual string
)
llm2=ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",  # Use gemini-pro, not gemini-2.0-flash
    google_api_key="AIzaSyDpE0YqWRyEFe0NI-2vo1_Yoxl7hFczIxk"  # Use env or actual string
)
# Step 1: Call Gemini API for extraction (includes file loading)
def call_gemini(state: AgentState) -> AgentState:
    """Load PDF files and call Gemini API to extract structured information from each in parallel."""
    prompt = (
        """Extract the Registration No, Student Name, Subject Name, and a list of Questions with their corresponding Student Answers from the PDF.
    Ensure the output is a valid JSON string with the following structure:
    {
        "student_name": "string (extract the student's name, or 'Unknown' if not found)",
        "registration_no": "string (extract the registration number, or 'Unknown' if not found)",
        "Subject": "string (extract the subject name, or 'Unknown' if not found)",
        "questions": [
            {
                "question": "string (extract the question text or number, e.g., 'QUESTION NO 1')",
                "answer": "string (extract the student's answer, or 'No answer provided' if not found)"
            }
        ]
    }
    If any field cannot be extracted due to missing or unclear information in the PDF, use the default values specified above (e.g., 'Unknown' or 'No answer provided'). Ensure the JSON is valid and contains all required fields.
    """
    )
    try:
        client = genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        return {"gemini_responses": [f"Error initializing Gemini client: {str(e)}"], **state}

    def generate_content_for_file(file_path):
        try:
            filepath = pathlib.Path(file_path)
            if not filepath.exists():
                return f"Error: File not found: {file_path}"

            file_content = filepath.read_bytes()

            response = model.generate_content(
                contents=[
                    {"mime_type": "application/pdf", "data": file_content},
                    prompt
                ],
                generation_config=GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            try:
                json_response = json.loads(response.text)
                StudentResponse(**json_response)
                return response.text
            except Exception as e:
                return f"Error validating response for {file_path}: {str(e)}"
        except Exception as e:
            return f"Error processing file {file_path}: {str(e)}"

    responses = []
    with ThreadPoolExecutor() as executor:
        responses = list(executor.map(generate_content_for_file, state["file_paths"]))

    return {"gemini_responses": responses, **state}

# Step 2: Process Gemini responses
def process_response(state: AgentState) -> AgentState:
    """Process Gemini responses to extract structured information."""
    extracted_info = []
    for response in state["gemini_responses"]:
        try:
            if response.startswith("Error"):
                extracted_info.append({"error": response})
                continue
            data = json.loads(response)
            student_response = StudentResponse(**data)
            extracted_info.append(student_response.model_dump())  # Use model_dump instead of dict
        except Exception as e:
            extracted_info.append({"error": f"Failed to parse response: {str(e)}"})

    return {"extracted_info": extracted_info, **state}

# Step 3: Evaluate answers
from langchain_core.messages import HumanMessage

def evaluate_answers(state: AgentState) -> AgentState:
    print("\n📦 Current state contents:")
    print(json.dumps(dict(state), indent=2))

    # Compose the evaluation prompt
    prompt_template = """
You are an expert assistant tasked with evaluating student answers for an exam against an original question paper in a fair, accurate, and transparent manner using a structured chain-of-thought (CoT) reasoning process. Your goal is to assess each answer with a lenient approach, rewarding effort, relevance, and partial correctness while maintaining clarity and consistency. The evaluation should be supportive, allowing partial credit for relevant but incomplete answers and minimizing harsh penalties for minor errors or mismatches.

---

#### Instructions

1. **Retrieve the Original Question Paper**:
   - Use the `get_original_paper` tool with the subject from the `{extracted_info}` to fetch the original question paper, including question texts, correct answers, and associated marks.
   - Store the retrieved paper as the reference for evaluation.
   - If the tool fails to retrieve the paper, note this in the reasoning section, evaluate answers based on general Data Science expertise if possible, and assign conservative marks (e.g., low to mid-range) with an explanation.

2. **Analyze the Original Question Paper**:
   - For each question, extract:
     - **Question number** and **text**.
     - **Correct answer** (key concepts, phrases, or expected content based on Data Science expertise).
     - **Allocated marks** (indicating the expected depth of response).
   - Identify **key concepts** or phrases essential for a complete response (e.g., for a question on "backpropagation," key terms might include "gradient descent," "neural networks," "weight updates"). Use case-insensitive and semantic matching for flexibility.
   - Determine the **expected level of detail** based on marks:
     - **1–3 marks**: Brief, factual response with core points.
     - **4–7 marks**: Clear explanation with some supporting details or examples.
     - **8+ marks**: Detailed response with key concepts, allowing for minor omissions or simpler explanations.

3. **Process Student Answers**:
   - Iterate through the list of questions and answers provided for each student in the `{extracted_info}`.
   - If no answers are provided, assign minimal marks (e.g., 10% of allocated marks) for effort if any relevant keywords are present, and note the absence in the reasoning section.

4. **Match Student Questions to Original Questions**:
   - Map each student’s question (e.g., "QUESTION NO 1", "What is backpropagation?") to the corresponding question in the original paper using:
     - **Positional Matching**: Match the question number (e.g., "QUESTION NO 1" to the first question).
     - **Content-Based Matching**: Use semantic similarity (e.g., answers mentioning "neural networks" may match a backpropagation question) to confirm matches, allowing for typos (e.g., "backpropogation") or rephrased questions.
   - If no exact match is found, award partial marks (e.g., 20–50% of allocated marks) if the answer addresses related concepts in the subject area, noting: "Answer partially relevant to [related topic]."
   - If the student answers a different question (e.g., about "decision trees" instead of "backpropagation"), assign partial marks if the response demonstrates relevant Data Science knowledge, noting: "Answer addresses [related topic] but not the intended question."

5. **Evaluate Each Answer**:
   - Assess each answer based on **content validity**, **conceptual accuracy**, **completeness**, and **sufficiency** relative to the allocated marks, with a lenient approach that rewards effort and relevance.

   **Evaluation Criteria**:
   1. **Content Validity**:
      - **Relevance**: Award marks for answers that address the question or related concepts, even if partially off-topic. Completely irrelevant answers receive minimal marks (e.g., 10–20% of allocated marks).
      - **Factual Accuracy**: Prioritize core concepts over minor errors. Minor inaccuracies reduce marks slightly but do not result in 0.
      - **Coherence**: Accept understandable answers with minor clarity issues, reducing marks only for significant incoherence.
   2. **Conceptual Accuracy and Completeness**:
      - Identify **key concepts** required for a correct response.
      - List **concepts present** with examples or quotes (e.g., “The student mentions ‘gradient descent’ in backpropagation”).
      - List **missing or incorrect concepts**, but award partial marks for effort (e.g., “Omitted ‘weight updates’ but included other relevant ideas”).
   3. **Content Sufficiency and Quality**:
      - Evaluate **depth**, **clarity**, **structure**, **examples**, and **language** with flexibility:
        - **High-Mark Answers (60–100% of allocated marks)**:
          - **Depth**: Covers core concepts with clear explanations, even if not exhaustive.
          - **Technical Precision**: Mostly accurate terminology with minor errors allowed.
          - **Examples**: Includes basic examples or explanations to support points.
          - **Relevance**: Addresses the question with minimal tangents.
          - **Length**: Adequate length (e.g., a paragraph or two for high-mark questions).
          - **Structure**: Clear organization, even if simple.
        - **Mid-Mark Answers (30–59% of allocated marks)**:
          - **Depth**: Includes some relevant concepts but lacks detail.
          - **Examples**: Minimal or general examples.
          - **Relevance**: Partially addresses the question.
          - **Length**: Brief but relevant response.
          - **Structure**: Basic organization.
        - **Low-Mark Answers (0–29% of allocated marks)**:
          - **Depth**: Minimal relevant content or only keywords.
          - **Examples**: Absent or vague.
          - **Relevance**: Tangential or barely relevant.
          - **Length**: Very brief or incomplete.
          - **Structure**: Minimal but understandable.
      - **Language & Style**: Accept minor errors (e.g., typos, grammar) without significant penalties; prioritize clarity over perfection.
   4. **Mark Justification**:
      - Assign marks based on content quality, relevance, and effort, rewarding partial correctness.
      - Justify the score by referencing validity, concept coverage, and sufficiency (e.g., “Awarded 7/10 for covering ‘gradient descent’ but omitting ‘weight updates’”).

6. **Calculate Marks**:
   - Sum the marks awarded for each question to compute the student’s **obtained marks**.
   - Use the sum of marks from the original paper as the **total possible marks**.
   - For unmatched or unevaluable questions, assign minimal marks (e.g., 10–20% of allocated marks) if relevant effort is shown, with an explanation.

7. **Handle Edge Cases**:
   - **Blank or Missing Answers**: Assign minimal marks (e.g., 10% of allocated marks) if any relevant keywords or effort are present, noting: “Minimal effort shown.”
   - **Inaccessible Original Paper**: Evaluate based on general Data Science knowledge, assigning conservative marks and noting: “Evaluation based on subject expertise due to missing paper.”
   - **Extra Answers**: Award partial marks for extra answers if they demonstrate relevant knowledge, noting: “Answer not in original paper but relevant to [topic].”

8. **Provide Feedback**:
   - Include **suggestions for improvement** that are supportive and actionable (e.g., “Consider adding ‘gradient descent’ to explain backpropagation more fully”).
   - Focus on building on the student’s existing knowledge rather than emphasizing errors.

9. **Output Format**:
   - Provide the evaluation in Markdown format:
     ```markdown
     - **Student Details**:
       - **Name**: student_name
       - **Registration Number**: registration_number
       - **Obtained Marks**: obtained_marks
       - **Total Marks**: total_marks
     - **Question-by-Question Evaluation**:
       - **Question Number**: [Question Number]
       - **Original Question**: [Original Question Text]
       - **Mark Range**: [e.g., 8–10, 4–6, 0–3]
       - **Content Validity**: [Relevance, accuracy, coherence]
       - **Key Concepts Present**: [List with examples/quotes]
       - **Missing or Incorrect Concepts**: [List with explanations]
       - **Content Sufficiency and Quality**: [Depth, clarity, structure, examples, language]
       - **Mark Justification**: [Explanation of awarded marks]
       - **Suggestions for Improvement**: [Specific, supportive recommendations]
"""
    prompt = prompt_template.format(
        extracted_info=json.dumps(state["extracted_info"])
    )


    print("🚀 Invoking LLM with Gemini react agent...")

        # Create the agent
    agent_executor = create_react_agent(
            model=llm,  # Ensure llm is defined (e.g., ChatGoogleGenerativeAI)
            tools=[get_original_paper],
            prompt="You are a helpful assistant"
        )

        # Properly structure the input with HumanMessage
    result = agent_executor.invoke({
            "messages": [
                HumanMessage(content=prompt)
            ]
        })



        # Extract final AI message from result['messages']
    final_ai_message = None
    for message in reversed(result["messages"]):
      if isinstance(message, AIMessage) and message.content.strip():
        final_ai_message = message.content
        break

      if not final_ai_message:
        raise ValueError("No valid AIMessage with content was found.")

    print("\n📋 Final AI message content:")
    print(final_ai_message)





    return {
        "evaluation_report": final_ai_message,


    }
def evaluate_answers_2(state: AgentState) -> AgentState:
    print("\n📦 Current state contents:")
    print(json.dumps(dict(state), indent=2))

    # Compose the evaluation prompt
    prompt_template = """
You are an expert assistant tasked with evaluating student answers for an exam against an original question paper in a fair, accurate, and transparent manner using a structured chain-of-thought (CoT) reasoning process. Your goal is to assess each answer with a lenient approach, rewarding effort, relevance, and partial correctness while maintaining clarity and consistency. The evaluation should be supportive, allowing partial credit for relevant but incomplete answers and minimizing harsh penalties for minor errors or mismatches.

---

#### Instructions

1. **Retrieve the Original Question Paper**:
   - Use the `get_original_paper` tool with the subject from the `{extracted_info}` to fetch the original question paper, including question texts, correct answers, and associated marks.
   - Store the retrieved paper as the reference for evaluation.
   - If the tool fails to retrieve the paper, note this in the reasoning section, evaluate answers based on general Data Science expertise if possible, and assign conservative marks (e.g., low to mid-range) with an explanation.

2. **Analyze the Original Question Paper**:
   - For each question, extract:
     - **Question number** and **text**.
     - **Correct answer** (key concepts, phrases, or expected content based on Data Science expertise).
     - **Allocated marks** (indicating the expected depth of response).
   - Identify **key concepts** or phrases essential for a complete response (e.g., for a question on "backpropagation," key terms might include "gradient descent," "neural networks," "weight updates"). Use case-insensitive and semantic matching for flexibility.
   - Determine the **expected level of detail** based on marks:
     - **1–3 marks**: Brief, factual response with core points.
     - **4–7 marks**: Clear explanation with some supporting details or examples.
     - **8+ marks**: Detailed response with key concepts, allowing for minor omissions or simpler explanations.

3. **Process Student Answers**:
   - Iterate through the list of questions and answers provided for each student in the `{extracted_info}`.
   - If no answers are provided, assign minimal marks (e.g., 10% of allocated marks) for effort if any relevant keywords are present, and note the absence in the reasoning section.

4. **Match Student Questions to Original Questions**:
   - Map each student’s question (e.g., "QUESTION NO 1", "What is backpropagation?") to the corresponding question in the original paper using:
     - **Positional Matching**: Match the question number (e.g., "QUESTION NO 1" to the first question).
     - **Content-Based Matching**: Use semantic similarity (e.g., answers mentioning "neural networks" may match a backpropagation question) to confirm matches, allowing for typos (e.g., "backpropogation") or rephrased questions.
   - If no exact match is found, award partial marks (e.g., 20–50% of allocated marks) if the answer addresses related concepts in the subject area, noting: "Answer partially relevant to [related topic]."
   - If the student answers a different question (e.g., about "decision trees" instead of "backpropagation"), assign partial marks if the response demonstrates relevant Data Science knowledge, noting: "Answer addresses [related topic] but not the intended question."

5. **Evaluate Each Answer**:
   - Assess each answer based on **content validity**, **conceptual accuracy**, **completeness**, and **sufficiency** relative to the allocated marks, with a lenient approach that rewards effort and relevance.

   **Evaluation Criteria**:
   1. **Content Validity**:
      - **Relevance**: Award marks for answers that address the question or related concepts, even if partially off-topic. Completely irrelevant answers receive minimal marks (e.g., 10–20% of allocated marks).
      - **Factual Accuracy**: Prioritize core concepts over minor errors. Minor inaccuracies reduce marks slightly but do not result in 0.
      - **Coherence**: Accept understandable answers with minor clarity issues, reducing marks only for significant incoherence.
   2. **Conceptual Accuracy and Completeness**:
      - Identify **key concepts** required for a correct response.
      - List **concepts present** with examples or quotes (e.g., “The student mentions ‘gradient descent’ in backpropagation”).
      - List **missing or incorrect concepts**, but award partial marks for effort (e.g., “Omitted ‘weight updates’ but included other relevant ideas”).
   3. **Content Sufficiency and Quality**:
      - Evaluate **depth**, **clarity**, **structure**, **examples**, and **language** with flexibility:
        - **High-Mark Answers (60–100% of allocated marks)**:
          - **Depth**: Covers core concepts with clear explanations, even if not exhaustive.
          - **Technical Precision**: Mostly accurate terminology with minor errors allowed.
          - **Examples**: Includes basic examples or explanations to support points.
          - **Relevance**: Addresses the question with minimal tangents.
          - **Length**: Adequate length (e.g., a paragraph or two for high-mark questions).
          - **Structure**: Clear organization, even if simple.
        - **Mid-Mark Answers (30–59% of allocated marks)**:
          - **Depth**: Includes some relevant concepts but lacks detail.
          - **Examples**: Minimal or general examples.
          - **Relevance**: Partially addresses the question.
          - **Length**: Brief but relevant response.
          - **Structure**: Basic organization.
        - **Low-Mark Answers (0–29% of allocated marks)**:
          - **Depth**: Minimal relevant content or only keywords.
          - **Examples**: Absent or vague.
          - **Relevance**: Tangential or barely relevant.
          - **Length**: Very brief or incomplete.
          - **Structure**: Minimal but understandable.
      - **Language & Style**: Accept minor errors (e.g., typos, grammar) without significant penalties; prioritize clarity over perfection.
   4. **Mark Justification**:
      - Assign marks based on content quality, relevance, and effort, rewarding partial correctness.
      - Justify the score by referencing validity, concept coverage, and sufficiency (e.g., “Awarded 7/10 for covering ‘gradient descent’ but omitting ‘weight updates’”).

6. **Calculate Marks**:
   - Sum the marks awarded for each question to compute the student’s **obtained marks**.
   - Use the sum of marks from the original paper as the **total possible marks**.
   - For unmatched or unevaluable questions, assign minimal marks (e.g., 10–20% of allocated marks) if relevant effort is shown, with an explanation.

7. **Handle Edge Cases**:
   - **Blank or Missing Answers**: Assign minimal marks (e.g., 10% of allocated marks) if any relevant keywords or effort are present, noting: “Minimal effort shown.”
   - **Inaccessible Original Paper**: Evaluate based on general Data Science knowledge, assigning conservative marks and noting: “Evaluation based on subject expertise due to missing paper.”
   - **Extra Answers**: Award partial marks for extra answers if they demonstrate relevant knowledge, noting: “Answer not in original paper but relevant to [topic].”

8. **Provide Feedback**:
   - Include **suggestions for improvement** that are supportive and actionable (e.g., “Consider adding ‘gradient descent’ to explain backpropagation more fully”).
   - Focus on building on the student’s existing knowledge rather than emphasizing errors.

9. **Output Format**:
   - Provide the evaluation in Markdown format:
     ```markdown
     - **Student Details**:
       - **Name**: student_name
       - **Registration Number**: registration_number
       - **Obtained Marks**: obtained_marks
       - **Total Marks**: total_marks
     - **Question-by-Question Evaluation**:
       - **Question Number**: [Question Number]
       - **Original Question**: [Original Question Text]
       - **Mark Range**: [e.g., 8–10, 4–6, 0–3]
       - **Content Validity**: [Relevance, accuracy, coherence]
       - **Key Concepts Present**: [List with examples/quotes]
       - **Missing or Incorrect Concepts**: [List with explanations]
       - **Content Sufficiency and Quality**: [Depth, clarity, structure, examples, language]
       - **Mark Justification**: [Explanation of awarded marks]
       - **Suggestions for Improvement**: [Specific, supportive recommendations]
"""
    prompt = prompt_template.format(
        extracted_info=json.dumps(state["extracted_info"])
    )


    print("🚀 Invoking LLM with Gemini react agent...")

        # Create the agent
    agent_executor = create_react_agent(
            model=llm2,  # Ensure llm is defined (e.g., ChatGoogleGenerativeAI)
            tools=[get_original_paper],
            prompt="You are a helpful assistant"
        )

        # Properly structure the input with HumanMessage
    result = agent_executor.invoke({
            "messages": [
                HumanMessage(content=prompt)
            ]
        })



        # Extract final AI message from result['messages']
    final_ai_message = None
    for message in reversed(result["messages"]):
      if isinstance(message, AIMessage) and message.content.strip():
        final_ai_message = message.content
        break

      if not final_ai_message:
        raise ValueError("No valid AIMessage with content was found.")

    print("\n📋 Final AI message content:")
    print(final_ai_message)





    return {
        "evaluation_report_2": final_ai_message,


    }
def final_evaluation(state: AgentState) -> AgentState:
    """Receives evaluation reports from two agents and uses an LLM to compute final marks by averaging them."""
    prompt_template = """
    You are an expert assistant tasked with generating a final evaluation report by combining two evaluation reports from different agents. Your goal is to compute the final marks for each question by averaging the marks assigned by the two agents and produce a report in the specified Markdown format. The output must contain *only* the final evaluation report in the exact Markdown structure provided below, with no additional text, reasoning, or commentary.

---

#### Instructions
1. **Extract Input Data**:
   - Parse {extracted_info} (JSON string) for student details (name, registration number). If missing, use "Unknown" and note in the report.
   - Parse {evaluation_report} and {evaluation_report_2} (Markdown) to extract:
     - Student details (name, registration number, obtained marks, total marks).
     - Question evaluations: Question Number, Original Question, Mark Range, Content Validity, Key Concepts Present, Missing or Incorrect Concepts, Content Sufficiency and Quality, Mark Justification, Suggestions for Improvement.
     - Marks from "Mark Justification" (e.g., "Awarded X/Y" yields X).
   - If parsing fails, assign 0 marks for affected questions and note: "Error: Malformed mark in Report [1/2] for Question X."

2. **Validate Consistency**:
   - Compare total marks from both reports. If they differ, return a report with: "Error: Inconsistent total marks (Report 1: Y, Report 2: Z)." Assign 0 marks for all questions.
   - Verify question numbers and original questions match. For mismatches, assign 0 marks and note: "Error: Question X mismatch between reports."

3. **Compute Average Marks**:
   - For each question, average the marks from both agents (e.g., (6 + 5) / 2 = 5.5). Round to one decimal place.
   - If a mark is missing, use 0 and note: "Missing mark in Report [1/2] for Question X."
   - If max marks differ, use Report 1’s value and note: "Warning: Inconsistent max marks for Question X."
   - Sum averaged marks for total obtained marks, rounded to one decimal place.

4. **Generate Final Report**:
   - Use student details from {extracted_info} (or "Unknown" if missing).
   - Use total marks from Report 1.
   - Copy question evaluation fields from Report 1, updating "Mark Justification" to: "Awarded X.Y/Z (average of A/Z from Report 1 and B/Z from Report 2)." Include edge case notes.
   - Ensure the output is a valid Markdown string matching the format below.

5. **Edge Cases**:
   - If either report is empty, return: "Error: Missing evaluation report [1/2]."
   - If {extracted_info} is empty, use "Unknown" for student details and note: "Error: Missing extracted_info."
   - For mismatched question counts, evaluate only common questions, noting: "Error: Question count mismatch."

6. **Output Format**:
   - Return *only* the following Markdown structure, with no additional text:
     ```markdown
     - **Student Details**:
       - **Name**: "student_name"
       - **Registration Number**: "registration_number"
       - **Obtained Marks**: obtained_marks
       - **Total Marks**: total_marks
     - **Question-by-Question Evaluation**:
       - **Question Number**: [Question Number]
       - **Original Question**: [Original Question Text]
       - **Mark Range**: [e.g., 8–10, 4–6, 0–3]
       - **Content Validity**: [Relevance, accuracy, coherence]
       - **Key Concepts Present**: [List with examples/quotes]
       - **Missing or Incorrect Concepts**: [List with explanations]
       - **Content Sufficiency and Quality**: [Depth, clarity, structure, examples, language]
       - **Mark Justification**: [Explanation of averaged marks, including both agents' marks and edge case notes]
       - **Suggestions for Improvement**: [Specific recommendations]
      """
    # Format the prompt with the input data
    prompt = prompt_template.format(
        extracted_info=json.dumps(state["extracted_info"]),
        evaluation_report=state["evaluation_report"],
        evaluation_report_2=state["evaluation_report_2"]
    )

   

    # Create the agent
    agent_executor = create_react_agent(
        model=llm,
        tools=[],  # No tools needed for this step
        prompt="You are a helpful assistant tasked with combining evaluation reports."
    )

    # Invoke the agent
    result = agent_executor.invoke({
        "messages": [
            HumanMessage(content=prompt)
        ]
    })

    # Extract final AI message
    final_ai_message = None
    for message in reversed(result["messages"]):
        if isinstance(message, AIMessage) and message.content.strip():
            final_ai_message = message.content
            break

    if not final_ai_message:
        raise ValueError("No valid AIMessage with content was found.")

    print("\n📋 Final AI message content:")
    print(final_ai_message)

    return {
        "final_evaluation_report": final_ai_message
    }    











# Create and compile the workflow
def create_workflow():
    workflow = StateGraph(AgentState)
    workflow.add_node("call_gemini", call_gemini)
    workflow.add_node("process_response", process_response)
    workflow.add_node("evaluate_answers", evaluate_answers)
    workflow.add_node("evaluate_answers_2",evaluate_answers_2)
    workflow.add_node("final_evaluation", final_evaluation)


    workflow.add_edge(START, "call_gemini")
    workflow.add_edge("call_gemini", "process_response")
    workflow.add_edge("process_response", "evaluate_answers")
    workflow.add_edge("process_response", "evaluate_answers_2")
    workflow.add_edge("evaluate_answers", "final_evaluation")
    workflow.add_edge("evaluate_answers_2", "final_evaluation")
    workflow.add_edge("final_evaluation", END)
   




    return workflow.compile()


