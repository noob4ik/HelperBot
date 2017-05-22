from telegram import Update, Bot
import logging
from core.functions.triggers import trigger_decorator
from core.types import AdminType, Admin, admin, session
from core.utils import send_async
from core.functions.reply_markup import generate_standard_markup

logger = logging.getLogger(__name__)


def error(bot: Bot, update, error, **kwargs):
    """ Error handling """
    logger.error("An error (%s) occurred: %s"
                 % (type(error), error.message))


def start(bot: Bot, update: Update):
    if update.message.chat.type == 'private':
        send_async(bot, chat_id=update.message.chat.id, text='Привет')


@admin()
def admin_panel(bot: Bot, update: Update):
    if update.message.chat.type == 'private':
        send_async(bot, chat_id=update.message.chat.id, text='Да здравствует админ!', reply_markup=generate_standard_markup())


@admin()
def kick(bot: Bot, update: Update):
    bot.leave_chat(update.message.chat.id)


@trigger_decorator
def help_msg(bot: Bot, update):
    admin_user = session.query(Admin).filter_by(user_id=update.message.from_user.id).all()
    global_adm = False
    for adm in admin_user:
        if adm.admin_type == AdminType.FULL.value:
            global_adm = True
            break
    if global_adm:
        send_async(bot, chat_id=update.message.chat.id, text='Команды приветствия:\n'
                                                             '/enable_welcome - Включить приветствие\n'
                                                             '/disable_welcome - Выключить приветствие\n'
                                                             '/set_welcome <текст> - Установить текст приветствия. '
                                                             'Может содержать %username% - будет заменено на @username, '
                                                             'если не установлено на Имя Фамилия, %first_name% - на имя, '
                                                             '%last_name% - на фамилию, %id% - на id\n'
                                                             '/show_welcome - Показать текущий текст приветствия для '
                                                             'данного чата'
                                                             '\n\n'
                                                             'Команды триггеров:\n'
                                                             '/set_trigger <триггер>::<сообщение> - Установить сообщение, '
                                                             'которое бот будет кидать по триггеру.\n'
                                                             '/add_trigger <триггер>::<сообщение> - Добавляет сообщение, '
                                                             'которое бот будет кидать по триггеру, но не заменяет старый.\n'
                                                             '/del_trigger <триггер> - Удалить соответствующий триггер\n'
                                                             '/list_triggers - Показать все существующие триггеры'
                                                             '\n\n'
                                                             'Команды глобаладмина:\n'
                                                             '/add_admin <юзернэйм> - Добавить админа для текущего чата\n'
                                                             '/del_admin <юзернэйм> - Забрать привелегии у админа текущего '
                                                             'чата\n'
                                                             '/list_admins - Показать список местных админов\n'
                                                             '/enable_trigger - Разрешить триггерить всем в группе\n'
                                                             '/disable_trigger - Запретить триггерить всем в группе')
    elif len(admin_user) != 0:
        send_async(bot, chat_id=update.message.chat.id, text='Команды приветствия:\n'
                                                             '/enable_welcome - Включить приветствие\n'
                                                             '/disable_welcome - Выключить приветствие\n'
                                                             '/set_welcome <текст> - Установить текст приветствия. '
                                                             'Может содержать %username% - будет заменено на @username, '
                                                             'если не установлено на Имя Фамилия, %first_name% - на имя, '
                                                             '%last_name% - на фамилию, %id% - на id\n'
                                                             '/show_welcome - Показать текущий текст приветствия для '
                                                             'данного чата'
                                                             '\n\n'
                                                             'Команды триггеров:\n'
                                                             '/add_trigger <триггер>::<сообщение> - Добавляет сообщение, '
                                                             'которое бот будет кидать по триггеру, но не заменяет старый.\n'
                                                             '/list_triggers - Показать все существующие триггеры\n'
                                                             '/enable_trigger - Разрешить триггерить всем в группе\n'
                                                             '/disable_trigger - Запретить триггерить всем в группе')
    else:
        send_async(bot, chat_id=update.message.chat.id, text='Команды триггеров:\n'
                                                             '/list_triggers - Показать все существующие триггеры')


@admin(adm_type=AdminType.GROUP)
def ping(bot: Bot, update: Update):
    send_async(bot, chat_id=update.message.chat.id, text='Иди освежись, @' + update.message.from_user.username + '!')


def get_diff(dict_one, dict_two):
    resource_diff = {}
    for key, val in dict_one.items():
        if key in dict_two:
            diff_count = dict_one[key] - dict_two[key]
            if diff_count != 0:
                resource_diff[key] = diff_count
        else:
            resource_diff[key] = val
    for key, val in dict_two.items():
        if key not in dict_one:
            resource_diff[key] = -val
    return resource_diff


def stock_compare(bot: Bot, update: Update, chat_data: dict):
    strings = update.message.text.splitlines()
    resources = {}
    for string in strings[1:]:
        resource = string.split(' (')
        resource[1] = resource[1][:-1]
        resources[resource[0]] = int(resource[1])
    if 'resources' in chat_data:
        resource_diff = get_diff(resources, chat_data['resources'])
        msg = 'Изменения ресурсов:\n'
        if len(resource_diff):
            for key, val in resource_diff.items():
                msg += '{} ({})\n'.format(key, val)
        else:
            msg += 'Ничего не изменилось'
        send_async(bot, chat_id=update.message.chat.id, text=msg)
    else:
        send_async(bot, chat_id=update.message.chat.id, text='Жду с чем сравнивать...')
    chat_data['resources'] = resources


def trade_compare(bot: Bot, update: Update, chat_data: dict):
    strings = update.message.text.splitlines()
    items = {}
    for string in strings:
        if string.startswith('/add_'):
            item = string.split('   ')[1]
            item = item.split(' x ')
            items[item[0]] = int(item[1])
    if 'items' in chat_data:
        resource_diff = get_diff(items, chat_data['items'])
        msg = 'Изменения предметов:\n'
        if len(resource_diff):
            for key, val in resource_diff.items():
                msg += '{} ({})\n'.format(key, val)
        else:
            msg += 'Ничего не изменилось'
        send_async(bot, chat_id=update.message.chat.id, text=msg)
    else:
        send_async(bot, chat_id=update.message.chat.id, text='Жду с чем сравнивать...')
    chat_data['items'] = items