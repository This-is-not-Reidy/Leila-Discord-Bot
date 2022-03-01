from typing import Literal

import disnake
from disnake.ext import commands
from Tools.exceptions import CustomError


class Settings(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, inter):
        if not inter.author.guild_permissions.administrator:
            raise commands.MissingPermissions(['administrator'])
        else:
            return True
    
    @commands.slash_command(description="Настрой-ка меня, Сен-пай u-u.")
    @commands.has_permissions(administrator=True)
    async def settings(self, inter):
        ...

    @settings.sub_command_group(description="Автомодерация")
    async def automoderation(self, inter):
        ...

    @settings.sub_command_group(description="Уровни")
    async def level(self, inter):
        ...

    @settings.sub_command_group(description="Автороли")
    async def autoroles(self, inter):
        ...

    @settings.sub_command_group(description="Логи")
    async def logs(self, inter):
        ...

    @settings.sub_command_group(description="Велкомер")
    async def welcome(self, inter):
        ...

    @settings.sub_command()
    @commands.is_nsfw()
    async def nsfw(self, inter, channel: disnake.TextChannel):
        if await self.bot.config.DB.nsfw.count_documents({"_id": inter.guild.id}) == 0:
            await self.bot.config.DB.nsfw.insert_one({"_id": inter.guild.id, "channel": channel.id})
        else:
            await self.bot.config.DB.nsfw.update_one({"_id": inter.guild.id}, {"$set": {"channel": channel.id}})

        await inter.send(embed=await self.bot.embeds.simple(title='Leyla settings **(posting)**', description="Канал автопостинга NSFW был установлен, картинка отсылается каждые 30 секунд."))

    @autoroles.sub_command(name="add-role", description="Настройка авторолей")
    async def add_autoroles(self, inter, role: disnake.Role):
        if await self.bot.config.DB.autoroles.count_documents({"guild": inter.guild.id}) == 0:
            await self.bot.config.DB.autoroles.insert_one({"guild": inter.guild.id, "roles": [role.id]})
        else:
            if role.id in dict(await self.bot.config.DB.autoroles.find_one({"guild": inter.guild.id}))['roles']:
                raise CustomError("Роль уже установлена")
            else:
                await self.bot.config.DB.autoroles.update_one({"guild": inter.guild.id}, {"$push": {"roles": role.id}})

        await inter.send(embed=await self.bot.embeds.simple(
                title='Leyla settings **(autoroles)**', 
                description="Роль при входе на сервер установлена", 
                footer={'text': f'Роль: {role.name}', 'icon_url': inter.guild.icon.url if inter.guild.icon.url else None}
            )
        )

    @autoroles.sub_command(name='remove-role', description='Удаляет роль с авторолей')
    async def remove_autorrole(self, inter, role: disnake.Role):
        if await self.bot.config.DB.autoroles.count_documents({"guild": inter.guild.id}) == 0:
            raise CustomError('А где? Авторолей здесь нет ещё(')
        elif not role.id in dict(await self.bot.config.DB.autoroles.count_documents({"guild": inter.guild.id}))['roles']:
            raise CustomError("Эта роль не стоит в авторолях!")
        else:
            await self.bot.config.DB.autoroles.update_one({"guild": inter.guild.id}, {"$pull": {"roles": role.id}})

        await inter.send(embed=await self.bot.embeds.simple(
                title='Leyla settings **(autoroles)**', 
                description="Роль была убрана с авторолей!", 
                fields=[{'name': 'Роль', 'value': role.mention}]
            )
        )

    @logs.sub_command(name="channel", description="Настройка кАнальчика для логов")
    async def logs_channel(self, inter, channel: disnake.TextChannel):
        if await self.bot.config.DB.logs.count_documents({"guild": inter.guild.id}) == 0:
            await self.bot.config.DB.logs.insert_one({"guild": inter.guild.id, "channel": channel.id})
        else:
            await self.bot.config.DB.logs.update_one({"guild": inter.guild.id}, {"$set": {"channel": channel.id}})
        
        await inter.send(embed=await self.bot.embeds.simple(title="Leyla settings **(logs)**", description="Канал логов был установлен", fields=[{"name": "Канал", "value": channel.mention}]))

    @logs.sub_command(name="remove", description="Убирает кАнал логов")
    async def log_channel_remove(self, inter):
        if await self.bot.config.DB.logs.count_documents({"guild": inter.guild.id}) == 0:
            raise CustomError("Канала логов на этом сервере и так нет :thinking:")
        else:
            await self.bot.config.DB.logs.delete_one({"guild": inter.guild.id})
        
        await inter.send(embed=await self.bot.embeds.simple(
                title="Leyla settings **(logs)**", 
                description="Канал логов был убран отседа u-u",
            )
        )

    @automoderation.sub_command(description="Настройка наказания для любителей покричать (Caps Lock)")
    async def capslock(self, inter, action: Literal['ban', 'timeout', 'kick', 'warn'], percent: int = 50, message: str = None, administrator_ignore: Literal["Игнорировать", "Не игнорировать"] = "Игнорировать"):
        admin_ignore = {
            "Игнорировать": True,
            "Не игнорировать": False, 
        }

        if await self.bot.config.DB.automod.count_documents({"_id": inter.guild.id}) == 0:
            await self.bot.config.DB.automod.insert_one({"_id": inter.guild.id, "action": action, "percent": percent, "message": message, "admin_ignore": admin_ignore[administrator_ignore]})
        else:
            if action == "timeout": 
                data = {
                    "timeout": {
                        "duration": 43200
                    }
                }
                await self.bot.config.DB.automod.update_one({"_id": inter.guild.id}, {"$set": {"action": data, "message": message, "admin_ignore": admin_ignore[administrator_ignore]}})
            else:
                await self.bot.config.DB.automod.update_one({"_id": inter.guild.id}, {"$set": {"action": action, "message": message, "admin_ignore": admin_ignore[administrator_ignore]}})

        await inter.send(
            embed=await self.bot.embeds.simple(
                title='Leyla settings **(automoderation)**', 
                description=f"Настройки были успешно сохранены и применены",
                footer={"text": f"Наказание: {action}", "icon_url": inter.guild.icon.url if inter.guild.icon.url else None}
            )
        )

    @level.sub_command(description="Настройка системы уровней")
    async def mode(self, inter, system_mode: Literal['Включить', 'Выключить']):
        mode = {
            "Включить": True,
            "Выключить": False,
        }

        if not dict(await self.bot.config.DB.levels.find_one({"_id": inter.guild.id}))['mode']:
            await self.bot.config.DB.levels.update_one({"_id": inter.guild.id}, {"$set": {"mode": mode[system_mode]}})

        elif mode[system_mode] == dict(await self.bot.config.DB.levels.find_one({"_id": inter.guild.id}))['mode']:
            raise CustomError(f"На данный момент система уровней стоит такая же, как вы указали.")

        else:
            await self.bot.config.DB.levels.update_one({"_id": inter.guild.id}, {"$set": {"mode": mode[system_mode]}})
        
        await inter.send(embed=await self.bot.embeds.simple(title="Leyla settings **(ranks)**", description="Режим уровней успешно изменён."))

    @level.sub_command(description="Настройка сообщения при повышении уровня")
    async def message(self, inter, message):
        if await self.bot.config.DB.levels.count_documents({"_id": inter.guild.id}) == 0:
            await self.bot.config.DB.levels.insert_one({"_id": inter.guild.id, "message": message})
        else:
            await self.bot.config.DB.levels.update_one({"_id": inter.guild.id}, {"$set": {"message": message}})

        await inter.send(embed=await self.bot.embeds.simple(
                title='Leyla settings **(ranks)**', 
                description=f"Установлено новое сообщение о повышении уровня\n**Сообщение:**\n{message}"
            )
        )

    @level.sub_command(description="Выбор канала в который будут приходить оповещения о повышении уровня")
    async def channel(self, inter, channel: disnake.TextChannel):
        if await self.bot.config.DB.levels.count_documents({"_id": inter.guild.id}) == 0:
            await self.bot.config.DB.levels.insert_one({"_id": inter.guild.id, "channel": channel.id})
        if await self.bot.config.DB.levels.count_documents({"_id": inter.guild.id, "channel": channel.id}) != 0:
            raise CustomError("Сейчас и так выбран этот канал")
        else:
            await self.bot.config.DB.levels.update_one({"_id": inter.guild.id}, {"$set": {"channel": channel.id}})

        await inter.send(embed=await self.bot.embeds.simple(
                title="Leyla settings **(ranks)**", 
                description="Вы успешно установили канал, в котором будет говориться и о повышении уровня участников",
                fields=[{"name": "Канал", "value": channel.mention}]
            )
        )

    @level.sub_command(name='role', description="Настройка ролей, которые будут даваться за определённый уровень")
    async def level_roles(self, inter, role: disnake.Role, level: int):
        if dict(await self.bot.config.DB.levels.find_one({"_id": inter.guild.id}))['roles'] is not None:
            if str(role.id) in dict(await self.bot.config.DB.levels.find_one({"_id": inter.guild.id}))['roles']:
                raise CustomError("На эту роль уже есть уровень!")
            else:
                data = {
                    str(role.id): str(level)
                }
                await self.bot.config.DB.update_one({"_id": inter.guild.id}, {"$push": {"roles": data}})          
        
        await inter.send(embed=await self.bot.embeds.simple(title='Leyla settings **(ranks)**', description="Роль успешно поставлена!"))

    @level.sub_command(name='role-remove', description="Настройка ролей, которые будут даваться за определённый уровень")
    async def level_roles_remove(self, inter, role: disnake.Role):
        if str(role) in dict(await self.bot.config.DB.levels.find_one({"_id": inter.guild.id}))['roles']:
            await self.bot.config.DB.update_one({"_id": inter.guild.id}, {"$pull": {"roles": role}})
        else:
            raise CustomError("Роль, которую вы указали, не удалось найти в лвл-ролях((")
        
        await inter.send(embed=await self.bot.embeds.simple(title='Leyla settings **(ranks)**', description="Роль была успешно убрана!", fields=[{'name': 'Роль', 'value': role.mention}]))

    @level.sub_command(name="help", description="Справка по уровням (Сообщение при повышении уровня)")
    async def level_help(self, inter):
        await inter.send(
            embed=await self.bot.embeds.simple(
                title="Справка по велкомеру (/settings welcome ...)",
                description="[memberMention] - Упоминание участника, который зашёл\n[member] - Никнейм и тег зашедшего участника\n[xp] - Количество опыта, нужного до следующего уровня\n[lvl] - Показывает уровень, который участник получил при повышении.",
                ephemeral=True
            )
        )

    @welcome.sub_command(name='setup', description='Устанавливает канал приветствий u-u')
    async def welcome_setup(self, inter, welcome_channel: disnake.TextChannel, goodbye_channel: disnake.TextChannel, welcome_message: str = None, goodbye_message: str = None):
        if await self.bot.config.DB.welcome.count_documents({"_id": inter.guild.id}) == 0:
            await self.bot.config.DB.welcome.insert_one(
                {
                    "_id": inter.guild.id, 
                    "welcome_channel": welcome_channel.id, 
                    "goodbye_channel": goodbye_channel.id, 
                    "welcome_message": welcome_message, 
                    "goodbye_message": goodbye_message,
                }
            )
        else:
            await self.bot.config.DB.welcome.update_one({"_id": inter.guild.id}, 
                {
                    "$set": {
                        "welcome_channel": welcome_channel.id,
                        "welcome_message": welcome_message,
                        "goodbye_message": goodbye_message,
                        "goodbye_channel": goodbye_channel.id,
                    }
                }
            )

        await inter.send(embed=await self.bot.embeds.simple(
                title='Leyla settings **(welcomer)**', 
                description="Настройки велкомера применены успешно!!", 
                fields=[{'name': 'Каналы', 'value': f'{welcome_channel.mention} / {goodbye_channel.mention}'}]
            )
        )

    @welcome.sub_command(name="help", description="Справка по велкомеру (Сообщение при входе/выходе)")
    async def welcome_help(self, inter):
        await inter.send(
            embed=await self.bot.embeds.simple(
                title="Справка по велкомеру (/settings welcome ...)", 
                description="[memberMention] - Упоминание участника, который зашёл\n[member] - Никнейм и тег зашедшего участника\n[guild] - Название сервера\n[guildMembers] - Количество участников, после захода человека на Ваш сервер.",
                ephemeral=True
            )
        )

def setup(bot):
    bot.add_cog(Settings(bot))
