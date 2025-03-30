from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.routes import TimeEntry, auth, clientes, contracts, reports, tasks, events

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)


app.include_router(auth.router)
app.include_router(clientes.router)
app.include_router(tasks.router)
app.include_router(TimeEntry.router)
app.include_router(reports.router)
app.include_router(events.router)
app.include_router(contracts.router)

@app.get('/')
def root():
    pass