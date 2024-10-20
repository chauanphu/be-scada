# Serve the firmware file
import os
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
        return FileResponse(file_path, media_type='application/octet-stream')
    else:
        raise HTTPException(status_code=404, detail="Firmware not found")
@router.get("/version")
def get_version():
    return {
        "version": "1.0.2",
        "description": "This is version 1.0.2 of the ESP32 firmware"
    }

# Upload the firmware file
@router.post("/upload/")
async def upload_firmware(file: UploadFile = File(...)):
    if not file.filename.endswith(".bin"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .bin files are allowed.")

    file_location = os.path.join(FIRMWARE_DIRECTORY, file.filename)

    # Save the uploaded file
    with open(file_location, "wb") as f:
        f.write(await file.read())

    return {"filename": file.filename, "message": "File uploaded successfully"}
