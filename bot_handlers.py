from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from db_models import User, Round, Match, Prediction, Payment, RoundAccess, PaymentStatus
from config import PAYMENT_AMOUNT, PAYMENT_CARD, PAYMENT_SBP, PAYMENT_COMMENT_PREFIX
from datetime import datetime

class RegState(StatesGroup):
    waiting_nickname = State()

class PredictState(StatesGroup):
    waiting_score = State()

def main_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🏆 Участвовать в туре")],
        [KeyboardButton(text="⚽ Сделать прогнозы")],
        [KeyboardButton(text="📋 Мои прогнозы"), KeyboardButton(text="📊 Таблица игроков")],
    ], resize_keyboard=True)

async def has_access(session, user_id: int, round_id: int) -> bool:
    result = await session.execute(select(RoundAccess).where(RoundAccess.user_id==user_id, RoundAccess.round_id==round_id, RoundAccess.has_access==True))
    return result.scalar_one_or_none() is not None

def register_handlers(dp, session_maker):
    
    @dp.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext):
        async with session_maker() as session:
            user = await session.get(User, message.from_user.id)
            if user:
                await message.answer(f"👋 С возвращением, *{user.nickname}*!", parse_mode="Markdown", reply_markup=main_menu())
                return
        await message.answer("🏆 Добро пожаловать в Шоу-игру ЧМ!\n\nПридумай *никнейм* (до 20 символов):", parse_mode="Markdown")
        await state.set_state(RegState.waiting_nickname)
    
    @dp.message(RegState.waiting_nickname)
    async def process_nick(message: Message, state: FSMContext):
        nickname = message.text.strip()[:20]
        if len(nickname) < 3:
            await message.answer("⚠️ Минимум 3 символа. Попробуй ещё:")
            return
        async with session_maker() as session:
            existing = await session.execute(select(User).where(User.nickname == nickname))
            if existing.scalar_one_or_none():
                await message.answer("⚠️ Ник занят. Выбери другой:")
                return
            user = User(id=message.from_user.id, username=message.from_user.username, nickname=nickname)
            session.add(user)
            await session.commit()
        await state.clear()
        await message.answer(f"✅ Отлично, *{nickname}*! Ты в игре!", parse_mode="Markdown", reply_markup=main_menu())
    
    @dp.message(F.text == "🏆 Участвовать в туре")
    async def join_round(message: Message):
        async with session_maker() as session:
            round = await session.execute(select(Round).where(Round.is_active==True).order_by(Round.id.desc()))
            round = round.scalar_one_or_none()
            if not round:
                await message.answer("⚠️ Активных туров нет. Ожидай старта!")
                return
            has_acc = await has_access(session, message.from_user.id, round.id)
            if has_acc:
                await message.answer(f"✅ У тебя уже есть доступ к туру *{round.name}*. Делай прогнозы!", parse_mode="Markdown")
                return
            matches = await session.execute(select(Match).where(Match.round_id==round.id))
            matches = matches.scalars().all()
            text = f"🏆 *Тур: {round.name}*\n📅 Дедлайн: {round.deadline.strftime('%d.%m %H:%M')}\n\n💳 Участие: *{PAYMENT_AMOUNT} ₽*\n\n"
            text += f"📦 Матчи ({len(matches)}):\n"
            for m in matches:
                text += f"{m.home_team} vs {m.away_team}\n"
            text += f"\n💳 Для участия оплати {PAYMENT_AMOUNT} ₽:\n"
            text += f"💳 Карта: `{PAYMENT_CARD}`\n"
            text += f"📱 СБП: {PAYMENT_SBP}\n"
            text += f"✉️ Комментарий: `{PAYMENT_COMMENT_PREFIX}{message.from_user.id}`"
            payment = Payment(user_id=message.from_user.id, round_id=round.id, amount=PAYMENT_AMOUNT, comment=f"{PAYMENT_COMMENT_PREFIX}{message.from_user.id}")
            session.add(payment)
            await session.commit()
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"paid:{payment.id}")]])
            await message.answer(text, parse_mode="Markdown", reply_markup=kb)
    
    @dp.callback_query(F.data.startswith("paid:"))
    async def paid_confirm(call: CallbackQuery):
        payment_id = int(call.data.split(":")[1])
        async with session_maker() as session:
            payment = await session.get(Payment, payment_id)
            if payment and payment.status == PaymentStatus.pending:
                payment.status = PaymentStatus.pending
                await session.commit()
                await call.message.edit_text("🕐 Оплата отправлена на проверку. Жди подтверждения администратором.")
        await call.answer()
    
    @dp.message(F.text == "⚽ Сделать прогнозы")
    async def make_predictions(message: Message):
        async with session_maker() as session:
            round = await session.execute(select(Round).where(Round.is_active==True).order_by(Round.id.desc()))
            round = round.scalar_one_or_none()
            if not round:
                await message.answer("⚠️ Активных туров нет.")
                return
            has_acc = await has_access(session, message.from_user.id, round.id)
            if not has_acc:
                await message.answer("⚠️ Нет доступа. Оплати участие в туре.")
                return
            matches = await session.execute(select(Match).where(Match.round_id==round.id))
            matches = matches.scalars().all()
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"⚽ {m.home_team} vs {m.away_team}", callback_data=f"predict:{m.id}")] for m in matches])
            await message.answer(f"⚽ Выбери матч для прогноза:", reply_markup=kb)
    
    @dp.callback_query(F.data.startswith("predict:"))
    async def select_match(call: CallbackQuery, state: FSMContext):
        match_id = int(call.data.split(":")[1])
        async with session_maker() as session:
            match = await session.get(Match, match_id)
            await state.update_data(match_id=match_id)
            await state.set_state(PredictState.waiting_score)
            await call.message.edit_text(f"⚽ *{match.home_team} vs {match.away_team}*\n\nВведи счёт (например: `2:1`):", parse_mode="Markdown")
        await call.answer()
    
    @dp.message(PredictState.waiting_score)
    async def process_score(message: Message, state: FSMContext):
        try:
            home, away = map(int, message.text.split(":"))
        except:
            await message.answer("⚠️ Неверный формат. Введи: `2:1`", parse_mode="Markdown")
            return
        data = await state.get_data()
        match_id = data["match_id"]
        async with session_maker() as session:
            pred = await session.execute(select(Prediction).where(Prediction.user_id==message.from_user.id, Prediction.match_id==match_id))
            pred = pred.scalar_one_or_none()
            if pred:
                pred.home_score = home
                pred.away_score = away
            else:
                pred = Prediction(user_id=message.from_user.id, match_id=match_id, home_score=home, away_score=away)
                session.add(pred)
            await session.commit()
        await state.clear()
        await message.answer(f"✅ Прогноз `{home}:{away}` сохранён!", parse_mode="Markdown", reply_markup=main_menu())
    
    @dp.message(F.text == "📋 Мои прогнозы")
    async def my_predictions(message: Message):
        async with session_maker() as session:
            preds = await session.execute(select(Prediction).where(Prediction.user_id==message.from_user.id).order_by(Prediction.id.desc()).limit(10))
            preds = preds.scalars().all()
            if not preds:
                await message.answer("🤷 У тебя пока нет прогнозов.")
                return
            text = "📋 *Твои прогнозы:*\n\n"
            for p in preds:
                match = await session.get(Match, p.match_id)
                text += f"{match.home_team} vs {match.away_team}: `{p.home_score}:{p.away_score}` (🎖️ {p.points} оч.)\n"
            await message.answer(text, parse_mode="Markdown")
    
    @dp.message(F.text == "📊 Таблица игроков")
    async def leaderboard(message: Message):
        async with session_maker() as session:
            users = await session.execute(select(User).order_by(User.id))
            users = users.scalars().all()
            text = "🏆 *ТАБЛИЦА ИГРОКОВ*\n\n"
            for user in users:
                preds = await session.execute(select(Prediction).where(Prediction.user_id==user.id))
                total = sum([p.points for p in preds.scalars().all()])
                text += f"{user.nickname}: {total} оч.\n"
            await message.answer(text, parse_mode="Markdown")