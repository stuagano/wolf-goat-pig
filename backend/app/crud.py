from . import models, database

def get_rules(db):
    return db.query(models.Rule).all() 