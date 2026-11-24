import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- СОСТОЯНИЯ ---
class QuizState(StatesGroup):
    playing = State()

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.getenv('BOT_TOKEN')
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- БАЗА ДАННЫХ ВОПРОСОВ ---
quizzes = {
    "mechanics": [
        {"question": "В чём измеряется сила?", "options": ["Ватты", "Ньютоны", "Джоули", "Паскали"], "correct": 1, "expl": "Сила измеряется в ньютонах (Н)."},
        {"question": "Чему примерно равно ускорение свободного падения на Земле?", "options": ["10 м/с²", "2 м/с²", "50 м/с²", "100 м/с²"], "correct": 0, "expl": "Обычно берут g ≈ 9,8 м/с² или округляют до 10 м/с²."},
        {"question": "Какой закон описывает силу упругости пружины?", "options": ["Закон Гука", "Закон Ома", "Закон Архимеда", "Закон сохранения массы"], "correct": 0, "expl": "Сила упругости при растяжении или сжатии пружины описывается законом Гука: F = k·Δx."},
        {"question": "Что является мерой инертности тела?", "options": ["Скорость", "Масса", "Время", "Путь"], "correct": 1, "expl": "Чем больше масса тела, тем сложнее изменить его скорость."},
        {"question": "Какая энергия есть у любого движущегося тела?", "options": ["Потенциальная", "Кинетическая", "Тепловая", "Ядерная"], "correct": 1, "expl": "Энергия движения называется кинетической: E = mv² / 2."},
        {"question": "Какая сила мешает скольжению одного тела по другому?", "options": ["Сила трения", "Сила тяжести", "Сила упругости", "Магнитная сила"], "correct": 0, "expl": "Сила трения направлена против движения."},
        {"question": "Какая формула соответствует второму закону Ньютона?", "options": ["F = ma", "S = vt", "P = UI", "Q = cmΔt"], "correct": 0, "expl": "Второй закон Ньютона: F = ma (сила равна произведению массы на ускорение)."},
        {"question": "В чём измеряется работа и энергия?", "options": ["В ньютонах", "В джоулях", "В амперах", "В вольтах"], "correct": 1, "expl": "И работа, и энергия измеряются в джоулях (Дж)."},
        {"question": "Какая сила тянет все тела вниз к Земле?", "options": ["Сила тяжести", "Сила трения", "Сила натяжения", "Сила реакции опоры"], "correct": 0, "expl": "Притяжение к Земле создаёт силу тяжести."},
        {"question": "В чём измеряется давление?", "options": ["В паскалях", "В джоулях", "В ваттах", "В омах"], "correct": 0, "expl": "Давление измеряется в паскалях (Па)."}
    ],
    "electricity": [
        {"question": "В чём измеряется электрическое сопротивление?", "options": ["В амперах", "В вольтах", "В омах", "В ваттах"], "correct": 2, "expl": "Сопротивление измеряется в омах (Ом)."},
        {"question": "Какой закон связывает силу тока, напряжение и сопротивление?", "options": ["Закон Ома", "Закон Гука", "Закон Архимеда", "Закон всемирного тяготения"], "correct": 0, "expl": "Закон Ома для участка цепи: I = U / R."},
        {"question": "В чём измеряется напряжение?", "options": ["В амперах", "В вольтах", "В омах", "В джоулях"], "correct": 1, "expl": "Электрическое напряжение измеряется в вольтах (В)."},
        {"question": "В чём измеряется сила тока?", "options": ["В вольтах", "В омах", "В амперах", "В паскалях"], "correct": 2, "expl": "Сила тока измеряется в амперах (А)."},
        {"question": "Что движется по металлическим проводам при электрическом токе?", "options": ["Электроны", "Нейтроны", "Атомы железа", "Молекулы воздуха"], "correct": 0, "expl": "В металлах электрический ток — это движение свободных электронов."},
        {"question": "Каким прибором измеряют силу тока?", "options": ["Вольтметром", "Амперметром", "Термометром", "Барометром"], "correct": 1, "expl": "Силу тока измеряют амперметром."},
        {"question": "Каким прибором измеряют напряжение?", "options": ["Вольтметром", "Амперметром", "Секундомером", "Весами"], "correct": 0, "expl": "Напряжение измеряют вольтметром."},
        {"question": "Как изменится сопротивление провода, если сделать его в 2 раза длиннее?", "options": ["Увеличится в 2 раза", "Уменьшится в 2 раза", "Не изменится", "Станет равно нулю"], "correct": 0, "expl": "Чем длиннее провод, тем больше его сопротивление."},
        {"question": "В чём измеряется мощность?", "options": ["В джоулях", "В ваттах", "В омах", "В метрах"], "correct": 1, "expl": "Мощность измеряется в ваттах (Вт)."},
        {"question": "Как включают амперметр в цепь?", "options": ["Последовательно", "Параллельно", "В розетку без нагрузки", "Наоборот"], "correct": 0, "expl": "Амперметр подключают последовательно с участком цепи."}
    ],
    "thermodynamics": [
        {"question": "В чём измеряется количество теплоты?", "options": ["В джоулях", "В ваттах", "В амперах", "В вольтах"], "correct": 0, "expl": "Количество теплоты — это энергия, поэтому измеряется в джоулях (Дж)."},
        {"question": "Что такое плавление?", "options": ["Переход из твёрдого в жидкое", "Переход из жидкого в твёрдое", "Переход из жидкого в газ", "Переход из газа в твёрдое"], "correct": 0, "expl": "Плавление — это переход вещества из твёрдого состояния в жидкое (например, таяние льда)."},
        {"question": "Что такое кипение?", "options": ["Переход жидкости в газ", "Переход газа в жидкость", "Замерзание воды", "Сжатие газа"], "correct": 0, "expl": "При кипении жидкость превращается в газ."},
        {"question": "При какой температуре кипит обычная вода при нормальном давлении?", "options": ["0 °C", "50 °C", "100 °C", "150 °C"], "correct": 2, "expl": "Вода кипит при 100 °C."},
        {"question": "Как называется переход газа в жидкость?", "options": ["Конденсация", "Плавление", "Испарение", "Горение"], "correct": 0, "expl": "Переход пара или газа в жидкость называется конденсацией."},
        {"question": "При какой температуре тает лёд при нормальном давлении?", "options": ["-10 °C", "0 °C", "20 °C", "100 °C"], "correct": 1, "expl": "Лёд начинает плавиться при 0 °C."},
        {"question": "Что происходит с телом при нагревании (в большинстве случаев)?", "options": ["Оно расширяется", "Оно исчезает", "Оно становится холоднее", "Ничего не происходит"], "correct": 0, "expl": "При нагревании тела обычно расширяются."},
        {"question": "Как передаётся тепло от горячего чайника к воздуху вокруг?", "options": ["Теплообменом", "Магнитным полем", "Звуком", "Светом"], "correct": 0, "expl": "Более тёплое тело отдаёт тепло более холодному в процессе теплообмена."},
        {"question": "Какая формула используется при нагревании вещества?", "options": ["Q = cmΔt", "F = ma", "v = S/t", "I = U/R"], "correct": 0, "expl": "Количество теплоты при нагревании или охлаждении: Q = cmΔt."},
        {"question": "Как называется переход вещества из жидкого состояния в газообразное?", "options": ["Парообразование", "Кристаллизация", "Охлаждение", "Сжатие"], "correct": 0, "expl": "Переход из жидкости в газ называется парообразованием."}
    ],
    "optics": [
        {"question": "Какой раздел физики изучает свет?", "options": ["Оптика", "Механика", "Термодинамика", "Акустика"], "correct": 0, "expl": "Световые явления изучает оптика."},
        {"question": "Чему примерно равна скорость света в вакууме?", "options": ["300 000 км/с", "300 км/с", "30 км/с", "1 000 км/с"], "correct": 0, "expl": "Скорость света в вакууме — около 300 000 км/с."},
        {"question": "Как называется изменение направления света на границе двух сред?", "options": ["Преломление", "Нагрев", "Охлаждение", "Растяжение"], "correct": 0, "expl": "При переходе из одной среды в другую свет преломляется (например, ложка в стакане с водой кажется «сломанной»)."},
        {"question": "Как называется возвращение света от поверхности?", "options": ["Отражение", "Испарение", "Плавление", "Сжатие"], "correct": 0, "expl": "От зеркала или другой поверхности свет отражается."},
        {"question": "Какая линза собирает лучи в одну точку?", "options": ["Собирающая", "Рассеивающая", "Чёрная", "Металлическая"], "correct": 0, "expl": "Собирающая линза фокусирует параллельные лучи в одной точке."},
        {"question": "Что происходит с белым светом в призме?", "options": ["Он раскладывается в спектр", "Он превращается в звук", "Он пропадает", "Он становится твёрдым"], "correct": 0, "expl": "В призме белый свет раскладывается на цвета спектра — это дисперсия."},
        {"question": "Расстояние от линзы до фокуса — это...", "options": ["Фокусное расстояние", "Масса линзы", "Температура линзы", "Толщина провода"], "correct": 0, "expl": "Это фокусное расстояние."},
        {"question": "В чём измеряется оптическая сила линзы?", "options": ["В диоптриях", "В амперах", "В килограммах", "В секундах"], "correct": 0, "expl": "Оптическая сила линзы измеряется в диоптриях (дптр)."},
        {"question": "Какой прибор помогает рассмотреть очень мелкие предметы рядом?", "options": ["Лупа", "Компас", "Барометр", "Термометр"], "correct": 0, "expl": "Лупа даёт увеличенное изображение мелких объектов."},
        {"question": "Какое зрение часто корректируют рассеивающими линзами?", "options": ["Близорукость", "Дальтонизм", "Глухоту", "Утомляемость"], "correct": 0, "expl": "Рассеивающие линзы часто применяют при близорукости."}
    ]
}

