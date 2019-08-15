# -*- coding: future_fstrings -*-

import logging, telethon

from .. import loader, utils

def register(cb):
    cb(RecentActionsMod())

class RecentActionsMod(loader.Module):
    """Reads recent actions"""
    def __init__(self):
        self.commands = {"recoverdeleted":self.yourcmd}
        self.config = {}
        self.name = "Recent Actions"

    async def yourcmd(self, message):
        """Restores deleted messages sent after replied message"""
        msgs = message.client.iter_admin_log(message.to_id, delete=True)
        print(msgs)
        if not message.is_reply:
            await utils.answer(message, "<code>Reply to a message to specify where to start</code>")
        target = (await message.get_reply_message()).date
        ret = []
        try:
            async for msg in msgs:
                if msg.original.date < target:
                    break
                if msg.original.action.message.date < target:
                    continue
                ret += [msg]
        except telethon.errors.rpcerrorlist.ChatAdminRequiredError:
            await utils.answer(message, "<code>Admin is required to read deleted messages</code>")
        for msg in reversed(ret):
            orig = msg.original.action.message
            deldate = msg.original.date.isoformat()
            origdate = orig.date.isoformat()
            await message.respond(f"=== Deleted message recovered. Originally sent at {origdate}, deleted at {deldate}. ===")
            await message.respond(orig)
