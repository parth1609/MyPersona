import os

def extract_txt_file(file_path):
    """
    Extracts and returns the content of a .txt file.
    Args:
        file_path (str): Path to the .txt file.
    Returns:
        dict: {"file": file_path, "content": str, "status": "success"/"error", "error": None or str}
    """
    result = {"file": file_path, "content": None, "status": "unknown", "error": None}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        result["content"] = content
        result["status"] = "success"
    except Exception as e:
        result["error"] = str(e)
        result["status"] = "error"
    return result