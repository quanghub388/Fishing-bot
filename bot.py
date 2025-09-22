import discord
from discord.ext import commands
import random
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=("/", ":"), intents=intents, help_command=None)

# === DATA ===
# Các loại cá
fishes = {
    # Common (giảm giá 10 lần)
    "Cá nhỏ": {"price": 5, "luck": 50},
    "Cá trích": {"price": 8, "luck": 45},
    "Cá chép": {"price": 12, "luck": 40},
    "Cá rô": {"price": 15, "luck": 35},
    # Rare (giảm giá 10 lần)
    "Cá hồi": {"price": 50, "luck": 20},
    "Cá ngừ": {"price": 80, "luck": 15},
    "Cá thu": {"price": 100, "luck": 12},
    # Epic (giảm giá 10 lần)
    "Cá kiếm": {"price": 200, "luck": 8},
    "Cá heo": {"price": 300, "luck": 5},
    # Exotic (giữ nguyên giá)
    "CatFish": {"price": 350000, "luck": 1},
    "Megalodon": {"price": 500000, "luck": 1},
}

# Giảm giá 10 lần trừ Exotic
for name, data in fishes.items():
    if name not in ["CatFish", "Megalodon"]:
        data["price"] = data["price"] // 10

# Cần câu
rods = {
    "Cần tre": {"price": 50, "durability": 50},
    "Cần sắt": {"price": 100, "durability": 100},
    "Cần vàng": {"price": 500, "durability": 200},
    "Cần bạc": {"price": 150, "durability": 120},
    "Cần kim cương": {"price": 1000, "durability": 500},
    "Cần newbie": {"price": 10, "durability": 30},
    "Cần rẻ 1": {"price": 20, "durability": 40},
    "Cần rẻ 2": {"price": 25, "durability": 35},
}

# Mồi câu
baits = {
    "Giun đất": {"price": 5, "luck": 3, "durability": 35},
    "Mồi cá nhỏ": {"price": 10, "luck": 5, "durability": 50},
    "Mồi tôm": {"price": 20, "luck": 10, "durability": 70},
    "Mồi đặc biệt": {"price": 100, "luck": 30, "durability": 100},
    "Mồi newbie": {"price": 1, "luck": 1, "durability": 15},
    "Mồi rẻ 1": {"price": 2, "luck": 2, "durability": 20},
    "Mồi rẻ 2": {"price": 3, "luck": 3, "durability": 25},
    "Mồi rẻ 3": {"price": 4, "luck": 4, "durability": 30},
}

# === PLAYER DATA ===
players = {}  # {user_id: {"level": int, "exp": int, "rod": str, "bait": str, "coins": int}}

# === HELPER FUNCTIONS ===
def add_exp(user_id, amount):
    if user_id not in players:
        players[user_id] = {"level": 1, "exp": 0, "rod": None, "bait": None, "coins": 0}
    players[user_id]["exp"] += amount
    level = players[user_id]["level"]
    if players[user_id]["exp"] >= level * 100:
        players[user_id]["exp"] -= level * 100
        players[user_id]["level"] += 1
        return True
    return False

def get_fish():
    # tỉ lệ cá exotic 0.1%
    if random.random() <= 0.001:
        return random.choice(["CatFish", "Megalodon"])
    # Random các loại còn lại
    normal_fishes = [f for f in fishes if f not in ["CatFish", "Megalodon"]]
    return random.choice(normal_fishes)

# === COMMANDS ===
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="🎣 Lệnh Bot Câu Cá", color=0x00ff00)
    embed.add_field(name=":cauca hoặc /cauca", value="Đi câu cá", inline=False)
    embed.add_field(name=":shop hoặc /shop", value="Xem shop cần/mồi", inline=False)
    embed.add_field(name=":inventory hoặc /inventory", value="Xem đồ của bạn", inline=False)
    embed.add_field(name=":level hoặc /level", value="Xem level và kinh nghiệm", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def cauca(ctx):
    user_id = ctx.author.id
    fish = get_fish()
    price = fishes[fish]["price"]
    leveled_up = add_exp(user_id, price)
    if user_id not in players:
        players[user_id] = {"level": 1, "exp": 0, "rod": None, "bait": None, "coins": 0}
    players[user_id]["coins"] += price
    msg = f"Bạn đã câu được **{fish}**! Giá: {price} coins."
    if leveled_up:
        msg += f" 🎉 Chúc mừng! Bạn đã lên level {players[user_id]['level']}!"
    await ctx.send(msg)

@bot.command()
async def shop(ctx):
    embed = discord.Embed(title="🏪 Shop Cần & Mồi", color=0x00ff00)
    rods_list = "\n".join([f"{name}: {data['price']} coins" for name, data in rods.items()])
    baits_list = "\n".join([f"{name}: {data['price']} coins" for name, data in baits.items()])
    embed.add_field(name="Cần câu", value=rods_list, inline=False)
    embed.add_field(name="Mồi câu", value=baits_list, inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def inventory(ctx):
    user_id = ctx.author.id
    if user_id not in players:
        await ctx.send("Bạn chưa có gì trong kho. Đi câu cá đi!")
        return
    p = players[user_id]
    embed = discord.Embed(title=f"Kho của {ctx.author.name}", color=0x00ff00)
    embed.add_field(name="Level", value=p["level"])
    embed.add_field(name="Exp", value=p["exp"])
    embed.add_field(name="Cần câu", value=p["rod"] or "Chưa có")
    embed.add_field(name="Mồi câu", value=p["bait"] or "Chưa có")
    embed.add_field(name="Coins", value=p["coins"])
    await ctx.send(embed=embed)

@bot.command()
async def level(ctx):
    user_id = ctx.author.id
    if user_id not in players:
        await ctx.send("Bạn chưa có level nào.")
        return
    p = players[user_id]
    await ctx.send(f"{ctx.author.name}, bạn đang level {p['level']} với {p['exp']} exp.")

# === RUN BOT ===
bot.run(os.getenv("DISCORD_TOKEN"))
        
