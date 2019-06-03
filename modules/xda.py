from .. import loader
import logging, random

def register(cb):
    logging.debug('Registering %s', __file__)
    cb(XDAMod())

RANDOM_WORDS = ["sur", "Sir", "bro", "yes", "no", "bolte", "bolit", "bholit", "volit", "mustah", "fap", "lit", "lmao", "iz", "jiosim", "ijo", "nut", "workz", "workang"]
WEIGHT_WORDS = [6    , 6,     6    , 5    , 5   , 2      , 2      , 3       , 3      , 4       , 5    , 3    , 6     , 7   , 8       , 4    , 7    , 4      , 4        ]

RANDOM_WORDS += ["flashabl zip", "bateri", "bacup", "bad englis", "sar", "treble wen", "gsi", "fox bag", "bag fox", "fine", "bast room", "fax"]
WEIGHT_WORDS += [6             , 6       , 6      , 5           , 5    ,  2          , 6    , 3        , 3        , 4     , 5          , 3    ]

RANDOM_WORDS += ["plz make room", "andreid pai", "when", "port", "mtk", "send moni", "bad rom", "dot", "kenzo", "rr", "linage"]
WEIGHT_WORDS += [3              , 2            , 4     , 5     , 3    , 3          , 2        , 4    , 4      , 4   , 4       ]

class XDAMod(loader.Module):
    """Pretends to be XDA"""
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'xda':self.xdacmd}
        self.config = {"XDA_RANDOM_WORDS":RANDOM_WORDS, "XDA_WEIGHT_WORDS":WEIGHT_WORDS}
        self.name = "XDA"
        self.help = "Gibes BhoLIT bro"

    async def xdacmd(self, message):
        length = random.randint(3, 10)
        string = random.choices(self.config["XDA_RANDOM_WORDS"], weights=self.config["XDA_WEIGHT_WORDS"], k=length)
        random.shuffle(string)
        await message.edit(" ".join(string))

