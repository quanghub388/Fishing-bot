import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import random
from flask import Flask

# --- Web service để bot luôn online trên Render ---
app = Flask(__name__)

@app.route("/")
def home():
    return "Fishing Bot is running!"

def run_flask():
    from threading import Thread
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))).start()

# --- Bot setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=":", intents=intents)
tree = bot.tree  # slash commands

run_flask()

# --- Data ---
fishes = {
    "Common": {
        "🐟 Cá Trích": 50,
        "🐠 Cá Hồi": 70,
        "🐡 Cá Vàng": 100,
    },
    "Uncommon": {
        "🦈 Cá Mập Nhỏ": 500,
        "🐋 Cá Voi Nhỏ": 700,
    },
    "Epic": {
        "🐠 Cá Ngũ Sắc": 2000,
        "🐟 Cá Hồng": 1500,
    },
    "Legendary": {
        "🐉 Cá Rồng": 5000,
        "🦑 Mực Khổng Lồ": 5500,
    },
    "Mythic": {
        "🦈 Cá Megalodon": 100000,
    },
    "Exotic": {
        "🦑 CatFish": 350000,
        "🦈 Megalodon": 500000,
    }
}

rods = {
    "Cần tre": {"price": 100, "durability": 50, "luck": 1},
    "Cần sắt": {"price": 500, "durability": 100, "luck": 3},
    "Cần vàng": {"price": 5000, "durability": 200, "luck": 5},
    "Cần titan": {"price": 20000, "durability": 500, "luck": 8},
    "Cần newbie": {"price": 10, "durability": 20, "luck": 0.5}
}

baits = {
    "🪱 Giun đất": {"price": 50, "luck": 2},
    "🦐 Tôm nhỏ": {"price": 100, "luck": 3},
    "🐛 Sâu vàng": {"price": 200, "luck": 5},
    "🦑 Mực con": {"price": 500, "luck": 7},
    "🦐 Tôm hùm": {"price": 1000, "luck": 10}
}

users = {}  # user_id: {"money": int, "rod": str, "bait": str, "inventory": {}, "level": int, "exp": int}

# --- Helper ---
def get_user(uid):
    if uid not in users:
        users[uid] = {"money": 1000, "rod": "Cần tre", "bait": "🪱 Giun đất", "inventory": {}, "level": 1, "exp": 0}
    return users[uid]

def gain_exp(user, amount):
    user["exp"] += amount
    if user["exp"] >= user["level"] * 100:
        user["exp"] -= user["level"] * 100
        user["level"] += 1
        return True
    return False

def catch_fish(user):
    rod_luck = rods[user["rod"]]["luck"]
    bait_luck = baits[user["bait"]]["luck"]
    luck = rod_luck + bait_luck
    # Exotic chance 0.1%
    if random.random() < 0.001:
        fish = random.choice(list(fishes["Exotic"].keys()))
    else:
        pool = []
        for tier in ["Common","Uncommon","Epic","Legendary","Mythic"]:
            for f in fishes[tier]:
                pool.extend([f]*1)  # weight can be tuned
        fish = random.choice(pool)
    price = None
    for tier in fishes:
        if fish in fishes[tier]:
            price = fishes[tier][fish]
            break
    user["inventory"][fish] = user["inventory"].get(fish,0) + 1
    leveled_up = gain_exp(user, price//10)
    return fish, price, leveled_up

# --- Commands ---
@bot.command()
async def cauca(ctx):
    user = get_user(ctx.author.id)
    fish, price, leveled_up = catch_fish(user)
    embed = discord.Embed(title=f"{ctx.author.name} đã câu được!", color=0x00ff00)
    embed.add_field(name="Cá", value=fish)
    embed.add_field(name="Giá", value=f"{price}$")
    embed.add_field(name="Level", value=user["level"])
    if leveled_up:
        embed.set_footer(text="🎉 Level Up!")
    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Fishing Bot Commands", color=0x00ffff)
    embed.add_field(name=":cauca", value="Câu cá", inline=False)
    embed.add_field(name=":shop", value="Xem cửa hàng", inline=False)
    embed.add_field(name=":buy <item>", value="Mua cần/mồi", inline=False)
    embed.add_field(name=":inventory", value="Xem kho đồ", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def inventory(ctx):
    user = get_user(ctx.author.id)
    embed = discord.Embed(title=f"{ctx.author.name}'s Inventory", color=0xffcc00)
    for fish, qty in user["inventory"].items():
        embed.add_field(name=fish, value=qty, inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def shop(ctx):
    embed = discord.Embed(title="Cửa hàng", color=0xff9900)
    rods_text = "\n".join([f"{r} - {rods[r]['price']}$" for r in rods])
    bait_text = "\n".join([f"{b} - {baits[b]['price']}$" for b in baits])
    embed.add_field(name="Cần", value=rods_text, inline=False)
    embed.add_field(name="Mồi", value=bait_text, inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def buy(ctx, *, item):
    user = get_user(ctx.author.id)
    if item in rods:
        if user["money"] >= rods[item]["price"]:
            user["money"] -= rods[item]["price"]
            user["rod"] = item
            await ctx.send(f"Bạn đã mua cần {item}")
        else:
            await ctx.send("Không đủ tiền")
    elif item in baits:
        if user["money"] >= baits[item]["price"]:
            user["money"] -= baits[item]["price"]
            user["bait"] = item
            await ctx.send(f"Bạn đã mua mồi {item}")
        else:
            await ctx.send("Không đủ tiền")
    else:
        await ctx.send("Món không tồn tại")

# --- Slash commands ---
@tree.command(name="cauca", description="Câu cá")
async def slash_cauca(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    fish, price, leveled_up = catch_fish(user)
    embed = discord.Embed(title=f"{interaction.user.name} đã câu được!", color=0x00ff00)
    embed.add_field(name="Cá", value=fish)
    embed.add_field(name="Giá", value=f"{price}$")
    embed.add_field(name="Level", value=user["level"])
    if leveled_up:
        embed.set_footer(text="🎉 Level Up!")
    await interaction.response.send_message(embed=embed)

# --- Run bot ---
bot.run(os.getenv("DISCORD_TOKEN"))
    
