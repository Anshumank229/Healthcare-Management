from fastapi import FastAPI
app=FastAPI(Tittle='Healthcare-Management')

app = FastAPI(title="Healthcare Management API")

@app.get("/")
def root():
    return {"message": "Healthcare API is running"}