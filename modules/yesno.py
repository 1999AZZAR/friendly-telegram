from .. import loader
import logging
import random


def register(cb):
    logging.info('Registering %s', __file__)
    cb(YesNoMod())


class YesNoMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'yesno': self.yesnocmd}
        self.config = {}
        self.name = "YesNoMod"

    async def yesnocmd(self, message):
        if random.randint(1, 2) == 1:
            await message.edit("Yes")
        else:
            await message.edit("No")