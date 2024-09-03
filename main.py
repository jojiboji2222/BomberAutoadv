import colorama
import asyncio
import yaml
import requests
import random
import time
import os
from datetime import datetime

colorama.init(autoreset=True)

# Load or initialize configuration
def load_config():
    if not os.path.exists('config.yml'):
        default_config = {
            'tokens': [],
            'interval': 15,
            'randomize_interval': {
                'enabled': False,
                'minimum_interval': 10,
                'maximum_interval': 30,
            },
            'wait_between_messages': {
                'enabled': False,
                'minimum_interval': 1,
                'maximum_interval': 5,
            },
            'debug_mode': False,
        }
        with open('config.yml', 'w') as file:
            yaml.dump(default_config, file)
    with open('config.yml', "r") as file:
        return yaml.load(file, Loader=yaml.FullLoader)

def save_config(config):
    with open('config.yml', 'w') as file:
        yaml.dump(config, file)

config = load_config()

# ASCII Banner
print(colorama.Fore.RED + '''
     █████╗ ██╗   ██╗████████╗ ██████╗      █████╗ ██████╗ 
    ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗    ██╔══██╗██╔══██╗
    ███████║██║   ██║   ██║   ██║   ██║    ███████║██║  ██║
    ██╔══██║██║   ██║   ██║   ██║   ██║    ██╔══██║██║  ██║
    ██║  ██║╚██████╔╝   ██║   ╚██████╔╝    ██║  ██║██████╔╝
    ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝     ╚═╝  ╚═╝╚═════╝ 
''' + colorama.Fore.RESET + "  AUTO AD by Bomber\n")

# Menu for changing settings
def settings_menu():
    while True:
        print("\nSettings Menu")
        print("1. Add Token")
        print("2. Remove Token")
        print("3. Add Channel to a Token")
        print("4. Remove Channel from a Token")
        print("5. Change Message for a Channel")
        print("6. Toggle Debug Mode")
        print("7. Save and Exit")
        
        choice = input("Choose an option (1-7): ")

        if choice == "1":
            token = input("Enter the new token: ")
            config['tokens'].append({'token': token, 'channels': []})
            print("Token added.")

        elif choice == "2":
            token_index = int(input("Enter the token index to remove (1-{}): ".format(len(config['tokens'])))) - 1
            if 0 <= token_index < len(config['tokens']):
                del config['tokens'][token_index]
                print("Token removed.")

        elif choice == "3":
            token_index = int(input("Enter the token index to add a channel (1-{}): ".format(len(config['tokens'])))) - 1
            if 0 <= token_index < len(config['tokens']):
                channel_id = input("Enter the channel ID: ")
                message = input("Enter the message for this channel: ")
                config['tokens'][token_index]['channels'].append({'id': channel_id, 'message': message})
                print("Channel added.")

        elif choice == "4":
            token_index = int(input("Enter the token index to remove a channel (1-{}): ".format(len(config['tokens'])))) - 1
            if 0 <= token_index < len(config['tokens']):
                channel_index = int(input("Enter the channel index to remove (1-{}): ".format(len(config['tokens'][token_index]['channels'])))) - 1
                if 0 <= channel_index < len(config['tokens'][token_index]['channels']):
                    del config['tokens'][token_index]['channels'][channel_index]
                    print("Channel removed.")

        elif choice == "5":
            token_index = int(input("Enter the token index to change a channel message (1-{}): ".format(len(config['tokens'])))) - 1
            if 0 <= token_index < len(config['tokens']):
                channel_index = int(input("Enter the channel index to change the message (1-{}): ".format(len(config['tokens'][token_index]['channels'])))) - 1
                if 0 <= channel_index < len(config['tokens'][token_index]['channels']):
                    new_message = input("Enter the new message: ")
                    config['tokens'][token_index]['channels'][channel_index]['message'] = new_message
                    print("Message updated.")

        elif choice == "6":
            config['debug_mode'] = not config.get('debug_mode', False)
            print("Debug mode set to", config['debug_mode'])

        elif choice == "7":
            save_config(config)
            print("Settings saved.")
            break

        else:
            print("Invalid option. Please try again.")

settings_menu()

async def getChannelInfo(channel_id, headers):
    try:
        channel = requests.get(f'https://discord.com/api/v9/channels/{channel_id}', headers=headers).json()
        guild_id = channel.get('guild_id')
        if guild_id:
            guild = requests.get(f'https://discord.com/api/v9/guilds/{guild_id}', headers=headers).json()
            guild_name = guild.get('name', 'Unknown guild')
        else:
            guild_name = 'Unknown guild'
        channel_name = channel.get('name', channel_id)
        return channel_name, guild_name
    except KeyError as e:
        print(f"{colorama.Fore.RED}KeyError in getChannelInfo: {e}{colorama.Fore.RESET}")
        return channel_id, 'Unknown guild'
    except Exception as e:
        print(f"{colorama.Fore.RED}Error in getChannelInfo: {e}{colorama.Fore.RESET}")
        return channel_id, 'Unknown guild'

async def sendToChannel(channel_id, message, channel_name, guild_name, headers):
    try:
        response = requests.post(
            f'https://discord.com/api/v9/channels/{channel_id}/messages', 
            json={'content': message}, 
            headers=headers
        ).json()
        if 'code' in response:
            if response['code'] == 50013:  # Muted
                print(f'{colorama.Fore.RED} > There was a problem sending a message to "{channel_name}" in "{guild_name}" (MUTED){colorama.Fore.RESET}')
            elif response['code'] == 20016:  # Slowmode
                print(f'{colorama.Fore.YELLOW} > Slowmode is active in "{channel_name}" in "{guild_name}". Message not sent.{colorama.Fore.RESET}')
            elif response['code'] == 40002:  # Invalid token
                print(f'{colorama.Fore.RED} > Invalid token used for "{channel_name}" in "{guild_name}".{colorama.Fore.RESET}')
            else:
                print(f'{colorama.Fore.RED} > Failed to send message to "{channel_name}" in "{guild_name}". Reason: {response["message"]}{colorama.Fore.RESET}')
        else:
            print(f'{colorama.Fore.GREEN} > Message sent successfully in "{channel_name}" in "{guild_name}"{colorama.Fore.RESET}')
    except Exception as e:
        print(f'{colorama.Fore.RED} > Error sending message to "{channel_name}" in "{guild_name}": {e}{colorama.Fore.RESET}')

async def sendMessages():
    for token_info in config.get('tokens', []):
        headers = {
            'Authorization': token_info.get('token', ''),
            'Content-Type': 'application/json'
        }

        for channel in token_info.get('channels', []):
            channel_id = channel.get('id', '')
            message = channel.get('message', '')

            try:
                channel_name, guild_name = await getChannelInfo(channel_id, headers)
                await sendToChannel(channel_id, message, channel_name, guild_name, headers)
            except Exception as e:
                print(f'{colorama.Fore.RED} > There was a problem sending a message to "{channel_id}": {e}{colorama.Fore.RESET}')

        # Delay between tokens - wait 10 seconds before processing the next token
        print(f'{colorama.Fore.CYAN}Waiting 10 seconds ... dont ask why just watch{colorama.Fore.RESET}')
        await asyncio.sleep(10)  # 10 seconds delay

async def start():
    while True:
        try:
            await sendMessages()
        except Exception as e:
            print(colorama.Fore.RED + f' > Error: {e}' + colorama.Fore.RESET)
            exit()

try:
    asyncio.run(start())
except KeyboardInterrupt:
    exit()
