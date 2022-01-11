import subprocess
import re
import os
from aiogram.types import message
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN, TOKEN
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types.message import ContentType

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    if ADMIN == str(message.from_user.id):
        hello_text = "Добро пожаловать в сервис VolkiTech SerBot!"
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.clean()
        keyboard.add(types.KeyboardButton(text="Services"))
        keyboard.add(types.KeyboardButton(text="Ports"))
        await bot.send_message(message.from_user.id, text=hello_text, reply_markup=keyboard)

@dp.message_handler(content_types=ContentType.ANY)
async def unknown_message(message: types.Message):
    if ADMIN == str(message.from_user.id):
        if(message.text == "Services"):
            page = 1
            all_services_str = all_services()
            while len(all_services_str) > 0:
                if len(all_services_str) <= 10:
                    result = []
                    for i in range(len(all_services_str)):
                        result.append(all_services_str.pop(0))
                    await bot.send_message(message.from_user.id, text="Page " + str(page), reply_markup=generate_services_list(result))
                if len(all_services_str) > 10:
                    result = []
                    for i in range(10):
                        result.append(all_services_str.pop(0))
                    await bot.send_message(message.from_user.id, text="Page " + str(page), reply_markup=generate_services_list(result))
                    page += 1
                result = []
        elif(message.text == "Ports"):
            all_ports_str = ports()
            while len(all_ports_str) > 0:
                if len(all_ports_str) <= 10:
                    result = []
                    for i in range(len(all_ports_str)):
                        result.append(all_ports_str.pop(0))
                    await bot.send_message(message.from_user.id, text=generate_ports(result))
                if len(all_ports_str) > 10:
                    result = []
                    for i in range(10):
                        result.append(all_ports_str.pop(0))
                    await bot.send_message(message.from_user.id, text=generate_ports(result))
                result = []
            
        elif("Command " in message.text):
            command = message.text.replace("Command ", "")
            await bot.send_message(message.from_user.id, text=custom_command(command))
        elif("Writer " in message.text):
            command = message.text.replace("Writer ", "").split(" ")
            name = command.pop(0)
            mode = command.pop(0)
            writeto(name, mode, " ".join(command))
        else:
            message_text = "Команда не распознана"
            await message.reply(message_text, parse_mode=ParseMode.MARKDOWN)


@dp.callback_query_handler(lambda c: c.data)
async def call_main_menu(call: types.CallbackQuery):
    if "reload_" in call.data:
        splited = call.data.split('_')
        splited.pop()
        name = '_'.join(splited)
        await bot.send_message(chat_id=call.message.chat.id, text=restart_service(name))
    elif "active_" in call.data:
        splited = call.data.split('_')
        splited.pop()
        name = '_'.join(splited)
        await bot.send_message(chat_id=call.message.chat.id, text=stop_service(name))
    elif "inactive_" in call.data:
        splited = call.data.split('_')
        splited.pop()
        name = '_'.join(splited)
        await bot.send_message(chat_id=call.message.chat.id, text=start_service(name))
    elif "service_" in call.data:
        splited = call.data.split('_')
        splited.pop()
        name = '_'.join(splited)
        await bot.send_message(chat_id=call.message.chat.id, text=status(status_service(name)))
    else:
        await bot.send_message(chat_id=call.message.chat.id, text="🤔")

def writeto(filename, mode, data):
    f = open(os.path.join(os.path.dirname(__file__), filename), mode)
    f.write(str(data))
    f.close()
    return

def all_services():
    command = subprocess.check_output("systemctl list-units --type=service --all --no-pager", shell=True).strip().decode()
    command_split = command.split("\n")
    for i, line in reversed(list(enumerate(command_split))):
        if ".service" not in line:
            del command_split[i]
    cell_data = []
    for i in command_split:
        if i == "":
            continue
        parts = i.split()
        description = ' '.join(i.split()[4:])
        if parts[0] == "●":
            description = ' '.join(i.split()[5:])
        if parts[0] == "●":
            cell_data.append([parts[1], parts[2], parts[3], parts[4], description])
            continue
        cell_data.append([parts[0], parts[1], parts[2], parts[3], description])
    return cell_data

def generate_services_list(services):
    inline_kb_full = InlineKeyboardMarkup(row_width=3)
    for line in services:
        inline_kb_full.row(unit_name(line[0]))
        inline_kb_full.row(InlineKeyboardButton('DESCR: ' + line[4], callback_data='call'))
        inline_kb_full.add(active_name(line[2], line[0]), reload_button(line[0]))
    return inline_kb_full

