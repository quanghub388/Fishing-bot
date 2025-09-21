import discord
from discord.ext import commands, tasks
import random
import os

# -----------------------------
# Bot setup
# -----------------------------
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=":", intents=intents)  # Prefix ':'
bot.remove_command("help")  # Dùng custom help

# -----------------------------
# Fish data
# -----------------------------
fish_data = {
    "Common": {"🐟 Cá chép": 6000, "🐠 Cá rô phi": 4000, "🐡 Cá trê": 5000, "🐠 Cá basa": 5500},
    "Uncommon": {"🐟 Cá lóc": 7000, "🐠 Cá chim trắng": 8000, "🐟 Cá mè": 6000, "🦐 Tôm": 25000},
    "Rare": {"🐟 Cá hồi": 35000, "🦑 Mực": 20000, "🐟 Cá bống tượng": 18000},
    "Epic": {"🐟 Cá tra dầu": 40000, "🐍 Cá chình": 50000, "🐠 Cá dìa": 22000, "🦪 Bào ngư": 60000},
    "Legendary": {"🐟 Cá ngừ đại dương": 70000, "🐋 Cá nhám voi": 100000, "🐟 Cá nhụ": 45000, "🦪 Sò điệp lớn": 55000},
    "Mythic": {"🦈 Cá mập": 150000, "🐢 Rùa Hoàn Kiếm": 500000, "💎 Ngọc trai quý": 300000},
    "Exotic": {"🐱 CatFish": 350000, "🦈 Megalodon": 500000}  # 0.1% chance
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
# Shop
# -----------------------------
shop_items = {
    "🎣 Cần tre": {"price": 0, "luck": 0, "durability": 50},
    "🎣 Cần sắt": {"price": 10000, "luck": 5, "durability": 100},
    "🎣 Cần vàng": {"price": 50000, "luck": 15, "durability": 200},
    "🎣 Cần kim cương": {"price": 200000, "luck": 30, "durability": 500},
    "🪱 Mồi thường": {"price": 1000, "luck": 2, "durability": 20},
    "🪱 Mồi đặc biệt": {"price": 10000, "luck": 10, "durability": 50},
    "🪱 Mồi siêu cấp": {"price": 50000, "luck": 25, "durability": 100},
}

# -----------------------------
# Player data
# -----------------------------
inventories = {}   # user_id -> [(fish, weight, rarity)]
balances = {}      # user_id -> money
gears = {}         # user_id -> {"rod":..., "bait":..., "rod_dur":..., "bait_dur":...}
fish_log = {}      # user_id -> {fish_name: {"rarity": str, "max_weight": float}}
player_levels = {} # user_id -> {"level":1, "exp":0, "next_level_exp":1000}

# -----------------------------
# Utils
# -----------------------------
def random_weight(rarity):
    ranges = {
        "Common": (0.2,3), "Uncommon": (0.5,4), "Rare": (1,6),
        "Epic": (2,10), "Legendary": (5,50), "Mythic": (10,200),
        "Exotic": (50,500)
    }
    low, high = ranges.get(rarity,(1,1))
    return round(random.uniform(low, high),2)

def get_random_fish(user):
    rates = rarity_base_rates.copy()
    luck_bonus = 0
    if user in gears:
        rod = gears[user].get("rod")
        bait = gears[user].get("bait")
        if rod: luck_bonus += rod["luck"]
        if bait: luck_bonus += bait["luck"]

    # apply bonus
    for r in ["Rare","Epic","Legendary","Mythic"]:
        rates[r] += luck_bonus / 2
    rates["Common"] = max(5, rates["Common"] - luck_bonus)
    
    rarities, probs = zip(*rates.items())
    rarity = random.choices(rarities, weights=probs, k=1)[0]
    fish = random.choice(list(fish_data[rarity].keys()))
    price = fish_data[rarity][fish]
    weight = random_weight(rarity)
    return fish, weight, rarity, price

def gain_exp(user, amount):
    if user not in player_levels:
        player_levels[user] = {"level":1,"exp":0,"next_level_exp":1000}
    player_levels[user]["exp"] += amount
    while player_levels[user]["exp"] >= player_levels[user]["next_level_exp"]:
        player_levels[user]["level"] += 1
        player_levels[user]["exp"] -= player_levels[user]["next_level_exp"]
        player_levels[user]["next_level_exp"] = int(player_levels[user]["next_level_exp"] * 1.5)

# -----------------------------
# Commands
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
        await ctx.send("❌ Cần hỏng rồi!")
        return
    if gears[user]["bait_dur"] <= 0:
        await ctx.send("❌ Hết mồi!")
        return
    gears[user]["rod_dur"] -= 1
    gears[user]["bait_dur"] -= 1
    caught = []
    for _ in range(random.randint(1,3)):
        fish, weight, rarity, price = get_random_fish(user)
        inventories.setdefault(user,[]).append((fish,weight,rarity))
        fish_log.setdefault(user,{})
        if fish not in fish_log[user] or weight > fish_log[user][fish]["max_weight"]:
            fish_log[user][fish] = {"rarity":rarity,"max_weight":weight}
        caught.append(f"{fish} — {rarity} — {weight}kg")
    embed = discord.Embed(title=f"{ctx.author.name} 🎣 câu được:", description="\n".join(caught), color=discord.Color.blue())
    embed.set_footer(text=f"Durability: Rod {gears[user]['rod_dur']} | Bait {gears[user]['bait_dur']}")
    await ctx.send(embed=embed)

@bot.command()
async def inventory(ctx):
    user = ctx.author.id
    if user not in inventories or not inventories[user]:
        await ctx.send("🎒 Túi trống!")
        return
    items = "\n".join([f"{f} ({w}kg, {r})" for f,w,r in inventories[user]])
    bal = balances.get(user,0)
    level = player_levels.get(user,{"level":1})["level"]
    await ctx.send(f"🎒 Túi {ctx.author.name}:\n{items}\n💰 Số dư: {bal:,} VNĐ\n🏅 Level: {level}")

@bot.command()
async def ban(ctx):
    user = ctx.author.id
    if user not in inventories or not inventories[user]:
        await ctx.send("👜 Túi trống!")
        return
    total = 0
    details = []
    for fish, weight, rarity in inventories[user]:
        price = fish_data[rarity][fish]*weight
        total += price
        details.append(f"{fish} ({weight}kg, {rarity}) = {round(price):,} VNĐ")
    inventories[user].clear()
    balances[user] = balances.get(user,0)+total
    gain_exp(user, total//1000)
    await ctx.send(f"💸 {ctx.author.name} bán cá:\n"+"\n".join(details)+f"\n**Tổng: {round(total):,} VNĐ**")

@bot.command()
async def shop(ctx):
    lines = [f"{name} — {info['price']:,} VNĐ (Luck {info['luck']} | Durability {info['durability']})" for name,info in shop_items.items()]
    await ctx.send("🛒 **Shop:**\n"+ "\n".join(lines))

@bot.command()
async def mua(ctx,item:str):
    user = ctx.author.id
    if item not in shop_items:
        await ctx.send("❌ Item không tồn tại!")
        return
    price = shop_items[item]["price"]
    if balances.get(user,0) < price:
        await ctx.send("❌ Không đủ tiền!")
        return
    balances[user]-=price
    if "Cần" in item:
        gears.setdefault(user,{})["rod"]=shop_items[item].copy()
        gears[user]["rod_dur"]=shop_items[item]["durability"]
    elif "Mồi" in item:
        gears.setdefault(user,{})["bait"]=shop_items[item].copy()
        gears[user]["bait_dur"]=shop_items[item]["durability"]
    await ctx.send(f"✅ Mua thành công {item}!")

@bot.command()
async def help(ctx):
    cmds = [
        ":cauca — Câu cá",
        ":inventory — Xem túi và level",
        ":ban — Bán cá",
        ":shop — Xem shop",
        ":mua <item> — Mua cần/mồi",
        ":help — Lệnh này"
    ]
    await ctx.send("📜 **Danh sách lệnh:**\n"+"\n".join(cmds))

# -----------------------------
# Run bot
# -----------------------------
bot.run(os.getenv("DISCORD_TOKEN"))
    "🪱 Giun đất":{"price":500,"luck":3,"durability":35},
    "🪱 Mồi đặc biệt":{"price":1000,"luck":7,"durability":50},
    "🪱 Mồi chuyên nghiệp":{"price":10000,"luck":10,"durability":75
}

# -----------------------------
# Player data
# -----------------------------
inventories = {}
balances = {}
gears = {}
fish_log = {}
levels = {}   # user_id: {"xp":x,"level":y}

# -----------------------------
# Helpers
# -----------------------------
def random_weight(rarity):
    ranges = {"Common":(0.2,3),"Uncommon":(0.5,4),"Rare":(1,6),"Epic":(2,10),"Legendary":(5,50),"Mythic":(10,200),"Exotic":(50,1000)}
    return round(random.uniform(*ranges[rarity]),2)

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
    rates["Exotic"] += luck_bonus//10

    rarities, probs = zip(*rates.items())
    rarity = random.choices(rarities, weights=probs, k=1)[0]
    fish = random.choice(list(fish_data[rarity].keys()))
    price = fish_data[rarity][fish]
    weight = random_weight(rarity)
    return fish, weight, rarity, price

def add_xp(user, amount):
    if user not in levels:
        levels[user] = {"xp":0,"level":1}
    levels[user]["xp"] += amount
    # Level up every 100 XP
    while levels[user]["xp"] >= levels[user]["level"]*100:
        levels[user]["xp"] -= levels[user]["level"]*100
        levels[user]["level"] += 1

# -----------------------------
# Commands
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
        await ctx.send("❌ Cần câu của bạn đã hỏng!")
        return
    if gears[user]["bait_dur"] <= 0:
        await ctx.send("❌ Hết mồi!")
        return

    gears[user]["rod_dur"] -= 1
    gears[user]["bait_dur"] -= 1

    caught = []
    xp_gained = 0
    for _ in range(random.randint(1,3)):
        fish, weight, rarity, price = get_random_fish(user)
        inventories.setdefault(user,[]).append((fish,weight,rarity))
        fish_log.setdefault(user,{})
        if fish not in fish_log[user]:
            fish_log[user][fish] = {"rarity":rarity,"max_weight":weight}
        else:
            if weight > fish_log[user][fish]["max_weight"]:
                fish_log[user][fish]["max_weight"] = weight
        caught.append(f"{fish} — {rarity} — {weight}kg")
        xp_gained += 10  # mỗi cá +10 XP

    add_xp(user,xp_gained)
    level = levels[user]["level"]

    embed = discord.Embed(title=f"🎣 {ctx.author.name} vừa câu được:", color=0x00ff00)
    embed.description = "\n".join(caught)
    embed.set_footer(text=f"⚙️ Rod: {gears[user]['rod_dur']} | Bait: {gears[user]['bait_dur']} | Level: {level} (+{xp_gained} XP)")
    await ctx.send(embed=embed)

@bot.command(name="inventory")
async def inventory(ctx):
    user = ctx.author.id
    if user not in inventories or not inventories[user]:
        await ctx.send("🎒 Túi của bạn đang rỗng!")
        return
    embed = discord.Embed(title=f"🎒 Túi đồ {ctx.author.name}", color=0x00ff00)
    items = "\n".join([f"{fish} ({w}kg, {r})" for fish,w,r in inventories[user]])
    bal = balances.get(user,0)
    lvl = levels.get(user,{"level":1,"xp":0})
    embed.add_field(name="Items", value=items, inline=False)
    embed.add_field(name="Số dư", value=f"{bal:,} VNĐ", inline=True)
    embed.add_field(name="Level", value=f"{lvl['level']} (+{lvl['xp']} XP)", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="shop")
async def shop(ctx):
    embed = discord.Embed(title="🛒 Shop", color=0x00ff00)
    for item, info in shop_items.items():
        embed.add_field(name=item, value=f"Price: {info['price']:,} VNĐ | Luck: {info['luck']} | Durability: {info['durability']}", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="mua")
async def mua(ctx, *, item: str):
    user = ctx.author.id
    if item not in shop_items:
        await ctx.send("❌ Item không tồn tại!")
        return
    price = shop_items[item]["price"]
    if balances.get(user,0) < price:
        await ctx.send("❌ Không đủ tiền!")
        return
    balances[user] -= price
    if "Cần" in item:
        gears.setdefault(user,{})["rod"] = shop_items[item].copy()
        gears[user]["rod_dur"] = shop_items[item]["durability"]
    elif "Mồi" in item:
        gears.setdefault(user,{})["bait"] = shop_items[item].copy()
        gears[user]["bait_dur"] = shop_items[item]["durability"]
    await ctx.send(f"✅ {ctx.author.name} đã mua {item} thành công!")

@bot.command(name="ban")
async def ban(ctx):
    user = ctx.author.id
    if user not in inventories or not inventories[user]:
        await ctx.send("👜 Túi trống!")
        return
    total = 0
    details = []
    for fish,weight,rarity in inventories[user]:
        price = fish_data[rarity][fish]*weight
        total += price
        details.append(f"{fish} ({weight}kg, {rarity}) = {round(price):,} VNĐ")
    inventories[user].clear()
    balances[user] = balances.get(user,0)+total
    embed = discord.Embed(title=f"💸 {ctx.author.name} bán cá thành công!", color=0x00ff00)
    embed.description = "\n".join(details) + f"\n**Tổng cộng: {round(total):,} VNĐ**"
    await ctx.send(embed=embed)

@bot.command(name="fishdex")
async def fishdex(ctx):
    user = ctx.author.id
    if user not in fish_log or not fish_log[user]:
        await ctx.send("📘 Fishdex trống!")
        return
    embed = discord.Embed(title=f"📘 Fishdex {ctx.author.name}", color=0x00ff00)
    for fish,info in fish_log[user].items():
        embed.add_field(name=fish, value=f"Rarity: {info['rarity']}\nMax Weight: {info['max_weight']}kg", inline=False)
    await ctx.send(embed=embed)

# -----------------------------
# Keep bot alive
# -----------------------------
app = Flask("")
@app.route("/")
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# -----------------------------
# Run bot
# -----------------------------
bot.run(os.getenv("DISCORD_TOKEN"))
