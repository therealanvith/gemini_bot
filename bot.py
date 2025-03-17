import discord
import random
import requests
import os
from discord.ext import commands


# --- CONFIGURATION ---
YOUR_USER_ID = 1208069980076118016  # Your Discord User ID
YOUR_API_KEY = os.getenv('API_KEY')  # Replace with your actual AI API key
API_URL = os.getenv('API_URL')
YOUR_BOT_TOKEN = os.getenv('BOT_TOKEN')  # Replace with your actual Discord Bot Token

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True  # Needed to listen to message content
bot = commands.Bot(command_prefix="!", intents=intents)

# --- HELPER FUNCTIONS ---
def chunk_text(text, max_length=2000):
    """Splits text into a list of substrings, each up to max_length characters."""
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

def get_ai_response(message_text):
    """Calls the AI API and returns its text response."""
    headers = {'Content-Type': 'application/json'}
    data = {
        'contents': [{
            'parts': [{
                'text': message_text
            }]
        }]
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        ai_response = response.json()
        return ai_response['candidates'][0]['content']['parts'][0]['text']
    except requests.exceptions.RequestException as e:
        return f"Error calling the AI API: {str(e)}"

async def fetch_referenced_message(message: discord.Message) -> discord.Message:
    """
    Safely fetch the message that the user is replying to.
    If it's not in cache, attempt to fetch it from the channel.
    """
    if not message.reference:
        return None

    ref = message.reference.resolved
    if ref:
        return ref
    else:
        try:
            return await message.channel.fetch_message(message.reference.message_id)
        except:
            return None

# --- BOT EVENT HANDLERS ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == bot.user:
        return

    # Fetch the referenced message if this is a reply
    referenced_msg = await fetch_referenced_message(message)

    if referenced_msg:
        if referenced_msg.author == bot.user:
            # Case 1: Reply to the bot's message (continuation)
            cleaned_content = message.content.replace(bot.user.mention, "").strip()
            combined_prompt = (
                f"Previous bot message:\n{referenced_msg.content}\n\n"
                f"User's new message:\n{cleaned_content}\n\n"
                "Answer the user's new question, continuing the context."
            )
            ai_response = get_ai_response(combined_prompt)
            chunks = chunk_text(ai_response, 2000)
            if not chunks:
                await message.channel.send("No response from AI.", reference=message)
            else:
                for chunk in chunks:
                    await message.channel.send(chunk, reference=message)
        elif bot.user in message.mentions:
            # Case 2: Reply to any message with bot mentioned (new feature)
            cleaned_content = message.content.replace(bot.user.mention, "").strip()
            context_prompt = (
                f"The user is replying to the following message:\n{referenced_msg.content}\n\n"
                f"Now, the user is asking:\n{cleaned_content}\n\n"
                "Please respond to the user's question, taking the context into account if relevant."
            )
            ai_response = get_ai_response(context_prompt)
            chunks = chunk_text(ai_response, 2000)
            if not chunks:
                await message.channel.send(f"Hey {message.author.mention}, no response from AI.", reference=message)
            else:
                await message.channel.send(f"Hey {message.author.mention},", reference=message)
                for chunk in chunks:
                    await message.channel.send(chunk, reference=message)
    else:
        # Case 3: Not a reply, check for direct mention
        if bot.user in message.mentions:
            cleaned_content = message.content.replace(bot.user.mention, "").strip()
            ai_response = get_ai_response(cleaned_content)
            chunks = chunk_text(ai_response, 2000)
            if not chunks:
                await message.channel.send(f"Hey {message.author.mention}, no response from AI.", reference=message)
            else:
                await message.channel.send(f"Hey {message.author.mention},", reference=message)
                for chunk in chunks:
                    await message.channel.send(chunk, reference=message)

bot.run(YOUR_BOT_TOKEN)
