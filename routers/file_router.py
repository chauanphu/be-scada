# Serve the firmware file
import os
import hashlib
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

router = APIRouter(
    prefix='/file',
    tags=['file']
)

FIRMWARE_DIRECTORY = "./firmware_files"

# Serve the firmware file
@router.get("/{filename}")
def get_firmware(filename: str):
    file_path = os.path.join(FIRMWARE_DIRECTORY, filename)

    if os.path.exists(file_path):
        # Add checksum file if it exists
        checksum_file = file_path + ".sha256"
        if os.path.exists(checksum_file):
            with open(checksum_file, "r") as f:
                checksum = f.read()
            return FileResponse(file_path, media_type='application/octet-stream', headers={"X-Checksum": checksum})
        return FileResponse(file_path, media_type='application/octet-stream')
    else:
        raise HTTPException(status_code=404, detail="Firmware not found")
    
@router.get("/version")
def get_version():
    return {
        "version": "1.0.2",
        "description": "This is version 1.0.2 of the ESP32 firmware"
    }

def write_binary_file(file_location, data):
    try:
        with open(file_location, "wb") as f:
            # Write data in chunks
            chunk_size = 1024 * 1024  # 1 MB
            for i in range(0, len(data), chunk_size):
                f.write(data[i:i + chunk_size])
        
        # Verify data integrity
        with open(file_location, "rb") as f:
            written_data = f.read()
            if written_data != data:
                raise ValueError("Data integrity check failed: written data does not match original data")
    except Exception as e:
        # Log the exception (you can use logging module for more advanced logging)
        print(f"An error occurred: {e}")
        # Optionally, remove the corrupted file
        if os.path.exists(file_location):
            os.remove(file_location)
        raise
    
# Upload the firmware file
@router.post("/upload/")
async def upload_firmware(file: UploadFile = File(...)):
    if not file.filename.endswith(".bin"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .bin files are allowed.")

    file_location = os.path.join(FIRMWARE_DIRECTORY, file.filename)

    # Save the uploaded file and calculate checksum
    file_content = await file.read()
    write_binary_file(file_location, file_content)

    # Calculate SHA-256 hash
    sha256_hash = hashlib.sha256(file_content).hexdigest()
    hash_file_location = file_location + ".sha256"

    # Write the hash to a .sha256 file
    with open(hash_file_location, "w") as hash_file:
        hash_file.write(sha256_hash)

    return {"filename": file.filename, "message": "File uploaded successfully"}

@router.get("/checksum/{filename}")
async def get_checksum(filename: str):
    file_location = os.path.join(FIRMWARE_DIRECTORY, filename)
    
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail="File not found")

    with open(file_location, "rb") as f:
        file_content = f.read()

    sha256_hash = hashlib.sha256(file_content).hexdigest()
    return {"filename": filename, "checksum": sha256_hash}