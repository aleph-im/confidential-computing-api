import uvicorn
from fastapi import FastAPI

from endpoints.platform import router as platform_router
from endpoints.vms import router as vm_router

app = FastAPI(title="Aleph SEV Compute Resource Node")


app.include_router(platform_router)
app.include_router(vm_router)


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
