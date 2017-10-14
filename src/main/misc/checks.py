import asyncio
import json
import traceback

import discord
from discord.ext import commands
from discord.ext.commands import errors

from utils import utils as u

owner_id = u.config['owner_id']
listed_ids = u.config['listed_ids']


def is_owner():
    async def predicate(ctx):
        return ctx.message.author.id == owner_id
    return commands.check(predicate)


def is_admin():
    def predicate(ctx):
        return ctx.message.author.guild_permissions.administrator
    return commands.check(predicate)


def is_mod():
    def predicate(ctx):
        return ctx.message.author.guild_permissions.ban_members
    return commands.check(predicate)


def is_listed():
    def predicate(ctx):
        return ctx.message.author.id in listed_ids
    return commands.check(predicate)


def owner(ctx):
    return ctx.message.author.id == owner_id


def admin(ctx):
    return ctx.message.author.guild_permissions.administrator


def mod(ctx):
    return ctx.message.author.guild_permissions.ban_members


def is_nsfw():
    def predicate(ctx):
        if isinstance(ctx.message.channel, discord.TextChannel):
            return ctx.message.channel.is_nsfw()
        return True
    return commands.check(predicate)


def del_ctx():
    async def predicate(ctx):
        if isinstance(ctx.message.channel, discord.TextChannel):
            await ctx.message.delete()
        return True
    return commands.check(predicate)
