from langchain_core.tools import tool
import os
import json

@tool
def web_search(query: str) -> str:
    """Search the web for information based on the query."""
    # Mock implementation
    return f"Mock search results for: {query}"

@tool
def file_read(file_path: str) -> str:
    """Read the content of a file."""
    if not os.path.exists(file_path):
        return "Error: File does not exist."
    with open(file_path, 'r') as f:
        return f.read()

@tool
def file_write(file_path: str, content: str) -> str:
    """Write content to a file."""
    with open(file_path, 'w') as f:
        f.write(content)
    return f"Successfully wrote to {file_path}"

@tool
def code_execution(code: str) -> str:
    """Execute Python code in a sandboxed environment."""
    # Highly mocked and unsafe for real prod without a real sandbox
    try:
        # We capture locals/globals to return result
        exec_globals = {}
        exec(code, exec_globals)
        return str(exec_globals.get("result", "Code executed successfully. No 'result' variable found."))
    except Exception as e:
        return f"Error executing code: {str(e)}"

@tool
def database_query(query: str) -> str:
    """Execute a query on the database."""
    # Mock implementation
    return f"Mock DB query results for: {query}"

@tool
def api_call(url: str, method: str = "GET", payload: str = "") -> str:
    """Make an API call."""
    # Mock implementation
    return f"Mock API response from {method} {url}"

def get_specialist_tools(specialist_type: str):
    if specialist_type == "research":
        return [web_search, api_call]
    elif specialist_type == "data":
        return [database_query, file_read, file_write]
    elif specialist_type == "execution":
        return [code_execution, file_read, file_write]
    elif specialist_type == "writing":
        return [file_read, file_write]
    return []
