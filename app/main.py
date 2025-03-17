from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.routes import TimeEntry, auth, clientes, reports, tasks

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

@app.get('/')
def root():
    pass