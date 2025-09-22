import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os
from flask import Flask
import threading

# ========================== BOT SETUP ==========================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=":", intents=intents)
tree = bot.tree

DATA_FILE = "userdata.json"

# ========================== SAVE/LOAD ==========================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

users = load_data()

def get_user(uid):
    if str(uid) not in users:
        users[str(uid)] = {
            "money": 1000,
            "inventory": {},
            "rods": [],
            "baits": []
        }
    return users[str(uid)]

# ========================== FISH LIST ==========================
fish_list = {
    "common": {
        "🐟 Cá chép": 50, "🐠 Cá rô": 40, "🐡 Cá nóc": 30,
        "🦐 Tôm": 25, "🦀 Cua": 35, "🐙 Bạch tuộc nhỏ": 60,
    },
    "uncommon": {
        "🐟 Cá mè": 100, "🐠 Cá trê": 120, "🦑 Mực": 110,
        "🐡 Cá nóc xanh": 90, "🐢 Rùa con": 150,
    },
    "rare": {
        "🐟 Cá hồi": 250, "🐠 Cá ngừ": 300, "🦞 Tôm hùm": 350,
        "🦐 Tôm sú": 200, "🐡 Cá nóc vàng": 280,
    },
    "epic": {
        "🐟 Cá thu": 500, "🐠 Cá mập con": 700, "🐉 Cá rồng nhỏ": 800,
        "🐡 Cá nóc đỏ": 650, "🦑 Mực khổng lồ": 750,
    },
    "legendary": {
        "🐟 Cá kiếm": 1200, "🐠 Cá mập trắng": 1500, "🐉 Cá rồng vàng": 1800,
        "🐡 Cá nóc độc": 1300, "🐢 Rùa vàng": 1700,
    },
    "mythic": {
        "🐉 Rồng biển": 2500, "🐟 Cá tiên": 2200, "🐠 Cá thần": 2400,
        "🦑 Kraken con": 2600, "🐢 Rùa thần": 2300,
    },
    "exotic": {
        "🐉 Rồng nước": 5000, "🐟 Cá kỳ lân": 4500, "🐠 Cá phượng hoàng": 4800,
        "🦑 Kraken": 5200, "🐢 Rùa huyền thoại": 4700,
    }
}

rarity_weights = {
    "common": 50, "uncommon": 25, "rare": 12,
    "epic": 7, "legendary": 4, "mythic": 1.5, "exotic": 0.5
}

# ========================== SHOP ==========================
shop_items = {
    "rod": {
        "🎣 Cần tre": 100, "🎣 Cần gỗ": 150, "🎣 Cần sắt": 300,
        "🎣 Cần đồng": 400, "🎣 Cần bạc": 600, "🎣 Cần vàng": 1000,
        "🎣 Cần platinum": 2000, "🎣 Cần kim cương": 4000, "🎣 Cần titan": 6000,
        "🎣 Cần huyền thoại": 8000, "🎣 Cần bóng tối": 12000, "🎣 Cần ánh sáng": 15000,
        "🎣 Cần rồng": 20000, "🎣 Cần thần": 30000, "🎣 Cần cực quang": 40000,
        "🎣 Cần thiên hà": 50000, "🎣 Cần vũ trụ": 60000, "🎣 Cần hỗn mang": 80000,
        "🎣 Cần huyết long": 100000, "🎣 Cần bất tử": 150000
    },
    "bait": {
        "🪱 Giun đất": 10, "🪱 Giun đỏ": 20, "🪱 Giun vàng": 30,
        "🦐 Mồi tôm": 50, "🦐 Mồi tép": 60, "🦐 Mồi tôm càng": 80,
        "🐛 Sâu đất": 40, "🐛 Sâu gỗ": 45, "🐛 Sâu đỏ": 55,
        "🐟 Mồi cá nhỏ": 100, "🐟 Mồi cá cơm": 120, "🐟 Mồi cá mòi": 130,
        "🦗 Châu chấu": 70, "🦟 Muỗi": 25, "🦋 Bướm": 90,
        "🐜 Kiến": 15, "🕷 Nhện": 35, "🪰 Ruồi": 20,
        "🦎 Thằn lằn nhỏ": 150, "🐸 Ếch con": 180, "🐍 Rắn nhỏ": 200,
        "🦞 Tôm nhỏ": 110, "🦀 Cua nhỏ": 115, "🦑 Mực nhỏ": 140,
        "🐢 Rùa con": 160
    }
}

# ========================== ERROR HANDLER ==========================
@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"⚠️ Lỗi: `{error}`")

