import discord
from discord.ext import commands
import random
import asyncio
import os
from flask import Flask
import threading

# -----------------------------
# Intents & Bot
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=("/", ":"), intents=intents)

# -----------------------------
# Cá theo độ hiếm
# -----------------------------
fish_data = {
    "Common": {
        "🐟 Cá chép": 6000,
        "🐠 Cá rô phi": 4000,
        "🐡 Cá trê": 5000,
        "🐠 Cá basa": 5500,
    },
    "Uncommon": {
        "🐟 Cá lóc": 7000,
        "🐠 Cá chim trắng": 8000,
        "🐟 Cá mè": 6000,
        "🦐 Tôm": 25000,
    },
    "Rare": {
        "🐟 Cá hồi": 35000,
        "🦑 Mực": 20000,
        "🐟 Cá bống tượng": 18000,
    },
    "Epic": {
        "🐟 Cá tra dầu": 40000,
        "🐍 Cá chình": 50000,
        "🐠 Cá dìa": 22000,
        "🦪 Bào ngư": 60000,
    },
    "Legendary": {
        "🐟 Cá ngừ đại dương": 70000,
        "🐋 Cá nhám voi": 100000,
        "🐟 Cá nhụ": 45000,
        "🦪 Sò điệp lớn": 55000,
    },
    "Mythic": {
        "🦈 Cá mập": 150000,
        "🐢 Rùa Hoàn Kiếm": 500000,
        "💎 Ngọc trai quý": 300000,
    },
    "Exotic": {
        "🐟 CatFish": 350000,
        "🦈 Megalodon": 500000,
    }
}

rarity_base_rates = {
    "Common": 60,
    "Uncommon": 20,
    "Rare": 10,
    "Epic": 5,
    "Legendary": 3,
    "Mythic": 1.9,
    "Exotic": 0.1
}

# -----------------------------
# Shop items
# -----------------------------
shop_items = {
    # Rods
    "🎣 Cần tre": {"price": 0, "luck": 0, "durability": 50},
    "🎣 Cần sắt": {"price": 10000, "luck": 5, "durability": 100},
    "🎣 Cần vàng": {"price": 50000, "luck": 15, "durability": 200},
    "🎣 Cần kim cương": {"price": 200000, "luck": 30, "durability": 500},
    # Baits
    "🪱 Mồi thường": {"price": 100, "luck": 2, "durability": 20},
    "🪱 Mồi đặc biệt": {"price": 1000, "luck": 10, "durability": 50},
    "🪱 Giun đất": {"price": 500, "luck": 3, "durability": 35},
}

# -----------------------------
# Dữ liệu người chơi
# -----------------------------
inventories = {}   # {user_id: [(fish, weight, rarity), ...]}
balances = {}      # {user_id: money}
gears = {}         # {user_id: {"rod": {...}, "bait": {...}, "rod_dur": x, "bait_dur": y}}
fish_log = {}      # {user_id: {fish_name: {"rarity": str, "max_weight": float}}}
levels = {}        # {user_id: level}

# -----------------------------
# Random trọng lượng
# -----------------------------
def random_weight(rarity):
    if rarity == "Common":
        return round(random.uniform(0.2, 3), 2)
    elif rarity == "Uncommon":
        return round(random.uniform(0.5, 4), 2)
    elif rarity == "Rare":
        return round(random.uniform(1, 6), 2)
    elif rarity == "Epic":
        return round(random.uniform(2, 10), 2)
    elif rarity == "Legendary":
        return round(random.uniform(5, 50), 2)
    elif rarity == "Mythic":
        return round(random.uniform(10, 200), 2)
    elif rarity == "Exotic":
        return round(random.uniform(50, 500), 2)
    return 1.0

# -----------------------------
# Chọn cá theo rarity
# -----------------------------
def get_random_fish(user):
    rates = rarity_base_rates.copy()
    luck_bonus = 0
    if user in gears:
        rod = gears[user].get("rod")
        bait = gears[user].get("bait")
        if rod: luck_bonus += rod["luck"]
        if bait: luck_bonus += bait["luck"]

    # Phân bổ luck
    rates["Rare"] += luck_bonus
    rates["Epic"] += luck_bonus // 2
    rates["Legendary"] += luck_bonus // 3
    rates["Mythic"] += luck_bonus // 5
    rates["Common"] = max(5, rates["Common"] - luck_bonus)

    rarities, probs = zip(*rates.items())
    rarity = random.choices(rarities, weights=probs, k=1)[0]
    fish = random.choice(list(fish_data[rarity].keys()))
    price = fish_data[rarity][fish]
    weight = random_weight(rarity)
    return fish, weight, rarity, price

