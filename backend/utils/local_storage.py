import os
import shutil
from pathlib import Path

# Define the root of the backend directory
BACKEND_ROOT = Path(__file__).parent.parent.resolve()
LOCAL_STORAGE_PATH = BACKEND_ROOT / "uploaded_csv"

def setup_local_storage():
    """Create the base directory for local sessions if it doesn't exist."""
    LOCAL_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

def get_session_dir(session_id: str) -> Path:
    """Returns the path to a session directory, creating it if necessary."""
    session_dir = LOCAL_STORAGE_PATH / session_id
    session_dir.mkdir(exist_ok=True)
    return session_dir

def save_uploaded_file(session_id: str, file):
    """Saves an uploaded file to a session-specific directory."""
    session_dir = get_session_dir(session_id)
    file_path = session_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return str(file_path)

def get_session_file(session_id: str):
    """Gets the path of the CSV file in a session directory."""
    session_dir = LOCAL_STORAGE_PATH / session_id
    if not session_dir.exists():
        return None
    
    # Find the first CSV file in the directory
    csv_files = list(session_dir.glob("*.csv"))
    if csv_files:
        return str(csv_files[0])
    return None

def save_output_image(session_id: str, source_path: str, timestamp: str):
    """Saves a generated image to the session directory with a timestamp."""
    session_dir = get_session_dir(session_id)
    destination_path = session_dir / f"output_{timestamp}.png"
    shutil.copy(source_path, destination_path)
    return str(destination_path)

def get_image_path(session_id: str, timestamp: str):
    """Gets the path of a generated image from a session directory."""
    session_dir = LOCAL_STORAGE_PATH / session_id
    # The key is just the timestamp, so we construct the filename
    image_path = session_dir / f"output_{timestamp}.png"
    if image_path.exists():
        return str(image_path)
    return None

def clear_local_session(session_id: str):
    """
    Deletes a session directory and its contents completely.
    Returns True if the session was found and deleted, False otherwise.
    """
    session_dir = LOCAL_STORAGE_PATH / session_id
    print(f"\nAttempting to delete session directory: {session_dir}")
    
    if not session_dir.exists():
        print("Directory doesn't exist - already clean")
        return True

    def log_dir_state():
        """Log the current state of the directory"""
        try:
            if session_dir.exists():
                print(f"Directory exists: {session_dir}")
                items = list(session_dir.glob('*'))
                print(f"Contents: {[item.name for item in items]}")
                print(f"Is directory empty: {len(items) == 0}")
                if os.name == 'nt':  # Windows
                    import stat
                    attrs = os.stat(session_dir).st_file_attributes
                    print(f"Directory attributes: {attrs}")
            else:
                print("Directory no longer exists")
        except Exception as e:
            print(f"Error checking directory state: {e}")

    log_dir_state()
    print("\nAttempting cleanup...")

    try:
        # 1. Release any handles and reset attributes (Windows)
        if os.name == 'nt':
            try:
                import win32con
                import win32file
                attrs = win32file.GetFileAttributes(str(session_dir))
                win32file.SetFileAttributes(str(session_dir), win32con.FILE_ATTRIBUTE_NORMAL)
                print("Reset Windows file attributes")
            except Exception as e:
                print(f"Warning: Could not reset Windows attributes: {e}")

        # 2. Force close any open handles (Windows)
        if os.name == 'nt':
            try:
                os.system(f'handle -c "{session_dir}"')  # Requires sysinternals handle.exe
            except Exception:
                pass

        # 3. Recursive permission reset and cleanup
        for root, dirs, files in os.walk(str(session_dir), topdown=False):
            for name in files:
                try:
                    path = Path(root) / name
                    print(f"Processing file: {path}")
                    # Reset attributes and permissions
                    if os.name == 'nt':
                        os.system(f'attrib -r -h -s "{path}"')
                    os.chmod(str(path), 0o666)
                    path.unlink()
                    print(f"Deleted file: {path}")
                except Exception as e:
                    print(f"Warning: Could not delete file {name}: {e}")
                    
            for name in dirs:
                try:
                    path = Path(root) / name
                    print(f"Processing directory: {path}")
                    if os.name == 'nt':
                        os.system(f'attrib -r -h -s "{path}"')
                    os.chmod(str(path), 0o777)
                    path.rmdir()
                    print(f"Deleted directory: {path}")
                except Exception as e:
                    print(f"Warning: Could not delete directory {name}: {e}")

        # 4. Final directory removal attempts
        print("\nAttempting to remove main directory...")
        deletion_methods = [
            lambda: session_dir.rmdir(),
            lambda: shutil.rmtree(str(session_dir), ignore_errors=True),
            lambda: os.rmdir(str(session_dir)),
            # Windows-specific aggressive cleanup
            lambda: os.system(f'rmdir /s /q "{session_dir}"') if os.name == 'nt' else None,
            lambda: os.system(f'del /f /s /q "{session_dir}\\*" && rmdir /s /q "{session_dir}"') if os.name == 'nt' else None,
            # Unix-specific cleanup
            lambda: os.system(f'rm -rf "{session_dir}"') if os.name != 'nt' else None
        ]

        for method in deletion_methods:
            if method is None:
                continue
            try:
                method()
                if not session_dir.exists():
                    print("Directory successfully deleted!")
                    return True
            except Exception as e:
                print(f"Deletion method failed: {e}")

        # 5. Final check
        log_dir_state()
        if not session_dir.exists():
            print("Directory successfully removed")
            return True
        else:
            print("WARNING: Directory still exists after all deletion attempts")
            return False

    except Exception as e:
        print(f"Error during session cleanup: {e}")
        log_dir_state()
        return False

