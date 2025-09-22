import discord
from discord.ext import commands
import os
import random
from flask import Flask
import threading

# --- Dữ liệu cá ---
fish = {
    "common": {
        "🐟 Cá nhỏ": {"price": 10, "luck": 1},
        "🐠 Cá vàng": {"price": 20, "luck": 2},
        "🐡 Cá trích": {"price": 15, "luck": 2},
        "🐟 Cá rô phi": {"price": 25, "luck": 3}
    },
    "uncommon": {
        "🐡 Cá nóc": {"price": 50, "luck": 5},
        "🐟 Cá rô": {"price": 40, "luck": 4},
        "🐠 Cá hồi nhỏ": {"price": 45, "luck": 5}
    },
    "epic": {
        "🐟 Cá chép đỏ": {"price": 100, "luck": 10},
        "🐠 Cá hồng": {"price": 120, "luck": 12},
        "🐟 Cá mặt quỷ": {"price": 150, "luck": 15},
        "🐡 Cá thu": {"price": 130, "luck": 13}
    },
    "legendary": {
        "🐟 Cá rồng": {"price": 500, "luck": 50},
        "🐠 Cá thần": {"price": 550, "luck": 55},
        "🐡 Cá mập trắng": {"price": 600, "luck": 60}
    },
    "mythic": {
        "🐟 Cá khổng lồ": {"price": 1000, "luck": 100},
        "🐠 Cá leviathan": {"price": 1200, "luck": 120}
    },
    "exotic": {
        "CatFish": {"price": 350000, "luck": 5000},
        "Megalodon": {"price": 500000, "luck": 8000},
        "🐉 Cá thần tiên": {"price": 400000, "luck": 6000}
    }
}

# Giảm giá cá 10 lần (trừ exotic)
for rarity in fish:
    if rarity != "exotic":
        for f in fish[rarity]:
            fish[rarity][f]["price"] //= 10

# --- Dữ liệu cần ---
rods = [
    {"name": "Cần tre", "price": 50, "durability": 20},
    {"name": "Cần sắt", "price": 100, "durability": 40},
    {"name": "Cần vàng", "price": 500, "durability": 100},
    {"name": "Cần bạc", "price": 200, "durability": 60},
    {"name": "Cần kim cương", "price": 1000, "durability": 200}
]

# --- Dữ liệu mồi ---
baits = [
    {"name": "Giun đất", "price": 5, "luck": 3},
    {"name": "Trứng côn trùng", "price": 10, "luck": 5},
    {"name": "Tôm nhỏ", "price": 15, "luck": 8},
    {"name": "Cá mồi", "price": 20, "luck": 10},
    {"name": "Bánh mì", "price": 2, "luck": 1},
    {"name": "Hạt ngô", "price": 1, "luck": 1}
]

# --- Intents & Bot ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=[":", "/"], intents=intents, help_command=None)

# --- Cơ chế level ---
user_data = {}  # user_id: {"xp": ..., "level": ...}

def add_xp(user_id, amount):
    if user_id not in user_data:
        user_data[user_id] = {"xp": 0, "level": 1}
    user_data[user_id]["xp"] += amount
    level = user_data[user_id]["level"]
    while user_data[user_id]["xp"] >= level * 100:
        user_data[user_id]["xp"] -= level * 100
        user_data[user_id]["level"] += 1
        level = user_data[user_id]["level"]

# --- Lệnh câu cá ---
@bot.command()
async def cauca(ctx):
    luck = random.randint(1, 1000)
    caught = None
    if luck <= 1:  # 0.1% ra exotic
        caught = random.choice(list(fish["exotic"].keys()))
    else:
        rarity_roll = random.randint(1, 100)
        if rarity_roll <= 50:
            rarity = "common"
        elif rarity_roll <= 75:
            rarity = "uncommon"
        elif rarity_roll <= 90:
            rarity = "epic"
        elif rarity_roll <= 98:
            rarity = "legendary"
        else:
            rarity = "mythic"
        caught = random.choice(list(fish[rarity].keys()))
    
    # Thêm XP
    add_xp(ctx.author.id, 10)

    embed = discord.Embed(title="🎣 Kết quả câu cá", color=discord.Color.blue())
    embed.add_field(name="Người chơi", value=ctx.author.name, inline=True)
    embed.add_field(name="Cá bắt được", value=caught, inline=True)
    embed.add_field(name="Level hiện tại", value=user_data[ctx.author.id]["level"], inline=True)
    await ctx.send(embed=embed)

# --- Lệnh help ---
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📜 Lệnh bot câu cá", color=discord.Color.green())
    embed.add_field(name=":cauca", value="Câu cá", inline=False)
    embed.add_field(name=":help", value="Xem danh sách lệnh", inline=False)
    await ctx.send(embed=embed)

# --- Web server để chạy Render free ---
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

threading.Thread(target=run_web).start()

# --- Chạy bot ---
bot.run(os.getenv("DISCORD_TOKEN"))
