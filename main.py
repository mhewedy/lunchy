#!/usr/bin/env python
# pylint: disable=unused-argument
import logging
import random

import dateutil.parser
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CommandHandler

import envars
import summarizer
from meta import command, job

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging = logging.getLogger(__name__)

users = []
order = {}


@command
async def capture_users_and_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global users, order
    msg = update.edited_message if update.edited_message else update.message

    captured_user = update.effective_user.first_name + " " + update.effective_user.last_name
    if captured_user not in users:
        users.append(captured_user)
        logging.info(f'user {captured_user} added!')

    order[(msg.id, captured_user)] = msg.text
    logging.info(f'order {order}')


@command
async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Pong!")


@command
async def yalla_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await select_user(context, update.message.chat_id)


@command
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global users
    user = " ".join(context.args)
    if user:
        users.append(user)
        await update.message.reply_text(f"تم إضافة {user} إلى القائمة ")
    else:
        await update.message.reply_text("خطأ، يجب كتابة الإسم")


@command
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global users
    await update.message.reply_text(
        "قائمة الأسماء هي: \n" + "\n".join(users) if len(users) > 0 else "قائمة المستخدمين فارغة")


@command
async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global users, order
    users = []
    order = {}
    await update.message.reply_text("تم مسح جميع الأسماء من القائمة")


@command
async def summarize_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global users, order
    if len(order) == 0:
        await update.message.reply_text("لا يوجد طلبات")
        return

    ai_response = summarizer.summarize_order("\n".join(f'{o}' for (_, u), o in order.items()))
    await update.message.reply_text(ai_response if ai_response else 'حدث خطأ')


@command
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global users
    await update.message.reply_text("""
يعمل البوت تلقائياً خلال ساعات الغداء، مما يلغي الحاجة إلى الأوامر اليدوية في إدارة البوت إذا كنت تفضل عدم استخدامها.

خلال المحادثات التي تسبق وقت الغداء، يقوم البوت بتسجيل أسماء المشاركين. وعندما يقترب وقت الغداء، يقوم البوت بتحديد اسم بشكل عشوائي من القائمة.

لديك السيطرة على القائمة من خلال أوامر القائمة مثل عرضها، ومسحها، وإضافة عناصر إليها. بالإضافة إلى ذلك، يمكنك تسريع عملية تحديد الاسم في أي وقت.
    """)


def help_clojure(cmds_fn):
    @command
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        global users
        await update.message.reply_text("\n".join(f'/{c} -> {msg}' for (c, _, msg) in cmds_fn()))

    return help_command


@job
async def send_lunch_headsup(context: ContextTypes.DEFAULT_TYPE, chat_id):
    global users, order
    users = []
    order = {}
    await context.bot.send_message(chat_id, text="يلا يا شباب أبدأو ضيفو طلابتكم")


@job
async def send_lunch_selection(context: ContextTypes.DEFAULT_TYPE, chat_id):
    await select_user(context, chat_id)


async def select_user(context: ContextTypes.DEFAULT_TYPE, chat_id):
    global users
    if len(users) > 0:
        selected_user = random.choice(users)
        logging.info(f'we have this list of users: {users}, randomly selected user is: {selected_user}')
        await context.bot.send_message(chat_id=chat_id, text="صاحب الحظ السعيد اليوم هو" + f" {selected_user}")
    else:
        logging.warning(f'user list might be empty: {users}')
        await context.bot.send_message(chat_id=chat_id, text="قائمة المستخدمين فارغة")


def main() -> None:
    application = Application.builder().token(envars.BOT_TOKEN).build()

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, capture_users_and_order))

    cmds = [
        ("ping", ping_command, "اختبار البوت"),
        ("yalla", yalla_command, "اختيار اسم عشوائي من القائمة"),
        ("add", add_command, "إضافة اسم إلى القائمة"),
        ("list", list_command, "عرض جميع الأسماء في القائمة"),
        ("clear", clear_command, "مسح جميع الأسماء من القائمة"),
        ("summarize", summarize_command, "تلخيص الطلب"),
        ("about", about_command, "عن البوت"),
        ("help", help_clojure(lambda: cmds), "عرض المساعدة"),
    ]
    for (cmd, func, _) in cmds:
        application.add_handler(CommandHandler(cmd, func))

    application.add_handler(MessageHandler(filters.COMMAND, help_clojure(lambda: cmds)))

    jobs = [
        (envars.HEADS_UP_TIME, send_lunch_headsup),
        # ("selection", envars.SELECTION_TIME, send_lunch_selection),
    ]
    for (t, func) in jobs:
        parsed_time = dateutil.parser.parse(t).time()
        logging.info(f'scheduling job {func.__name__} at: {parsed_time} UTC')
        application.job_queue.run_daily(func, time=parsed_time)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
