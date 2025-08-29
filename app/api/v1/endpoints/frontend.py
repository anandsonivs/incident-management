from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import os
from pathlib import Path

router = APIRouter()

# Get the frontend directory path - corrected path
frontend_dir = Path(__file__).parent.parent.parent.parent.parent / "app" / "frontend"

@router.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the main index.html file."""
    index_path = frontend_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    
    with open(index_path, 'r') as f:
        return HTMLResponse(content=f.read())

@router.get("/login.html", response_class=HTMLResponse)
async def serve_login():
    """Serve the login.html file."""
    login_path = frontend_dir / "login.html"
    if not login_path.exists():
        raise HTTPException(status_code=404, detail="Login page not found")
    
    with open(login_path, 'r') as f:
        return HTMLResponse(content=f.read())

@router.get("/{filename}")
async def serve_static_file(filename: str):
    """Serve static files (CSS, JS, etc.)."""
    file_path = frontend_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)
