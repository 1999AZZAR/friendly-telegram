from .. import loader, utils
import logging, lyricsgenius

logger = logging.getLogger(__name__)

def register(cb):
    cb(LyricsMod())


class LyricsMod(loader.Module):
    """Sings songs"""
    def __init__(self):
        self.commands = {'lyrics': self.lyricscmd}
        self.config = {"GENIUS_API_TOKEN": ""}
        self.name = "Lyrics"

    def config_complete(self):
        self.genius = lyricsgenius.Genius(self.config["GENIUS_API_TOKEN"])

    async def lyricscmd(self, message):
        """.lyrics Song, Artist"""
        args = utils.get_args_split_by(message, ",")
        if len(args) != 2:
            logger.debug(args)
            await message.edit("<code>Please specify song and artist.</code>")
            return
        logger.debug("getting song lyrics for "+args[0]+", "+args[1])
        try:
            song = await utils.run_sync(self.genius.search_song, args[0], args[1])
        except TypeError:
            # Song not found causes internal library error
            song = None
        if song is None:
            await message.edit("<code>Song not found.</code>")
            return
        logger.debug(song)
        logger.debug(song.lyrics)
        await utils.answer(message, utils.escape_html(song.lyrics))