# --- КЛАВИАТУРЫ ---

def get_main_inline_keyboard():
    """Главное меню с Inline-кнопками"""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Механика ⚙️", callback_data="start_quiz_mechanics"))
    builder.row(types.InlineKeyboardButton(text="Электричество ⚡️", callback_data="start_quiz_electricity"))
    builder.row(types.InlineKeyboardButton(text="Термодинамика 🔥", callback_data="start_quiz_thermodynamics"))
    builder.row(types.InlineKeyboardButton(text="Оптика 👁", callback_data="start_quiz_optics"))
    return builder.as_markup()

def get_quiz_keyboard(quiz_type, q_index):
    builder = InlineKeyboardBuilder()
    for idx, opt in enumerate(quizzes[quiz_type][q_index]["options"]):
        builder.row(types.InlineKeyboardButton(text=opt, callback_data=f"ans_{quiz_type}_{q_index}_{idx}"))
    return builder.as_markup()

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Выбери раздел физики для начала тестирования:",
        reply_markup=get_main_inline_keyboard()
    )

@dp.callback_query(F.data.startswith("start_quiz_"))
async def handle_start_quiz(callback: types.CallbackQuery, state: FSMContext):
    """Начало теста через нажатие Inline-кнопки"""
    quiz_type = callback.data.replace("start_quiz_", "")
    titles = {
        "mechanics": "Механика",
        "electricity": "Электричество",
        "thermodynamics": "Термодинамика",
        "optics": "Оптика"
    }

    await state.set_state(QuizState.playing)
    await state.update_data(score=0, quiz_type=quiz_type)

    await callback.message.edit_text(
        f"🚀 Раздел: **{titles[quiz_type]}**\n\n**Вопрос 1:**\n{quizzes[quiz_type][0]['question']}",
        reply_markup=get_quiz_keyboard(quiz_type, 0),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("ans_"))
