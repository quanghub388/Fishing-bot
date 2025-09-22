import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import asyncio
from flask import Flask
from threading import Thread
import os
import json

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=":", intents=intents, help_command=None)

PLAYERS_FILE = "players.json"
players = {}

# ========================= SAVE/LOAD =========================
def load_players():
    global players
    if os.path.exists(PLAYERS_FILE):
        with open(PLAYERS_FILE, "r") as f:
            players = json.load(f)
    else:
        players = {}

def save_players():
    with open(PLAYERS_FILE, "w") as f:
        json.dump(players, f, indent=4)

# ========================= ITEM DATA =========================
# Cá
fish_data = {
    "Common": {"Goldfish🐟":10, "Carp🐟":20, "Salmon🐟":30, "Tilapia🐟":15, "Catla🐟":18, "Perch🐟":22, "Goby🐟":12, "Minnow🐟":8, "Crappie🐟":14, "Sunfish🐟":17},
    "Uncommon": {"Trout🐟":50, "Pike🐟":60, "Bass🐟":55, "Mackerel🐟":52, "Herring🐟":48},
    "Epic": {"Tuna🐟":100, "Swordfish🐟":150, "Eel🐟":120, "Snapper🐟":130},
    "Legendary": {"Shark🦈":250, "Marlin🐟":300, "Sturgeon🐟":270},
    "Mythic": {"Catfish🐟":350000, "Megalodon🦈":500000},
    "Exotic": {"Dragonfish🐉":1000000, "Golden Koi🐟":750000}
}

# Cần
rod_data = {
    "Bamboo🎣":50, "Wooden🎣":80, "Iron🎣":200, "Steel🎣":500, "Diamond🎣":2000, "ExoticRod🎣":10000,
    "Silver🎣":350, "Gold🎣":500, "Platinum🎣":1000, "Titanium🎣":1500, "Obsidian🎣":2500, "Crystal🎣":3000,
    "EliteRod🎣":5000, "LegendRod🎣":8000, "MythicRod🎣":15000
}

# Mồi
bait_data = {
    "Worm🪱":5, "Insect🪲":10, "Shrimp🦐":20, "FishEgg🥚":50, "Bread🍞":15, "Corn🌽":12, "Cheese🧀":18,
    "Chicken🍗":25, "Squid🦑":30, "SalmonEgg🥚":40, "FrogLeg🐸":35, "Lobster🦞":60, "Crab🦀":55, "Plankton🪸":2,
    "Maggot🪰":3, "Caterpillar🐛":4, "Anchovy🐟":8, "Minnow🐟":7, "Kelp🌿":6, "Beetle🪲":9, "Ant🐜":5, "Snail🐌":10,
    "Mantis🐛":12, "Grasshopper🦗":6
}

# ========================= HELP =========================
@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(title="Fishing Bot Commands", color=discord.Color.blue())
    embed.add_field(name=":cauca or /cauca", value="Câu cá 🐟", inline=False)
    embed.add_field(name=":shop or /shop", value="Xem shop cần 🎣 / mồi 🪱", inline=False)
    embed.add_field(name=":balance or /balance", value="Xem tiền 💶 & level", inline=False)
    embed.add_field(name=":buy or /buy", value="Mua cần/mồi: `:buy Iron🎣`", inline=False)
    embed.add_field(name=":transfer or /transfer", value="Chuyển tiền 💶: `:transfer @user 100`", inline=False)
    await ctx.send(embed=embed)

# ========================= BALANCE =========================
@bot.command(name="balance")
async def balance(ctx):
    user = str(ctx.author.id)
    if user not in players:
        players[user] = {"money":1000, "level":1}
        save_players()
    await ctx.send(f"{ctx.author.mention}, bạn có {players[user]['money']} 💶, level {players[user]['level']}")

# ========================= SHOP =========================
@bot.command(name="shop")
async def shop(ctx):
    embed = discord.Embed(title="Shop Cần 🎣 & Mồi 🪱", color=discord.Color.purple())
    rods = "\n".join([f"{name}: {price} 💶" for name, price in rod_data.items()])
    baits = "\n".join([f"{name}: {price} 💶" for name, price in bait_data.items()])
    embed.add_field(name="Cần 🎣", value=rods, inline=True)
    embed.add_field(name="Mồi 🪱", value=baits, inline=True)
    await ctx.send(embed=embed)

# ========================= BUY =========================
@bot.command(name="buy")
async def buy(ctx, item: str):
    user = str(ctx.author.id)
    if user not in players:
        players[user] = {"money":1000, "level":1}
    cost = rod_data.get(item) or bait_data.get(item)
    if not cost:
        await ctx.send("Item không tồn tại.")
        return
    if players[user]["money"] < cost:
        await ctx.send("Bạn không đủ tiền!")
        return
    players[user]["money"] -= cost
    save_players()
    await ctx.send(f"{ctx.author.mention} đã mua {item} với giá {cost} 💶!")

