from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import auth, users, datasets, events, incidents, notes, chat, reports, admin

app = FastAPI(
    title="IntelliBlue SOC API",
    description="Offline Security Operations Center assistant",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(datasets.router)
app.include_router(events.router)
app.include_router(incidents.router)
app.include_router(notes.router)
app.include_router(chat.router)
app.include_router(reports.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "IntelliBlue SOC"}
