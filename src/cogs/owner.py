import asyncio
import code
import io
import os
import re
import sys
import traceback as tb
from contextlib import redirect_stdout, suppress

import discord as d
from discord.ext import commands as cmds

from misc import exceptions as exc
from misc import checks
from utils import utils as u
from utils import formatter


class Bot(cmds.Cog):

    def __init__(self, bot):
        self.bot = bot

    # Close connection to Discord - immediate offline
    @cmds.command(name=',die', aliases=[',d'], brief='Kills the bot', description='BOT OWNER ONLY\nCloses the connection to Discord', hidden=True)
    @cmds.is_owner()
    async def die(self, ctx):
        await u.add_reaction(ctx.message, '\N{CRESCENT MOON}')

        chantype = 'guild' if isinstance(ctx.channel, d.TextChannel) else 'private'
        u.temp['startup'] = (chantype, ctx.channel.id if chantype == 'guild' else ctx.author.id, ctx.message.id)
        u.dump(u.temp, 'temp/temp.pkl')

        # loop = self.bot.loop.all_tasks()
        # for task in loop:
        #     task.cancel()
        print('\n< < < < < < < < < < < <\nD I S C O N N E C T E D\n< < < < < < < < < < < <\n')
        await self.bot.logout()

    @cmds.command(name=',restart', aliases=[',res', ',r'], hidden=True)
    @cmds.is_owner()
    async def restart(self, ctx):
        await u.add_reaction(ctx.message, '\N{SLEEPING SYMBOL}')

        print('\n^ ^ ^ ^ ^ ^ ^ ^ ^ ^\nR E S T A R T I N G\n^ ^ ^ ^ ^ ^ ^ ^ ^ ^\n')

        chantype = 'guild' if isinstance(ctx.channel, d.TextChannel) else 'private'
        u.temp['startup'] = (chantype, ctx.channel.id if chantype == 'guild' else ctx.author.id, ctx.message.id)
        u.dump(u.temp, 'temp/temp.pkl')

        # loop = self.bot.loop.all_tasks()
        # for task in loop:
        #     task.cancel()
        await self.bot.logout()
        os.execl(sys.executable, 'python3', 'run.py')

    # Invite bot to bot owner's server
    @cmds.command(name=',invite', aliases=[',inv', ',link'], brief='Invite the bot', description='BOT OWNER ONLY\nInvite the bot to a server (Requires admin)', hidden=True)
    @cmds.is_owner()
    async def invite(self, ctx):
        await u.add_reaction(ctx.message, '\N{ENVELOPE}')

        await ctx.send('https://discordapp.com/oauth2/authorize?&client_id={}&scope=bot&permissions={}'.format(u.config['client_id'], u.config['permissions']))

    @cmds.command(name=',guilds', aliases=[',gs'])
    @cmds.is_owner()
    async def guilds(self, ctx):
        paginator = cmds.Paginator()

        for guild in self.bot.guilds:
            paginator.add_line(f'{guild.name}: {guild.id}\n'
                               f'  @{guild.owner}: {guild.owner.id}')

        for page in paginator.pages:
            await ctx.send(f'**Guilds:**\n{page}')

    @cmds.group(name=',block', aliases=[',bl', ',b'])
    @cmds.is_owner()
    async def block(self, ctx):
        pass

    @block.group(name='list', aliases=['l'])
    async def block_list(self, ctx):
        pass

    @block_list.command(name='guilds', aliases=['g'])
    async def block_list_guilds(self, ctx):
        await formatter.paginate(ctx, u.block['guild_ids'])

    @block.command(name='user', aliases=['u'])
    async def block_user(self, ctx, *users: d.User):
        for user in users:
            u.block['user_ids'].append(user.id)

        u.dump(u.block, 'cogs/block.json', json=True)

    @block.command(name='guild', aliases=['g'])
    async def block_guild(self, ctx, *guilds):
        for guild in guilds:
            u.block['guild_ids'].append(guild)

        u.dump(u.block, 'cogs/block.json', json=True)

    @cmds.group(name=',unblock', aliases=[',unbl', ',unb'])
    @cmds.is_owner()
    async def unblock(self, ctx):
        pass

    @unblock.command(name='user', aliases=['u'])
    async def unblock_user(self, ctx, *users: d.User):
        for user in users:
            u.block['user_ids'].remove(user.id)

        u.dump(u.block, 'cogs/block.json', json=True)

        await ctx.send('\N{WHITE HEAVY CHECK MARK} **Unblocked users**')

    @unblock.command(name='guild', aliases=['g'])
    async def unblock_guild(self, ctx, *guilds):
        for guild in guilds:
            u.block['guild_ids'].remove(guild)

        u.dump(u.block, 'cogs/block.json', json=True)

        await ctx.send('\N{WHITE HEAVY CHECK MARK} **Unblocked guilds**')

    @cmds.command(name=',leave', aliases=[',l'])
    @cmds.is_owner()
    async def leave(self, ctx, *guilds):
        for guild in guilds:
            temp = d.utils.get(self.bot.guilds, id=int(guild))

            await temp.leave()

    @cmds.command(name=',permissions', aliases=[',permission', ',perms', ',perm'])
    @cmds.is_owner()
    async def permissions(self, ctx, *args: d.Member):
        members = list(args)
        permissions = {}

        if not members:
            members.append(ctx.guild.me)

        for member in members:
            permissions[member.mention] = []

            for k, v in dict(ctx.channel.permissions_for(member)).items():
                if v:
                    permissions[member.mention].append(k)

        await formatter.paginate(ctx, permissions)

    @cmds.command(name=',tasks', aliases=[',task'])
    @cmds.is_owner()
    async def tasks(self, ctx):
        tasks = [task for task in asyncio.Task.all_tasks() if not task.done()]

        await ctx.send(f'**Tasks active:** `{int((len(tasks) - 6) / 3)}`')

    @cmds.command(name=',status', aliases=[',presence', ',game'], hidden=True)
    @cmds.is_owner()
    async def change_status(self, ctx, *, game=None):
        if game:
            await self.bot.change_presence(game=d.Game(name=game))
            u.config['playing'] = game
            u.dump(u.config, 'config.json', json=True)
            await ctx.send(f'**Game changed to** `{game}`')
        else:
            await self.bot.change_presence(game=None)
            u.config['playing'] = ''
            u.dump(u.config, 'config.json', json=True)
            await ctx.send('**Game changed to** ` `')

    @cmds.command(name=',username', aliases=[',user'], hidden=True)
    @cmds.is_owner()
    async def change_username(self, ctx, *, username=None):
        if username:
            await self.bot.user.edit(username=username)
            await ctx.send(f'**Username changed to** `{username}`')
        else:
            await ctx.send('**Invalid string**')
            await u.add_reaction(ctx.message, '\N{HEAVY EXCLAMATION MARK SYMBOL}')