# ========================== COMMANDS ==========================
@bot.command(name="sotien")
async def sotien(ctx):
    user = get_user(ctx.author.id)
    await ctx.send(f"💶 {ctx.author.mention} có: {user['money']} Coincat")

@bot.command(name="khodo")
async def khodo(ctx):
    user = get_user(ctx.author.id)
    inv = "\n".join([f"{fish} x{qty}" for fish, qty in user["inventory"].items()]) or "Trống"
    await ctx.send(f"📦 Kho đồ của {ctx.author.mention}:\n{inv}")

@bot.command(name="cuahang")
async def cuahang(ctx):
    rods = "\n".join([f"{n} - 💶 {p} Coincat" for n, p in shop_items["rod"].items()])
    baits = "\n".join([f"{n} - 💶 {p} Coincat" for n, p in shop_items["bait"].items()])
    await ctx.send(f"🏪 **Cửa hàng**:\n\n🎣 **Cần câu:**\n{rods}\n\n🪱 **Mồi:**\n{baits}")

@bot.command(name="mua")
async def mua(ctx, *, item_name: str):
    user = get_user(ctx.author.id)
    for cat, items in shop_items.items():
        for name, price in items.items():
            if item_name.lower() in name.lower():
                if user["money"] < price:
                    await ctx.send("❌ Không đủ tiền!")
                    return
                user["money"] -= price
                if cat == "rod":
                    user["rods"].append(name)
                else:
                    user["baits"].append(name)
                save_data()
                await ctx.send(f"✅ Đã mua {name} với giá 💶 {price} Coincat")
                return
    await ctx.send("❌ Không tìm thấy vật phẩm!")

@bot.command(name="cauca")
async def cauca(ctx, so_lan: int = 1):
    user = get_user(ctx.author.id)
    if so_lan < 1: return await ctx.send("❌ Số lần >= 1")
    if so_lan > 10: return await ctx.send("⚠️ Tối đa 10 lần")

    results = []
    for _ in range(so_lan):
        rarity = random.choices(list(rarity_weights.keys()), weights=rarity_weights.values())[0]
        fish, price = random.choice(list(fish_list[rarity].items()))
        user["inventory"][fish] = user["inventory"].get(fish, 0) + 1
        results.append(f"{fish} ({rarity.upper()} - 💶 {price})")
    save_data()
    await ctx.send(f"🎣 {ctx.author.mention} câu được:\n" + "\n".join(results))

@bot.command(name="banca")
async def banca(ctx, *, arg: str):
    user = get_user(ctx.author.id)
    if arg.lower() == "all":
        total = 0
        for f, q in list(user["inventory"].items()):
            for rarity in fish_list:
                if f in fish_list[rarity]:
                    total += fish_list[rarity][f] * q
            del user["inventory"][f]
        user["money"] += total
        save_data()
        await ctx.send(f"💰 Đã bán toàn bộ cá, nhận {total} Coincat")
        return

    for rarity in fish_list:
        for f, price in fish_list[rarity].items():
            if arg.lower() in f.lower():
                if user["inventory"].get(f, 0) > 0:
                    user["inventory"][f] -= 1
                    user["money"] += price
                    if user["inventory"][f] == 0: del user["inventory"][f]
                    save_data()
                    await ctx.send(f"💰 Đã bán 1 {f} giá {price} Coincat")
                    return
    await ctx.send("❌ Bạn không có cá đó!")

@bot.command(name="chuyentien")
async def chuyentien(ctx, member: discord.Member, so_tien: int):
    if so_tien > 300000: return await ctx.send("❌ Giới hạn 300000 Coincat")
    sender, receiver = get_user(ctx.author.id), get_user(member.id)
    if sender["money"] < so_tien: return await ctx.send("❌ Không đủ tiền!")
    sender["money"] -= so_tien
    receiver["money"] += so_tien
    save_data()
    await ctx.send(f"💸 {ctx.author.mention} đã chuyển {so_tien} Coincat cho {member.mention}")

# ========================== SLASH MIRROR ==========================
@tree.command(name="cauca", description="Câu cá (tối đa 10 lần)")
async def cauca_slash(interaction: discord.Interaction, so_lan: int = 1):
    ctx = await bot.get_context(await interaction.original_response())
    await cauca(ctx, so_lan=so_lan)

# ========================== KEEP-ALIVE ==========================
app = Flask("")

@app.route("/")
def home():
    return "Fishing Bot is alive!"

def run():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run).start()

# ========================== BOT RUN ==========================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print("Sync error:", e)

bot.run(os.getenv("DISCORD_TOKEN"))
        
