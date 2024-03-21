import base64
import os

from aiogram import Bot, F, Router, types
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Article, Product
from database.orm import orm_add_product
from impoer_for_bd_art import process_excel_file
from keyboards.inline import get_callback_btns
from make_data import update_excel_with_product

bot = Bot(token=os.getenv('TOKEN'))
my_first_handler = Router()

start_kb = get_callback_btns(btns={"Добавить брак": "Брак"})
add_kb = get_callback_btns(btns={"Отменить текущее дейсвтие": "Отмена"})
nikita_kb = get_callback_btns(btns={"Добавить брак": "Брак",
                                    "Добавить 1 новый артикул в бд": "new",
                                    "Скачать эксельку с браком": "dwn",
                                    "Для импорта артикулов через эксель, просто скинь файл": "mda"})

# @my_first_handler.message(CommandStart())
# async def start_cmd(message: types.Message):
    
#     if message.from_user.id in [477820068, 428270889]:
#         return await message.answer("Дарова Никита", reply_markup=types.ReplyKeyboardRemove())
#     await message.answer("Зафиксировать брак?", reply_markup=types.ReplyKeyboardRemove())

@my_first_handler.message(CommandStart())
async def start_cmd(message: types.Message):
    
    if message.from_user.id in [477820068, 428270889]:
        return await message.answer("Админ 0_о", reply_markup=nikita_kb)
    await message.answer("Зафиксировать брак?", reply_markup=start_kb)



class AddProduct(StatesGroup):
    #Шаги состояний
    articul = State()
    photo = State()


@my_first_handler.callback_query(F.data.startswith("Отмена"))
async def cancel_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    try:
        await state.clear()
    finally:
        await callback.message.edit_text("Действия отменены", reply_markup=start_kb)



@my_first_handler.callback_query(F.data.startswith("Брак"))
async def add_product(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите артикул товара", reply_markup=add_kb)
    await state.set_state(AddProduct.articul)

@my_first_handler.message(AddProduct.articul, F.text)
async def add_name(message: types.Message, state: FSMContext, session: AsyncSession):
    article = message.text
    query = select(Article).filter_by(article=article)
    result = await session.execute(query)
    exist = result.scalars()

    exist = result.scalars().all()
    ilike_query = select(Article).filter(Article.article.ilike(f'%{article}%'))
    ilike_results = await session.execute(ilike_query)  
    matching_products = ilike_results.scalars().all()
    if matching_products:
        response = {}
        for product in matching_products:
            response[product.article] = f'art${product.article}'
        response["Отменить текущее действие"] = "Отмена"
        return await message.answer("Вот какие похожие артикулы есть", reply_markup=get_callback_btns(btns=response))
    if not exist:
        return await message.answer(f"Нет ничего похожего на {message.text}", reply_markup=add_kb)
                                    
@my_first_handler.callback_query(AddProduct.articul, F.data.startswith("art$"))
async def add_name_callback(callback: types.CallbackQuery,  state: FSMContext):
    product_art = callback.data.split("$")[-1]
    await state.update_data(article=product_art)
    await callback.message.edit_text("Есть такой артикул. Теперь пришлите фото брака", reply_markup=add_kb)
    await state.set_state(AddProduct.photo)


@my_first_handler.message(AddProduct.photo, F.photo)
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(photo=message.photo[-1].file_id)
    data = await state.get_data()
    await orm_add_product(session, data)
    query = select(Product).filter_by(article=data['article'])
    result = await session.execute(query)
    product = result.scalars().all()[-1]
    photo = message.photo[-1]

    photo_file = await bot.download(photo)
    bytes_data = photo_file.getvalue()

    encoded_photo = base64.b64encode(bytes_data).decode('utf-8')
    product_data = {
        "article": product.article,
        "created_at": product.created_at,
        "photo": encoded_photo
    }

    # Обновление/создание файла Excel
    await update_excel_with_product("products.xlsx", product_data)
    await message.answer("Товар добавлен", reply_markup=start_kb)
    await state.clear()


@my_first_handler.message(AddProduct.photo)
async def add__wrong_image(message: types.Message, state: FSMContext):
    await message.answer("Ожидается фото брака", reply_markup=add_kb)


@my_first_handler.callback_query(F.data.startswith("dwn"))
async def send_file(callback: types.CallbackQuery,):

    file_path = "products.xlsx"

    input_file = FSInputFile(file_path)
    await bot.send_document(chat_id=callback.message.chat.id, document=input_file)
    await bot.send_message(callback.message.chat.id, "Готово, дальше чё?", reply_markup=nikita_kb)


@my_first_handler.callback_query(F.data.startswith("mda"))
async def mda(callback: types.CallbackQuery,):

    await bot.send_message(callback.message.chat.id, "Чё кнопку то жмёшь, скидывай фал, если уж надо импорт и эксельки сделать")

class Add_art(StatesGroup):
    articul = State()


@my_first_handler.callback_query(F.data.startswith("new"))
async def add_new_product(callback: types.CallbackQuery, state: FSMContext):

    await callback.message.edit_text("Жду новый артикул для добавления в базу", reply_markup=add_kb)
    await state.set_state(Add_art.articul)


@my_first_handler.message(Add_art.articul)
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(article=message.text)
    data = await state.get_data()

    # Создать новый объект Article
    new_article = Article(article=data['article'])

    try:
        # Добавить объект в базу данных
        session.add(new_article)
        await session.commit()

        await state.clear()
        await message.answer("Новый артикул добавлен :)", reply_markup=start_kb)
    except IntegrityError:
        # Обработка возможной ошибки уникальности
        await message.answer("Объект с таким артикулом уже существует.")
        await session.rollback()

@my_first_handler.message(~(F.text | F.photo))
async def handle_document(message: types.Message, session: AsyncSession):
    if message.from_user.id != 428270889:
        await message.answer("А А А, Нельзя")

    document = message.document

    # Получаем информацию о файле
    file_info = await bot.get_file(document.file_id)

    # Загружаем содержимое файла в байтовый объект
    file_bytes = await bot.download_file(file_info.file_path)
    articles = await process_excel_file(file_bytes)
    try:
        for article in articles:
            session.add(article)
        await session.commit()
    except Exception as ex:
        return await message.answer(f"Уже добавлял такой артикул, а точнее { ex }")
    # Коммитим изменения в базу данных
    await session.commit()

    await message.answer("Файл успешно получен и обработан.")


@my_first_handler.message()
async def handle_document(message: types.Message):
    await message.answer("Вводите команды только с кнопочек, пожалуйста", reply_markup=start_kb)