async def check_answer(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    quiz_type, q_idx, a_idx = parts[1], int(parts[2]), int(parts[3])
    data = await state.get_data()
    score = data.get("score", 0)

    q_data = quizzes[quiz_type][q_idx]
    if a_idx == q_data["correct"]:
        score += 1
        await state.update_data(score=score)
        status = "✅ **Верно!**"
    else:
        status = f"❌ **Неверно.** Правильный ответ: *{q_data['options'][q_data['correct']]}*"

    text = f"{status}\n\nℹ️ {q_data['expl']}"
    next_q = q_idx + 1

    builder = InlineKeyboardBuilder()
    if next_q < len(quizzes[quiz_type]):
        builder.row(types.InlineKeyboardButton(text="Следующий вопрос ➡️", callback_data=f"next_{quiz_type}_{next_q}"))
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        total = len(quizzes[quiz_type])
        percent = (score / total) * 100

        builder.row(types.InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_menu"))

        await callback.message.edit_text(
            f"{text}\n\n🏁 **Тест завершен!**\n📊 Ваш результат: **{score}/{total}** (**{int(percent)}%**)",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await state.clear()
    await callback.answer()

@dp.callback_query(F.data.startswith("next_"))
async def show_question(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    quiz_type, q_idx = parts[1], int(parts[2])
    await callback.message.edit_text(
        f"**Вопрос {q_idx + 1}:**\n{quizzes[quiz_type][q_idx]['question']}",
        reply_markup=get_quiz_keyboard(quiz_type, q_idx),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    """Возврат к выбору разделов"""
    await callback.message.edit_text(
        "Выбери раздел физики для начала тестирования:",
        reply_markup=get_main_inline_keyboard()
    )
    await callback.answer()

async def handle(request):
    return web.Response(text="Bot is running!")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
