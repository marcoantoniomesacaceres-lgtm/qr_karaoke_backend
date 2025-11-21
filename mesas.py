from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import crud, schemas, models
import re # Importar para el filtro de groserías
from database import SessionLocal
from security import api_key_auth

router = APIRouter()

# Lista de palabras inapropiadas (puedes expandirla según sea necesario)
PROFANITY_LIST = {
    "puta","pene","vagina","parolo", "pendejo", "cabron", "mierda", "coño", "gilipollas", "joder",
    "culero", "chinga", "verga", "mamón", "idiota", "imbecil", "zorra",
    "maricon", "puto", "fuck", "shit", "asshole", "bitch", "cunt", "dick",
    "bastard", "whore", "faggot", "perra", "cagon", "caca", "culo", "lameculo","teta"
}

def contains_profanity(text: str) -> bool:
    """Verifica si el texto contiene palabras inapropiadas (case-insensitive y por palabra)."""
    normalized_text = re.sub(r'[_\-.]', ' ', text.lower()) # Reemplazar separadores comunes con espacios
    words = normalized_text.split()
    return any(word in PROFANITY_LIST for word in words)

# Dependencia para obtener la sesión de la base de datos en cada request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[schemas.Mesa], summary="Listar todas las mesas", dependencies=[Depends(api_key_auth)])
def get_mesas(db: Session = Depends(get_db)):
    """
    **[Admin]** Devuelve una lista de todas las mesas creadas en el sistema.
    """
    mesas = crud.get_mesas(db)
    return mesas

@router.post("/", response_model=schemas.Mesa, status_code=201, summary="Crear una nueva mesa", dependencies=[Depends(api_key_auth)])
def create_mesa_endpoint(
    mesa: schemas.MesaCreate, 
    db: Session = Depends(get_db)
):
    """
    Crea una nueva mesa en el sistema con un nombre y un código QR único.
    """
    db_mesa = crud.get_mesa_by_qr(db, qr_code=mesa.qr_code)
    if db_mesa:
        raise HTTPException(status_code=400, detail="El código QR ya está registrado")
    try:
        return crud.create_mesa(db=db, mesa=mesa)
    except Exception as e:
        # Manejar colisiones de unique constraint en caso de condiciones de carrera
        try:
            from sqlalchemy.exc import IntegrityError
            if isinstance(e, IntegrityError):
                raise HTTPException(status_code=400, detail="El código QR ya está registrado (conflicto).")
        except Exception:
            # si sqlalchemy no está disponible por alguna razón, continuar con manejo genérico
            pass
        # Si no es un IntegrityError, relanzamos como 500 para no ocultar errores inesperados
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{qr_code}/conectar", response_model=schemas.Usuario, summary="Conectar un usuario a una mesa")
def conectar_usuario_a_mesa(
    qr_code: str, usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)
):
    """
    Busca una mesa por su QR y crea un nuevo usuario asociado a ella.
    LIMITACIÓN: Máximo 10 usuarios pueden estar conectados a la misma mesa.
    Este es el endpoint que el cliente usa al escanear el QR.
    """
    db_mesa = crud.get_mesa_by_qr(db, qr_code=qr_code)
    if not db_mesa:
        raise HTTPException(status_code=404, detail=f"El código QR '{qr_code}' no corresponde a ninguna mesa válida.")

    if not db_mesa.is_active:
        raise HTTPException(status_code=403, detail="Esta mesa se encuentra desactivada temporalmente. Por favor, contacta al personal.")
    
    # NUEVO: Verificar límite de usuarios conectados (máximo 10)
    usuarios_activos = db.query(models.Usuario).filter(
        models.Usuario.mesa_id == db_mesa.id,
        models.Usuario.is_active == True
    ).count()
    
    if usuarios_activos >= 10:
        raise HTTPException(
            status_code=429, 
            detail="La mesa ha alcanzado el máximo de 10 usuarios conectados. Por favor, intenta más tarde."
        )
    
    # 1. Validación de palabras inapropiadas
    if contains_profanity(usuario.nick):
        raise HTTPException(status_code=400, detail="El apodo contiene palabras inapropiadas. Por favor, elige otro.")

    # Verificamos si el nick ya está en uso o baneado en una sola consulta
    db_usuario_existente = crud.get_usuario_by_nick(db, nick=usuario.nick)
    if db_usuario_existente:
        # 2. Mensaje más sugerente para apodos repetidos
        raise HTTPException(status_code=409, detail=f"El apodo '{usuario.nick}' ya está en uso. Intenta con '{usuario.nick}1', '{usuario.nick}_karaoke' o similar.")

    # Si el nick no está en uso, verificamos si está en la lista de baneados
    if crud.is_nick_banned(db, nick=usuario.nick):
        raise HTTPException(status_code=403, detail="Este nick de usuario ha sido bloqueado y no puede registrarse.")

    return crud.create_usuario_en_mesa(db=db, usuario=usuario, mesa_id=db_mesa.id)

@router.get("/{mesa_id}/usuarios-conectados", response_model=List[schemas.UsuarioConectado], summary="Ver usuarios conectados a una mesa")
def get_usuarios_conectados(mesa_id: int, db: Session = Depends(get_db)):
    """
    Devuelve la lista de usuarios conectados actualmente a una mesa específica (máximo 10).
    Incluye nick, puntos, nivel y si están activos.
    """
    mesa = crud.get_mesa_by_id(db, mesa_id=mesa_id)
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada.")
    
    usuarios_activos = db.query(models.Usuario).filter(
        models.Usuario.mesa_id == mesa_id,
        models.Usuario.is_active == True
    ).all()
    
    return usuarios_activos

@router.get("/{mesa_id}/payment-status", response_model=schemas.MesaEstadoPago, summary="Obtener estado de cuenta de una mesa")
def get_mesa_payment_status(mesa_id: int, db: Session = Depends(get_db)):
    """
    Endpoint público que devuelve el estado de cuenta de una mesa específica.
    Incluye total consumido, total pagado, saldo pendiente, y listas de consumos y pagos.
    Este endpoint es accesible desde la dashboard de usuarios para ver "Mi Cuenta".
    """
    status = crud.get_table_payment_status(db, mesa_id=mesa_id)
    if not status:
        raise HTTPException(status_code=404, detail="Mesa no encontrada.")
    return status