class Tools(cmds.Cog):

    def __init__(self, bot):
        self.bot = bot

    def format(self, i='', o=''):
        if len(o) > 1:
            return '>>> {}\n{}'.format(i, o)
        else:
            return '>>> {}'.format(i)

    async def generate(self, d, i='', o=''):
        return await d.send('```python\n{}```'.format(self.format(i, o)))

    async def refresh(self, m, i='', o=''):
        output = m.content[9:-3]
        if len(re.findall('\n', output)) <= 20:
            await m.edit(content='```python\n{}\n{}\n>>>```'.format(output, self.format(i, o)))
        else:
            await m.edit(content='```python\n{}```'.format(self.format(i, o)))

    async def generate_err(self, d, o=''):
        return await d.send('```\n{}```'.format(o))

    async def refresh_err(self, m, o=''):
        await m.edit(content='```\n{}```'.format(o))

    @cmds.command(name=',console', aliases=[',con', ',c'], hidden=True)
    @cmds.is_owner()
    async def console(self, ctx):
        def execute(msg):
            if msg.content.lower().startswith('exec ') and msg.author.id is ctx.author.id and msg.channel.id is ctx.channel.id:
                msg.content = msg.content[5:]
                return True
            return False

        def evaluate(msg):
            if msg.content.lower().startswith('eval ') and msg.author.id is ctx.author.id and msg.channel.id is ctx.channel.id:
                msg.content = msg.content[5:]
                return True
            return False

        def exit(reaction, user):
            if reaction.emoji == '\N{OCTAGONAL SIGN}' and user.id is ctx.author.id and reaction.message.id == ctx.message.id:
                raise exc.Abort
            return False

        try:
            console = await self.generate(ctx)
            exception = await self.generate_err(ctx)

            await u.add_reaction(ctx.message, '\N{OCTAGONAL SIGN}')

            while not self.bot.is_closed():
                try:
                    done, pending = await asyncio.wait([self.bot.wait_for('message', check=execute), self.bot.wait_for('message', check=evaluate), self.bot.wait_for('reaction_add', check=exit)], return_when=asyncio.FIRST_COMPLETED)

                    message = done.pop().result()
                    print(message.content)

                except exc.Execute:
                    try:
                        sys.stdout = io.StringIO()
                        sys.stderr = io.StringIO()
                        exec(message.content)

                    except Exception:
                        await self.refresh_err(exception, tb.format_exc(limit=1))

                    finally:
                        await self.refresh(console, message.content, sys.stdout.getvalue() if sys.stdout.getvalue() != console.content else None)
                        sys.stdout = sys.__stdout__
                        sys.stderr = sys.__stderr__
                        with suppress(d.NotFound):
                            await message.delete()

                except exc.Evaluate:
                    try:
                        sys.stdout = io.StringIO()
                        sys.stderr = io.StringIO()
                        eval(message.content)

                    except Exception:
                        await self.refresh_err(exception, tb.format_exc(limit=1))

                    finally:
                        await self.refresh(console, message.content, sys.stdout.getvalue() if sys.stdout.getvalue() != console.content else None)
                        sys.stdout = sys.__stdout__
                        sys.stderr = sys.__stderr__
                        with suppress(d.NotFound):
                            await message.delete()

        except exc.Abort:
            pass

        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            print('RESET : sys.std output/error')

    @cmds.command(name=',execute', aliases=[',exec'], hidden=True)
    @cmds.is_owner()
    async def execute(self, ctx, *, exe):
        try:
            with io.StringIO() as buff, redirect_stdout(buff):
                exec(exe)
                await self.generate(ctx, exe, f'\n{buff.getvalue()}')

        except Exception:
            await self.generate(ctx, exe, f'\n{tb.format_exc()}')

    @cmds.command(name=',evaluate', aliases=[',eval'], hidden=True)
    @cmds.is_owner()
    async def evaluate(self, ctx, *, evl):
        try:
            with io.StringIO() as buff, redirect_stdout(buff):
                eval(evl)
                await self.generate(ctx, evl, f'\n{buff.getvalue()}')

        except Exception:
            await self.generate(ctx, evl, f'\n{tb.format_exc()}')

    @cmds.group(aliases=[',db'], hidden=True)
    @cmds.is_owner()
    async def debug(self, ctx):
        console = await self.generate(ctx)

    @debug.command(name='inject', aliases=['inj'])
    async def _inject(self, ctx, *, input_):
        pass

    @debug.command(name='inspect', aliases=['ins'])
    async def _inspect(self, ctx, *, input_):
        pass

    # @cmds.command(name='endpoint', aliases=['end'])
    # async def get_endpoint(self, ctx, *args):
    #     await ctx.send(f'```\n{await u.fetch(f"https://{args[0]}/{args[1]}/{args[2]}", params={args[3]: args[4], "limit": 1}, json=True)}```')
