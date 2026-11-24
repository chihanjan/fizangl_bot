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
        {"question": "Как называется единица измерения силы в СИ?", "options": ["Ватт", "Ньютон", "Джоуль", "Паскаль"], "correct": 1, "expl": "Ньютон (Н) — единица измерения силы. Названа в честь Исаака Ньютона. 1 Н = 1 кг·м/с²."},
        {"question": "Чему равно ускорение свободного падения на Земле?", "options": ["9,8 м/с²", "10 м/с²", "8,9 м/с²", "9,8 км/с²"], "correct": 0, "expl": "Ускорение свободного падения g ≈ 9,8 м/с². При расчётах часто округляют до 10 м/с²."},
        {"question": "Какой закон описывает силу упругости?", "options": ["Закон Ньютона", "Закон Гука", "Закон Паскаля", "Закон Архимеда"], "correct": 1, "expl": "Закон Гука: сила упругости пропорциональна деформации: F = k·Δx."},
        {"question": "Что характеризует инертность тела?", "options": ["Сила", "Скорость", "Масса", "Ускорение"], "correct": 2, "expl": "Масса — мера инертности тела. Чем больше масса, тем труднее изменить скорость."},
        {"question": "Энергия движения тела — это...", "options": ["Потенциальная", "Внутренняя", "Кинетическая", "Химическая"], "correct": 2, "expl": "Кинетическая энергия — это энергия движения: E = mv²/2."},
        {"question": "Значение g на Земле (м/с²):", "options": ["9,81", "8,87", "3,71", "1,62"], "correct": 0, "expl": "На Земле g = 9,81 м/с². На Луне — 1,62 м/с²."},
        {"question": "Сила при движении тел по поверхности:", "options": ["Тяжести", "Упругости", "Трения", "Архимеда"], "correct": 2, "expl": "Сила трения всегда направлена против движения."},
        {"question": "Второй закон Ньютона:", "options": ["F = ma", "F = mg", "F = kx", "p = mv"], "correct": 0, "expl": "F = ma: ускорение пропорционально силе и обратно пропорционально массе."},
        {"question": "Единица работы в СИ:", "options": ["Ньютон", "Ватт", "Джоуль", "Паскаль"], "correct": 2, "expl": "Джоуль (Дж) — работа, совершаемая силой 1 Н при перемещении на 1 м."},
        {"question": "Работа силы тяжести при падении:", "options": ["Положительная", "Отрицательная", "Нулевая", "Не совершается"], "correct": 0, "expl": "Сила тяжести совпадает с направлением движения, работа положительна."}
    ],
    "electricity": [
        {"question": "Как называется единица измерения сопротивления?", "options": ["Ампер", "Вольт", "Ом", "Ватт"], "correct": 2, "expl": "Ом (Ом) — единица измерения электрического сопротивления."},
        {"question": "Какой закон описывает зависимость силы тока?", "options": ["Закон Джоуля-Ленца", "Закон Ома", "Закон Кулона", "Закон Ампера"], "correct": 1, "expl": "Закон Ома: I = U/R."},
        {"question": "Как называется единица измерения напряжения?", "options": ["Ампер", "Вольт", "Ом", "Кулон"], "correct": 1, "expl": "Вольт (В) — единица измерения напряжения."},
        {"question": "Как называется единица измерения силы тока?", "options": ["Вольт", "Ом", "Ампер", "Ватт"], "correct": 2, "expl": "Ампер (А) — единица измерения силы тока."},
        {"question": "Как называются частицы тока в металлах?", "options": ["Протоны", "Нейтроны", "Электроны", "Ионы"], "correct": 2, "expl": "В металлах ток — это упорядоченное движение свободных электронов."},
        {"question": "Прибор для измерения силы тока:", "options": ["Вольтметр", "Амперметр", "Омметр", "Ваттметр"], "correct": 1, "expl": "Амперметр включается в цепь последовательно."},
        {"question": "Прибор для измерения напряжения:", "options": ["Вольтметр", "Амперметр", "Омметр", "Гальванометр"], "correct": 0, "expl": "Вольтметр подключается параллельно участку цепи."},
        {"question": "Как изменится сопротивление проводника при увеличении его длины в 2 раза?", "options": ["Увеличится в 2 раза", "Уменьшится в 2 раза", "Не изменится", "Увеличится в 4 раза"], "correct": 0, "expl": "R = ρ·l/S. Длина l прямо пропорциональна сопротивлению."},
        {"question": "Единица электрической мощности:", "options": ["Джоуль", "Вольт", "Ампер", "Ватт"], "correct": 3, "expl": "Ватт (Вт) — единица мощности. P = U·I."},
        {"question": "Соединение в ёлочных гирляндах:", "options": ["Параллельное", "Последовательное", "Смешанное", "Сложное"], "correct": 1, "expl": "При последовательном соединении обрыв в одном месте гасит всю цепь."}
    ],
    "thermodynamics": [
        {"question": "Единица количества теплоты в СИ:", "options": ["Ватт", "Ньютон", "Джоуль", "Паскаль"], "correct": 2, "expl": "Количество теплоты измеряется в джоулях (Дж)."},
        {"question": "Какой процесс называется плавлением?", "options": ["Жидкое → твёрдое", "Твёрдое → жидкое", "Жидкое → газ", "Газ → жидкое"], "correct": 1, "expl": "Плавление — переход из твёрдого состояния в жидкое."},
        {"question": "Какой процесс называется парообразованием?", "options": ["Жидкое → газ", "Газ → жидкое", "Твёрдое → газ", "Газ → твёрдое"], "correct": 0, "expl": "Парообразование — переход из жидкого состояния в газообразное."},
        {"question": "Какая температура кипения воды при нормальном давлении?", "options": ["0°C", "50°C", "100°C", "200°C"], "correct": 2, "expl": "При нормальном давлении вода кипит при 100°C."},
        {"question": "Как называется энергия при теплообмене?", "options": ["Внутренняя энергия", "Количество теплоты", "Работа", "Мощность"], "correct": 1, "expl": "Это количество теплоты (Q)."},
        {"question": "Единица удельной теплоёмкости:", "options": ["Дж/кг", "Дж/°С", "Дж/(кг·°С)", "Дж/кг·К"], "correct": 2, "expl": "Единица: Дж/(кг·°С)."},
        {"question": "Какой закон запрещает вечный двигатель 2-го рода?", "options": ["Первый", "Второй", "Третий", "Нулевой"], "correct": 1, "expl": "Второй закон термодинамики определяет направление тепловых процессов."},
        {"question": "Переход из газа в жидкость:", "options": ["Испарение", "Кипение", "Конденсация", "Сублимация"], "correct": 2, "expl": "Этот процесс называется конденсацией."},
        {"question": "Формула теплоты при нагревании:", "options": ["Q = qm", "Q = λm", "Q = cmΔt", "Q = Lm"], "correct": 2, "expl": "Q = c·m·Δt."},
        {"question": "Температура плавления льда (норм. P):", "options": ["-10°C", "0°C", "10°C", "100°C"], "correct": 1, "expl": "Лёд плавится при 0°C."}
    ],
    "optics": [
        {"question": "Как называется раздел физики о световых явлениях?", "options": ["Механика", "Электричество", "Оптика", "Термодинамика"], "correct": 2, "expl": "Это оптика."},
        {"question": "Какова скорость света в вакууме?", "options": ["300 000 м/с", "300 000 км/с", "3 000 000 км/с", "300 000 км/ч"], "correct": 1, "expl": "Скорость света ≈ 300 000 км/с."},
        {"question": "Изменение направления света на границе сред:", "options": ["Отражение", "Преломление", "Поглощение", "Рассеяние"], "correct": 1, "expl": "Это явление преломления."},
        {"question": "Возвращение света в ту же среду от границы:", "options": ["Преломление", "Поглощение", "Отражение", "Дисперсия"], "correct": 2, "expl": "Это отражение света."},
        {"question": "Какая линза собирает лучи в фокусе?", "options": ["Рассеивающая", "Собирающая", "Плоская", "Двояковогнутая"], "correct": 1, "expl": "Собирающая (выпуклая) линза."},
        {"question": "Разложение света в спектр через призму:", "options": ["Преломление", "Отражение", "Дисперсия", "Интерференция"], "correct": 2, "expl": "Это дисперсия — зависимость преломления от цвета."},
        {"question": "Расстояние от линзы до фокуса:", "options": ["Оптическая сила", "Фокусное расстояние", "Увеличение", "Оптический центр"], "correct": 1, "expl": "Это фокусное расстояние (F)."},
        {"question": "В чем измеряется оптическая сила линзы?", "options": ["Метры", "Диоптрии", "Джоули", "Ватты"], "correct": 1, "expl": "Оптическая сила измеряется в диоптриях (дптр)."},
        {"question": "Какое изображение дает лупа?", "options": ["Действит., увел.", "Действит., умен.", "Мнимое, увел.", "Мнимое, умен."], "correct": 2, "expl": "Лупа дает мнимое, прямое и увеличенное изображение."},
        {"question": "Заболевание, корректируемое «минусом»:", "options": ["Дальнозоркость", "Близорукость", "Астигматизм", "Катаракта"], "correct": 1, "expl": "Близорукость (миопия) требует рассеивающих линз."}
    ]
}

# --- КЛАВИАТУРЫ ---

def get_main_inline_keyboard():
    """Новое главное меню с Inline-кнопками"""
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
    titles = {"mechanics": "Механика", "electricity": "Электричество",
              "thermodynamics": "Термодинамика", "optics": "Оптика"}

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
