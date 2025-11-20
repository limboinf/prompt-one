import json
from app.llm.langchain_client import LangChainClient

def generate_variables_meta(template: str) -> str:
    """
    Generates a JSON Schema for variables in a Jinja2 template using an LLM.
    
    Args:
        template: The Jinja2 template string.
        
    Returns:
        A JSON string representing the variables metadata (JSON Schema).
    """
    client = LangChainClient(temperature=0)
    prompt_text = f"""You are an expert in Jinja2 templates and JSON Schema.
Please analyze the following template and extract all variables that need to be filled.
Generate a JSON Schema (Draft 7) that describes the structure of the input variables.

Template:
{template}

Requirements:
1. Output MUST be a valid JSON Schema object.
2. Root type must be "object".
3. "properties" should contain the variables found in the template.
4. Infer types ("string", "number", "boolean", "array", "object") based on usage.
   - If a variable is used in a loop (e.g. `{{% for x in items %}}`), it is an "array".
   - If a variable is accessed with dot notation (e.g. `user.name`), it is an "object".
5. Include "description" for each property based on context.
6. List all variables in the "required" array unless they appear optional (e.g. inside `if`).
7. For arrays and objects, try to infer the nested structure/items if visible in the template.
8. Do NOT return any other text or markdown formatting (like ```json), just the raw JSON string.

JSON Output:
"""
    response = client.invoke(prompt_text)
    
    # Clean up potential markdown formatting
    clean_response = response.strip()
    if clean_response.startswith("```json"):
        clean_response = clean_response[7:]
    elif clean_response.startswith("```"):
        clean_response = clean_response[3:]
    if clean_response.endswith("```"):
        clean_response = clean_response[:-3]
    clean_response = clean_response.strip()
    
    # Validate JSON
    try:
        # We try to parse it to ensure it's valid JSON, but we return the string
        # so it can be displayed in the text area.
        parsed = json.loads(clean_response)
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        # If parsing fails, return the raw response but maybe log it?
        # For now, just return it, the user might see the error in the UI when they try to save.
        return clean_response
