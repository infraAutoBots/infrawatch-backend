import os
import uvicorn
from fastapi import FastAPI
from auth_routes import auth_router
from monitor_routes import monitor_router



app = FastAPI()


app.include_router(auth_router)
app.include_router(monitor_router)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000))
    )
