from fastapi import FastAPI, Depends
from . import models, schemas, crud, database

app = FastAPI()

@app.on_event("startup")
def startup():
    database.init_db()

@app.get("/rules", response_model=list[schemas.Rule])
def get_rules():
    return crud.get_rules() 