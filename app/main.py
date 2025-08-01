from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.routes import TimeEntry, auth, clientes, rentabilitie, reports, tasks, events, google_auth, user_crud,groups,pendientes

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
app.include_router(user_crud.router)
app.include_router(rentabilitie.router)
app.include_router(google_auth.router)
app.include_router(groups.router)
app.include_router(pendientes.router)

@app.get('/')
def root():
    pass