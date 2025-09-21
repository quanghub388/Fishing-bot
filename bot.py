import discord
from discord.ext import commands, tasks
import random
import os

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=":", intents=intents)

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
    }
}

rarity_base_rates = {
    "Common": 60,
    "Uncommon": 20,
    "Rare": 10,
    "Epic": 5,
    "Legendary": 3,
    "Mythic": 2
}

# -----------------------------
# Shop items
# -----------------------------
shop_items = {
    "🎣 Cần tre": {"price": 0, "luck": 0, "durability": 50},
    "🎣 Cần sắt": {"price": 1000, "luck": 5, "durability": 100},
    "🎣 Cần vàng": {"price": 5000, "luck": 15, "durability": 200},
    "🎣 Cần kim cương": {"price": 20000, "luck": 30, "durability": 500},
    "🪱 Mồi thường": {"price": 100, "luck": 2, "durability": 20},
    "🪱 Mồi đặc biệt": {"price": 1000, "luck": 10, "durability": 50},
}

# -----------------------------
# Dữ liệu người chơi
# -----------------------------
inventories = {}   # {user_id: [(fish, weight, rarity), ...]}
balances = {}      # {user_id: money}
gears = {}         # {user_id: {"rod": {...}, "bait": {...}, "rod_dur": x, "bait_dur": y}}
fish_log = {}      # {user_id: {fish_name: {"rarity": str, "max_weight": float}}}

# -----------------------------
# Random trọng lượng
# -----------------------------
def random_weight(rarity):
    if rarity == "Common": return round(random.uniform(0.2, 3), 2)
    if rarity == "Uncommon": return round(random.uniform(0.5, 4), 2)
    if rarity == "Rare": return round(random.uniform(1, 6), 2)
    if rarity == "Epic": return round(random.uniform(2, 10), 2)
    if rarity == "Legendary": return round(random.uniform(5, 50), 2)
    if rarity == "Mythic": return round(random.uniform(10, 200), 2)
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
    rates["Epic"] += luck_bonus//2
    rates["Legendary"] += luck_bonus//3
    rates["Mythic"] += luck_bonus//5
    rates["Common"] = max(5, rates["Common"] - luck_bonus)
    rarities, probs = zip(*rates.items())
    rarity = random.choices(rarities, weights=probs, k=1)[0]
    fish = random.choice(list(fish_data[rarity].keys()))
    price = fish_data[rarity][fish]
    weight = random_weight(rarity)
    return fish, weight, rarity, price

# -----------------------------
# Lệnh :cauca
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
    if gears[user]["rod_dur"] <=0:
        await ctx.send("❌ Cần câu đã hỏng, mua mới trong :shop!")
        return
    if gears[user]["bait_dur"] <=0:
        await ctx.send("❌ Hết mồi, mua thêm trong :shop!")
        return
    gears[user]["rod_dur"] -=1
    gears[user]["bait_dur"] -=1
    caught=[]
    for _ in range(random.randint(1,3)):
        fish, weight, rarity, price = get_random_fish(user)
        inventories.setdefault(user, []).append((fish, weight, rarity))
        fish_log.setdefault(user, {})
        if fish not in fish_log[user]:
            fish_log[user][fish] = {"rarity": rarity, "max_weight": weight}
        else:
            if weight > fish_log[user][fish]["max_weight"]:
                fish_log[user][fish]["max_weight"]=weight
        caught.append(f"{fish} — {rarity} — {weight}kg")
    await ctx.send(f"{ctx.author.mention} 🎣 câu được:\n" + "\n".join(caught) + 
                   f"\n⚙️ Durability: Rod {gears[user]['rod_dur']} | Bait {gears[user]['bait_dur']}")

# -----------------------------
# Lệnh :inventory
# -----------------------------
@bot.command()
async def inventory(ctx):
    user=ctx.author.id
    if user not in inventories or not inventories[user]:
        await ctx.send("🎒 Túi của bạn đang rỗng!")
        return
    items="\n".join([f"{fish} ({w}kg, {r})" for fish,w,r in inventories[user]])
    bal = balances.get(user,0)
    await ctx.send(f"🎒 Túi đồ {ctx.author.mention}:\n{items}\n\n💰 Số dư: {bal:,} VNĐ")

