import logging

class MemoryHandler(logging.Handler):
    """Keeps 2 buffers. One for dispatched messages. One for unused messages.
       When the length of the 2 together is > 100, truncate to make them 100 together, first trimming handled then unused."""
    def __init__(self, target, capacity):
        super().__init__(0)
        self.target = target
        self.capacity = capacity
        self.buffer = []
        self.handledbuffer = []
        self.lvl = logging.WARNING
    def setLevel(self, level):
        self.lvl = level
    def dump(self):
        return self.handledbuffer + self.buffer
    def dumps(self, lvl=0):
        return [self.target.format(record) for record in (self.buffer+self.handledbuffer) if record.levelno >= lvl]
    def emit(self, record):
        if len(self.buffer) + len(self.handledbuffer) >= self.capacity:
            if len(self.handledbuffer):
                del self.handledbuffer[0]
            else:
                del self.buffer[0]
        self.buffer.append(record)
        if record.levelno >= self.lvl and self.lvl >= 0:
            self.acquire()
            try:
                for record in self.buffer:
                    self.target.handle(record)
                self.handledbuffer = self.handledbuffer[-(self.capacity-len(self.buffer)):] + self.buffer
                self.buffer = []
            finally:
                self.release()
formatter = logging.Formatter(logging.BASIC_FORMAT, "")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logging.getLogger().addHandler(MemoryHandler(handler, 500))
logging.getLogger().setLevel(0)

import os, sys, argparse, asyncio, json, functools

from telethon import TelegramClient, sync, events
from telethon.errors.rpcerrorlist import PhoneNumberInvalidError

from . import utils, loader, __main__

from .database import backend, frontend

async def handle_command(modules, db, event):
    logging.debug("Incoming command!")
    if not event.message:
        logging.debug("Ignoring command with no text.")
        return
    if event.via_bot_id:
        logging.debug("Ignoring inline bot.")
        return
    message = utils.censor(event.message)
    blacklist_chats = db.get(__name__, "blacklist_chats", [])
    whitelist_chats = db.get(__name__, "whitelist_chats", [])
    if (utils.get_chat_id(message) in blacklist_chats or (whitelist_chats and not utils.get_chat_id(message) in whitelist_chats)) and not utils.get_chat_id(message) == message.from_id:
        logging.debug("Message is blacklisted or not in whitelist")
        return
    if len(message.message) > 1 and message.message[:2] == ".." and message.message != len(message.message) * ".":
        # Allow escaping commands using .'s
        await message.edit(utils.escape_html(message.message[1:]))
    logging.debug(message)
    command = message.message.split(' ',1)[0]
    logging.debug(command)
    coro = modules.dispatch(command, message) # modules.dispatch is not a coro, but returns one
    if not coro is None:
        try:
            await coro
        except Exception:
            await message.edit("<code>Request failed! Request was " + message.message + ". Please report it in the support group (`.support`) with the logs (`.logs error`)</code>")
            raise
async def handle_incoming(modules, db, event):
    logging.debug("Incoming message!")
    message = utils.censor(event.message)
    logging.debug(message)
    blacklist_chats = db.get(__name__, "blacklist_chats", [])
    whitelist_chats = db.get(__name__, "whitelist_chats", [])
    if (utils.get_chat_id(message) in blacklist_chats or (whitelist_chats and not utils.get_chat_id(message) in whitelist_chats)) and not utils.get_chat_id(message) == message.from_id:
        logging.debug("Message is blacklisted or not in whitelist")
        return
    for fun in modules.watchers:
        try:
            await fun(message)
        except:
            logging.exception("Error running watcher")

def run_config(db, phone=None):
    from . import configurator
    return configurator.run(db, phone, phone == None)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", "-s", action="store_true")
    parser.add_argument("--config", "-c", action="append")
    parser.add_argument("--value", "-v", action="append")
    parser.add_argument("--phone", "-p", action="append")
    arguments = parser.parse_args()
    logging.debug(arguments)

    if sys.platform == 'win32':
        # Subprocess support
        asyncio.set_event_loop(asyncio.ProactorEventLoop())

    clients = []

    phones = arguments.phone if arguments.phone else []
    phones += list(map(lambda f: f[18:-8], filter(lambda f: f[:19] == "friendly-telegram-+" and f[-8:] == ".session", os.listdir(os.path.dirname(utils.get_base_dir())))))

    try:
        from . import api_token
        if len(phones) == 0 and os.path.isfile(os.path.join(os.path.dirname(utils.get_base_dir()), 'friendly-telegram.session')):
            clients += [TelegramClient('friendly-telegram', api_token.ID, api_token.HASH).start()]
        for phone in phones:
            try:
                #phone = arguments.phone or input("Please enter your phone: ")
                clients += [TelegramClient(os.path.join(os.path.dirname(utils.get_base_dir()), 'friendly-telegram-'+phone), api_token.ID, api_token.HASH, connection_retries=None).start(phone)]
                clients[-1].phone = phone # so we can format stuff nicer in configurator
            except PhoneNumberInvalidError:
                print("Please check the phone number. Use international format (+XX...) and don't put spaces in it.")
                return
    except ImportError:
        run_config({})
        return
    finally:
        # Stop modules taking personal data so easily, or by accident
        try:
            del api_token.ID
            del api_token.HASH
        except UnboundLocalError:
            pass

    cfg = arguments.config if arguments.config else []
    vlu = arguments.value if arguments.value else []

    loops = []
    for client in clients:
        loops += [amain(client, dict(zip(cfg, vlu)), arguments.setup)]

    asyncio.get_event_loop().set_exception_handler(lambda _, x: logging.error("Exception on event loop! %s", x["message"], exc_info=x["exception"]))

    asyncio.get_event_loop().run_until_complete(asyncio.gather(*loops))

async def amain(client, cfg, setup=False):
    async with client as c:
        await c.start()
        await client.catch_up()
        c.parse_mode = "HTML"
        if setup:
            db = backend.CloudBackend(c)
            await db.init()
            jdb = await db.do_download()
            try:
                pdb = json.loads(jdb)
            except:
                pdb = {}
            pdb = run_config(pdb, c.phone)
            await db.do_upload(json.dumps(pdb))
            return
        db = frontend.Database(backend.CloudBackend(c))
        await db.init()
        logging.debug("got db")
        logging.info("Loading logging config...")
        [handler] = logging.getLogger().handlers
        handler.setLevel(db.get(__name__, "loglevel", logging.WARNING))

        modules = loader.Modules()
        modules.register_all(db.get(__name__, "disable_modules", []))

        blacklist_chats = db.get(__name__, "blacklist_chats", [])
        whitelist_chats = db.get(__name__, "whitelist_chats", [])
        modules.send_config(db, cfg)
        await modules.send_ready(client, db)
        client.add_event_handler(functools.partial(handle_incoming, modules, db), events.NewMessage(incoming=True, forwards=False))
        client.add_event_handler(functools.partial(handle_command, modules, db), events.NewMessage(outgoing=True, forwards=False, pattern=r'\..*'))
        print("Started")
        await c.run_until_disconnected()