def reload_button(name):
    return InlineKeyboardButton('🔄', callback_data='reload_' + deservice(name))

def unit_name(name):
    return InlineKeyboardButton(deservice(name), callback_data='service_' + deservice(name))

def deservice(name):
    return name.replace(".service", "")

def load_name(status, name):
    if status == "loaded":
        return InlineKeyboardButton('LOADED ✅', callback_data='load_' + deservice(name))
    elif status == "not-found":
        return InlineKeyboardButton('NFOUND 🟥', callback_data='not-found_' + deservice(name))
    else: 
        return InlineKeyboardButton('ERROR ?', callback_data='error_' + deservice(name))

def active_name(status, name):
    if status == "active":
        return InlineKeyboardButton('ACTIVE ✅', callback_data='active_' + deservice(name))
    elif status == "inactive":
        return InlineKeyboardButton('INACTIVE 🟥', callback_data='inactive_' + deservice(name))
    else:
        return InlineKeyboardButton('ERROR ?', callback_data='error_' + deservice(name))

def sub_name(status, name):
    if status == "running":
        return InlineKeyboardButton('RUNNING ✅', callback_data='running_' + deservice(name))
    elif status == "dead":
        return InlineKeyboardButton('DEAD 🟥', callback_data='dead_' + deservice(name))
    elif status == "exited":
        return InlineKeyboardButton('EXITED 🟥', callback_data='exited_' + deservice(name))
    else:
        return InlineKeyboardButton('ERROR ?', callback_data='error_' + deservice(name))

def start_service(name_service):
    try:
        command = subprocess.check_output("systemctl start " +  name_service, shell=True).strip()
        (output, err) = command.communicate()
        output = output.decode('utf-8')
    except subprocess.CalledProcessError as e:
        return "Error: " + str(e)
    except AttributeError as e:
        pass
    return name_service + " Started"

def stop_service(name_service):
    try:
        command = subprocess.check_output("systemctl stop " +  name_service, shell=True).strip()
        (output, err) = command.communicate()
        output = output.decode('utf-8')
    except subprocess.CalledProcessError as e:
        return "Error: " + str(e)
    except AttributeError as e:
        pass
    return name_service + " Stopped"

def restart_service(name_service):
    try:
        command = subprocess.check_output("systemctl restart " +  name_service, shell=True).strip()
        (output, err) = command.communicate()
        output = output.decode('utf-8')
    except subprocess.CalledProcessError as e:
        return "Error " + str(e)
    except AttributeError as e:
        pass
    return name_service + " Restarted"

def status_service(name_service):
    command = subprocess.Popen(["systemctl", "status",  name_service], stdout=subprocess.PIPE)
    (output, err) = command.communicate()
    output = output.decode('utf-8')
    service_regx = r"Loaded:.*\/(.*service);"
    status_regx= r"Active:(.*) since (.*);(.*)"
    service_status = {}
    for line in output.splitlines():
        service_search = re.search(service_regx, line)
        status_search = re.search(status_regx, line)
        if service_search:
            service_status['service'] = service_search.group(1)
        elif status_search:
            service_status['status'] = status_search.group(1).strip()
            service_status['since'] = status_search.group(2).strip()
            service_status['uptime'] = status_search.group(3).strip()
    service_status['real_name'] = name_service + ".service"
    return service_status

def status(service_status):
    service = service_status.get('real_name')
    status = service_status.get('status')
    since = service_status.get('since')
    uptime = service_status.get('uptime')
    return "SERVICE: " + str(service) + "\n" + "STATUS: " + str(status) + "\n" + "SINCE: " + str(since) + "\n" + "UPTIME: " + str(uptime)

def ports():
    command = subprocess.check_output("netstat -ltnp", shell=True).strip().decode()
    command_split = command.split("\n")
    del command_split[0]
    del command_split[0]
    cell_data = []
    for i in command_split:
        if i == "":
            continue
        parts = i.split()
        cell_data.append([parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6]])
    return cell_data

def generate_ports(ports_data):
    ports_string = ""
    for line in ports_data:
        ports_string += line[0] + " " + line[3] + " " + line[4] + " " + line[5] + " " + line[6] + "\n"
    return ports_string

def custom_command(command_to_execute):
    try:
        command = subprocess.check_output(command_to_execute, shell=True).strip().decode()
    except subprocess.CalledProcessError as e:
        return "Error: " + str(e)
    except (AttributeError, ValueError) as e:
        return "Error: " + str(e)
    return command


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)