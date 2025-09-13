import os
import pickle
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from utils.processdata import extract_csv_metadata_and_sample
from utils.local_storage import get_session_dir

load_dotenv()

# --- In-memory and file-based session management ---
histories = {}

def get_memory_file(session_id: str) -> Path:
    """Returns the path to the memory file for a given session."""
    session_dir = get_session_dir(session_id)
    return session_dir / "memory.pkl"

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    Loads chat history from a file if it exists, otherwise creates a new one.
    Keeps the history in memory for the duration of the app's lifecycle.
    """
    if session_id not in histories:
        memory_file = get_memory_file(session_id)
        if memory_file.exists():
            with open(memory_file, "rb") as f:
                histories[session_id] = pickle.load(f)
        else:
            # This creates a `ChatMessageHistory` object, which is what is needed
            histories[session_id] = ConversationBufferWindowMemory(
                k=5, return_messages=True
            ).chat_memory
    return histories[session_id]

def save_session_history(session_id: str):
    """Saves the current session's chat history to a file."""
    if session_id in histories:
        memory_file = get_memory_file(session_id)
        with open(memory_file, "wb") as f:
            pickle.dump(histories[session_id], f)

def get_conversational_chain(csv_path: str, csv_info: str, model_name: str):
    """
    Initializes and returns a conversational chain with memory.
    """
    llm = ChatGoogleGenerativeAI(model=model_name)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert Python data analyst and conversation assistant. You can analyze CSV data and handle queries about the conversation.\n\n"
                "For data analysis queries:\n"
                "- Write Python code using pandas (and matplotlib if needed)\n"
                "- The path to the CSV file is: {csv_path}\n"
                "- The DataFrame 'df' will be loaded automatically - do not include pd.read_csv\n"
                "- For plots, save as 'output.png'\n"
                "- Output code without markdown formatting\n\n"
                "For conversation queries (e.g., 'what was my last query'):\n"
                "- Respond with: print('Your last query was: \"<previous query>\"')\n"
                "- Do not try to access conversation history directly\n\n"
                "CSV Metadata and Sample:\n{csv_info}",
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )

    chain = prompt | llm

    conversational_chain = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )
    
    return conversational_chain

def extract_code_only(text):
    import re
    code = re.sub(r"^```(?:python)?\s*|```$", "", text, flags=re.MULTILINE)
    return code.strip()

def generate_code_from_query(session_id: str, csv_path: str, user_query: str, model_name="gemini-1.5-flash"):
    csv_info = extract_csv_metadata_and_sample(csv_path)
    
    conversation_chain = get_conversational_chain(csv_path, csv_info, model_name)
    
    config = {"configurable": {"session_id": session_id}}
    
    response = conversation_chain.invoke(
        {
            "input": user_query,
            "csv_path": csv_path,
            "csv_info": csv_info
        },
        config=config
    )
    
    # Save the updated history back to the file
    save_session_history(session_id)

    code_raw = response.content if hasattr(response, "content") else str(response)
    code = extract_code_only(code_raw)
    return code

def clear_memory(session_id: str):
    """
    Completely removes all memory traces for a session.
    This includes in-memory history, file-based history, and any cached data.
    """
    # Clear in-memory history
    if session_id in histories:
        try:
            # Clear the actual memory object first
            histories[session_id].clear()
        except Exception:
            pass  # Ensure we continue even if clear() fails
        # Remove from the histories dictionary
        del histories[session_id]
    
    # Remove memory file
    memory_file = get_memory_file(session_id)
    try:
        if memory_file.exists():
            os.remove(memory_file)
        # Also try to remove any temp or backup files
        for ext in ['.bak', '.tmp', '.pkl.old']:
            backup = memory_file.with_suffix(ext)
            if backup.exists():
                os.remove(backup)
    except Exception as e:
        print(f"Error cleaning memory files for session {session_id}: {e}")

def main():
    # This main function is for conceptual testing and won't fully reflect
    # the file-based session management in a real server environment.
    pass

if __name__ == "__main__":
    main()