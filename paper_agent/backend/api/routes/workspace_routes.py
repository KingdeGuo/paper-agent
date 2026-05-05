"""Complete workspace team collaboration API."""

import logging

from backend.services.registry import get_db
from backend.services.workspace_service import WorkspaceService
from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()


def get_ws(db=Depends(get_db)) -> WorkspaceService:
    return WorkspaceService(db)


@router.post("/workspaces", summary="Create a research workspace")
async def create_workspace(name: str, description: str = "", user_id: str = "default",
                           ws: WorkspaceService = Depends(get_ws)):
    return await ws.create_workspace(name, user_id, description)


@router.get("/workspaces", summary="List user's workspaces")
async def list_workspaces(user_id: str = "default", ws: WorkspaceService = Depends(get_ws)):
    return await ws.list_user_workspaces(user_id)


@router.get("/workspaces/{workspace_id}", summary="Get workspace details")
async def get_workspace(workspace_id: str, user_id: str = "default", ws=Depends(get_ws)):
    result = await ws.get_workspace(workspace_id, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return result


@router.put("/workspaces/{workspace_id}", summary="Update workspace")
async def update_workspace(workspace_id: str, name: str = None, description: str = None,
                           is_public: bool = None, user_id: str = "default", ws=Depends(get_ws)):
    kwargs = {}
    if name is not None: kwargs["name"] = name
    if description is not None: kwargs["description"] = description
    if is_public is not None: kwargs["is_public"] = is_public
    return await ws.update_workspace(workspace_id, user_id, **kwargs)


@router.delete("/workspaces/{workspace_id}", summary="Delete workspace")
async def delete_workspace(workspace_id: str, user_id: str = "default", ws=Depends(get_ws)):
    if not await ws.delete_workspace(workspace_id, user_id):
        raise HTTPException(status_code=403, detail="Only the owner can delete a workspace")
    return {"message": "Workspace deleted"}


# ─── Membership ──────────────────────────────────────────────

@router.post("/workspaces/{workspace_id}/invite", summary="Invite member")
async def invite_member(workspace_id: str, email: str = None, role: str = "member",
                        user_id: str = "default", ws=Depends(get_ws)):
    return await ws.invite_member(workspace_id, user_id, email=email, role=role)


@router.post("/workspaces/join/{invite_code}", summary="Accept invitation")
async def accept_invitation(invite_code: str, user_id: str = "default", ws=Depends(get_ws)):
    result = await ws.accept_invitation(invite_code, user_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/workspaces/{workspace_id}/members", summary="List workspace members")
async def list_members(workspace_id: str, ws=Depends(get_ws)):
    return await ws.list_members(workspace_id)


@router.put("/workspaces/{workspace_id}/members/{target_user_id}", summary="Update member role")
async def update_member_role(workspace_id: str, target_user_id: str, role: str,
                             user_id: str = "default", ws=Depends(get_ws)):
    if not await ws.update_member_role(workspace_id, target_user_id, role, user_id):
        raise HTTPException(status_code=403, detail="Permission denied")
    return {"message": "Role updated"}


@router.delete("/workspaces/{workspace_id}/members/{target_user_id}", summary="Remove member")
async def remove_member(workspace_id: str, target_user_id: str,
                        user_id: str = "default", ws=Depends(get_ws)):
    if not await ws.remove_member(workspace_id, target_user_id, user_id):
        raise HTTPException(status_code=403, detail="Permission denied")
    return {"message": "Member removed"}


# ─── Shared Documents ────────────────────────────────────────

@router.post("/workspaces/{workspace_id}/documents", summary="Add document to workspace")
async def add_document(workspace_id: str, document_id: str, permission: str = "view",
                       user_id: str = "default", ws=Depends(get_ws)):
    return await ws.add_document(workspace_id, document_id, user_id, permission)


@router.get("/workspaces/{workspace_id}/documents", summary="List workspace documents")
async def list_documents(workspace_id: str, user_id: str = "default", ws=Depends(get_ws)):
    return await ws.list_documents(workspace_id, user_id)


# ─── Annotations ─────────────────────────────────────────────

@router.post("/workspaces/{workspace_id}/annotations", summary="Add annotation")
async def add_annotation(workspace_id: str, document_id: str, content: str,
                         annotation_type: str = "comment", page_number: int = None,
                         user_id: str = "default", ws=Depends(get_ws)):
    return await ws.add_annotation(workspace_id, document_id, user_id, content,
                                    annotation_type, page_number)


@router.get("/workspaces/{workspace_id}/annotations", summary="List annotations")
async def list_annotations(workspace_id: str, document_id: str = None, ws=Depends(get_ws)):
    return await ws.list_annotations(workspace_id, document_id)


# ─── Goals ───────────────────────────────────────────────────

@router.post("/workspaces/{workspace_id}/goals", summary="Create workspace goal")
async def create_goal(workspace_id: str, title: str, target_papers: int = 5,
                      period: str = "weekly", user_id: str = "default", ws=Depends(get_ws)):
    return await ws.create_goal(workspace_id, title, target_papers, period, user_id)


@router.get("/workspaces/{workspace_id}/goals", summary="List workspace goals")
async def list_goals(workspace_id: str, ws=Depends(get_ws)):
    return await ws.list_goals(workspace_id)


# ─── Activity ────────────────────────────────────────────────

@router.get("/workspaces/{workspace_id}/activity", summary="Get workspace activity")
async def get_activity(workspace_id: str, limit: int = 30, ws=Depends(get_ws)):
    return await ws.list_activity(workspace_id, limit)


# ─── Labels ─────────────────────────────────────────────────

@router.post("/workspaces/{workspace_id}/labels", summary="Create label")
async def create_label(workspace_id: str, name: str, color: str = "#2563eb", ws=Depends(get_ws)):
    return await ws.create_label(workspace_id, name, color)


@router.get("/workspaces/{workspace_id}/labels", summary="List labels")
async def list_labels(workspace_id: str, ws=Depends(get_ws)):
    return await ws.list_labels(workspace_id)


# ─── Team Digest ─────────────────────────────────────────────

@router.get("/workspaces/{workspace_id}/digest", summary="Generate team digest")
async def generate_team_digest(workspace_id: str, days: int = 7, ws=Depends(get_ws)):
    return await ws.generate_team_digest(workspace_id, days)
