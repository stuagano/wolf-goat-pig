from . import models, database

def get_rules():
    db = database.SessionLocal()
    return db.query(models.Rule).all() 