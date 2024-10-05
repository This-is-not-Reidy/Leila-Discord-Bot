from datetime import datetime

from config import Config

import disnake
from disnake.ext import commands
from Tools.exceptions import CustomError


class MarryButton(disnake.ui.View):

    def __init__(self, author, partner: disnake.Member):
        super().__init__()
        self.partner = partner
        self.author = author
        self.value = None
        self.config = Config()
    
    @disnake.ui.button(label="Принять", style=disnake.ButtonStyle.green)
    async def marry_button_accept(self, button, inter):
        if inter.author.id != self.partner.id:
            await inter.response.send_message("Принять должен тот, кого попросили!", ephemeral=True)
        else:
            await inter.response.send_message(f'{inter.author.mention} Согласен(на) быть партнёром 🎉')
            await self.config.DB.marries.insert_one({"_id": self.author.id, "mate": self.partner.id, 'time': datetime.now()})
            self.stop()

    @disnake.ui.button(label="Отказать", style=disnake.ButtonStyle.red)
    async def marry_button_cancel(self, button, inter):
        if inter.author.id != self.partner.id:
            await inter.response.send_message("Нажать должен(на) тот, кого попросили!", ephemeral=True)
        else:
            await inter.response.send_message(f'{inter.author.id} Не согласен(на) быть партнёром')
            self.stop()


class DivorceButton(disnake.ui.View):

    def __init__(self, partner: disnake.Member):
        super().__init__()
        self.partner = partner
        self.value = None
        self.config = Config()
    
    @disnake.ui.button(label="Разорвать брак", style=disnake.ButtonStyle.red)
    async def divorce_button_accept(self, button, inter):
        if inter.author.id != self.partner.id:
            await inter.response.send_message("Нажать должен(а) тот(а), с кем пользователь замужем!", ephemeral=True)
        else:
            await inter.response.send_message(f'{self.partner.mention} Согласился(ась) расторгнуть брак(. Удачи.')
            await self.config.DB.marries.delete_one({"$or": [{"_id": inter.author.id}, {"mate": self.partner.id}]})
            self.stop()


class Marries(commands.Cog, name="свадьбы", description="Можно пожениться с кем-нибудь, хихи"):

    COG_EMOJI = "💍"

    async def is_married(self, author: disnake.Member, bot):
        return await bot.config.DB.marries.count_documents({'$or': [{'_id': author.id}, {'mate': author.id}]})

    @commands.slash_command(name='marry', description="Свадьбы")
    async def marry_cmd(self, inter):
        ...

    @marry_cmd.sub_command(name="invite", description="Предложить сыграть свадьбу кому-либо")
    async def marry_invite(self, inter, member: disnake.Member):
        member_married = await self.is_married(member, inter.bot)
        author_married = await self.is_married(inter.author, inter.bot)

        if inter.author.id == member.id:
            raise CustomError("Выйти замуж за самого себя..?")
        elif member_married:
            raise CustomError(f"Эм) {member.mention} в браке. На что вы надеетесь?")
        elif author_married:
            partner = await inter.bot.fetch_user((await inter.bot.config.DB.marries.find_one({'_id': inter.author.id}))['mate'])
            raise CustomError(f"Эм) Вы уже в браке с {partner.mention}. На что вы надеетесь?")
        
        await inter.send(
            embed=await inter.bot.embeds.simple(
                title="Свадьба, получается <3", 
                description=f"{inter.author.mention} предлагает {member.mention} сыграть свадьбу. Ммм...)",
                footer={"text": "Только, давайте, без беременная в 16, хорошо?", 'icon_url': inter.author.display_avatar.url}
            ), view=MarryButton(author=inter.author, partner=member)
        )

    @marry_cmd.sub_command(name='divorce', description="Развод с партнёром")
    async def marry_divorce(self, inter):
        if await self.is_married(inter.author, inter.bot) > 0:
            await inter.send(
                embed=await inter.bot.embeds.simple(
                    title='Вы уверены? :(', 
                    description=f"{inter.author.mention} вдруг захотел(-а) порвать брачные узы."),
                view=DivorceButton(partner=inter.bot.get_user(dict(await inter.bot.config.DB.marries.find_one({'mate': inter.author.id}))['_id']) if await inter.bot.config.DB.marries.count_documents({"mate": inter.author.id}) != 0 else inter.bot.get_user(dict(await inter.bot.config.DB.marries.find_one({'_id': inter.author.id}))['mate']))
            )
        else:
            raise CustomError("Вы и так не в браке, хихи.")

    @marry_cmd.sub_command(name="marries", description="Выводит браки")
    async def marry_marries(self, inter):
        data = [
            f"`{inter.guild.get_member(i['_id']).name}` + `{inter.guild.get_member(i['mate']).name}` | <t:{round(i['time'].timestamp())}:D>"
            async for i in inter.bot.config.DB.marries.find()
            if i['_id'] in [i.id for i in inter.guild.members] and i['mate'] in [i.id for i in inter.guild.members]
        ]
        await inter.send(
            embed=await inter.bot.embeds.simple(
                title='Парочки, которые есть тута', 
                description='\n'.join(data) if len(data) != 0 else "Нет парочек, получается."
            )
        )


def setup(bot):
    bot.add_cog(Marries(bot))
