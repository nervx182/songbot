import logging
import os
import re
from uuid import uuid4

from dotenv import load_dotenv
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import Updater, CallbackContext, InlineQueryHandler, CommandHandler

from streamings.spotify import Spotify
from streamings.yandex import YandexMusic
from streamings.youtube_music import YoutubeMusic

load_dotenv()

logger = logging.getLogger(__name__)


class SongBot(object):
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    INLINE_PATTERN = re.compile("([A-Z]+) (.*)")

    def __init__(self):
        spotify = Spotify(self.CLIENT_ID, self.CLIENT_SECRET)
        self.default_streaming = spotify
        streamings_list = [spotify,
                           YandexMusic(),
                           YoutubeMusic()]

        self.streaming_dict = {}
        for streaming in streamings_list:
            if streaming.command_code() in self.streaming_dict:
                raise Exception("Collision in command codes!")

            self.streaming_dict[streaming.command_code().upper()] = streaming

    def search_song(self, update: Update, context: CallbackContext) -> None:
        songs = self.spotify.search(update.message.text[6:])
        if songs:
            context.bot.send_message(update.message.chat_id, songs[0].url)
        else:
            context.bot.send_message(update.message.chat_id, "No results :(")

    def inline_query(self, update: Update, context: CallbackContext) -> None:
        """Handle the inline query. This is run when you type: @botusername <query>"""
        q = update.inline_query.query

        if self.INLINE_PATTERN.match(q):
            split = self.INLINE_PATTERN.split(q)
            streaming_key = split[1].upper()
            if streaming_key in self.streaming_dict:
                q = split[2]
                streaming = self.streaming_dict[streaming_key]
            else:
                streaming = self.default_streaming
        else:
            streaming = self.default_streaming

        print(q)

        songs = streaming.search(q)

        results = map(lambda song: InlineQueryResultArticle(
            id=str(uuid4()),
            title="{} - {}".format(song.artist, song.name),
            input_message_content=InputTextMessageContent(song.url),
            thumb_url=song.image
        ), songs)

        update.inline_query.answer(list(results))

    def main(self) -> None:
        # Start the background thread
        # stop_run_continuously = self.run_continuously()

        updater = Updater(f"{self.BOT_TOKEN}")

        # Get the dispatcher to register handlers
        # Then, we register each handler and the conditions the update must meet to trigger it
        dispatcher = updater.dispatcher

        # Register commands
        dispatcher.add_handler(CommandHandler("song", self.search_song))
        dispatcher.add_handler(InlineQueryHandler(self.inline_query))

        # Start the Bot
        updater.start_polling(allowed_updates=Update.ALL_TYPES)

        # Run the bot until you press Ctrl-C
        updater.idle()

        # Stop the background thread
        # stop_run_continuously.set()


if __name__ == '__main__':
    SongBot().main()
