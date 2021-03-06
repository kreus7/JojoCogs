import asyncio
import logging
import random
from typing import Literal

import discord
from redbot.core import Config, bank, checks, commands
from redbot.core.utils import menus

log = logging.getLogger('red.jojo.collectables')


class Collectables(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=153607829, force_registration=True)
        self.config.register_guild(
            Vanguards=100
        )
        self.config.register_user(
            collectables={}
        )

    async def red_delete_data_for_user(
        self,
        requester: Literal["discord", "owner", "user", "user_strict"],
        user_id: int
    ) -> None:
        await self.config.user_from_id(user_id).clear()

    @commands.Cog.listener()
    async def on_member_remove(self, member) -> None:
        try:
            await self.config.user(member).clear()
        except KeyError:
            return

    @commands.group()
    async def collectable(self, ctx):
        """Commands working with the Collectable cog!"""

    @collectable.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def add(self, ctx, user: discord.Member = None, *, collectable: str = None):
        """Add a collectable to someone's collection"""
        if collectable is not None:
            try:
                collectable_data = await self.config.guild(ctx.guild).get_raw(collectable)
            except KeyError:
                return await ctx.send("I could not find that collectable!")
            data = Embed.create(self, ctx, description="Success!", title="Adding {} to {}'s collection".format(
                collectable, user.display_name), footer="Collectables | Collect them all!")
            await ctx.send(embed=data)
            await self.config.user(user).collectables.set_raw(collectable, value=collectable_data)

    @collectable.command()
    @checks.guildowner_or_permissions(administrator=True)
    async def create(self, ctx, collectable_name: str, price: int = 100):
        """Adds collectables to a user."""
        data = Embed.create(
            self, ctx, title='Adding {} as a Collectable. :trophy:'.format(
                collectable_name),
            description='Added {0} as a Collectable which can be purchased for {1}'.format(
                collectable_name, price)
        )
        await self.config.guild(ctx.guild).set_raw(collectable_name, value=price)
        await ctx.send(embed=data)

    @collectable.command(name="list")
    async def collectable_list(self, ctx):
        """List all of the collectables in your guild"""
        try:
            coll = await self.config.guild(ctx.guild).get_raw()
        except Exception:
            return await ctx.send("Your guild does not have any collectables!\nHave an admin run `{}collectable create <collectable> [cost]` to start collecting!".format(ctx.clean_prefix))
        await self.page_logic(ctx, coll, item="{}'s Collectables".format(ctx.guild.name))

    @collectable.command()
    async def buy(self, ctx, collectable: str):
        """Buys a collectable"""
        try:
            cost = await self.config.guild(ctx.guild).get_raw(collectable)
        except KeyError:
            await ctx.send("I could not find that Collectable")
            return

        if await bank.can_spend(ctx.author, cost):
            await self.config.user(ctx.author).collectables.set_raw(
                collectable, value=cost
            )
            await ctx.send("You have purchased {0} for {1}!".format(collectable, cost))
            await bank.withdraw_credits(ctx.author, cost)

    @commands.command()
    async def collectables(self, ctx, user: discord.Member = None):
        """Displays a users collectables."""
        if user is None:
            user = ctx.author
        try:
            collectable_list = await self.config.user(user).get_raw("collectables")
        except Exception:
            return await ctx.send("{} doesn't have any collectables!".format(user.display_name))
        await self.page_logic(ctx, collectable_list, item="{}'s items".format(user.display_name))

    @commands.command(name='99')
    async def nine_nine(self, ctx):
        """Responds with a random quote from Brooklyn 99

        **Side note: this was in the original cog (before it was a red cog) by Otriux, the brains behind this cog's logic so I left it in here**"""
        brooklyn_99_quotes = [
            'I\'m the human form of the 💯 emoji.',
            'Bingpot!',
            (
                'Cool. Cool cool cool cool cool cool cool, '
                'no doubt no doubt no doubt no doubt.'
            ),
        ]

        await ctx.send(random.choice(brooklyn_99_quotes))

    async def page_logic(self, ctx: commands.Context, dictionary: dict, item: str, field_num: int = 15) -> None:
        """Convert a dictionary into a pagified embed"""
        embeds = []
        count = 0
        title = item
        embed = Embed.create(
            self, ctx=ctx, title=title, thumbnail=ctx.guild.icon_url
        )
        if field_num >= 26:
            field_num = 25
        for key, value in dictionary.items():
            if count == field_num - 1:
                embed.add_field(name=key, value=value, inline=True)
                embeds.append(embed)
                embed = Embed.create(
                    self, ctx=ctx, title=title, thumbnail=ctx.guild.icon_url
                )
                count = 0
            else:
                embed.add_field(name=key, value=value, inline=True)
                count += 1
        embeds.append(embed)
        msg = await ctx.send(embed=embeds[0])
        control = menus.DEFAULT_CONTROLS if len(embeds) > 1 else {
            "\N{CROSS MARK}": menus.close_menu
        }
        asyncio.create_task(menus.menu(ctx, embeds, control, message=msg))
        menus.start_adding_reactions(msg, control.keys())


class Embed:
    def __init__(self, bot):
        self.bot = bot

    def create(self, ctx, title="", description="", image: str = None, thumbnail: str = None,
               footer_url: str = None, footer: str = None) -> discord.Embed:
        if isinstance(ctx.message.channel, discord.abc.GuildChannel):
            color = ctx.message.author.color
        data = discord.Embed(title=title, color=color)
        if description is not None:
            if len(description) <= 1500:
                data.description = description
        data.set_author(name=ctx.author.display_name,
                        icon_url=ctx.author.avatar_url)
        if image is not None:
            data.set_image(url=image)
        if thumbnail is not None:
            data.set_thumbnail(url=thumbnail)
        if footer is None:
            footer = "{0.name}'s Embed Maker".format(ctx.bot.user)
        if footer_url is None:
            footer_url = ctx.bot.user.avatar_url
        data.set_footer(text=footer, icon_url=footer_url)
        return data
