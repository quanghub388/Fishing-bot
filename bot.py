import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import os
from flask import Flask
import threading

# ====================== CONFIG ======================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=":", intents=intents)
TOKEN = os.getenv("DISCORD_TOKEN")

# ====================== DATA ========================
# Cá với giá đã giảm 10 lần trừ Exotic
fishes = {
    # Common
    "🐟 Cá trích": {"price": 10, "luck": 3, "level_exp": 5},
    "🐠 Cá rô": {"price": 15, "luck": 4, "level_exp": 6},
    "🐡 Cá vàng": {"price": 20, "luck": 5, "level_exp": 8},
    # Uncommon
    "🐟 Cá hồng": {"price": 50, "luck": 10, "level_exp": 12},
    "🐠 Cá chép": {"price": 60, "luck": 12, "level_exp": 15},
    # Epic
    "🦈 Cá mập con": {"price": 100, "luck": 15, "level_exp": 20},
    "🐠 Cá kiếm": {"price": 120, "luck": 18, "level_exp": 25},
    # Legendary
    "🐋 Cá voi": {"price": 200, "luck": 25, "level_exp": 35},
    # Mythic
    "🦈 Cá Megalodon Baby": {"price": 300, "luck": 30, "level_exp": 50},
    # Exotic (không giảm giá)
    "🐟 CatFish": {"price": 350000, "luck": 50, "level_exp": 500},
    "🦈 Megalodon": {"price": 500000, "luck": 60, "level_exp": 800},
}

# Cần + Mồi
rods = {
    "Cần tre": {"price": 100, "durability": 10},
    "Cần sắt": {"price": 500, "durability": 30},
    "Cần vàng": {"price": 2000, "durability": 50},
    "Cần kim cương": {"price": 10000, "durability": 100},
    "Cần newbie": {"price": 10, "durability": 5},
}

baits = {
    "🪱 Giun đất": {"price": 500, "luck": 3, "durability": 35},
    "🐛 Sâu đất": {"price": 1000, "luck": 5, "durability": 50},
    "🦐 Tôm nhỏ": {"price": 2000, "luck": 10, "durability": 80},
    "🍤 Mồi tôm": {"price": 5000, "luck": 20, "durability": 120},
    "🐟 Cá nhỏ": {"price": 100, "luck": 2, "durability": 20},
    "🐞 Bọ cánh cứng": {"price": 50, "luck": 1, "durability": 15},
}

# Player data
players = {}  # {user_id: {"level": int, "exp": int, "rod": str, "bait": str, "fish": []}}

# ====================== FLASK APP ====================
app = Flask('')

@app.route('/')
def home():
    return "Fishing Bot is running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# ====================== HELP COMMAND ======================
@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(title="Fishing Bot Commands", color=discord.Color.blue())
    embed.add_field(name=":cauca or /cauca", value="Câu cá", inline=False)
    embed.add_field(name=":shop or /shop", value="Xem cửa hàng cần và mồi", inline=False)
    embed.add_field(name=":inventory or /inventory", value="Xem cá và đồ của bạn", inline=False)
    embed.add_field(name=":upgrade or /upgrade", value="Mua cần/mồi nâng cấp", inline=False)
    embed.add_field(name=":level or /level", value="Xem level của bạn", inline=False)
    await ctx.send(embed=embed)

# ====================== SLASH COMMAND ======================
@bot.tree.command(name="cauca", description="Câu cá thôi!")
async def slash_cauca(interaction: discord.Interaction):
    user_id = interaction.user.id
    await interaction.response.defer()  # Avoid timeout

    rod = "Cần newbie"
    bait = "🪱 Giun đất"

    fish_list = list(fishes.keys())
    weights = [fishes[f]["luck"] for f in fish_list]

    exotic_fishes = ["CatFish", "Megalodon"]
    if random.randint(1, 1000) <= 1:
        fish_caught = random.choice(exotic_fishes)
    else:
        fish_caught = random.choices(fish_list, weights=weights)[0]

    if user_id not in players:
        players[user_id] = {"level": 1, "exp": 0, "rod": rod, "bait": bait, "fish": []}

    players[user_id]["fish"].append(fish_caught)
    players[user_id]["exp"] += fishes[fish_caught]["level_exp"]

    while players[user_id]["exp"] >= players[user_id]["level"] * 100:
        players[user_id]["exp"] -= players[user_id]["level"] * 100
        players[user_id]["level"] += 1

    embed = discord.Embed(title=f"🎣 {interaction.user.name} câu cá!", color=discord.Color.green())
    embed.add_field(name="Cá câu được", value=fish_caught, inline=False)
    embed.add_field(name="Level hiện tại", value=str(players[user_id]["level"]), inline=True)
    embed.add_field(name="Exp hiện tại", value=str(players[user_id]["exp"]), inline=True)
    await interaction.followup.send(embed=embed)

# Prefix version
@bot.command(name="cauca")
async def prefix_cauca(ctx):
    user_id = ctx.author.id
    await slash_cauca(await ctx.send("Đang câu cá..."))

# ====================== READY ======================
@bot.event
async def on_ready():
    await bot.tree.sync()
    keep_alive()
    print(f"{bot.user} is online and ready!")

# ====================== RUN BOT ======================
bot.run(TOKEN)
