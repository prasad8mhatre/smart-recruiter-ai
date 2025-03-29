import logging
import json
from typing import Dict, Any
from bs4 import BeautifulSoup
from recruitment_utils import (
    calculate_profile_score,
    generate_outreach_message,
    send_notifications,
    model
)
import re
import pdb

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('RecruitmentAgent')

def clean_profile_data(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean HTML from profile data and extract plain text."""
    if isinstance(profile_data, str):
        # Clean direct string content
        text = BeautifulSoup(profile_data, 'html.parser').get_text()
        # Replace multiple newlines with single newline
        text = '\n'.join(line.strip() for line in text.splitlines() if line.strip())
        return text
    
    if isinstance(profile_data, dict):
        cleaned_data = {}
        for key, value in profile_data.items():
            if isinstance(value, str):
                # Clean HTML and newlines from string values
                text = BeautifulSoup(value, 'html.parser').get_text()
                cleaned_data[key] = '\n'.join(line.strip() for line in text.splitlines() if line.strip())
            elif isinstance(value, list):
                # Clean HTML and newlines from list items
                cleaned_data[key] = [
                    '\n'.join(line.strip() for line in BeautifulSoup(item, 'html.parser').get_text().splitlines() if line.strip())
                    if isinstance(item, str) else item 
                    for item in value
                ]
            else:
                cleaned_data[key] = value
        return cleaned_data
    
    return profile_data

def safe_eval_params(params_str: str) -> Dict[str, Any]:
    """Safely evaluate parameters string to dict."""
    try:
        # Clean up and escape the string
        cleaned = params_str.strip()
        logger.debug(f"Original params: {cleaned}")
        
        # Fix common formatting issues
        cleaned = cleaned.replace('None', 'null')
        cleaned = cleaned.replace('True', 'true')
        cleaned = cleaned.replace('False', 'false')
        
        # Handle nested quotes
        cleaned = re.sub(r'(?<!\\)"([^"]*)"', r'"\1"', cleaned)
        
        logger.debug(f"Cleaned params: {cleaned}")
        return json.loads(cleaned)
    except Exception as e:
        logger.error(f"❌ Parameter parsing failed: {e}")
        logger.error(f"Problem string: {params_str}")
        raise ValueError(f"Invalid parameters format: {e}")

def function_caller(func_name: str, params: Dict[str, Any]) -> Any:
    """Maps function names to actual functions"""
    logger.info("=" * 80)
    logger.info(f"🔄 FUNCTION CALL: {func_name}")
    logger.info(f"📥 INPUT PARAMETERS:")
    for key, value in params.items():
        logger.info(f"  - {key}: {str(value)[:200]}{'...' if len(str(value)) > 200 else ''}")
    
    function_map = {
        "calculate_profile_score": calculate_profile_score,
        "generate_outreach_message": generate_outreach_message,
        "send_notifications": send_notifications
    }
    
    if func_name in function_map:
        try:
            result = function_map[func_name](**params)
            logger.info(f"📤 OUTPUT:")
            if isinstance(result, tuple):
                for i, item in enumerate(result):
                    logger.info(f"  Return value {i+1}: {str(item)[:200]}{'...' if len(str(item)) > 200 else ''}")
            else:
                logger.info(f"  Return value: {str(result)[:200]}{'...' if len(str(result)) > 200 else ''}")
            
            logger.info(f"✅ Function {func_name} completed successfully")
            
            # Log next steps based on function and result
            if func_name == "calculate_profile_score" and isinstance(result, tuple):
                score = result[0]
                logger.info("📋 NEXT STEPS:")
                if score > 90:
                    logger.info("  - High match (>90): Generate message and send notifications")
                elif score > 50:
                    logger.info("  - Good match (>50): Generate outreach message")
                else:
                    logger.info("  - Low match: No further action needed")
            
            logger.info("=" * 80)
            return result
            
        except Exception as e:
            logger.error(f"❌ Function {func_name} failed: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    else:
        logger.warning(f"⚠️ Function {func_name} not found")
        return f"Function {func_name} not found"

def run_recruitment_agent(profile_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
    logger.info("\n" + "=" * 80)
    logger.info("🚀 STARTING RECRUITMENT AGENT ANALYSIS")
    #pdb.set_trace()  # Debug: Initial data
    
    # Clean profile data before processing
    cleaned_profile_data_res = clean_profile_data(profile_data)
    #pdb.set_trace()  # Debug: After cleaning
    
    logger.info("🧹 Cleaned profile data of HTML tags")
    print("Received profile data:", json.dumps(cleaned_profile_data_res, indent=2))
    
    cleaned_profile_data_res = str(json.dumps(cleaned_profile_data_res['content']))
    # Clean up multiple newlines in the JSON string
    cleaned_profile_data_res = re.sub(r'\\n+', '\\n', cleaned_profile_data_res)

    # Limit profile data length if needed
    if isinstance(cleaned_profile_data_res, str):
        cleaned_profile_data_res = cleaned_profile_data_res[:5000]
    elif isinstance(cleaned_profile_data_res, dict):
        cleaned_profile_data_res = {k: str(v)[:5000] if isinstance(v, str) else v 
                              for k, v in cleaned_profile_data_res.items()}
    
    logger.info(f"📄 Processing cleaned profile with {len(str(cleaned_profile_data_res))} characters")
    
    system_prompt = """You are a recruitment agent analyzing profiles. Respond with EXACTLY ONE of these formats:
    1. FUNCTION_CALL: function_name|{"profile_content": "content", "job_description": "description"}
    2. FUNCTION_CALL: generate_outreach_message|{"name": "candidate_name", "score": score_value, "message_section": "message"}
    3. FUNCTION_CALL: send_notifications|{"profile_data": "profile", "score": score_value, "message_section": "message"}
    4. FINAL_ANSWER: {
        "success": true,
        "matchScore": score_value,
        "match_analysis": "analysis",
        "key_qualifications": "qualifications",
        "message": "message"
    }

    Available functions:
    1. calculate_profile_score(profile_content: str, job_description: str) -> Returns tuple(score, analysis, qualifications, message)
    2. generate_outreach_message(name: str, score: int, message_section: str) -> Returns str
    3. send_notifications(profile_data: str, score: int, message_section: str) -> None
    
    Follow these steps EXACTLY:
    1. First, call calculate_profile_score
    2. Based on the score:
       - If score > 50: call generate_outreach_message in next iteration
       - If score > 50: also call send_notifications after outreach message in next iteration
    3. Only return FINAL_ANSWER after completing all required function calls
    
    
    Current score and analysis must be used for subsequent function calls.
    DO NOT provide any other text apart from asked for and verify your answer before answering
    DO NOT enclose the output in ```json or another
    """

    max_iterations = 7
    last_response = None
    iteration = 0
    iteration_responses = []
    score = None
    message = None
    
    while iteration < max_iterations:
        #pdb.set_trace()  # Debug: Start of iteration
        logger.info(f"\n=== 🔄 Starting Iteration {iteration + 1}/{max_iterations} ===")
        
        if last_response is None:
            current_query = f"Analyze profile:\nProfile: {cleaned_profile_data_res}\nJob: {job_description}"
            logger.info("📝 Initial query created")
        else:
            current_query = f"{current_query}\n\n" + " ".join(iteration_responses) + "\nWhat should I do next?"
            logger.info("📝 Follow-up query created with previous results")

        logger.info("🤖 Requesting LLM response")
        prompt = f"{system_prompt}\n\nQuery: {current_query}"
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        logger.info(f"📥 Received response: {response_text[:100]}...")

        if response_text.startswith("FUNCTION_CALL:"):
            #pdb.set_trace()  # Debug: Before function call
            logger.info("🔍 Function call detected")
            try:
                _, function_info = response_text.split(":", 1)
                func_name, params_str = [x.strip() for x in function_info.split("|", 1)]
                logger.info(f"📋 Parsed function call: {func_name}")
                
                # Add more robust parameter preprocessing
                params_str = params_str.strip()
                if params_str.startswith('"') and params_str.endswith('"'):
                    params_str = params_str[1:-1]
                
                # Log the parameters for debugging
                logger.debug(f"Raw parameters: {params_str}")
                
                params = safe_eval_params(params_str)
                #pdb.set_trace()  # Debug: After params processing
                
                iteration_result = function_caller(func_name, params)
                #pdb.set_trace()  # Debug: After function execution
                
                last_response = iteration_result
                iteration_responses.append(f"Called {func_name} with {json.dumps(params)}, got result: {iteration_result}")
                logger.info(f"✅ Function executed successfully")

                # Store important results for next iterations
                if func_name == "calculate_profile_score" and isinstance(iteration_result, tuple):
                    score, analysis, qualifications, message = iteration_result
                    # Signal next steps in the query
                    if score > 90:
                        iteration_responses.append("Score > 90, need to generate message and send notification")
                    elif score > 50:
                        iteration_responses.append("Score > 50, need to generate message")
                
                elif func_name == "generate_outreach_message":
                    message = iteration_result
                    if score > 90:  # Use the stored score
                        iteration_responses.append("Message generated, need to send notification")

            except Exception as e:
                logger.error(f"❌ Error in function execution: {str(e)}")
                logger.error(f"Raw params string: {params_str}")
                raise

        elif response_text.startswith("FINAL_ANSWER:"):
            logger.info("🏁 Final answer received")
            try:
                _, result = response_text.split(":", 1)
                # Replace javascript-style booleans with Python booleans
                result = result.replace('false', 'False').replace('true', 'True')
                result = result.strip()
                
                # Get the most recent analysis result
                if last_response and isinstance(last_response, tuple):
                    score, analysis, qualifications_text, message = last_response
                    
                    # Extract key qualifications
                    key_qualifications = ""
                    if '#### Key Qualifications' in qualifications_text:
                        key_quals = qualifications_text.split('#### Key Qualifications')[1]
                        key_quals = key_quals.split('####')[0].strip()
                        key_qualifications = key_quals

                    final_result = {
                        "success": True,
                        "matchScore": score,
                        "match_analysis": analysis.strip(),
                        "key_qualifications": key_qualifications,
                        "message": message
                    }
                else:
                    # Parse the provided result
                    try:
                        final_result = json.loads(result)
                    except json.JSONDecodeError:
                        final_result = eval(result)
                
                logger.info(f"📊 Final result: {json.dumps(final_result, indent=2)}")
                return final_result
            except Exception as e:
                logger.error(f"❌ Error evaluating final result: {str(e)}")
                return {
                    "success": False,
                    "matchScore": 0,
                    "match_analysis": "",
                    "key_qualifications": "",
                    "message": f"Error processing result: {str(e)}"
                }

        iteration += 1
        logger.info(f"➡️ Completed iteration {iteration}")

    logger.warning("⚠️ Max iterations reached without conclusion")
    return {
        "success": False,
        "matchScore": 0,
        "message": "Max iterations reached without conclusion"
    }
