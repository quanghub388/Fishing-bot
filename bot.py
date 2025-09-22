import discord
from discord.ext import commands
import random
import json
import os
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=":", intents=intents)

# ========================== HTTP KEEP-ALIVE ==========================
app = Flask('')

@app.route('/')
def home():
    return "Fishing Bot is alive!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ========================== SAVE & LOAD ==========================
SAVE_FILE = "data.json"

def load_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}}

def save_data():
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

data = load_data()

def get_user(user_id):
    if str(user_id) not in data["users"]:
        data["users"][str(user_id)] = {
            "money": 0,
            "inventory": {},
            "rods": [],
            "baits": []
        }
    return data["users"][str(user_id)]

# ========================== FISH LIST ==========================
fish_list = {
    "common": {
        "🐟 Cá rô phi": 10,
        "🐠 Cá vàng": 15,
        "🦐 Tôm nhỏ": 8,
        "🐡 Cá nóc": 20,
        "🦀 Cua đồng": 12
    },
    "uncommon": {
        "🐟 Cá trê": 50,
        "🐡 Cá chép": 60,
        "🦐 Tôm hùm baby": 80,
        "🐢 Rùa nước ngọt": 100
    },
    "rare": {
        "🐠 Cá hồi": 200,
        "🐟 Cá ngừ": 250,
        "🦑 Mực nang": 300
    },
    "epic": {
        "🦈 Cá mập con": 1000,
        "🐬 Cá heo": 1200,
        "🐟 Cá chim trắng": 900
    },
    "legendary": {
        "🐉 Rồng biển": 5000,
        "🐡 Cá mặt trăng": 4000,
        "🐟 Cá đuối khổng lồ": 4500
    },
    "mythic": {
        "🐲 Leviathan": 20000,
        "🦈 Megalodon": 500000
    },
    "exotic": {
        "🐟 Exotic Koi": 350000
    }
}

rarity_weights = {
    "common": 60,
    "uncommon": 25,
    "rare": 10,
    "epic": 4,
    "legendary": 0.9,
    "mythic": 0.5,
    "exotic": 0.1
}

# ========================== COMMANDS ==========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot {bot.user} đã online và slash commands đã sync!")

# :sotien
@bot.command(name="sotien")
async def sotien(ctx):
    user = get_user(ctx.author.id)
    await ctx.send(f"💶 {ctx.author.mention}, bạn đang có **{user['money']} Coincat**.")

# :cauca
@bot.command(name="cauca")
async def cauca(ctx):
    user = get_user(ctx.author.id)
    rarity = random.choices(list(rarity_weights.keys()), weights=rarity_weights.values())[0]
    fish, price = random.choice(list(fish_list[rarity].items()))
    user["inventory"][fish] = user["inventory"].get(fish, 0) + 1
    save_data()
    await ctx.send(f"🎣 {ctx.author.mention} câu được {fish} ({rarity.upper()}) trị giá 💶 {price} Coincat!")

# :khodo
@bot.command(name="khodo")
async def khodo(ctx):
    user = get_user(ctx.author.id)
    if not user["inventory"]:
        await ctx.send("📦 Kho đồ của bạn trống rỗng!")
        return
    items = "\n".join([f"{fish} x{amount}" for fish, amount in user["inventory"].items()])
    await ctx.send(f"🎒 Kho đồ của {ctx.author.mention}:\n{items}")

# :banca
@bot.command(name="banca")
async def banca(ctx, *, fish_name=None):
    user = get_user(ctx.author.id)
    if not user["inventory"]:
        await ctx.send("❌ Bạn không có cá nào để bán!")
        return

    if fish_name is None or fish_name.lower() == "all":
        total = 0
        for rarity, fishes in fish_list.items():
            for fish, price in fishes.items():
                if fish in user["inventory"]:
                    total += price * user["inventory"][fish]
        user["money"] += total
        user["inventory"] = {}
        save_data()
        await ctx.send(f"💰 {ctx.author.mention} đã bán toàn bộ cá và nhận được 💶 {total} Coincat!")
    else:
        for rarity, fishes in fish_list.items():
            for fish, price in fishes.items():
                if fish_name.lower() in fish.lower():
                    if fish in user["inventory"] and user["inventory"][fish] > 0:
                        user["money"] += price
                        user["inventory"][fish] -= 1
                        if user["inventory"][fish] == 0:
                            del user["inventory"][fish]
                        save_data()
                        await ctx.send(f"💰 {ctx.author.mention} đã bán {fish} và nhận được 💶 {price} Coincat!")
                        return
        await ctx.send("❌ Không tìm thấy cá bạn muốn bán!")

# :chuyentien
@bot.command(name="chuyentien")
async def chuyentien(ctx, member: discord.Member, amount: int):
    sender = get_user(ctx.author.id)
    receiver = get_user(member.id)

    if amount <= 0:
        await ctx.send("❌ Số tiền không hợp lệ!")
        return
    if amount > 300000:
        await ctx.send("❌ Giới hạn chuyển tối đa là 300000 Coincat!")
        return
    if sender["money"] < amount:
        await ctx.send("❌ Bạn không đủ tiền để chuyển!")
        return

    sender["money"] -= amount
    receiver["money"] += amount
    save_data()
    await ctx.send(f"💸 {ctx.author.mention} đã chuyển 💶 {amount} Coincat cho {member.mention}!")

# ========================== SLASH COMMANDS ==========================
@bot.tree.command(name="sotien", description="Xem số tiền bạn đang có")
async def sotien_slash(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    await interaction.response.send_message(f"💶 {interaction.user.mention}, bạn đang có **{user['money']} Coincat**.")

@bot.tree.command(name="cauca", description="Câu cá và nhận phần thưởng!")
async def cauca_slash(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    rarity = random.choices(list(rarity_weights.keys()), weights=rarity_weights.values())[0]
    fish, price = random.choice(list(fish_list[rarity].items()))
    user["inventory"][fish] = user["inventory"].get(fish, 0) + 1
    save_data()
    await interaction.response.send_message(f"🎣 {interaction.user.mention} câu được {fish} ({rarity.upper()}) trị giá 💶 {price} Coincat!")

@bot.tree.command(name="khodo", description="Xem kho đồ cá của bạn")
async def khodo_slash(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    if not user["inventory"]:
        await interaction.response.send_message("📦 Kho đồ của bạn trống rỗng!")
        return
    items = "\n".join([f"{fish} x{amount}" for fish, amount in user["inventory"].items()])
    await interaction.response.send_message(f"🎒 Kho đồ của {interaction.user.mention}:\n{items}")

# ========================== RUN ==========================
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
        
