import sys
import io
import os
import pandas as pd
import chardet
from utils.llmhandler import generate_code_from_query

def try_read_csv(file_path: str, encoding: str) -> tuple[pd.DataFrame | None, Exception | None]:
    """Try to read CSV with a specific encoding, return (dataframe, error)."""
    try:
        df = pd.read_csv(file_path, encoding=encoding)
        return df, None
    except Exception as e:
        return None, e

def detect_encoding(file_path: str) -> str:
    """
    Detect the encoding of a file using a priority list of common encodings
    and falling back to chardet only if needed.
    """
    # Try common encodings first in order of likelihood
    common_encodings = ['utf-8', 'latin1', 'cp1252', 'ISO-8859-1']
    
    for encoding in common_encodings:
        df, error = try_read_csv(file_path, encoding)
        if df is not None:
            return encoding
    
    # If common encodings fail, try chardet but validate its suggestion
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        detected = result.get('encoding')
        
        if detected and detected.lower() not in ['johab']:  # Skip problematic encodings
            df, error = try_read_csv(file_path, detected)
            if df is not None:
                return detected
    
    # If all else fails, use latin1 (it can read any byte sequence)
    return 'latin1'

def run_generated_code(code: str, csv_path: str):
    """
    Executes the generated Python code with a DataFrame 'df' loaded from csv_path.
    Captures and returns stdout and stderr output.
    Also returns flags indicating if an image was generated, if stdout was produced, or both.
    """
    # Try to load the CSV with the best encoding
    encoding = detect_encoding(csv_path)
    df, error = try_read_csv(csv_path, encoding)
    
    if error:
        raise RuntimeError(f"Failed to read CSV with encoding {encoding}: {error}")

    # Prepare the execution environment
    local_vars = {'df': df}
    stdout = io.StringIO()
    stderr = io.StringIO()
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    image_path = "output.png"
    # Remove any existing output.png before running
    if os.path.exists(image_path):
        os.remove(image_path)
    try:
        sys.stdout = stdout
        sys.stderr = stderr
        exec(code, {}, local_vars)
    except Exception as e:
        print(f"Error during code execution: {e}")
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    output = stdout.getvalue()
    error = stderr.getvalue()
    image_generated = os.path.exists(image_path)
    stdout_generated = bool(output.strip())
    # Both means both image and stdout are present
    both_generated = image_generated and stdout_generated

    flags = {
        "image_generated": image_generated,
        "stdout_generated": stdout_generated,
        "both_generated": both_generated
    }
    return output, error, flags

def main():
    # Path to your CSV file
    csv_path = r"C:\Users\subar\OneDrive\Desktop\abhidas\Graphagent\backend\utils\products-1000.csv"
    # User's natural language query
    user_query = "generate a graph displaying linegraph of stocks"

    # Generate code from LLM
    code = generate_code_from_query(csv_path, user_query)
    print("Generated Python code:\n")
    print(code)
    print("\n--- Running generated code ---\n")
    output, error, flags = run_generated_code(code, csv_path)
    if output:
        print("Output:\n", output)
    if error:
        print("Error:\n", error)
    print("Flags:", flags)

if __name__ == "__main__":
    main()
