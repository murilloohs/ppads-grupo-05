from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import security
from app.database.session import get_db
from app.models.enums import UserRole
from app.models.institution import Institution
from app.models.user import User
from app.schemas.token import Token

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/login", response_model=Token)
def login_access_token( db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo"
        )
    
    access_token = security.create_access_token(
        subject=str(user.id),
        email=user.email,
        role=user.role 
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.post("/temp-create-admin")
def temp_create_admin(db: Session = Depends(get_db)):
    inst = db.query(Institution).first()
    if not inst:
        inst = Institution(name="Mackenzie", code="MACK", active=True)
        db.add(inst)
        db.commit()
        db.refresh(inst)

    if db.query(User).filter(User.email == "admin@validahoras.com").first():
        return {"msg": "Admin já existe!"}
    
    new_user = User(
        institution_id=inst.id,
        name="Admin Teste",
        email="admin@validahoras.com",
        password_hash=security.get_password_hash("senha123"),
        role=UserRole.ADMIN,
        active=True
    )
    db.add(new_user)
    db.commit()
    
    return {"msg": "Admin criado com sucesso! E-mail: admin@validahoras.com | Palavra-passe: senha123"}


@router.post("/temp-create-student")
def temp_create_student(db: Session = Depends(get_db)):
    inst = db.query(Institution).first()
    
    if db.query(User).filter(User.email == "aluno@validahoras.com").first():
        return {"msg": "Aluno já existe!"}
    
    new_user = User(
        institution_id=inst.id,
        name="Aluno Teste",
        email="aluno@validahoras.com",
        password_hash=security.get_password_hash("senha123"),
        role=UserRole.STUDENT,
        active=True
    )
    db.add(new_user)
    db.commit()
    
    return {"msg": "Aluno criado com sucesso! E-mail: aluno@validahoras.com | Senha: senha123"}


@router.post("/temp-create-evaluator")
def temp_create_evaluator(db: Session = Depends(get_db)):
    inst = db.query(Institution).first()
    
    if db.query(User).filter(User.email == "avaliador@validahoras.com").first():
        return {"msg": "Avaliador já existe!"}
    
    new_user = User(
        institution_id=inst.id,
        name="Avaliador Teste",
        email="avaliador@validahoras.com",
        password_hash=security.get_password_hash("senha123"),
        role=UserRole.EVALUATOR, 
        active=True
    )
    db.add(new_user)
    db.commit()
    
    return {"msg": "Avaliador criado com sucesso! E-mail: avaliador@validahoras.com | Senha: senha123"}