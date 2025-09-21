import discord
from discord.ext import commands
import random
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=[":", "/"], intents=intents)

# -----------------------------
# Cá theo độ hiếm
# -----------------------------
# Giá đã giảm 100 lần trừ Exotic
fish_data = {
    "Common": {
        "🐟 Cá chép": 60,
        "🐠 Cá rô phi": 40,
        "🐡 Cá trê": 50,
        "🐠 Cá basa": 55,
    },
    "Uncommon": {
        "🐟 Cá lóc": 70,
        "🐠 Cá chim trắng": 80,
        "🐟 Cá mè": 60,
        "🦐 Tôm": 250,
    },
    "Rare": {
        "🐟 Cá hồi": 350,
        "🦑 Mực": 200,
        "🐟 Cá bống tượng": 180,
    },
    "Epic": {
        "🐟 Cá tra dầu": 400,
        "🐍 Cá chình": 500,
        "🐠 Cá dìa": 220,
        "🦪 Bào ngư": 600,
    },
    "Legendary": {
        "🐟 Cá ngừ đại dương": 700,
        "🐋 Cá nhám voi": 1000,
        "🐟 Cá nhụ": 450,
        "🦪 Sò điệp lớn": 550,
    },
    "Exotic": {  # không giảm
        "🐟 CatFish": 350000,
        "🦈 Megalodon": 500000,
    },
    "Mythic": {
        "🦈 Cá mập": 15000,
        "🐢 Rùa Hoàn Kiếm": 50000,
        "💎 Ngọc trai quý": 30000,
    }
}

rarity_base_rates = {
    "Common": 60,
    "Uncommon": 20,
    "Rare": 10,
    "Epic": 5,
    "Legendary": 3,
    "Exotic": 0.1,
    "Mythic": 2
}

# -----------------------------
# Shop items
# -----------------------------
shop_items = {
    "🎣 Cần tre": {"price": 0, "luck": 0, "durability": 50},
    "🎣 Cần newbie": {"price": 2000, "luck": 2, "durability": 60},
    "🎣 Cần sắt": {"price": 100000, "luck": 5, "durability": 100},
    "🎣 Cần vàng": {"price": 500000, "luck": 15, "durability": 200},
    "🎣 Cần kim cương": {"price": 2000000, "luck": 30, "durability": 500},
    "🪱 Mồi thường": {"price": 1000, "luck": 2, "durability": 20},
    "🪱 Mồi rẻ": {"price": 500, "luck": 1, "durability": 15},
    "🪱 Mồi đặc biệt": {"price": 10000, "luck": 10, "durability": 50},
    "🪱 Giun đất": {"price": 500, "luck": 3, "durability": 35},
}

# -----------------------------
# Dữ liệu người chơi
# -----------------------------
inventories = {}
balances = {}
gears = {}
fish_log = {}
levels = {}

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
    elif rarity == "Exotic":
        return round(random.uniform(50, 150), 2)
    elif rarity == "Mythic":
        return round(random.uniform(10, 200), 2)
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
# Slash / Prefix commands
# -----------------------------
@bot.command(name="cauca")
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
        await ctx.send("❌ Cần câu của bạn đã hỏng, hãy mua cái mới trong :shop!")
        return
    if gears[user]["bait_dur"] <= 0:
        await ctx.send("❌ Hết mồi, hãy mua thêm trong :shop!")
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

    levels[user] = levels.get(user, 0) + len(caught)

    result = "\n".join(caught)
    await ctx.send(
        f"{ctx.author.mention} 🎣 câu được:\n{result}\n"
        f"⚙️ Durability còn lại: Rod {gears[user]['rod_dur']} | Bait {gears[user]['bait_dur']}\n"
        f"🏆 Level: {levels[user]}"
    )

# -----------------------------
# Bot chạy
# -----------------------------
bot.run(os.getenv("DISCORD_TOKEN"))
