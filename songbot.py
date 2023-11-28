import logging

from telegram import InlineQueryResultArticle, InputTextMessageContent, Update, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, InlineQueryHandler
import requests
from html import escape
from uuid import uuid4
from base64 import b64encode
import schedule, threading, time
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)

class SongBot(object):
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    BOT_TOKEN = os.getenv('BOT_TOKEN')

    def run_continuously(self, interval=1):
        """Continuously run, while executing pending jobs at each
        elapsed time interval.
        @return cease_continuous_run: threading. Event which can
        be set to cease continuous run. Please note that it is
        *intended behavior that run_continuously() does not run
        missed jobs*. For example, if you've registered a job that
        should run every minute and you set a continuous run
        interval of one hour then your job won't be run 60 times
        at each interval but only once.
        """
        cease_continuous_run = threading.Event()

        class ScheduleThread(threading.Thread):
            @classmethod
            def run(cls):
                while not cease_continuous_run.is_set():
                    schedule.run_pending()
                    time.sleep(interval)

        continuous_thread = ScheduleThread()
        continuous_thread.start()
        return cease_continuous_run

    def get_spotify_access_token(self) -> None:
        response = requests.post('https://accounts.spotify.com/api/token', data='grant_type=client_credentials', headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic {}'.format(b64encode(f"{self.CLIENT_ID}:{self.CLIENT_SECRET}".encode()).decode())
        })

        self.SPOTIFY_ACCESS_TOKEN = response.json()['access_token']

        secs = response.json()['expires_in']
        if secs > 300:
            secs -= 300
        #schedule new job to renew access token
        schedule.every(secs).seconds.do(self.get_spotify_access_token)

        #stop previous job
        return schedule.CancelJob


    def search_song(self, update: Update, context: CallbackContext) -> None:
        resp = requests.get('https://api.spotify.com/v1/search', headers={'Authorization': f"Bearer {self.SPOTIFY_ACCESS_TOKEN}"}, params={"q": update.message.text[6:], "type": "track"})
        context.bot.send_message(update.message.chat_id, resp.json()['tracks']['items'][0]['external_urls']['spotify'])

    def inline_query(self, update: Update, context: CallbackContext) -> None:
        """Handle the inline query. This is run when you type: @botusername <query>"""
        query = update.inline_query.query
        print(f'someone queried inline {query}')
        if not query:  # empty query should not be handled
            return

        resp = requests.get('https://api.spotify.com/v1/search', headers={'Authorization': f"Bearer {self.SPOTIFY_ACCESS_TOKEN}"}, params={"q": query, "type": "track"})

        if (resp.status_code == 200 and resp.json()['tracks']):
            results = map(lambda t:  InlineQueryResultArticle(
                    id=str(uuid4()),
                    title="{} - {}".format(t['artists'][0]['name'], t['name']),
                    input_message_content=InputTextMessageContent(t['external_urls']['spotify']),
                    thumb_url=t['album']['images'][-1]['url']
                ), resp.json()['tracks']['items'])

            update.inline_query.answer(list(results))

    def main(self) -> None:
        self.get_spotify_access_token()
        # Start the background thread
        stop_run_continuously = self.run_continuously()

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
        stop_run_continuously.set()


if __name__ == '__main__':
    SongBot().main()