# ========================= TRANSFER =========================
@bot.command(name="transfer")
async def transfer(ctx, member: discord.Member, amount: int):
    sender = str(ctx.author.id)
    receiver = str(member.id)
    if sender not in players:
        players[sender] = {"money":1000, "level":1}
    if receiver not in players:
        players[receiver] = {"money":1000, "level":1}
    if players[sender]["money"] < amount:
        await ctx.send("Bạn không đủ tiền!")
        return
    players[sender]["money"] -= amount
    players[receiver]["money"] += amount
    save_players()
    await ctx.send(f"{ctx.author.mention} đã chuyển {amount} 💶 cho {member.mention}")

# ========================= FISH =========================
@bot.command(name="cauca")
async def fish(ctx):
    user = str(ctx.author.id)
    if user not in players:
        players[user] = {"money":1000, "level":1}
    roll = random.random()
    if roll <= 0.001: rarity = "Exotic"
    elif roll <= 0.01: rarity = "Mythic"
    elif roll <= 0.05: rarity = "Legendary"
    elif roll <= 0.2: rarity = "Epic"
    elif roll <= 0.5: rarity = "Uncommon"
    else: rarity = "Common"
    fish = random.choice(list(fish_data[rarity].keys()))
    money_earned = fish_data[rarity][fish]
    if rarity not in ["Mythic","Exotic"]:
        money_earned //= 10
    players[user]["money"] += money_earned
    save_players()
    embed = discord.Embed(title=f"🎣 {ctx.author.name} câu cá!", color=discord.Color.green())
    embed.add_field(name=f"Rarity: {rarity}", value=f"Fish: {fish}", inline=False)
    embed.add_field(name="Coins kiếm được 💶", value=f"{money_earned}", inline=False)
    embed.set_footer(text=f"Level: {players[user]['level']}")
    await ctx.send(embed=embed)

# ========================= KEEP ALIVE TASK =========================
@tasks.loop(minutes=5)
async def keep_alive():
    print("Bot vẫn đang online...")

@bot.event
async def on_ready():
    load_players()
    print(f"{bot.user} đã online!")
    keep_alive.start()
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synced ({len(synced)})")
    except Exception as e:
        print(e)

# ========================= SLASH COMMANDS =========================
@bot.tree.command(name="cauca", description="Câu cá 🐟")
async def slash_cauca(interaction: discord.Interaction):
    await fish(interaction)

@bot.tree.command(name="balance", description="Xem tiền 💶 & level")
async def slash_balance(interaction: discord.Interaction):
    user = str(interaction.user.id)
    if user not in players:
        players[user] = {"money":1000, "level":1}
        save_players()
    await interaction.response.send_message(
        f"{interaction.user.mention}, bạn có {players[user]['money']} 💶, level {players[user]['level']}"
    )

@bot.tree.command(name="shop", description="Xem shop cần 🎣 / mồi 🪱")
async def slash_shop(interaction: discord.Interaction):
    embed = discord.Embed(title="Shop Cần 🎣 & Mồi 🪱", color=discord.Color.purple())
    rods = "\n".join([f"{name}: {price} 💶" for name, price in rod_data.items()])
    baits = "\n".join([f"{name}: {price} 💶" for name, price in bait_data.items()])
    embed.add_field(name="Cần 🎣", value=rods, inline=True)
    embed.add_field(name="Mồi 🪱", value=baits, inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="buy", description="Mua cần/mồi")
@app_commands.describe(item="Tên cần hoặc mồi muốn mua")
async def slash_buy(interaction: discord.Interaction, item: str):
    ctx = await bot.get_context(interaction.message)
    await buy(ctx, item)

@bot.tree.command(name="transfer", description="Chuyển tiền 💶")
@app_commands.describe(member="Người nhận", amount="Số tiền")
async def slash_transfer(interaction: discord.Interaction, member: discord.Member, amount: int):
    ctx = await bot.get_context(interaction.message)
    await transfer(ctx, member, amount)

# ========================= FLASK WEB SERVICE =========================
app = Flask("")

@app.route("/")
def home():
    return "Fishing Bot is online!"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

def keep_alive_flask():
    t = Thread(target=run)
    t.start()

# ========================= RUN BOT =========================
if __name__ == "__main__":
    keep_alive_flask()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Lỗi: Chưa có token Discord trong biến môi trường DISCORD_TOKEN")
    else:
        bot.run(token)
                  
