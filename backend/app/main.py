"""FastAPI 应用入口"""
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import Base, engine, get_db
from app.schemas import RuleCreate
from app.crud import RuleCRUD

app = FastAPI(title="Agent APS Rule Manager")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.post("/api/rules", status_code=201)
def create_rule(rule: RuleCreate, db: Session = Depends(get_db)):
    crud = RuleCRUD(db)
    return crud.create(rule)


@app.get("/api/rules")
def list_rules(
    rule_type: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    crud = RuleCRUD(db)
    return crud.list_all(rule_type=rule_type, status=status)


@app.get("/api/rules/{rule_id}")
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    crud = RuleCRUD(db)
    rule = crud.get_by_id(rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@app.put("/api/rules/{rule_id}")
def update_rule(rule_id: int, data: dict, db: Session = Depends(get_db)):
    crud = RuleCRUD(db)
    rule = crud.update(rule_id, data)
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@app.delete("/api/rules/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    crud = RuleCRUD(db)
    if not crud.delete(rule_id):
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"ok": True}
