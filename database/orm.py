import base64

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Product


async def orm_add_product(session: AsyncSession, data: dict):
    image_bytes = data["photo"].encode("utf-8")
    
    photo_base64 = base64.b64encode(image_bytes).decode("utf-8")
    obj = Product(
        article=data["article"],
        photo=photo_base64,
    )
    session.add(obj)
    await session.commit()
