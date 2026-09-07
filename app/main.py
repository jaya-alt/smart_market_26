from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config import GENERATED_DIR, BASE_DIR
from app.agent.agent import run_agent, clear_session, get_last_generated_files

from app.tools.inventory_tools import get_low_stock, get_all_products
from app.services.sales_service import get_daily_close
from app.services.billing_service import (
    create_draft_bill,
    add_item_to_bill,
    get_bill_details,
    edit_bill_item_by_name,
    remove_bill_item_by_name,
    finalize_bill
)


# ============================================================
# PATHS
# ============================================================

FRONTEND_DIR = BASE_DIR / "frontend"


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Supermarket Ops Agent API",
    description="AI-powered Supermarket Operations Management System",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ClearSessionRequest(BaseModel):
    session_id: str = "default"


class CreateBillRequest(BaseModel):
    payment_mode: Optional[str] = None


class AddBillItemRequest(BaseModel):
    bill_id: int
    product_name: str
    quantity: float


class EditBillItemRequest(BaseModel):
    bill_id: int
    product_name: str
    quantity: float


class RemoveBillItemRequest(BaseModel):
    bill_id: int
    product_name: str


class FinalizeBillRequest(BaseModel):
    bill_id: int
    payment_mode: Optional[str] = None


# ============================================================
# BASIC API
# ============================================================

@app.get("/api")
def api_root():
    return {
        "success": True,
        "message": "Supermarket Ops Agent API is running.",
        "version": "2.1.0"
    }


@app.get("/health")
def health():
    return {"success": True, "status": "healthy", "service": "Supermarket Ops Agent"}


# ============================================================
# AI CHAT
# ============================================================

@app.post("/chat")
def chat(request: ChatRequest):
    try:
        if not request.message.strip():
            return {"success": False, "response": "Please enter a message."}

        response = run_agent(user_message=request.message, session_id=request.session_id)
        files = get_last_generated_files(request.session_id)

        return {
            "success": True,
            "response": response,
            "files": [str(Path(f).name) for f in files]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/session/clear")
def clear_chat_session(request: ClearSessionRequest):
    try:
        return clear_session(request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# INVENTORY
# ============================================================

@app.get("/inventory")
def inventory():
    try:
        return get_all_products()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/low-stock")
def low_stock():
    try:
        return get_low_stock()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# DAILY CLOSING
# ============================================================

@app.get("/daily-close")
def daily_close():
    try:
        return get_daily_close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# BILLING
# ============================================================

@app.post("/billing/create")
def create_bill(request: CreateBillRequest):
    try:
        return create_draft_bill(payment_mode=request.payment_mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/billing/add-item")
def add_bill_item(request: AddBillItemRequest):
    try:
        return add_item_to_bill(
            bill_id=request.bill_id,
            product_name=request.product_name,
            quantity=request.quantity
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/billing/{bill_id}")
def bill_details(bill_id: int):
    try:
        return get_bill_details(bill_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/billing/edit-item")
def edit_bill_item_api(request: EditBillItemRequest):
    try:
        return edit_bill_item_by_name(
            bill_id=request.bill_id,
            product_name=request.product_name,
            quantity=request.quantity
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/billing/remove-item")
def remove_bill_item_api(request: RemoveBillItemRequest):
    try:
        return remove_bill_item_by_name(
            bill_id=request.bill_id,
            product_name=request.product_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/billing/finalize")
def finalize_bill_api(request: FinalizeBillRequest):
    try:
        return finalize_bill(bill_id=request.bill_id, payment_mode=request.payment_mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# GENERATED FILES
# ============================================================

@app.get("/files")
def list_files():
    try:
        files = []

        if GENERATED_DIR.exists():
            for path in GENERATED_DIR.rglob("*"):
                if path.is_file():
                    files.append({
                        "name": path.name,
                        "path": str(path.relative_to(GENERATED_DIR)),
                        "size": path.stat().st_size
                    })

        return {"success": True, "count": len(files), "files": files}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{file_path:path}")
def download_file(file_path: str):
    try:
        requested_file = (GENERATED_DIR / file_path).resolve()
        generated_root = GENERATED_DIR.resolve()

        if not str(requested_file).startswith(str(generated_root)):
            raise HTTPException(status_code=403, detail="Access denied.")

        if not requested_file.exists():
            raise HTTPException(status_code=404, detail="File not found.")

        if not requested_file.is_file():
            raise HTTPException(status_code=400, detail="Requested path is not a file.")

        return FileResponse(path=str(requested_file), filename=requested_file.name)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# API INFO
# ============================================================

@app.get("/api-info")
def api_info():
    return {
        "success": True,
        "application": "Supermarket Ops Agent",
        "modules": [
            "AI Assistant", "Inventory Management", "Billing",
            "GST Invoice", "Khata", "Sales Reports", "Daily Closing",
            "PowerPoint Reports"
        ],
        "endpoints": {
            "chat": "/chat",
            "clear_session": "/session/clear",
            "inventory": "/inventory",
            "low_stock": "/low-stock",
            "daily_close": "/daily-close",
            "create_bill": "/billing/create",
            "add_item": "/billing/add-item",
            "bill_details": "/billing/{bill_id}",
            "edit_item": "/billing/edit-item",
            "remove_item": "/billing/remove-item",
            "finalize": "/billing/finalize",
            "files": "/files",
            "download": "/download/{file_path}"
        }
    }


# ============================================================
# FRONTEND (optional; only served if app/../frontend exists)
# ============================================================

@app.get("/", include_in_schema=False)
def frontend_home():
    index_file = FRONTEND_DIR / "index.html"

    if not index_file.exists():
        return {
            "success": True,
            "message": "Supermarket Ops Agent API is running. See /docs for the API, "
                       "or message the Telegram bot directly."
        }

    return FileResponse(path=str(index_file), media_type="text/html")


@app.get("/style.css", include_in_schema=False)
def frontend_css():
    css_file = FRONTEND_DIR / "style.css"
    if not css_file.exists():
        raise HTTPException(status_code=404, detail="frontend/style.css not found.")
    return FileResponse(path=str(css_file), media_type="text/css")


@app.get("/app.js", include_in_schema=False)
def frontend_js():
    js_file = FRONTEND_DIR / "app.js"
    if not js_file.exists():
        raise HTTPException(status_code=404, detail="frontend/app.js not found.")
    return FileResponse(path=str(js_file), media_type="application/javascript")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
