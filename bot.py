import discord
import random
import requests
from discord.ext import commands

# --- CONFIGURATION ---
YOUR_USER_ID = 1208069980076118016  # Your Discord User ID
YOUR_API_KEY = 'AIzaSyDVf6PFqLxnl0ShFokVA-cGxAZtw6fcpj0'       # Replace with your actual AI API key
API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=AIzaSyDVf6PFqLxnl0ShFokVA-cGxAZtw6fcpj0'
YOUR_BOT_TOKEN = 'MTM0MzQzODgxNTI3MTk3NzAyMA.GIJMnA.aqRJ_vgTmzUWuXIWWw4VRhFjnFpZ-fWVjAB73A'   # Replace with your actual Discord Bot Token

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True  # Needed to listen to message content
bot = commands.Bot(command_prefix="!", intents=intents)

# --- RICKROLL RESPONSES ---
rickroll_responses = [
    "Never gonna give you up, never gonna let you down! 🎶 [You got rickrolled!](https://www.youtube.com/watch?v=dQw4w9WgXcQ)",
    "Oops, you did it again! 😎 [Here's your rickroll](https://www.youtube.com/watch?v=dQw4w9WgXcQ).",
    "Congratulations! You've been rickrolled! 🎉 [Watch this!](https://www.youtube.com/watch?v=dQw4w9WgXcQ)",
    "Haha, gotcha! 🎶 [Rickroll alert](https://www.youtube.com/watch?v=dQw4w9WgXcQ)! Enjoy the song!",
    "I just wanted to tell you, you're never gonna get this rickroll out of your head! 🎤 [Here's the link](https://www.youtube.com/watch?v=dQw4w9WgXcQ)"
]

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

    # 1) Check if this is a reply to one of the bot's messages
    referenced_msg = await fetch_referenced_message(message)
    if referenced_msg and referenced_msg.author == bot.user:
        # Build a combined prompt using the previous bot message and the new user text
        old_bot_text = referenced_msg.content
        new_user_text = message.content
        combined_prompt = (
            f"Previous bot message:\n{old_bot_text}\n\n"
            f"User's new message:\n{new_user_text}\n\n"
            "Answer the user's new question, continuing the context."
        )

        # If the message is from you, get an AI response; otherwise, rickroll.
        if message.author.id == YOUR_USER_ID:
            ai_response = get_ai_response(combined_prompt)
            chunks = chunk_text(ai_response, 2000)
            if not chunks:
                await message.channel.send("No response from AI.")
            else:
                # Send all chunks without a greeting (as requested for replies)
                for chunk in chunks:
                    await message.channel.send(chunk)
        else:
            # For non-owner replies, simply rickroll without the greeting
            rickroll = random.choice(rickroll_responses)
            await message.channel.send(rickroll)
        return  # Stop further processing for replies

    # 2) If it's not a reply, check if the bot is mentioned
    if bot.user in message.mentions:
        # Remove the bot mention from the message content
        content_without_mention = message.content.replace(bot.user.mention, "").strip()

        if message.author.id == YOUR_USER_ID:
            ai_response = get_ai_response(content_without_mention)
            chunks = chunk_text(ai_response, 2000)
            if not chunks:
                await message.channel.send(f"Hey {message.author.mention}, no response from AI.")
            else:
                await message.channel.send(f"Hey {message.author.mention},")
                for chunk in chunks:
                    await message.channel.send(chunk)
        else:
            rickroll = random.choice(rickroll_responses)
            await message.channel.send(f"Hey {message.author.mention}, {rickroll}")
    # 3) Otherwise, ignore the message
    return

bot.run(YOUR_BOT_TOKEN)
