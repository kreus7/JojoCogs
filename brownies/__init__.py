from .brownie import Brownies


def setup(bot):
    bot.add_cog(Brownies(bot))
