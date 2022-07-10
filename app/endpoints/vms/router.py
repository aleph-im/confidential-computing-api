from fastapi import APIRouter

router = APIRouter(
    prefix="/vm",
    tags=["vms"],
)
