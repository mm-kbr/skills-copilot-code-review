"""
Announcements endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


def is_valid_date(date_string: str) -> bool:
    """Validate ISO date format"""
    try:
        datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return True
    except (ValueError, TypeError):
        return False


def is_announcement_active(announcement: Dict) -> bool:
    """Check if announcement is currently active based on start and expiration dates"""
    now = datetime.now().date()
    
    # Check start date
    if announcement.get("start_date"):
        start_date = datetime.fromisoformat(
            announcement["start_date"].replace('Z', '+00:00')
        ).date()
        if now < start_date:
            return False
    
    # Check expiration date
    if announcement.get("expiration_date"):
        expiration_date = datetime.fromisoformat(
            announcement["expiration_date"].replace('Z', '+00:00')
        ).date()
        if now > expiration_date:
            return False
    
    return True


@router.get("/")
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get all active announcements"""
    all_announcements = list(announcements_collection.find({}))
    
    # Filter active announcements and format
    active_announcements = []
    for announcement in all_announcements:
        if is_announcement_active(announcement):
            announcement["_id"] = str(announcement["_id"])
            active_announcements.append(announcement)
    
    return active_announcements


@router.get("/all")
def get_all_announcements(username: str = Query(...)) -> List[Dict[str, Any]]:
    """Get all announcements (for authenticated users only)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    all_announcements = list(announcements_collection.find({}))
    
    # Format announcements
    for announcement in all_announcements:
        announcement["_id"] = str(announcement["_id"])
    
    return all_announcements


@router.post("/")
def create_announcement(
    title: str = Query(...),
    message: str = Query(...),
    expiration_date: str = Query(...),
    start_date: Optional[str] = Query(None),
    username: str = Query(...)
) -> Dict[str, Any]:
    """Create a new announcement (authenticated users only)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Validate dates
    if not is_valid_date(expiration_date):
        raise HTTPException(status_code=400, detail="Invalid expiration_date format. Use ISO format (YYYY-MM-DD)")
    
    if start_date and not is_valid_date(start_date):
        raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format (YYYY-MM-DD)")
    
    # Create announcement
    announcement = {
        "title": title,
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "created_by": username,
        "created_at": datetime.now().isoformat() + "Z"
    }
    
    result = announcements_collection.insert_one(announcement)
    announcement["_id"] = str(result.inserted_id)
    
    return announcement


@router.put("/{announcement_id}")
def update_announcement(
    announcement_id: str,
    title: str = Query(...),
    message: str = Query(...),
    expiration_date: str = Query(...),
    start_date: Optional[str] = Query(None),
    username: str = Query(...)
) -> Dict[str, Any]:
    """Update an announcement (authenticated users only)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Validate dates
    if not is_valid_date(expiration_date):
        raise HTTPException(status_code=400, detail="Invalid expiration_date format. Use ISO format (YYYY-MM-DD)")
    
    if start_date and not is_valid_date(start_date):
        raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format (YYYY-MM-DD)")
    
    # Check if announcement exists
    try:
        obj_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    announcement = announcements_collection.find_one({"_id": obj_id})
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    # Update announcement
    update_data = {
        "title": title,
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "updated_by": username,
        "updated_at": datetime.now().isoformat() + "Z"
    }
    
    announcements_collection.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )
    
    # Return updated announcement
    updated = announcements_collection.find_one({"_id": obj_id})
    updated["_id"] = str(updated["_id"])
    
    return updated


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    username: str = Query(...)
) -> Dict[str, str]:
    """Delete an announcement (authenticated users only)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Check if announcement exists
    try:
        obj_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    announcement = announcements_collection.find_one({"_id": obj_id})
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    # Delete announcement
    announcements_collection.delete_one({"_id": obj_id})
    
    return {"message": "Announcement deleted successfully", "id": announcement_id}
