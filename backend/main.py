from fastapi import FastAPI, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import shutil
from pathlib import Path
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from utils.llmhandler import generate_code_from_query, clear_memory
from utils.pythonexecutor import run_generated_code
from utils.processdata import extract_csv_metadata_and_sample
from datetime import datetime
from utils import local_storage

app = FastAPI()

# --- Storage Configuration ---
USE_S3 = False
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
s3 = None

try:
    if S3_BUCKET:
        s3 = boto3.client("s3")
        # Check if we can access the bucket
        s3.head_bucket(Bucket=S3_BUCKET)
        USE_S3 = True
        print("S3 configuration is valid. Using S3 for file storage.")
    else:
        print("S3_BUCKET_NAME not found.")
except (NoCredentialsError, PartialCredentialsError):
    print("AWS credentials not found.")
except ClientError as e:
    if e.response['Error']['Code'] == '404':
        print(f"S3 bucket '{S3_BUCKET}' not found.")
    else:
        print(f"An S3 client error occurred: {e}")
except Exception as e:
    print(f"An unexpected error occurred with S3 setup: {e}")

if not USE_S3:
    print("Using local storage as a fallback.")
    local_storage.setup_local_storage()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Allow your local frontend
        "*"  # Keep the wildcard for other environments if needed
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload/")
async def upload_csv(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    if USE_S3:
        s3_key = f"sessions/{session_id}/{file.filename}"
        s3.upload_fileobj(file.file, S3_BUCKET, s3_key)
    else:
        local_storage.save_uploaded_file(session_id, file)
    
    return {"session_id": session_id, "file_name": file.filename}

@app.post("/analyze/")
async def analyze_csv(
    session_id: str = Form(...),
    user_query: str = Form(...)
):
    local_path = None
    if USE_S3:
        prefix = f"sessions/{session_id}/"
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
        files = response.get("Contents", [])
        if not files:
            return JSONResponse(content={"error": "No file found for session"}, status_code=404)
        s3_key = files[0]["Key"]
        
        # Define a local path for temporary processing
        local_path = f"/tmp/{os.path.basename(s3_key)}"
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        s3.download_file(S3_BUCKET, s3_key, local_path)
    else:
        local_path = local_storage.get_session_file(session_id)
        if not local_path:
            return JSONResponse(content={"error": "No file found for session"}, status_code=404)

    csv_info = extract_csv_metadata_and_sample(local_path)
    code = generate_code_from_query(session_id, local_path, user_query)
    output, error, flags = run_generated_code(code, local_path)

    image_key = None
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    image_path = "output.png"

    if os.path.exists(image_path):
        if USE_S3:
            image_s3_key = f"sessions/{session_id}/output_{timestamp}.png"
            s3.upload_file(image_path, S3_BUCKET, image_s3_key)
            image_key = image_s3_key
        else:
            # For local storage, the key is the timestamp
            local_storage.save_output_image(session_id, image_path, timestamp)
            image_key = timestamp

    response = {
        "metadata_and_sample": csv_info,
        "generated_code": code,
        "stdout": output,
        "stderr": error,
        "flags": flags,
        "image_key": image_key,
        "image_timestamp": timestamp if image_key else None
    }

    return JSONResponse(content=response)

@app.post("/clear_session/")
async def clear_session(session_id: str = Form(...)):
    deletion_success = True
    error_messages = []

    # Step 1: Clear storage (S3 or local)
    try:
        if USE_S3:
            prefix = f"sessions/{session_id}/"
            # List all objects including potential hidden files
            response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
            files = response.get("Contents", [])
            if files:
                for obj in files:
                    try:
                        s3.delete_object(Bucket=S3_BUCKET, Key=obj["Key"])
                    except Exception as e:
                        error_messages.append(f"Failed to delete S3 object {obj['Key']}: {str(e)}")
                        deletion_success = False
            
            # Double-check deletion
            check_response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
            if check_response.get("Contents"):
                error_messages.append("Some S3 objects remained after deletion attempt")
                deletion_success = False
        else:
            # Local storage cleanup
            if not local_storage.clear_local_session(session_id):
                error_messages.append("Failed to fully clear local session directory")
                deletion_success = False
    except Exception as e:
        error_messages.append(f"Storage cleanup error: {str(e)}")
        deletion_success = False

    # Step 2: Clear memory
    try:
        clear_memory(session_id)
    except Exception as e:
        error_messages.append(f"Memory cleanup error: {str(e)}")
        deletion_success = False

    # Step 3: Clear any temporary files
    try:
        temp_patterns = [
            f"/tmp/*{session_id}*",
            f"/tmp/finanalyst_sessions/{session_id}*",
            f"output_{session_id}_*.png"
        ]
        for pattern in temp_patterns:
            for temp_file in Path("/tmp").glob(pattern):
                try:
                    if temp_file.is_file():
                        os.remove(temp_file)
                    elif temp_file.is_dir():
                        shutil.rmtree(temp_file, ignore_errors=True)
                except Exception as e:
                    error_messages.append(f"Failed to clean temp file {temp_file}: {str(e)}")
                    # Don't set deletion_success to False for temp files
    except Exception as e:
        error_messages.append(f"Temp cleanup error: {str(e)}")
        # Don't set deletion_success to False for temp cleanup errors

    if deletion_success:
        return JSONResponse(content={"status": "session cleared successfully"})
    else:
        return JSONResponse(
            content={
                "status": "session cleanup partially failed",
                "errors": error_messages
            },
            status_code=500
        )

@app.get("/get_image/")
async def get_image(session_id: str = Query(...), timestamp: str = Query(...)):
    if USE_S3:
        image_s3_key = f"sessions/{session_id}/output_{timestamp}.png"
        local_path = f"/tmp/output_{session_id}_{timestamp}.png"
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        try:
            s3.download_file(S3_BUCKET, image_s3_key, local_path)
            return FileResponse(local_path, media_type="image/png", filename=f"output_{timestamp}.png")
        except ClientError:
            return JSONResponse(content={"error": "No image found"}, status_code=404)
    else:
        # The local implementation uses a slightly different path structure
        image_path = local_storage.get_image_path(session_id, timestamp)
        if image_path and os.path.exists(image_path):
            return FileResponse(image_path, media_type="image/png", filename=f"output_{timestamp}.png")
        else:
            # Check the alternative path for compatibility
            legacy_path = f"/tmp/finanalyst_sessions/{session_id}/output_{session_id}_{timestamp}.png"
            if os.path.exists(legacy_path):
                return FileResponse(legacy_path, media_type="image/png", filename=f"output_{timestamp}.png")
            return JSONResponse(content={"error": "No image found"}, status_code=404)