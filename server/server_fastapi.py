import os
import sys
import base64
import tempfile
from typing import Optional, Literal

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


# -------------------------------------------------
# Make project root importable
# -------------------------------------------------

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

import print as print_module


# -------------------------------------------------
# Configuration
# -------------------------------------------------

API_TOKEN = os.getenv("THERMAL_API_TOKEN")

if not API_TOKEN:
    raise RuntimeError("THERMAL_API_TOKEN environment variable not set.")


# -------------------------------------------------
# FastAPI App
# -------------------------------------------------

app = FastAPI(title="Thermal Printer API")

WEB_FOLDER = os.path.join(PROJECT_ROOT, "website_to_print")
app.mount("/static", StaticFiles(directory=WEB_FOLDER, html=True), name="static")


# -------------------------------------------------
# Authentication
# -------------------------------------------------

def verify_token(x_api_key: str = Header(...)):
    if x_api_key != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API token")


# -------------------------------------------------
# Request Models
# -------------------------------------------------

class PrintOptions(BaseModel):
    mode: Literal["text", "image", "raw"]
    cut: bool = False


class PrintRequest(BaseModel):
    text: Optional[str] = None
    file_base64: Optional[str] = None
    filename: Optional[str] = None
    options: PrintOptions


# -------------------------------------------------
# API Endpoint
# -------------------------------------------------

@app.post("/api/print", dependencies=[Depends(verify_token)])
def print_endpoint(request: PrintRequest):

    if not request.text and not (request.file_base64 and request.filename):
        raise HTTPException(
            status_code=400,
            detail="Provide either 'text' or ('file_base64' and 'filename')."
        )

    temp_file_path = None

    try:
        # -----------------------------
        # Handle text
        # -----------------------------
        if request.text:
            temp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
            temp.write(request.text.encode("utf-8"))
            temp.close()
            temp_file_path = temp.name

        # -----------------------------
        # Handle base64 file
        # -----------------------------
        elif request.file_base64 and request.filename:
            decoded = base64.b64decode(request.file_base64)
            suffix = os.path.splitext(request.filename)[1] or ".bin"
            temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp.write(decoded)
            temp.close()
            temp_file_path = temp.name

        # -----------------------------
        # Call Core Print Engine
        # -----------------------------
        print_module.core_print(
            file=temp_file_path,
            mode=request.options.mode,
            cut=request.options.cut,
            extra_args=[]
        )

        return {"status": "success"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass