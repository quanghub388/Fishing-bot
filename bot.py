import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os
from flask import Flask
import threading

# ========================== CONFIG ==========================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=":", intents=intents)
tree = app_commands.CommandTree(bot)

DATA_FILE = "data.json"

# ========================== SAVE / LOAD ==========================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)

user_data = load_data()

# ========================== SHOP DATA ==========================
fish_types = {
    "common": [
        {"name": "🐟 Cá chép", "price": 100},
        {"name": "🐠 Cá rô phi", "price": 120},
        {"name": "🐡 Cá nóc", "price": 150}
    ],
    "uncommon": [
        {"name": "🐟 Cá trắm", "price": 300},
        {"name": "🐠 Cá mè", "price": 350}
    ],
    "rare": [
        {"name": "🦈 Cá mập con", "price": 1000},
        {"name": "🐡 Cá nóc hiếm", "price": 1200}
    ],
    "epic": [
        {"name": "🐬 Cá heo", "price": 5000},
        {"name": "🦑 Mực khổng lồ", "price": 7000}
    ],
    "legendary": [
        {"name": "🐉 Rồng biển", "price": 20000},
        {"name": "🐋 Cá voi xanh", "price": 15000}
    ],
    "mythic": [
        {"name": "🐲 Leviathan", "price": 50000}
    ],
    "exotic": [
        {"name": "🐊 Cá sấu cổ đại", "price": 350000},
        {"name": "🦈 Megalodon", "price": 500000}
    ]
}

shop_rods = {
    "🎣 Cần tre": {"price": 500, "luck": 1, "durability": 50},
    "🪝 Cần sắt": {"price": 2000, "luck": 2, "durability": 100},
    "⚓ Cần vàng": {"price": 10000, "luck": 4, "durability": 200}
}

shop_baits = {
    "🪱 Giun đất": {"price": 200, "luck": 1, "durability": 20},
    "🦐 Tôm nhỏ": {"price": 500, "luck": 2, "durability": 25},
    "🐛 Sâu đặc biệt": {"price": 1500, "luck": 3, "durability": 30}
}

# ========================== INIT DATA ==========================
def get_user(user_id):
    if str(user_id) not in user_data:
        user_data[str(user_id)] = {
            "coins": 0,
            "inventory": {"fish": {}, "rods": {}, "baits": {}}
        }
    return user_data[str(user_id)]

# ========================== COMMANDS ==========================
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot đã đăng nhập thành công dưới tên {bot.user}")

# :sotien
@bot.command(name="sotien")
async def sotien(ctx):
    user = get_user(ctx.author.id)
    await ctx.send(f"{ctx.author.mention}, bạn đang có 💶 {user['coins']} Coincat")

# :khodo
@bot.command(name="khodo")
async def khodo(ctx):
    user = get_user(ctx.author.id)
    fish_inv = user["inventory"]["fish"]
    if not fish_inv:
        await ctx.send("Bạn chưa có con cá nào 🐟")
        return
    msg = "🎒 **Kho đồ cá của bạn:**\n"
    for fish, amount in fish_inv.items():
        msg += f"{fish}: {amount} con\n"
    await ctx.send(msg)

# :cuahang
@bot.command(name="cuahang")
async def cuahang(ctx):
    msg = "🛒 **Cửa hàng**\n\n🎣 Cần câu:\n"
    for rod, info in shop_rods.items():
        msg += f"{rod} - 💶 {info['price']} Coincat\n"
    msg += "\n🪱 Mồi:\n"
    for bait, info in shop_baits.items():
        msg += f"{bait} - 💶 {info['price']} Coincat\n"
    await ctx.send(msg)

# :mua
@bot.command(name="mua")
async def mua(ctx, *, item_name):
    user = get_user(ctx.author.id)
    item = None
    if item_name in shop_rods:
        item = shop_rods[item_name]
        category = "rods"
    elif item_name in shop_baits:
        item = shop_baits[item_name]
        category = "baits"
    if item:
        if user["coins"] >= item["price"]:
            user["coins"] -= item["price"]
            user["inventory"][category][item_name] = user["inventory"][category].get(item_name, 0) + 1
            save_data()
            await ctx.send(f"Bạn đã mua {item_name} thành công!")
        else:
            await ctx.send("Bạn không đủ tiền 💸")
    else:
        await ctx.send("Không tìm thấy vật phẩm!")

# :banca
@bot.command(name="banca")
async def banca(ctx, *, fish_name=None):
    user = get_user(ctx.author.id)
    fish_inv = user["inventory"]["fish"]

    if not fish_inv:
        await ctx.send("Bạn không có con cá nào để bán 🐟")
        return

    if fish_name is None:
        # bán tất cả cá
        total = 0
        for rarity in fish_types:
            for fish in fish_types[rarity]:
                name, price = fish["name"], fish["price"]
                if name in fish_inv:
                    total += price * fish_inv[name]
        user["coins"] += total
        user["inventory"]["fish"] = {}
        save_data()
        await ctx.send(f"Bạn đã bán toàn bộ cá và nhận 💶 {total} Coincat!")
    else:
        # bán 1 loại cá
        sold = False
        for rarity in fish_types:
            for fish in fish_types[rarity]:
                if fish_name == fish["name"]:
                    if fish_name in fish_inv and fish_inv[fish_name] > 0:
                        amount = fish_inv[fish_name]
                        coins = fish["price"] * amount
                        user["coins"] += coins
                        del fish_inv[fish_name]
                        save_data()
                        await ctx.send(f"Bạn đã bán {amount}x {fish_name} và nhận 💶 {coins} Coincat!")
                        sold = True
                    else:
                        await ctx.send("Bạn không có con cá này.")
                        sold = True
        if not sold:
            await ctx.send("Không tìm thấy loại cá này.")
# ========================== SLASH COMMANDS ==========================

@tree.command(name="sotien", description="Xem số tiền bạn đang có")
async def sotien_slash(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    await interaction.response.send_message(
        f"{interaction.user.mention}, bạn đang có 💶 {user['coins']} Coincat"
    )

@tree.command(name="khodo", description="Xem kho đồ cá của bạn")
async def khodo_slash(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    fish_inv = user["inventory"]["fish"]
    if not fish_inv:
        await interaction.response.send_message("Bạn chưa có con cá nào 🐟")
        return
    msg = "🎒 **Kho đồ cá của bạn:**\n"
    for fish, amount in fish_inv.items():
        msg += f"{fish}: {amount} con\n"
    await interaction.response.send_message(msg)

@tree.command(name="cuahang", description="Xem cửa hàng")
async def cuahang_slash(interaction: discord.Interaction):
    msg = "🛒 **Cửa hàng**\n\n🎣 Cần câu:\n"
    for rod, info in shop_rods.items():
        msg += f"{rod} - 💶 {info['price']} Coincat\n"
    msg += "\n🪱 Mồi:\n"
    for bait, info in shop_baits.items():
        msg += f"{bait} - 💶 {info['price']} Coincat\n"
    await interaction.response.send_message(msg)

@tree.command(name="mua", description="Mua vật phẩm trong cửa hàng")
async def mua_slash(interaction: discord.Interaction, item_name: str):
    user = get_user(interaction.user.id)
    item = None
    if item_name in shop_rods:
        item = shop_rods[item_name]
        category = "rods"
    elif item_name in shop_baits:
        item = shop_baits[item_name]
        category = "baits"
    if item:
        if user["coins"] >= item["price"]:
            user["coins"] -= item["price"]
            user["inventory"][category][item_name] = user["inventory"][category].get(item_name, 0) + 1
            save_data()
            await interaction.response.send_message(f"Bạn đã mua {item_name} thành công!")
        else:
            await interaction.response.send_message("Bạn không đủ tiền 💸")
    else:
        await interaction.response.send_message("Không tìm thấy vật phẩm!")

@tree.command(name="banca", description="Bán cá lấy Coincat")
async def banca_slash(interaction: discord.Interaction, fish_name: str = None):
    user = get_user(interaction.user.id)
    fish_inv = user["inventory"]["fish"]

    if not fish_inv:
        await interaction.response.send_message("Bạn không có con cá nào để bán 🐟")
        return

    if fish_name is None:
        total = 0
        for rarity in fish_types:
            for fish in fish_types[rarity]:
                name, price = fish["name"], fish["price"]
                if name in fish_inv:
                    total += price * fish_inv[name]
        user["coins"] += total
        user["inventory"]["fish"] = {}
        save_data()
        await interaction.response.send_message(f"Bạn đã bán toàn bộ cá và nhận 💶 {total} Coincat!")
    else:
        sold = False
        for rarity in fish_types:
            for fish in fish_types[rarity]:
                if fish_name == fish["name"]:
                    if fish_name in fish_inv and fish_inv[fish_name] > 0:
                        amount = fish_inv[fish_name]
                        coins = fish["price"] * amount
                        user["coins"] += coins
                        del fish_inv[fish_name]
                        save_data()
                        await interaction.response.send_message(f"Bạn đã bán {amount}x {fish_name} và nhận 💶 {coins} Coincat!")
                        sold = True
                    else:
                        await interaction.response.send_message("Bạn không có con cá này.")
                        sold = True
        if not sold:
            await interaction.response.send_message("Không tìm thấy loại cá này.")

# ========================== CHUYỂN TIỀN ==========================

@bot.command(name="chuyentien")
async def chuyentien(ctx, member: discord.Member, amount: int):
    sender = get_user(ctx.author.id)
    receiver = get_user(member.id)

    if amount <= 0:
        await ctx.send("Số tiền phải lớn hơn 0 💸")
        return
    if amount > 300000:
        await ctx.send("Bạn chỉ có thể chuyển tối đa 💶 300000 Coincat/lần")
        return
    if sender["coins"] < amount:
        await ctx.send("Bạn không đủ tiền để chuyển!")
        return

    sender["coins"] -= amount
    receiver["coins"] += amount
    save_data()
    await ctx.send(f"{ctx.author.mention} đã chuyển 💶 {amount} Coincat cho {member.mention}!")

# ========================== WEB SERVICE (KEEP ALIVE) ==========================

app = Flask("")

@app.route("/")
def home():
    return "Fishing Bot is running!"

def run():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run).start()

# ========================== RUN BOT ==========================
bot.run(os.getenv("DISCORD_TOKEN"))
                      
