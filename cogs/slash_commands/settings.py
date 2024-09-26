import math
import random
from typing import Literal, Optional

import disnake
import emoji as emj
from disnake.ext import commands
from aiohttp import ClientSession

from core.classes.another_embeds import Field
from Tools.exceptions import CustomError


class Settings(commands.Cog, name='настройки', description="ЧТО ДЕЛАЕТ ЭТА КОМАНДА?!?!?!"):

    COG_EMOJI = "⚙️"

    def cog_check(self, inter):
        if not inter.author.guild_permissions.administrator:
            raise commands.MissingPermissions(['administrator'])
    
    @commands.slash_command(description="Настрой-ка меня, Сен-пай u-u.")
    @commands.has_permissions(administrator=True)
    async def settings(self, inter):
        ...

    @settings.sub_command_group(name='trigger')
    async def trigger(self, inter):
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

    @settings.sub_command_group(name='reaction-role', description="Роли за реакцию")
    async def reaction_role(self, inter):
        ...

    @settings.sub_command_group(name='voice', description='Настройка приватных голосовых каналов')
    async def voice_settings(self, inter):
        ...

    @settings.sub_command_group(description="Установка авто-постинга NSFW канала")
    @commands.is_nsfw()
    async def nsfw(self, inter):
        ...

    @settings.sub_command_group(name="word-game", description='Натсройка игры "в слова"')
    async def word_game(self, inter):
        ...

    @nsfw.sub_command(name='set', description='Установка авто-постинга NSFW канала')
    @commands.is_nsfw()
    async def nsfw_set(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
        avatar = await inter.bot.user.avatar.read()
        hook = await channel.create_webhook(name="Лейла", avatar=avatar)

        if await inter.bot.config.DB.nsfw.count_documents({"_id": inter.guild.id}) == 0:
            await inter.bot.config.DB.nsfw.insert_one({"_id": inter.guild.id, "hook": hook.url})
        else:
            nsfw_data = await inter.bot.config.DB.nsfw.find_one({"_id": inter.guild.id})
            async with ClientSession() as session:
                await disnake.Webhook.from_url(url=nsfw_data["hook"], session=session).delete()
                
            await inter.bot.config.DB.nsfw.update_one({"_id": inter.guild.id}, {"$set": {"hook": hook.url}})

        await inter.send(
            embed=await inter.bot.embeds.simple(
                title='Leyla settings **(posting)**',
                description="Канал автопостинга NSFW был установлен, картинка отсылается каждые 30 секунд."
            )
        )
        
        await inter.followup.send(embed=disnake.Embed(title=":warning: Предупреждение!", description="- На данный момент автопостинг не стабилен и может не работать, по независящим от меня причинам :(", color=disnake.Color.yellow()), ephemeral=True)
    
    @nsfw.sub_command(name='remove', description="Убирает авто-постинг в NSFW канал")
    @commands.is_nsfw()
    async def nsfw_remove(self, inter):
        if await inter.bot.config.DB.nsfw.count_documents({"_id": inter.guild.id}) == 0:
            raise CustomError('Ну... Сейчас нет каналов, куда я бы постила NSFW.')
        else:
            nsfw_data = await inter.bot.config.DB.nsfw.find_one({"_id": inter.guild.id})
            async with ClientSession() as session:
                await disnake.Webhook.from_url(url=nsfw_data["hook"], session=session).delete()

            await inter.bot.config.DB.nsfw.delete_one({"_id": inter.guild.id})

        await inter.send(embed=await inter.bot.embeds.simple(title='Leyla settings **(posting)**', description="Канал автопостинга NSFW был убран."))
        
    @autoroles.sub_command(name="add-role", description="Настройка авторолей")
    async def add_autoroles(self, inter, role: disnake.Role):
        if role.is_integration():
            raise CustomError('Я не могу установить роль интеграции, как роль на авто-выдачу!')
        elif role >= inter.me.top_role:
            raise CustomError('Эта роль выше моей!')
        else:
            if await inter.bot.config.DB.autoroles.count_documents({"guild": inter.guild.id}) == 0:
                await inter.bot.config.DB.autoroles.insert_one({"guild": inter.guild.id, "roles": [role.id]})
            else:
                if role.id in dict(await inter.bot.config.DB.autoroles.find_one({"guild": inter.guild.id}))['roles']:
                    raise CustomError("Роль уже установлена")
                else:
                    await inter.bot.config.DB.autoroles.update_one({"guild": inter.guild.id}, {"$push": {"roles": role.id}})

            await inter.send(embed=await inter.bot.embeds.simple(
                    title='Leyla settings **(autoroles)**', 
                    description="Роль при входе на сервер установлена", 
                    footer={'text': f'Роль: {role.name}', 'icon_url': inter.guild.icon.url if inter.guild.icon else None}
                )
            )

    @autoroles.sub_command(name='remove-role', description='Удаляет роль с авторолей')
    async def remove_autorrole(self, inter, role: disnake.Role):
        if await inter.bot.config.DB.autoroles.count_documents({"guild": inter.guild.id}) == 0:
            raise CustomError('А где? Авторолей здесь нет ещё(')
        elif not role.id in dict(await inter.bot.config.DB.autoroles.find_one({"guild": inter.guild.id}))['roles']:
            raise CustomError("Эта роль не стоит в авторолях!")
        else:
            await inter.bot.config.DB.autoroles.update_one({"guild": inter.guild.id}, {"$pull": {"roles": role.id}})

        await inter.send(embed=await inter.bot.embeds.simple(
                title='Leyla settings **(autoroles)**', 
                description="Роль была убрана с авторолей!", 
                fields=[{'name': 'Роль', 'value': role.mention}]
            )
        )

    @logs.sub_command(name="moderation", description="Показ действий модераторов")
    async def logs_moderation(self, inter, mode: Literal['Включить', 'Выключить']):
        modes = {
            'Включить': True,
            'Выключить': False,
        }

        if await inter.bot.config.DB.logs.count_documents({"_id": inter.guild.id}) == 0:
            await inter.bot.config.DB.logs.insert_one({"_id": inter.guild.id, "moderation": modes[mode], 'channel': None})
        else:
            await inter.bot.config.DB.logs.update_one({"_id": inter.guild.id}, {"$set": {"moderation": modes[mode]}})

        await inter.send(
            embed=await inter.bot.embeds.simple(
                title='Leyla settings **(logs)**',
                description="Режим логирования модерации переключён!",
                fields=[{"name": "Режим", "value": mode}],
                footer={"text": "И да, у вас не указан канал логирования, не забудьте его тоже!", 'icon_url': inter.guild.icon.url if inter.guild.icon else inter.author.display_avatar.url} if dict(await inter.bot.config.DB.logs.find_one({"_id": inter.guild.id}))['channel'] else None
            )
        )

    @logs.sub_command(name="channel", description="Настройка кАнальчика для логов")
    async def logs_channel(self, inter, channel: disnake.TextChannel):
        if await inter.bot.config.DB.logs.count_documents({"guild": inter.guild.id}) == 0:
            await inter.bot.config.DB.logs.insert_one({"guild": inter.guild.id, "channel": channel.id})
        else:
            await inter.bot.config.DB.logs.update_one({"guild": inter.guild.id}, {"$set": {"channel": channel.id}})
        
        await inter.send(
            embed=await inter.bot.embeds.simple(
                title="Leyla settings **(logs)**", 
                description="Канал логов был установлен", 
                fields=[{"name": "Канал", "value": channel.mention}]
            )
        )

    @logs.sub_command(name="remove", description="Убирает кАнал логов")
    async def log_channel_remove(self, inter):
        if await inter.bot.config.DB.logs.count_documents({"guild": inter.guild.id}) == 0:
            raise CustomError("Канала логов на этом сервере и так нет :thinking:")
        else:
            await inter.bot.config.DB.logs.delete_one({"guild": inter.guild.id})
        
        await inter.send(embed=await inter.bot.embeds.simple(
                title="Leyla settings **(logs)**", 
                description="Канал логов был убран отседа u-u",
            )
        )

    @automoderation.sub_command(description="Настройка наказания для любителей покричать (Caps Lock)")
    async def capslock(self, inter, mode: bool, action: Literal['ban', 'timeout', 'kick', 'warn'], percent: int = 50, message: str = None, administrator_ignore: Literal["Игнорировать", "Не игнорировать"] = "Игнорировать"):
        admin_ignore = {
            "Игнорировать": True,
            "Не игнорировать": False, 
        }

        if await inter.bot.config.DB.automod.count_documents({"_id": inter.guild.id}) == 0:
            await inter.bot.config.DB.automod.insert_one({"_id": inter.guild.id, "mode": mode, "action": action, "percent": percent, "message": message, "admin_ignore": admin_ignore[administrator_ignore]})
        else:
            if action == "timeout": 
                data = {
                    "timeout": {
                        "duration": 43200
                    }
                }
                await inter.bot.config.DB.automod.update_one({"_id": inter.guild.id}, {"$set": {"mode": mode, "action": data, "message": message, "admin_ignore": admin_ignore[administrator_ignore]}})
            else:
                await inter.bot.config.DB.automod.update_one({"_id": inter.guild.id}, {"$set": {"mode": mode, "action": action, "message": message, "admin_ignore": admin_ignore[administrator_ignore]}})

        await inter.send(
            embed=await inter.bot.embeds.simple(
                title='Leyla settings **(automoderation (caps-lock.))**', 
                description=f"Настройки были успешно сохранены и применены",
                footer={"text": f"Наказание: {action}", "icon_url": inter.guild.icon.url if inter.guild.icon else None}
            )
        )

    @automoderation.sub_command(name="anti-invite", description='Наказания для начинающих "пиар-менеджеров" :)')
    async def anti_invite(self, inter, user_mode: Literal['Включить', 'Выключить'], action: Literal['ban', 'timeout', 'kick', 'warn'], message: str = None, administrator_ignore: Literal["Игнорировать", "Не игнорировать"] = "Игнорировать"):
        admin_ignore = {
            "Игнорировать": True,
            "Не игнорировать": False, 
        }
        mode = {
            "Включить": True,
            "Выключить": False,
        }

        if await inter.bot.config.DB.invites.count_documents({"_id": inter.guild.id}) == 0:
            await inter.bot.config.DB.invites.insert_one({"_id": inter.guild.id, "action": action, "message": message, "admin_ignore": admin_ignore[administrator_ignore], 'mode': mode[user_mode]})
        else:
            if action == "timeout": 
                data = {
                    "timeout": {
                        "duration": 43200
                    }
                }
                await inter.bot.config.DB.invites.update_one({"_id": inter.guild.id}, {"$set": {"action": data, "message": message, "admin_ignore": admin_ignore[administrator_ignore], 'mode': mode[user_mode]}})
            else:
                await inter.bot.config.DB.invites.update_one({"_id": inter.guild.id}, {"$set": {"action": action, "message": message, "admin_ignore": admin_ignore[administrator_ignore], 'mode': mode[user_mode]}})

        await inter.send(
            embed=await inter.bot.embeds.simple(
                title='Leyla settings **(automoderation (a-invites.))**', 
                description=f"Настройки были успешно сохранены и применены",
                footer={"text": f"Наказание: {action}", "icon_url": inter.guild.icon.url if inter.guild.icon else None}
            )
        )

    @automoderation.sub_command(name="warn-limit", description="Указание наказания за достижение определённого количества предупреждений")
    async def warn_limit(
        self, inter, mode: Literal['Включить', 'Выключить'] = "Включить", 
        action: Literal['Кик', 'Мут', 'Бан'] = 'Мут', limit: int = 10,
        timeout_duration: int = None, timeout_unit: Literal['Секунды', 'Минуты', 'Часы', 'Дни'] = 'Секунды'
    ):
        actions = {
            'Мут': 'mute',
            'Бан': 'ban',
            'Кик': 'kick',
        }
        modes = {
            'Включить': True,
            'Выключить': False
        }

        if not None in (timeout_duration, timeout_unit):
            units = {
                'Секунды': timeout_duration,
                'Минуты': timeout_duration * 60,
                'Часы': timeout_duration * 60 * 60,
                'Дни': timeout_duration * 60 * 60 * 24
            }

        data = {"_id": inter.guild.id, "mode": modes[mode], "action": actions[action], "limit": limit}
        embed = await inter.bot.embeds.simple(
            title='Leyla settings **(automoderation (warn-limit))**',
            fields=[
                {"name": "Режим", "value": mode, "inline": True},
                {"name": "Действие", "value": action, "inline": True},
                {"name": "Лимит", "value": limit, "inline": True}
            ]
        )

        if await inter.bot.config.DB.warn_limit.count_documents({"_id": inter.guild.id}) == 0:
            match action:
                case 'Мут':
                    if not None in (timeout_duration, timeout_unit):
                        data.update({'timeout_duration': units[timeout_unit]})
                        await inter.bot.config.DB.warn_limit.insert_one(data)
                    else:
                        await inter.bot.config.DB.warn_limit.insert_one(data)
                case 'Бан':
                    await inter.bot.config.DB.warn_limit.insert_one(data)
                case 'Кик':
                    await inter.bot.config.DB.warn_limit.insert_one(data)
        else:
            match action:
                case 'Мут':
                    if not None in (timeout_duration, timeout_unit):
                        data.update({'timeout_duration': units[timeout_unit]})
                        await inter.bot.config.DB.warn_limit.update_one({"_id": inter.guild.id}, {"$set": data})
                    else:
                        await inter.bot.config.DB.warn_limit.update_one({"_id": inter.guild.id}, {"$set": data})
                case 'Бан':
                    await inter.bot.config.DB.warn_limit.update_one({"_id": inter.guild.id}, {"$set": data})
                case 'Кик':
                    await inter.bot.config.DB.warn_limit.update_one({"_id": inter.guild.id}, {"$set": data})

        await inter.send(embed=embed)


    @level.sub_command(name="info", description="Вся информация о ваших настройках в уровнях")
    async def level_info(self, inter):
        all_level_data = await inter.bot.config.DB.levels.find_one({"_id": inter.guild.id})
        fields_data = [
            {"name": "Режим", "value": "Включен" if all_level_data['mode'] else "Выключен", "inline": True},
            {"name": "Канал оповещений", "value": inter.guild.get_channel(all_level_data['channel']).mention if all_level_data['channel'] and all_level_data['channel'] in inter.guild.text_channels else "Канал не указан", "inline": True},
            {"name": "Роли, выдающиеся при повышении уровня", "value": ', '.join([''.join([inter.guild.get_role(int(i)).mention for i in list(i.keys()) if int(i) in [i.id for i in inter.guild.roles]]) for i in dict(await inter.bot.config.DB.levels.find_one({"_id": inter.guild.id}))['roles']]) if all_level_data['roles'] else "Ролей нет"},
            {"name": "Сообщение при повышении уровня", "value": all_level_data['message'] if all_level_data['message'] else "Сообщение не настроено", "inline": True},
            {"name": "Игнорируемые каналы", "value": ', '.join([inter.bot.get_channel(i).mention for i in all_level_data['channels']]) if len(all_level_data['channels']) != 0 else "Игнорируемые каналы отсутствуют", "inline": True},
            {"name": "Игнорируемые категории", "value": ', '.join([inter.bot.get_channel(i).name for i in all_level_data['category']]) if len(all_level_data['category']) != 0 else "Игнорируемые категории отсутствуют", "inline": True},
            {"name": "Игнорируемые пользователи", "value": ', '.join([inter.guild.get_member(i).mention for i in all_level_data['users']]) if len(all_level_data['users']) != 0 else "Игнорируемые пользователи отсутствуют", "inline": True}
        ]
        embed = await inter.bot.embeds.simple(
            title=f"Информация о системе уровней на {inter.guild.name}",
            thumbnail=inter.guild.icon.url if inter.guild.icon else None,
            footer={"text": inter.guild.id, "icon_url": inter.author.avatar.url if inter.author.avatar else None},
            image=inter.guild.banner.url if inter.guild.banner else None,
            fields=fields_data
        )
        
        await inter.send(embed=embed)

    @level.sub_command(name="mode", description="Настройка системы уровней")
    async def level_mode(self, inter, system_mode: Literal['Включить', 'Выключить']):
        mode = {
            "Включить": True,
            "Выключить": False,
        }

        if not dict(await inter.bot.config.DB.levels.find_one({"_id": inter.guild.id}))['mode']:
            await inter.bot.config.DB.levels.update_one({"_id": inter.guild.id}, {"$set": {"mode": mode[system_mode]}})

        elif mode[system_mode] == dict(await inter.bot.config.DB.levels.find_one({"_id": inter.guild.id}))['mode']:
            raise CustomError(f"На данный момент система уровней стоит такая же, как вы указали.")

        else:
            await inter.bot.config.DB.levels.update_one({"_id": inter.guild.id}, {"$set": {"mode": mode[system_mode]}})
        
        await inter.send(embed=await inter.bot.embeds.simple(title="Leyla settings **(ranks)**", description="Режим уровней успешно изменён."))

    @level.sub_command(name="message", description="Настройка сообщения при повышении уровня")
    async def level_message(self, inter, message):
        if await inter.bot.config.DB.levels.count_documents({"_id": inter.guild.id}) == 0:
            await inter.bot.config.DB.levels.insert_one({"_id": inter.guild.id, "message": message})
        else:
            await inter.bot.config.DB.levels.update_one({"_id": inter.guild.id}, {"$set": {"message": message}})

        await inter.send(embed=await inter.bot.embeds.simple(
                title='Leyla settings **(ranks)**', 
                description=f"Установлено новое сообщение о повышении уровня\n**Сообщение:**\n{message}"
            )
        )

    @level.sub_command(name="channel", description="Выбор канала в который будут приходить оповещения о повышении уровня")
    async def level_channel(self, inter, channel: disnake.TextChannel):
        if await inter.bot.config.DB.levels.count_documents({"_id": inter.guild.id}) == 0:
            await inter.bot.config.DB.levels.insert_one({"_id": inter.guild.id, "channel": channel.id})
        if await inter.bot.config.DB.levels.count_documents({"_id": inter.guild.id, "channel": channel.id}) != 0:
            raise CustomError("Сейчас и так выбран этот канал")
        else:
            await inter.bot.config.DB.levels.update_one({"_id": inter.guild.id}, {"$set": {"channel": channel.id}})

        await inter.send(embed=await inter.bot.embeds.simple(
                title="Leyla settings **(ranks)**", 
                description="Вы успешно установили канал, в котором будет говориться и о повышении уровня участников",
                fields=[{"name": "Канал", "value": channel.mention}]
            )
        )

    @level.sub_command(name='role', description="Настройка ролей, которые будут даваться за определённый уровень")
    async def level_roles(self, inter, role: disnake.Role, level: int):
        data = {
            str(role.id): str(level)
        }

        if dict(await inter.bot.config.DB.levels.find_one({"_id": inter.guild.id}))['roles'] is not None:
            for i in dict(await inter.bot.config.DB.levels.find_one({"_id": inter.guild.id}))['roles']:
                if str(level) in list(i.values()):
                    raise CustomError(f"На **{level}** уровень уже есть роль")
            else:
                await inter.bot.config.DB.levels.update_one({"_id": inter.guild.id}, {"$push": {"roles": data}})
        else:
            await inter.bot.config.DB.levels.update_one({"_id": inter.guild.id}, {"$set": {"roles": [data]}})
        
        await inter.send(
            embed=await inter.bot.embeds.simple(
                title='Leyla settings **(ranks)**', 
                description="Роль успешно поставлена!",
                fields=[{"name": "Роль", "value": role.mention, "inline": True}, {"name": "Уровень", "value": level, "inline": True}]
            )
        )

    @level.sub_command(name='role-remove', description="Настройка ролей, которые будут даваться за определённый уровень")
    async def level_roles_remove(self, inter, role: disnake.Role):
        dict_data = [i for i in dict(await inter.bot.config.DB.levels.find_one({"_id": inter.guild.id}))['roles'] if str(role.id) in i] # ААААААААААААААААААААААААААААААААА

        if len(dict_data):
            await inter.bot.config.DB.levels.update_one({"_id": inter.guild.id}, {"$pull": {"roles": dict_data[0]}})
        else:
            raise CustomError("Роль, которую вы указали, не удалось найти в лвл-ролях(")

        await inter.send(
            embed=await inter.bot.embeds.simple(
                title='Leyla settings **(ranks)**', 
                description="Роль была успешно убрана!", 
                fields=[{'name': 'Роль', 'value': role.mention}]
            )
        )

    @level.sub_command(name="help", description="Справка по уровням (Сообщение при повышении уровня)")
    async def level_help(self, inter):
        await inter.send(
            embed=await inter.bot.embeds.simple(
                title="Справка по уровневым сообщениям (/settings level ...)",
                description="**[memberMention]** - Упоминание участника, который зашёл\n**[member]** - Никнейм и тег зашедшего участника\n**[xp]** - Количество опыта, нужного до следующего уровня\n**[lvl]** - Показывает уровень, который участник получил при повышении."
            ), ephemeral=True
        )
    
    @level.sub_command(name='ignore', description="Настройка игнорирования (уровни), накладывающиеся на пользователя/канал/категорию")
    async def level_ignore(self, inter, ignore_object):
        _object = {
            str(ignore_object): inter.bot.get_channel(int(ignore_object)) if int(ignore_object) in [i.id for i in inter.guild.channels] else inter.guild.get_member(int(ignore_object)),
        }
        data = await inter.bot.config.DB.levels.find_one({"_id": inter.guild.id})

        if _object[str(ignore_object)].id in data['category']:
            raise CustomError("Эта категория уже игнорируется!")

        elif _object[str(ignore_object)].id in data['channels']:
            raise CustomError("Этот чат уже игнорируется!")

        elif _object[str(ignore_object)].id in data['users']:
            raise CustomError("Этот участник уже игнорируется!")
        else:
            if isinstance(_object[str(ignore_object)], (disnake.TextChannel, disnake.CategoryChannel, disnake.Member)):
                if isinstance(_object[str(ignore_object)], disnake.Member):
                    await inter.bot.config.DB.levels.update_one({"_id": inter.guild.id}, {"$push": {"users": _object[str(ignore_object)].id}})

                if isinstance(_object[str(ignore_object)], disnake.TextChannel):
                    await inter.bot.config.DB.levels.update_one({"_id": inter.guild.id}, {"$push": {"channels": _object[str(ignore_object)].id}})

                if isinstance(_object[str(ignore_object)], disnake.CategoryChannel):
                    await inter.bot.config.DB.levels.update_one({"_id": inter.guild.id}, {"$push": {"category": _object[str(ignore_object)].id}})
            else:
                raise CustomError("Нужно указать либо категорию, либо канал, либо участника!")

            await inter.send(
                embed=await inter.bot.embeds.simple(
                    title="Leyla settings **(levels)**",
                    description=f"Чат теперь будет игнорироваться!" if isinstance(_object[str(ignore_object)], disnake.TextChannel) else 'Участник теперь будет игнорироваться!' if isinstance(_object[str(ignore_object)], disnake.Member) else 'Категория теперь будет игнорироваться!' if isinstance(_object[str(ignore_object)], disnake.CategoryChannel) else 'Как ты это сделал!?',
                    fields=[{'name': 'Игнорируемый объект', 'value': _object[str(ignore_object)].mention}]
                )
            )

    @level.sub_command(name='ignore-remove', description="Данная команда убирает что-либо из игнорируемых")
    async def level_ignore_remove(self, inter, ignore_object):
        _object = {
            str(ignore_object): inter.bot.get_channel(int(ignore_object)) if int(ignore_object) in [i.id for i in inter.guild.channels] else inter.guild.get_member(int(ignore_object)),
        }

        if isinstance(_object[str(ignore_object)], (disnake.TextChannel, disnake.CategoryChannel, disnake.Member)):
            if isinstance(_object[str(ignore_object)], disnake.Member):
                await inter.bot.config.DB.levels.update_one({"_id": inter.guild.id}, {"$pull": {"users": _object[str(ignore_object)].id}})

            if isinstance(_object[str(ignore_object)], disnake.CategoryChannel):
                await inter.bot.config.DB.levels.update_one({"_id": inter.guild.id}, {"$pull": {"category": _object[str(ignore_object)].id}})

            if isinstance(_object[str(ignore_object)], disnake.TextChannel):
                await inter.bot.config.DB.levels.update_one({"_id": inter.guild.id}, {"$pull": {"channels": _object[str(ignore_object)].id}})
        else:
            raise CustomError("Нужно указать либо категорию, либо канал, либо участника!")

        await inter.send(
            embed=await inter.bot.embeds.simple(
                title="Leyla settings **(levels)**",
                description=f"Чат теперь не будет игнорироваться!" if isinstance(_object[str(ignore_object)], disnake.TextChannel) else 'Участник теперь не будет игнорироваться!' if isinstance(_object[str(ignore_object)], disnake.Member) else 'Категория теперь не будет игнорироваться!' if isinstance(_object[str(ignore_object)], disnake.CategoryChannel) else 'Как ты это сделал!?',
                fields=[{'name': 'Удалённый игнорируемый объект', 'value': _object[str(ignore_object)].mention}]
            )
        )

    @welcome.sub_command(name='setup', description='Устанавливает канал приветствий u-u')
    async def welcome_setup(
        self, 
        inter, 
        welcome_channel: disnake.TextChannel, 
        goodbye_channel: disnake.TextChannel, 
        welcome_message: str = None, 
        goodbye_message: str = None,
        main_welcome_or_not: Literal['Изменить основное сообщение', 'Добавить новое'] = 'Изменить основное сообщение'
    ):
        welcome_mode = {
            'Изменить основное сообщение': 1,
            'Добавить новое': 2
        }

        if await inter.bot.config.DB.welcome.count_documents({"_id": inter.guild.id}) == 0:
            await inter.bot.config.DB.welcome.insert_one(
                {
                    "_id": inter.guild.id,
                    "welcome_channel": welcome_channel.id,
                    "goodbye_channel": goodbye_channel.id,
                    "welcome_message": welcome_message,
                    "goodbye_message": goodbye_message,
                }
            )
        else:
            data = await inter.bot.config.DB.welcome.find_one({"_id": inter.guild.id})

            await inter.bot.config.DB.welcome.update_one({"_id": inter.guild.id}, 
                {
                    "$push": {
                        "welcome_messages": welcome_message,
                        "goodbye_messages": goodbye_message
                    }
                } if welcome_mode[main_welcome_or_not] == 2 else
                {
                    "$set": {
                        "welcome_channel": welcome_channel.id,
                        "welcome_message": welcome_message if welcome_mode[main_welcome_or_not] == 1 else data['welcome_message'],
                        "goodbye_message": goodbye_message if welcome_mode[main_welcome_or_not] == 1 else data['goodbye_message'],
                        "goodbye_channel": goodbye_channel.id,
                    }
                }
            )

        await inter.send(embed=await inter.bot.embeds.simple(
                title='Leyla settings **(welcomer)**', 
                description="Настройки велкомера применены успешно!!", 
                fields=[{'name': 'Каналы', 'value': f'{welcome_channel.mention} / {goodbye_channel.mention}'}]
            )
        )

    @welcome.sub_command(name='info', description='Информация о велкомере')
    async def welcome_info(self, inter):
        if await inter.bot.config.DB.welcome.count_documents({"_id": inter.guild.id}) == 0:
            raise CustomError("Велкомер не настроен на этом сервере!")
        else:
            data = await inter.bot.config.DB.welcome.find_one({"_id": inter.guild.id})
            embed = await inter.bot.embeds.simple(title='Информация о велкомере', description=f"Основное сообщение:\n{data['welcome_message']}")

            if 'welcome_messages' in data.keys():
                for i in range(len(data['welcome_messages'])):
                    embed.add_field(name=f"Номер [{i+1}] (Приветственное)", value=data['welcome_messages'][i], inline=True)
            
            if 'goodbye_messages' in data.keys():
                for i in range(len(data['goodbye_messages'])):
                    embed.add_field(name=f"Номер [{i+1}] (Прощальное)", value=data['welcome_messages'][i], inline=True)                

            await inter.send(embed=embed)

    @welcome.sub_command(name='reset', description="Сбрасывание настроек велкомера")
    async def welcome_reset(self, inter):
        await inter.bot.config.DB.welcome.delete_one({"_id": inter.guild.id})
        await inter.send(embed=await inter.bot.embeds.simple(title='Leyla settings **(welcomer)**', description="Настройки велкомера были сброшены :eyes:"))

    @welcome.sub_command(name="help", description="Справка по велкомеру (Сообщение при входе/выходе)")
    async def welcome_help(self, inter):
        await inter.send(
            embed=await inter.bot.embeds.simple(
                title="Справка по велкомеру (/settings welcome ...)", 
                description="**[memberMention]** - Упоминание участника, который зашёл\n**[member]** - Никнейм и тег зашедшего участника\n**[guild]** - Название сервера\n**[guildMembers]** - Количество участников, после захода человека на Ваш сервер."
            ), ephemeral=True
        )

    @reaction_role.sub_command(name="set", description="Установка роли за реакцию на сообщение")
    async def reaction_role_set(self, inter, channel: disnake.TextChannel, message_id: str, role: disnake.Role, emoji):
        message = await channel.fetch_message(int(message_id))
        emoji_data = emoji if emoji in emj.UNICODE_EMOJI_ALIAS_ENGLISH else str(emoji)

        if await inter.bot.config.DB.emojirole.count_documents({"_id": int(message_id)}) == 0:
            await inter.bot.config.DB.emojirole.insert_one({"_id": message.id, "emojis": [{emoji_data: [role.id]}]})
        else:
            await inter.bot.config.DB.emojirole.update_one({"_id": message.id}, {"$push": {"emojis": {emoji_data: [role.id]}}})

        await inter.send(
            embed=await inter.bot.embeds.simple(
                title="Leyla settings **(reaction role)**", 
                description=f"Теперь при нажатии на реакцию, на том сообщение, что вы указали, будет выдаваться роль", 
                fields=[{"name": "Роль", "value": role, "inline": True}, {"name": "ID сообщения", "value": message_id, "inline": True}],
                thumbnail=inter.author.display_avatar.url
            ), ephemeral=True
        )
        await message.add_reaction(emoji)

    @reaction_role.sub_command(name="remove", description="Удаление ролей за реакцию на сообщении")
    async def reaction_role_remove(self, inter, message_id: Optional[disnake.Message]):
        if await inter.bot.config.DB.emojirole.count_documents({"_id": message_id.id}) == 0:
            raise CustomError("На этом сообщение нет ролей за реакцию")
        else:
            await inter.bot.config.DB.emojirole.delete_one({"_id": message_id.id})

        await inter.send(
            embed=await inter.bot.embeds.simple(
                title="Leyla settings **(reaction role)**", 
                description=f"Больше роли за реакцию на этом сообщении работать не будут!",
                thumbnail=inter.author.display_avatar.url
            ), ephemeral=True
        )

    @voice_settings.sub_command(name="set-lobby", description="Указать лобби (категорию), где будут появляться голосовые каналы")
    async def voice_lobby(self, inter, lobby: disnake.CategoryChannel):
        if await inter.bot.config.DB.voice.count_documents({"_id": inter.guild.id}) == 0:
            await inter.bot.config.DB.voice.insert_one({"_id": inter.guild.id, "lobby": lobby.id})
        else:
            data = await inter.bot.config.DB.voice.find_one({"_id": inter.guild.id})

            if data['lobby'] == lobby.id:
                raise CustomError("Вообще-то, эта категория уже указана, как лобби!")
            else:
                await inter.bot.config.DB.voice.update_one({"_id": inter.guild.id}, {"$set": {"lobby": lobby.id}})
        
        await inter.send(
            embed=await inter.bot.embeds.simple(
                title="Приватные голосовые каналы", 
                description="Лобби было успешно указано :)",
                fields=[{"name": "Лобби", "value": lobby.name}]
            )
        )
    
    @voice_settings.sub_command(name="set-channel", description="Указание голосового канала, при входе в который, будет создаваться приватный канал")
    async def voice_channel_main(self, inter, channel: disnake.VoiceChannel):
        if await inter.bot.config.DB.voice.count_documents({"_id": inter.guild.id}) == 0:
            if bool(channel.category):
                await inter.bot.config.DB.voice.insert_one({"_id": inter.guild.id, "lobby": channel.category.id, "channel": channel.id})
            else:
                await inter.bot.config.DB.voice.insert_one({"_id": inter.guild.id, "channel": channel.id})
        else:
            data = await inter.bot.config.DB.voice.find_one({"_id": inter.guild.id})

            if 'channel' in data.keys():
                if data['channel'] == channel.id:
                    raise CustomError("Сейчас и так указан этот канал!")
            else:
                if bool(channel.category):
                    await inter.bot.config.DB.voice.update_one({"_id": inter.guild.id}, {"$set": {"lobby": channel.category.id, "channel": channel.id}})
                else:
                    await inter.bot.config.DB.voice.update_one({"_id": inter.guild.id}, {"$set": {"channel": channel.id}})
        
        await inter.send(
            embed=await inter.bot.embeds.simple(
                title="Приватные голосовые каналы",
                description="Голосовой канал для приватных комнат был создан",
                fields=[
                    {"name": "Канал", "value": channel.mention, "inline": True}, None if not bool(channel.category) else {"name": "Лобби", "value": channel.category.name, "inline": True}
                ]
            )
        )

    @settings.sub_command(name="prefix", description="Смена префикса бота")
    async def set_prefix(self, inter, prefix: str):
        if len(prefix) > 5:
            raise CustomError("Префикс не может быть больше чем >5-ти символов.")
        else:
            if await inter.bot.config.DB.prefix.count_documents({"_id": inter.guild.id}) == 0:
                await inter.bot.config.DB.prefix.insert_one({"_id": inter.guild.id, "prefix": prefix})
            else:
                await inter.bot.config.DB.prefix.update_one({"_id": inter.guild.id}, {"$set": {"prefix": prefix}})
            
            await inter.send(embed=await inter.bot.embeds.simple(description=f"Префикс успешно сменён на **{prefix}**!"))

    @settings.sub_command(name="counter", description="Канал, который вы укажете, будет указывать количество участников")
    async def settings_counter(self, inter, channel_type: Literal['Текстовый', 'Голосовой']):
        permissions = {
            inter.guild.default_role: disnake.PermissionOverwrite(
                send_messages=False, 
                read_messages=False, 
                connect=False
            )
        }

        if channel_type == "Текстовый":
            channel = await inter.guild.create_text_channel(name=f"Участников: {len(inter.guild.members)}", overwrites=permissions)
        else:
            channel = await inter.guild.create_voice_channel(name=f"Участников: {len(inter.guild.members)}", overwrites=permissions)

        if await inter.bot.config.DB.counter.count_documents({"_id": inter.guild.id}) == 0:
            await inter.bot.config.DB.counter.insert_one({"_id": inter.guild.id, "channel": channel.id})
        else:
            await inter.bot.config.DB.counter.update_one({"_id": inter.guild.id}, {"$set": {"channel": channel.id}})

        await inter.send(
            embed=await inter.bot.embeds.simple(
                title="Leyla settings **(counter)**", 
                description="Всё, счётчик участников включен :)", 
                fields=[{"name": "Канал", "value": channel.mention}]
            )
        )

    @trigger.sub_command(name='set', description="Устанавливает триггер-слово/предложение")
    async def trigger_set(self, inter, message: str = commands.Param(default=None, name="сообщение"), response: str = commands.Param(default=None, name='ответ-на-сообщение')):
        if await inter.bot.config.DB.trigger.count_documents({"guild": inter.guild.id, "trigger_message": message}) == 0:
            await inter.bot.config.DB.trigger.insert_one({"guild": inter.guild.id, "trigger_message": message.lower(), "response": response, 'trigger_id': random.randint(10000, 99999)})
        else:
            raise CustomError("Триггер на такое сообщение уже существует")
        
        await inter.send(
            embed=await inter.bot.embeds.simple(
                title='Leyla settings **(trigger)**',
                description="Триггер-сообщение установлено!",
                fields=[
                    {"name": 'Сообщение', 'value': message},
                    {'name': 'Мой ответ на это', 'value': response}
                ]
            )
        )

    @trigger.sub_command(name='remove', description="Убирает триггер")
    async def trigger_remove(self, inter, trigger_id: int):
        if await inter.bot.config.DB.trigger.count_documents({"guild": inter.guild.id, "trigger_id": trigger_id}) > 0:
            await inter.bot.config.DB.trigger.delete_one({"guild": inter.guild.id, "trigger_id": trigger_id})
        else:
            raise CustomError("Триггер на такое сообщение не существует")
        
        await inter.send(
            embed=await inter.bot.embeds.simple(
                title='Leyla settings **(trigger)**',
                description="Триггер-сообщение убрано!"
            )
        )

    @trigger.sub_command(name='list', description="Список триггеров")
    async def trigger_list(self, inter, page: int = 1):
        data = [i async for i in inter.bot.config.DB.trigger.find({"guild": inter.guild.id})]
        items_per_page = 10
        pages = math.ceil(len(data) / items_per_page)
        start = (page - 1) * items_per_page
        end = start + items_per_page
        trigger = ''

        for i, j in enumerate(data[start:end], start=start):
            trigger += f'[{i+1}] **{j["trigger_id"]}** | {j["trigger_message"]} | {j["response"]}\n'

        embed = await inter.bot.embeds.simple(
            title=f"Количество триггеров — {len(data)}",
            description=trigger if data else "На сервере нет триггеров",
            footer={"text": f"Страница: {page}/{pages}", "icon_url": inter.author.display_avatar.url}
        )

        await inter.send(embed=embed)

    @word_game.sub_command(name='channel', description='Установка канала для игры в слова')
    async def word_game_channel(self, inter, channel: disnake.TextChannel):
        db = inter.bot.config.DB.word_game

        if await db.count_documents({"_id": inter.guild.id}) == 0:
            await db.insert_one({"_id": inter.guild.id, "channel": channel.id})
        else:
            await db.update_one({"_id": inter.guild.id}, {"$set": {"channel": channel.id}})
        
        await inter.send(
            embed=inter.bot.embed(
                title='Leyla settings **(word game)**',
                description="Канал на игру в слова был выбран! Наслаждайтесь"
            ).start(fields=[Field(name="Канал", value=channel.mention)])
        )


def setup(bot):
    bot.add_cog(Settings(bot))
