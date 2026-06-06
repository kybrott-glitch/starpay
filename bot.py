import logging
import json
import os
from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from config import BOT_TOKEN, ADMIN_IDS
from db import db

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ─── ADMIN COMMANDS ──────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_admin = user.id in ADMIN_IDS

    if is_admin:
        text = (
            f"👑 *Admin Panel — Stars Bot*\n\n"
            f"Commands:\n"
            f"• /createlink `<stars> <label>` — create a payment link\n"
            f"• /setmessage `<link_id> <message>` — set custom reply message\n"
            f"• /links — list all your active links\n"
            f"• /deletelink `<link_id>` — delete a link\n"
            f"• /stats — view payment stats\n\n"
            f"_Example:_\n"
            f"`/createlink 50 VIP Access`\n"
            f"`/setmessage 1 Thanks! Here's your invite: t.me/+xxxx`"
        )
    else:
        text = (
            f"⭐ *Stars Payment Bot*\n\n"
            f"Hi {user.first_name}! Send /pay `<link_id>` to make a payment.\n\n"
            f"_Ask the admin for the link ID._"
        )

    await update.message.reply_text(text, parse_mode="Markdown")


async def create_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /createlink <stars_amount> <label>"""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return await update.message.reply_text("❌ Admin only.")

    args = context.args
    if len(args) < 2:
        return await update.message.reply_text(
            "Usage: `/createlink <stars_amount> <label>`\nExample: `/createlink 50 VIP Access`",
            parse_mode="Markdown"
        )

    try:
        amount = int(args[0])
        if amount < 1:
            raise ValueError
    except ValueError:
        return await update.message.reply_text("❌ Stars amount must be a positive integer.")

    label = " ".join(args[1:])
    link_id = db.create_link(admin_id=user.id, amount=amount, label=label)

    await update.message.reply_text(
        f"✅ *Payment link created!*\n\n"
        f"🆔 Link ID: `{link_id}`\n"
        f"⭐ Stars: `{amount}`\n"
        f"🏷 Label: `{label}`\n\n"
        f"Share with users: they run `/pay {link_id}`\n\n"
        f"Set a custom reply message:\n"
        f"`/setmessage {link_id} Your message here`",
        parse_mode="Markdown"
    )


async def set_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /setmessage <link_id> <custom message>"""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return await update.message.reply_text("❌ Admin only.")

    args = context.args
    if len(args) < 2:
        return await update.message.reply_text(
            "Usage: `/setmessage <link_id> <message>`\nExample: `/setmessage 1 Thanks! Here's your invite link: t.me/+xxx`",
            parse_mode="Markdown"
        )

    link_id = args[0]
    message = " ".join(args[1:])

    success = db.set_custom_message(link_id=link_id, admin_id=user.id, message=message)
    if success:
        await update.message.reply_text(
            f"✅ Custom message set for link `{link_id}`:\n\n_{message}_",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Link not found or not yours.")


async def list_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /links"""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return await update.message.reply_text("❌ Admin only.")

    links = db.get_admin_links(user.id)
    if not links:
        return await update.message.reply_text("No links yet. Use /createlink to create one.")

    text = "📋 *Your Payment Links*\n\n"
    for link in links:
        msg_preview = (link["message"][:30] + "...") if link["message"] and len(link["message"]) > 30 else (link["message"] or "_(not set)_")
        text += (
            f"🆔 `{link['id']}` — ⭐ {link['amount']} — {link['label']}\n"
            f"   💬 Reply: {msg_preview}\n"
            f"   💰 Paid: {link['payment_count']} time(s)\n\n"
        )

    await update.message.reply_text(text, parse_mode="Markdown")


async def delete_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /deletelink <link_id>"""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return await update.message.reply_text("❌ Admin only.")

    if not context.args:
        return await update.message.reply_text("Usage: `/deletelink <link_id>`", parse_mode="Markdown")

    link_id = context.args[0]
    success = db.delete_link(link_id=link_id, admin_id=user.id)

    if success:
        await update.message.reply_text(f"🗑 Link `{link_id}` deleted.", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Link not found or not yours.")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /stats"""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return await update.message.reply_text("❌ Admin only.")

    s = db.get_stats(user.id)
    await update.message.reply_text(
        f"📊 *Your Stats*\n\n"
        f"🔗 Total links: `{s['total_links']}`\n"
        f"💰 Total payments: `{s['total_payments']}`\n"
        f"⭐ Total stars earned: `{s['total_stars']}`",
        parse_mode="Markdown"
    )


# ─── USER COMMANDS ────────────────────────────────────────────────────────────

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/pay <link_id>"""
    if not context.args:
        return await update.message.reply_text(
            "Usage: `/pay <link_id>`\nAsk the admin for the link ID.",
            parse_mode="Markdown"
        )

    link_id = context.args[0]
    link = db.get_link(link_id)

    if not link:
        return await update.message.reply_text("❌ Invalid link ID. Please check with the admin.")

    # Send invoice (Stars = XTR currency)
    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title=link["label"],
        description=f"Payment of {link['amount']} ⭐ Stars",
        payload=json.dumps({"link_id": link_id, "admin_id": link["admin_id"]}),
        currency="XTR",
        prices=[LabeledPrice(label=link["label"], amount=link["amount"])],
    )


# ─── PAYMENT HANDLERS ─────────────────────────────────────────────────────────

async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Always approve pre-checkout for Stars."""
    query = update.pre_checkout_query
    await query.answer(ok=True)


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle confirmed Stars payment."""
    payment = update.message.successful_payment
    payload = json.loads(payment.invoice_payload)

    link_id = payload["link_id"]
    admin_id = payload["admin_id"]
    buyer = update.effective_user

    # Record payment
    db.record_payment(
        link_id=link_id,
        user_id=buyer.id,
        username=buyer.username or "",
        stars=payment.total_amount,
    )

    # Get custom message
    link = db.get_link(link_id)
    custom_msg = link["message"] if link and link["message"] else None

    if custom_msg:
        await update.message.reply_text(custom_msg)
    else:
        await update.message.reply_text(
            f"✅ Payment received! Thank you, {buyer.first_name}! ⭐"
        )

    # Notify admin
    try:
        await context.bot.send_message(
            chat_id=admin_id,
            text=(
                f"💰 *New Payment Received!*\n\n"
                f"👤 User: [{buyer.first_name}](tg://user?id={buyer.id})"
                + (f" (@{buyer.username})" if buyer.username else "") + "\n"
                f"🆔 Link: `{link_id}` — {link['label'] if link else ''}\n"
                f"⭐ Stars: `{payment.total_amount}`"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.warning(f"Could not notify admin {admin_id}: {e}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Admin commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("createlink", create_link))
    app.add_handler(CommandHandler("setmessage", set_message))
    app.add_handler(CommandHandler("links", list_links))
    app.add_handler(CommandHandler("deletelink", delete_link))
    app.add_handler(CommandHandler("stats", stats))

    # User commands
    app.add_handler(CommandHandler("pay", pay))

    # Payment handlers
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    logger.info("Bot started...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
