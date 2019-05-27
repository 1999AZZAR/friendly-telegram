from .. import loader
import logging

def register(cb):
    logging.debug('Registering %s', __file__)
    cb(TestMod())

class TestMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'ping':self.pingcmd}
        self.config = {}
        self.name = "Tester"
        self.help = "Self-tests"

    async def pingcmd(self, message):
        await message.edit('Pong')