# -----------------------------
# Slash & : commands
# -----------------------------
@bot.command()
async def cauca(ctx):
    user = ctx.author.id

    if user not in gears:
        gears[user] = {
            "rod": shop_items["🎣 Cần tre"].copy(),
            "bait": shop_items["🪱 Mồi thường"].copy(),
            "rod_dur": shop_items["🎣 Cần tre"]["durability"],
            "bait_dur": shop_items["🪱 Mồi thường"]["durability"]
        }

    if gears[user]["rod_dur"] <= 0:
        await ctx.send("❌ Cần câu hỏng, mua mới trong :shop")
        return
    if gears[user]["bait_dur"] <= 0:
        await ctx.send("❌ Hết mồi, mua mới trong :shop")
        return

    gears[user]["rod_dur"] -= 1
    gears[user]["bait_dur"] -= 1

    caught = []
    for _ in range(random.randint(1, 3)):
        fish, weight, rarity, price = get_random_fish(user)
        inventories.setdefault(user, []).append((fish, weight, rarity))

        fish_log.setdefault(user, {})
        if fish not in fish_log[user]:
            fish_log[user][fish] = {"rarity": rarity, "max_weight": weight}
        else:
            if weight > fish_log[user][fish]["max_weight"]:
                fish_log[user][fish]["max_weight"] = weight

        caught.append(f"{fish} — {rarity} — {weight}kg")

    # Update level
    levels[user] = levels.get(user, 1) + len(caught)

    embed = discord.Embed(title=f"{ctx.author.name} câu cá 🎣", color=discord.Color.blue())
    embed.add_field(name="Cá câu được", value="\n".join(caught), inline=False)
    embed.set_footer(text=f"Rod {gears[user]['rod_dur']} | Bait {gears[user]['bait_dur']} | Level {levels[user]}")
    await ctx.send(embed=embed)

@bot.command()
async def inventory(ctx):
    user = ctx.author.id
    if user not in inventories or not inventories[user]:
        await ctx.send("🎒 Túi trống!")
        return
    items = "\n".join([f"{fish} ({w}kg, {r})" for fish, w, r in inventories[user]])
    bal = balances.get(user, 0)
    await ctx.send(f"🎒 {ctx.author.name}:\n{items}\n💰 {bal:,} VNĐ")

@bot.command()
async def ban(ctx):
    user = ctx.author.id
    if user not in inventories or not inventories[user]:
        await ctx.send("👜 Túi trống!")
        return
    total = 0
    details = []
    for fish, weight, rarity in inventories[user]:
        price = fish_data[rarity][fish] * weight
        total += price
        details.append(f"{fish} ({weight}kg, {rarity}) = {round(price):,}")
    inventories[user] = []
    balances[user] = balances.get(user, 0) + total

    embed = discord.Embed(title=f"{ctx.author.name} bán cá 🐟", color=discord.Color.green())
    embed.add_field(name="Chi tiết bán", value="\n".join(details), inline=False)
    embed.add_field(name="Tổng", value=f"{round(total):,} VNĐ", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def shop(ctx):
    embed = discord.Embed(title="🛒 Shop", color=discord.Color.orange())
    for item, info in shop_items.items():
        embed.add_field(name=item, value=f"Giá: {info['price']:,} VNĐ | Luck: {info['luck']} | Durability: {info['durability']}", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def buy(ctx, *, item_name):
    user = ctx.author.id
    if item_name not in shop_items:
        await ctx.send("❌ Không tìm thấy item!")
        return
    price = shop_items[item_name]["price"]
    bal = balances.get(user, 0)
    if bal < price:
        await ctx.send("❌ Không đủ tiền!")
        return

    balances[user] = bal - price
    if "Cần" in item_name:
        gears.setdefault(user, {})["rod"] = shop_items[item_name].copy()
        gears[user]["rod_dur"] = shop_items[item_name]["durability"]
    else:
        gears.setdefault(user, {})["bait"] = shop_items[item_name].copy()
        gears[user]["bait_dur"] = shop_items[item_name]["durability"]

    await ctx.send(f"✅ {ctx.author.name} đã mua {item_name}!")

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📜 Lệnh Fishing Bot", color=discord.Color.purple())
    embed.add_field(name=":cauca hoặc /cauca", value="Câu cá", inline=False)
    embed.add_field(name=":inventory hoặc /inventory", value="Xem túi cá và tiền", inline=False)
    embed.add_field(name=":ban hoặc /ban", value="Bán toàn bộ cá trong túi", inline=False)
    embed.add_field(name=":shop hoặc /shop", value="Xem shop cần/mồi", inline=False)
    embed.add_field(name=":buy hoặc /buy <item>", value="Mua cần hoặc mồi", inline=False)
    await ctx.send(embed=embed)

# -----------------------------
# Flask server để Render free
# -----------------------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run).start()

# -----------------------------
# Run Bot
# -----------------------------
bot.run(os.getenv("DISCORD_TOKEN"))
                     
