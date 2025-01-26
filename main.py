from typing import List, Optional
import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Body
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uuid

app = FastAPI(title="FAST API REST Demo 🔥",version="1.0.0")


# Model for creating/updating items
class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None


# In-memory storage for items
items_db = {}


# Root endpoint
@app.get("/")
def read_root():
    return {"Hello": "World"}


# GET endpoint to retrieve all items
@app.get("/items")
def read_items():
    return list(items_db.values())


# GET endpoint with path parameter
@app.get("/items/{item_id}")
def read_item(item_id: str):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]


# GET endpoint with query parameters
@app.get("/items/search")
def search_items(
        name: Optional[str] = Query(None, min_length=1, max_length=50),
        min_price: Optional[float] = Query(None, ge=0)
):
    filtered_items = [
        item for item in items_db.values()
        if (name is None or name.lower() in item.name.lower()) and
           (min_price is None or item.price >= min_price)
    ]
    return filtered_items


# POST endpoint to create a new item
@app.post("/items")
def create_item(item: Item):
    item_id = str(uuid.uuid4())
    items_db[item_id] = {"id": item_id, **item.model_dump()}
    return {"id": item_id, **item.model_dump()}


# PUT endpoint to update an existing item
@app.put("/items/{item_id}")
def update_item(item_id: str, item: Item):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")

    # Update the item while preserving its ID
    updated_item = {"id": item_id, **item.model_dump()}
    items_db[item_id] = updated_item
    return updated_item


# PATCH endpoint for partial update
@app.patch("/items/{item_id}")
def patch_item(item_id: str, item: dict = Body(...)):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")

    # Partial update
    existing_item = items_db[item_id]
    for key, value in item.items():
        existing_item[key] = value

    return existing_item


# DELETE endpoint
@app.delete("/items/{item_id}")
def delete_item(item_id: str):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")

    del items_db[item_id]
    return {"message": "Item deleted successfully"}


# File upload endpoint
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Create uploads directory if it doesn't exist
    os.makedirs("uploads", exist_ok=True)

    # Generate unique filename
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else ''
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join("uploads", unique_filename)

    # Save the file
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return {
        "filename": unique_filename,
        "original_filename": file.filename,
        "message": "File uploaded successfully"
    }


# File download endpoint
@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join("uploads", filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        media_type='application/octet-stream',
        filename=filename
    )


# List uploaded files
@app.get("/files")
def list_files():
    try:
        files = os.listdir("uploads")
        return {"files": files}
    except FileNotFoundError:
        return {"files": []}


# Multiple file upload
@app.post("/upload-multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    os.makedirs("uploads", exist_ok=True)

    uploaded_files = []
    for file in files:
        # Generate unique filename
        file_ext = file.filename.split('.')[-1] if '.' in file.filename else ''
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join("uploads", unique_filename)

        # Save the file
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        uploaded_files.append({
            "filename": unique_filename,
            "original_filename": file.filename
        })

    return {"uploaded_files": uploaded_files}