# -----------------------------
# Lệnh :ban
# -----------------------------
@bot.command()
async def ban(ctx):
    user=ctx.author.id
    if user not in inventories or not inventories[user]:
        await ctx.send("👜 Túi trống!")
        return
    total=0
    details=[]
    for fish,weight,rarity in inventories[user]:
        price = fish_data[rarity][fish]*weight
        total+=price
        details.append(f"{fish} ({weight}kg, {rarity}) = {round(price):,} VNĐ")
    inventories[user].clear()
    balances[user]=balances.get(user,0)+total
    await ctx.send(f"💸 {ctx.author.mention} bán cá!\n" + "\n".join(details) + f"\n**Tổng: {round(total):,} VNĐ**")

# -----------------------------
# Lệnh :shop
# -----------------------------
@bot.command()
async def shop(ctx):
    items="\n".join([f"{item} — {info['price']:,} VNĐ (Luck {info['luck']} | Durability {info['durability']})"
                     for item,info in shop_items.items()])
    await ctx.send(f"🛒 **Shop**:\n{items}\n\nDùng :mua <tên> để mua")

# -----------------------------
# Lệnh :mua
# -----------------------------
@bot.command()
async def mua(ctx, *, item):
    user=ctx.author.id
    if item not in shop_items:
        await ctx.send("❌ Item không tồn tại!")
        return
    price = shop_items[item]["price"]
    if balances.get(user,0)<price:
        await ctx.send("❌ Không đủ tiền!")
        return
    balances[user]-=price
    if "Cần" in item:
        gears.setdefault(user,{})["rod"]=shop_items[item].copy()
        gears[user]["rod_dur"]=shop_items[item]["durability"]
    elif "Mồi" in item:
        gears.setdefault(user,{})["bait"]=shop_items[item].copy()
        gears[user]["bait_dur"]=shop_items[item]["durability"]
    await ctx.send(f"✅ {ctx.author.mention} đã mua {item} thành công!")

# -----------------------------
# Lệnh :leaderboard
# -----------------------------
@bot.command()
async def leaderboard(ctx):
    if not balances:
        await ctx.send("📉 Chưa có ai bán cá!")
        return
    ranking = sorted(balances.items(), key=lambda x:x[1], reverse=True)[:10]
    msg=[]
    for i,(user_id,money) in enumerate(ranking,start=1):
        user=await bot.fetch_user(user_id)
        msg.append(f"**{i}.** {user.name} — {money:,} VNĐ")
    await ctx.send("🏆 **Top 10 ngư ông giàu nhất** 🏆\n\n"+"\n".join(msg))

# -----------------------------
# Lệnh :fishdex
# -----------------------------
@bot.command()
async def fishdex(ctx):
    user=ctx.author.id
    if user not in fish_log or not fish_log[user]:
        await ctx.send("📖 Bạn chưa câu được con cá nào!")
        return
    records=[f"{fish} — {data['rarity']} — Max: {data['max_weight']}kg" for fish,data in fish_log[user].items()]
    await ctx.send(f"📖 Hồ sơ câu cá {ctx.author.mention}:\n"+"\n".join(records))

# -----------------------------
# Lệnh :help
# -----------------------------
@bot.command()
async def help(ctx):
    commands_list=[
        ":cauca — Câu cá 🎣",
        ":inventory — Xem túi đồ 🎒",
        ":ban — Bán cá 💸",
        ":shop — Xem shop 🛒",
        ":mua — Mua item",
        ":leaderboard — BXH ngư ông 💰",
        ":fishdex — Hồ sơ cá 📖",
        ":help — Hướng dẫn lệnh"
    ]
    await ctx.send("📜 **Danh sách lệnh** 📜\n"+"".join(commands_list))

# -----------------------------
# Giữ bot luôn online
# -----------------------------
@tasks.loop(minutes=5)
async def keep_alive():
    pass
keep_alive.start()

# -----------------------------
# Chạy bot
# -----------------------------
bot.run(os.getenv("DISCORD_TOKEN"))
