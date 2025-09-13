import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from utils.processdata import extract_csv_metadata_and_sample

load_dotenv()

# In-memory store for session chat histories
session_memory = {}

def get_conversational_chain(session_id: str, csv_path: str, csv_info: str, model_name: str) -> ConversationChain:
    """
    Initializes and returns a conversational chain with memory.
    A single chain is created per session and stored in memory.
    """
    if session_id not in session_memory:
        session_memory[session_id] = ConversationBufferWindowMemory(k=5)

    memory = session_memory[session_id]
    llm = ChatGoogleGenerativeAI(model=model_name)

    template = f"""
You are an expert Python data analyst. Given the following CSV metadata and sample rows, and the CSV file path, write Python code using pandas (and matplotlib if needed) to answer the user's query.
- The CSV metadata and sample rows are provided below.
- The path to the CSV file is: {csv_path}
- The code should load the data into a pandas DataFrame called 'df' using pd.read_csv and the provided csv_path. Do not generate your own data.
- If the query requires a plot or graph, use matplotlib to generate it and save it as 'output.png'.
- Only output the Python code, and do not include any markdown formatting or code block markers.

CSV Metadata and Sample:
{csv_info}

Current conversation:
{{history}}
Human: {{input}}
AI:
"""
    PROMPT = PromptTemplate(
        input_variables=["history", "input"], template=template
    )

    return ConversationChain(prompt=PROMPT, llm=llm, memory=memory)

def extract_code_only(text):
    # Remove any code block markers (e.g., ```python ... ```)
    import re
    # Remove triple backtick blocks (with or without python)
    code = re.sub(r"^```(?:python)?\s*|```$", "", text, flags=re.MULTILINE)
    # Remove any leading/trailing whitespace
    return code.strip()

def generate_code_from_query(session_id: str, csv_path: str, user_query: str, model_name="gemini-1.5-flash"):
    csv_info = extract_csv_metadata_and_sample(csv_path)
    
    conversation_chain = get_conversational_chain(session_id, csv_path, csv_info, model_name)
    response = conversation_chain.predict(input=user_query)
    
    code_raw = response if isinstance(response, str) else str(response)
    code = extract_code_only(code_raw)
    return code

def clear_memory(session_id: str):
    """Clears the memory for a given session."""
    if session_id in session_memory:
        del session_memory[session_id]

def main():
    csv_path = r"C:\Users\subar\OneDrive\Desktop\abhidas\Graphagent\backend\utils\products-1000.csv"
    session_id = "test_session"
    
    # First query
    user_query_1 = "generate a graph displaying histogram of stocks"
    print(f"User Query 1: {user_query_1}")
    code_1 = generate_code_from_query(session_id, csv_path, user_query_1)
    print("Generated Python code 1:\n")
    print(code_1)
    
    # Second query (contextual)
    user_query_2 = "now, make it a bar chart"
    print(f"\nUser Query 2: {user_query_2}")
    code_2 = generate_code_from_query(session_id, csv_path, user_query_2)
    print("Generated Python code 2:\n")
    print(code_2)

    # Clear memory for the session
    clear_memory(session_id)
    print(f"\nMemory for session '{session_id}' cleared.")

if __name__ == "__main__":
    main()