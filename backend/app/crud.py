from . import models


def get_rules(db):
    return db.query(models.Rule).all()
