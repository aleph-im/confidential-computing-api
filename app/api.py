from pathlib import Path

import uvicorn
from fastapi import FastAPI

from models.db import Base, engine

from endpoints.platform import router as platform_router
from endpoints.vms import router as vm_router

DOWNLOAD_DIR = Path.cwd().absolute() / "downloads"

GUEST_OWNER_CERTIFICATE_FILES = "godh.cert", "launch_blob.bin"

app = FastAPI(title="Aleph SEV Compute Resource Node")


app.include_router(platform_router)
app.include_router(vm_router)


# @app.get("/users/me")
# def read_current_user(username: str = Depends(get_current_username)):
#     return {"username": username}


@app.on_event("startup")
async def startup():
    # Create db tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
