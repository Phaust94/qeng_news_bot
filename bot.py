
import re

from telegram import Update
from telegram import forcereply
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
import os
os.chdir(os.path.join(*os.path.split(__file__)[:-1]))

from secrets import API_KEY
from constants import ZAPOVIT_TRANSLATED, ABETKA_TRANSLATED, LONG_TRANSLATED,\
    BAD_SYMBOLS_REGEX, BAD_MESSAGE_TRANLATED, ONLY_OUR_SYMBOLS_REGEX, TRANSLATOR, \
    ERROR, EASTER_EGG_TEXT, EASTER_EGG_CORRECT, EASTER_EGG_INCORRECT
from version import __version__


# noinspection PyUnusedLocal
def zapovit(update: Update, context: CallbackContext) -> None:
    txt = update.message.text
    update.message.reply_text(ZAPOVIT_TRANSLATED)
    return None


# noinspection PyUnusedLocal
def tranlate_response(update: Update, context: CallbackContext) -> None:
    msg = update.message.text
    update.message.reply_text(ABETKA_TRANSLATED, reply_markup=forcereply.ForceReply())
    return None


# noinspection PyUnusedLocal
def error_handler(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(ERROR)
    return None


# noinspection PyUnusedLocal
def handle_reply(update: Update, context: CallbackContext) -> None:
    txt = update.message.reply_to_message.text
    if txt == ABETKA_TRANSLATED:
        handle_actual_letter(update, context)
    elif txt == EASTER_EGG_TEXT:
        handle_easter_egg_reply(update, context)
    else:
        error_handler(update, context)
    return None


# noinspection PyUnusedLocal
def handle_actual_letter(update: Update, context: CallbackContext) -> None:
    msg = update.message.text.lower()
    if re.findall(BAD_SYMBOLS_REGEX, msg):
        update.message.reply_text(BAD_MESSAGE_TRANLATED)
    elif re.findall(ONLY_OUR_SYMBOLS_REGEX, msg):
        update.message.reply_text(msg)
    elif len(msg) > 1:
        update.message.reply_text(LONG_TRANSLATED)
    else:
        update.message.reply_text(msg.translate(TRANSLATOR))
    return None


# noinspection PyUnusedLocal
def easter_egg(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(EASTER_EGG_TEXT, reply_markup=forcereply.ForceReply())
    return None


# noinspection PyUnusedLocal
def handle_easter_egg_reply(update: Update, context: CallbackContext) -> None:
    msg = update.message.text.lower()
    if msg == str(42):
        update.message.reply_text(EASTER_EGG_CORRECT)
        path = os.path.abspath(os.path.join(__file__, '..', 'data', "jiusntirdwwhuibwlrn9t1qcvj0.jpeg"))
        with open(path, "rb") as pic:
            update.message.reply_photo(photo=pic)
    else:
        update.message.reply_text(EASTER_EGG_INCORRECT)
        path = os.path.abspath(os.path.join(__file__, '..', 'data', "77075268-square-grunge-red-epic-fail-stamp.jpg"))
        with open(path, "rb") as pic:
            update.message.reply_photo(photo=pic)

    return None


# noinspection PyUnusedLocal
def info(update: Update, context: CallbackContext) -> None:
    msg = f"This is a hidden Cthulhu alphabet bot\nVersion {__version__}"
    update.message.reply_text(msg)
    return None


def main():
    updater = Updater(API_KEY, workers=4)

    updater.dispatcher.add_handler(
        MessageHandler(
            Filters.text & ~Filters.command & Filters.reply,
            handle_reply
        )
    )
    updater.dispatcher.add_handler(CommandHandler("1", zapovit))
    updater.dispatcher.add_handler(CommandHandler("2", tranlate_response))
    updater.dispatcher.add_handler(CommandHandler("3", easter_egg))

    updater.dispatcher.add_handler(CommandHandler("info", info))

    updater.dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()
    return None


if __name__ == '__main__':
    main()
