from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime

from liderix_api.db import get_async_session
from liderix_api.schemas.client import ClientRead, ClientCreate, ClientUpdate
from liderix_api.models.client import Client
from liderix_api.models.users import User
from liderix_api.services.auth import get_current_user

router = APIRouter(prefix="/clients", tags=["Clients"])

# 🔹 Получить всех клиентов текущего пользователя
@router.get("/", response_model=list[ClientRead])
async def get_clients(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    result = await session.execute(
        select(Client).where(Client.owner_id == current_user.id)
    )
    return result.scalars().all()

# 🔹 Получить одного клиента по ID
@router.get("/{client_id}", response_model=ClientRead)
async def get_client(
    client_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    client = await session.get(Client, client_id)
    if not client or client.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

# 🔹 Создать клиента
@router.post("/", response_model=ClientRead)
async def create_client(
    data: ClientCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    new_client = Client(
        **data.dict(),
        owner_id=current_user.id,
        created_at=datetime.utcnow()
    )
    session.add(new_client)
    await session.commit()
    await session.refresh(new_client)
    return new_client

# 🔹 Обновить клиента
@router.put("/{client_id}", response_model=ClientRead)
async def update_client(
    client_id: UUID,
    data: ClientUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    client = await session.get(Client, client_id)
    if not client or client.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Client not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(client, field, value)

    await session.commit()
    await session.refresh(client)
    return client

# 🔹 Удалить клиента
@router.delete("/{client_id}")
async def delete_client(
    client_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    client = await session.get(Client, client_id)
    if not client or client.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Client not found")

    await session.delete(client)
    await session.commit()
    return {"detail": "Client deleted"}