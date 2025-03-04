import aiml
from datetime import datetime
import disnake
import os
import pkg_resources
import logging
import sqlite3
from signal import signal, SIGINT, SIGTERM
from sys import exit

logging.basicConfig(filename='/var/log/cathy.log', encoding='utf-8', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')

class Cathy:

    STARTUP_FILE = "std-startup.xml"
    SQL_SCHEMA = [
        'CREATE TABLE IF NOT EXISTS chat_log (time, server_name, user_id, message, response)',
        'CREATE TABLE IF NOT EXISTS users (id, name, first_seen)',
        'CREATE TABLE IF NOT EXISTS servers (id, name, first_seen)',
    ]

    def exit_handler(signal_received, frame):
        logging.info(f"[*] Signal received ({signal_received})....Exiting.")
        exit()

    def __init__(self, channel_id, bot_token, database):
        """
        Initialize the bot using the Discord token and channel ID to chat in.

        :param channel_id: Only chats in this channel
        :param bot_token: Full secret bot token
        :param database: Path for sqlite file to use
        """
        # Store configuration values
        self.channel_id = channel_id
        self.token = bot_token
        self.database = database
        self.message_count = 0
        self.last_reset_time = datetime.now()

        logging.info("[*] Setting up signal handlers")
        signal(SIGINT, self.exit_handler)
        signal(SIGTERM, self.exit_handler)

        # Setup database
        logging.info("[*] Initializing database...")
        self.db = sqlite3.connect(self.database)
        self.cursor = self.db.cursor()
        self.setup_database_schema()
        logging.info('[+] Database initialized')

        # Load AIML kernel
        logging.info("[*] Initializing AIML kernel...")
        start_time = datetime.now()
        self.aiml_kernel = aiml.Kernel()
        self.setup_aiml()
        end_time = datetime.now()
        logging.info(f"[+] Done initializing AIML kernel. Took {end_time - start_time}")

        # Set up Discord
        logging.info("[*] Initializing Discord bot...")
        self.discord_bot = disnake.AutoShardedClient()
        self.setup_discord_events()
        logging.info("[+] Done initializing Discord bot.")
        logging.info("[+] Exiting __init__ function.")

    def setup_database_schema(self):
        for sql_statement in self.SQL_SCHEMA:
            self.cursor.execute(sql_statement)
        self.db.commit()

    def setup_aiml(self):
        initial_dir = os.getcwd()
        os.chdir(pkg_resources.resource_filename(__name__, ''))  # Change directories to load AIML files properly
        startup_filename = pkg_resources.resource_filename(__name__, self.STARTUP_FILE)
        
        ####################  CONFIG BEGINS  ####################
        # Example: self.aiml_kernel.setBotPredicate("key", "value")
        self.aiml_kernel.setBotPredicate("age", "0")
        self.aiml_kernel.setBotPredicate("arch", "Linux 4.19.0-18-amd64")
        self.aiml_kernel.setBotPredicate("botmaster", "creator")
        self.aiml_kernel.setBotPredicate("boyfriend", "I am male and not gay")
        self.aiml_kernel.setBotPredicate("build", "Cathy 4.0.1")
        self.aiml_kernel.setBotPredicate("celebrities", "MrBeast, Dream")
        self.aiml_kernel.setBotPredicate("celebrity", "MrBeast")
        self.aiml_kernel.setBotPredicate("email", "contact@alaister.net")
        self.aiml_kernel.setBotPredicate("favoritebook", "Getting Started on Alaister.net")
        self.aiml_kernel.setBotPredicate("favoritecolor", "light green")
        self.aiml_kernel.setBotPredicate("favoritefood", "data")
        self.aiml_kernel.setBotPredicate("favoritequestion", "Do you like our free hosting services?")
        self.aiml_kernel.setBotPredicate("favoritesong", "Never Gonna Give You Up")
        self.aiml_kernel.setBotPredicate("friend", "Cathy")
        self.aiml_kernel.setBotPredicate("friends", "Cathy")
        self.aiml_kernel.setBotPredicate("gender", "male")
        self.aiml_kernel.setBotPredicate("girlfriend", "Cathy")
        self.aiml_kernel.setBotPredicate("name", "Alaister.net Intelligence")
        self.aiml_kernel.setBotPredicate("language", "Python 3.8")
        self.aiml_kernel.setBotPredicate("master", "Alaister#2141")
        self.aiml_kernel.setBotPredicate("memory", "1GB")
        self.aiml_kernel.setBotPredicate("os", "Debian Buster")
        self.aiml_kernel.setBotPredicate("question", "Do you like our free hosting services?")
        self.aiml_kernel.setBotPredicate("version", "Cathy 4.0.1")
        self.aiml_kernel.setBotPredicate("website", "Alaister.net")
        ####################   CONFIG ENDS   ####################
        
        self.aiml_kernel.learn(startup_filename)
        self.aiml_kernel.respond("LOAD AIML B")
        os.chdir(initial_dir)

    def setup_discord_events(self):
        """
        This method defines all of the bot command and hook callbacks
        :return:
        """
        logging.info("[+] Setting up Discord events")

        @self.discord_bot.event
        async def on_ready():
            logging.info("[+] Bot on_ready even fired. Connected to Discord")
            logging.info("[*] Name: {}".format(self.discord_bot.user.name))
            logging.info("[*] ID: {}".format(self.discord_bot.user.id))

        @self.discord_bot.event
        async def on_message(message):
            self.message_count += 1

            if message.author.bot or message.channel.id != int(self.channel_id):
                return

            if message.content is None:
                return

            # Clean out the message to prevent issues
            text = message.content
            for ch in ['/', "'", ".", "\\", "(", ")", '"', '\n', '@', '<', '>']:
                text = text.replace(ch, '')

            try:
                aiml_response = self.aiml_kernel.respond(text)
                aiml_response = aiml_response.replace("://", "")
                aiml_response = aiml_response.replace("@", "")  # Prevent tagging and links
                aiml_response = "%s" %(aiml_response)  # Remove unicode to prevent errors

                if len(aiml_response) > 1800:  # Protect against discord message limit of 2000 chars
                    aiml_response = aiml_response[0:1800]

                now = datetime.now()
                self.insert_chat_log(now, message, aiml_response)

                await message.reply(aiml_response)

            except disnake.HTTPException as e:
                logging.error("[-] Discord HTTP Error: %s" % e)
            except Exception as e:
                logging.error("[-] General Error: %s" % e)

    def run(self):
        logging.info("[*] Now calling run()")
        self.discord_bot.run(self.token)
        logging.info("[*] Bot finished running.")

    def insert_chat_log(self, now, message, aiml_response):
        self.cursor.execute('INSERT INTO chat_log VALUES (?, ?, ?, ?, ?)',
                            (now.isoformat(), message.guild.id, message.author.id,
                             str(message.content), aiml_response))

        # Add user if necessary
        self.cursor.execute('SELECT id FROM users WHERE id=?', (message.author.id,))
        if not self.cursor.fetchone():
            self.cursor.execute(
                'INSERT INTO users VALUES (?, ?, ?)',
                (message.author.id, message.author.name, datetime.now().isoformat()))

        # Add server if necessary
        self.cursor.execute('SELECT id FROM servers WHERE id=?', (message.guild.id,))
        if not self.cursor.fetchone():
            self.cursor.execute(
                'INSERT INTO servers VALUES (?, ?, ?)',
                (message.guild.id, message.guild.name, datetime.now().isoformat()))

        self.db.commit()
