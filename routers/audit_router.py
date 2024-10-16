from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from database.session import get_db
from models.Audit import Audit
from .dependencies import required_permission
from config import PermissionEnum
from schemas import AuditLogResponse

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(required_permission(PermissionEnum.VIEW_CHANGE_LOG))]
)

@router.get("/", response_model=List[AuditLogResponse])
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
    ):
    offset = (page - 1) * page_size
    audit_logs = db.query(Audit).offset(offset).limit(page_size).all()
    if not audit_logs:
        raise HTTPException(status_code=404, detail="No audit logs found")
    result = [
        AuditLogResponse(
            timestamp=audit.timestamp,
            email=audit.email,
            action=audit.action,
            details=audit.details
        ) for audit in audit_logs
    ]
    return result

# Download the audit logs as CSV
@router.get("/download", response_class=FileResponse)
async def download_audit_logs(
    db: Session = Depends(get_db)
    ):
    audit_logs = db.query(Audit).all()
    if not audit_logs:
        raise HTTPException(status_code=404, detail="No audit logs found")
    csv_file = "timestamp,email,action,details\n"
    for audit in audit_logs:
        action = audit.action.value
        csv_file += f"{audit.timestamp},{audit.email},{action},{audit.details}\n"
    response = Response(content=csv_file, media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=audit_logs.csv"
    return response