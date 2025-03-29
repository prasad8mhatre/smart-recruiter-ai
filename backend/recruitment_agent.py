import logging
from typing import Dict, Any
from recruitment_utils import (
    calculate_profile_score,
    generate_outreach_message,
    send_notifications,
    model
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('RecruitmentAgent')

def function_caller(func_name: str, params: Dict[str, Any]) -> Any:
    """Maps function names to actual functions"""
    logger.info(f"🔄 Calling function: {func_name} with params: {params}")
    
    function_map = {
        "calculate_profile_score": calculate_profile_score,
        "generate_outreach_message": generate_outreach_message,
        "send_notifications": send_notifications
    }
    
    if func_name in function_map:
        try:
            result = function_map[func_name](**params)
            logger.info(f"✅ Function {func_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"❌ Function {func_name} failed: {str(e)}")
            raise
    else:
        logger.warning(f"⚠️ Function {func_name} not found")
        return f"Function {func_name} not found"

def run_recruitment_agent(profile_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
    logger.info("🚀 Starting recruitment agent analysis")
    #only take first 1000 characters of profile data
    if isinstance(profile_data, str):
        profile_data = profile_data[:1000]
    elif isinstance(profile_data, dict):
        profile_data = str(profile_data)[:1000]
    else:
        raise ValueError("Invalid profile data format. Expected str or dict.")   
    
    logger.info(f"📄 Processing profile with {len(str(profile_data))} characters")
    
    system_prompt = """You are a recruitment agent analyzing profiles. Respond with EXACTLY ONE of these formats:
    1. FUNCTION_CALL: function_name|{"param1": value1, "param2": value2}
    2. FINAL_ANSWER: {"success": bool, "matchScore": int, "message": str}

    Available functions:
    1. calculate_profile_score(profile_content, job_description, profile_data) -> Returns score and analysis
    2. generate_outreach_message(name, score, message_section) -> Returns formatted message
    3. send_notifications(profile_data, score, message_section) -> Sends notifications
    
    Follow these steps:
    1. Calculate profile score
    2. If score > 50, generate message
    3. If score > 90, send notifications
    4. Return final result
    """

    max_iterations = 3
    last_response = None
    iteration = 0
    iteration_responses = []
    
    while iteration < max_iterations:
        logger.info(f"\n=== 🔄 Starting Iteration {iteration + 1}/{max_iterations} ===")
        
        if last_response is None:
            current_query = f"Analyze profile:\nProfile: {profile_data}\nJob: {job_description}"
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
            logger.info("🔍 Function call detected")
            _, function_info = response_text.split(":", 1)
            func_name, params = [x.strip() for x in function_info.split("|", 1)]
            logger.info(f"📋 Parsed function call: {func_name}")
            
            try:
                params = eval(params)
                iteration_result = function_caller(func_name, params)
                last_response = iteration_result
                iteration_responses.append(f"Called {func_name} with {params}, got result: {iteration_result}")
                logger.info(f"✅ Function executed successfully")
            except Exception as e:
                logger.error(f"❌ Error executing function: {str(e)}")
                raise

        elif response_text.startswith("FINAL_ANSWER:"):
            logger.info("🏁 Final answer received")
            _, result = response_text.split(":", 1)
            final_result = eval(result)
            logger.info(f"📊 Final result: {final_result}")
            return final_result

        iteration += 1
        logger.info(f"➡️ Completed iteration {iteration}")

    logger.warning("⚠️ Max iterations reached without conclusion")
    return {
        "success": False,
        "matchScore": 0,
        "message": "Max iterations reached without conclusion"
    }
