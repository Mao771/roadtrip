import os
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

from providers.cache_provider import CacheProvider
from adapters.db_mongo_adapter import MongoDbAdapter
from dto import SearchConfig
from base_algo import search_nodes_ways, generate_route

cache_provider = CacheProvider(MongoDbAdapter(host=os.environ.get('MONGODB_HOST', '127.0.0.1'),
                                              db_name=os.environ.get('MONGODB_DATABASE', 'road_trip'),
                                              series_name=os.environ.get('MONGODB_SERIES', 'user_search'),
                                              username=os.environ.get('MONGODB_USER', 'mongodbuser'),
                                              password=os.environ.get('MONGODB_PASSWORD',
                                                                      'your_mongodb_root_password')))

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def bot_error_handler(update: Update, callback_context: CallbackContext):
    logger.error(str(callback_context.error))
    try:
        update.message.reply_text('Sorry I have faced some internal error. Please, try again later')
    except AttributeError:
        try:
            update.callback_query.edit_message_text('Sorry I have faced some internal error. Please, try again later')
        except AttributeError:
            logger.error('Update does not have message or callback')


def error_handler(update: Update, error_msg: str):
    logger.error(error_msg)
    try:
        update.message.reply_text('Sorry I have faced some internal error. Please, try again later')
    except AttributeError:
        try:
            update.callback_query.edit_message_text('Sorry I have faced some internal error. Please, try again later')
        except AttributeError:
            logger.error('Update does not have message or callback')


def start(update: Update, _: CallbackContext) -> None:
    update.message.reply_text('Hi! I can help you to make a route for your roadtrip. Just send me your location.')


def help_command(update: Update, _: CallbackContext) -> None:
    update.message.reply_text('You can send location via message in format lon,lat or attach location.')


def location(update: Update, _: CallbackContext):
    user_id = str(update.message.from_user.id)
    if update.edited_message:
        message = update.edited_message
    else:
        message = update.message
    if message.location:
        search_config = SearchConfig(longitude=message.location.longitude,
                                     latitude=message.location.latitude)
        try:
            cache_provider.save_user_search(user_id, search_config)
            distance_choice(update, _)
        except ConnectionError as e:
            error_handler(update, str(e))
    else:
        try:
            message_text = message.text.replace(' ', '')
            message_location = message_text.split(',')
            search_config = SearchConfig(latitude=float(message_location[0]),
                                         longitude=float(message_location[1]))
            try:
                cache_provider.save_user_search(user_id, search_config)
                distance_choice(update, _)
            except ConnectionError as e:
                error_handler(update, str(e))
        except:
            update.message.reply_text('Sorry, I can not parse this location. Please, '
                                      'send it in the format: longitude, latitude')


def distance_choice(update: Update, _: CallbackContext) -> None:
    keyboard = [
        [
            InlineKeyboardButton("50 km", callback_data='50km'),
            InlineKeyboardButton("100 km", callback_data='100km'),
            InlineKeyboardButton("500 km", callback_data='500km'),
            InlineKeyboardButton("1000 km", callback_data='1000km'),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        'You need to choose approximate distance in kilometers of searching area and amount of places to search. '
        '\n\nPlease, choose approximate searching distance:', reply_markup=reply_markup)


def button(update: Update, _: CallbackContext) -> None:
    user_id = str(update.callback_query.from_user.id)
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    callback_data = query.data
    try:
        search_results = cache_provider.get_search_results(user_id)
        search_config = search_results.get('search_config')

        if 'km' in callback_data:

            cache_provider.update_user_search(user_id,
                                              SearchConfig(longitude=search_config.get('longitude'),
                                                           latitude=search_config.get('latitude'),
                                                           distance=int(callback_data[:-2]))
                                              )

            keyboard = [
                [
                    InlineKeyboardButton("3", callback_data='3'),
                    InlineKeyboardButton("5", callback_data='5'),
                    InlineKeyboardButton("7", callback_data='7'),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(
                'You need choose approximate distance in kilometers of searching area and amount of places to search. '
                '\n\nPlease, choose amount of places:', reply_markup=reply_markup)

        else:
            query.edit_message_text(text=f"Your route is generating, please wait...")
            search_config = SearchConfig(longitude=search_config.get('longitude'),
                                         latitude=search_config.get('latitude'),
                                         distance=search_config.get('distance'),
                                         nodes_count=int(callback_data))
            initial_coordinates = (search_config.longitude, search_config.latitude)
            nodes_, ways_ = search_nodes_ways(initial_coordinates, distance=search_config.distance)
            route_url = generate_route(nodes_, ways_, initial_coordinates, nodes_count=search_config.nodes_count)

            cache_provider.update_user_search(user_id, search_config)
            query.edit_message_text(text=f"Your route is generated! Please, follow the link: {route_url}")
    except ConnectionError as e:
        error_handler(update, str(e))


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.

    updater = Updater(os.environ.get('TELEGRAM_API_TOKEN'))

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler('search', distance_choice))
    dispatcher.add_handler(CallbackQueryHandler(button, run_async=True))
    dispatcher.add_handler(MessageHandler(Filters.text, location))
    dispatcher.add_handler(MessageHandler(Filters.location, location))
    dispatcher.add_error_handler(bot_error_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
