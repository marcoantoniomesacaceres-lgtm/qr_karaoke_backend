"""
Script to fix the admin_mark_consumo_despachado endpoint
"""
import re

# Read the admin.py file
with open('admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the corrupted function
old_function = r'''@router\.post\('/consumos/\{consumo_id\}/mark-despachado'.*?@router\.get\("/reports/gold-users"'''

new_function = '''@router.post('/consumos/{consumo_id}/mark-despachado', status_code=200, summary='Marcar consumo como despachado')
async def admin_mark_consumo_despachado(consumo_id: int, db: Session = Depends(get_db)):
    """
    **[Admin]** Marca un consumo como despachado.
    No elimina el consumo de la base de datos, solo lo marca como despachado para que no aparezca en "pedidos recientes".
    """
    db_consumo = db.query(models.Consumo).filter(models.Consumo.id == consumo_id).first()
    if not db_consumo:
        raise HTTPException(status_code=404, detail='Consumo no encontrado')

    # Mark as dispatched in DB
    db_consumo.is_dispatched = True
    db.commit()

    # Log the action
    crud.create_admin_log_entry(db, action="MARK_CONSUMO_DESPACHADO", details=f"Consumo ID {consumo_id} marcado como despachado.")

    # Notify clients that this consumption should be removed from recent lists
    try:
        await websocket_manager.manager.broadcast_consumo_deleted({'id': consumo_id})
    except Exception:
        pass # Don't break the response if notification fails

    return {"message": f"Consumo {consumo_id} marcado como despachado."}

@router.get("/reports/gold-users"'''

# Apply the replacement
content_fixed = re.sub(old_function, new_function, content, flags=re.DOTALL)

# Write back
with open('admin.py', 'w', encoding='utf-8') as f:
    f.write(content_fixed)

print("admin.py fixed!")
