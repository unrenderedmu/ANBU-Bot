import os
import datetime
import asyncio
import discord
from discord.ext import commands
import config
#from still_alive import still_alive
intents = discord.Intents.default()
intents.members = True

_token = os.environ['DISCORD_BOT_TOKEN']
bot = commands.Bot(command_prefix = '.', intents = intents)

@bot.event
async def on_ready():
  await bot.change_presence(activity = discord.Activity(name = config.WATCHING_STATUS, type = discord.ActivityType.watching))
  print(f'{bot.user.name} has connected to Discord!')

#COMMANDS
#MUTE
@bot.command(name = 'mute', help = 'Mutes the member', invoke_without_command = True)
async def _mute(ctx, member:discord.Member, *, _reason = None):
    muted_role = discord.utils.get(ctx.guild.roles, name = config.MUTED_ROLE_NAME)
    if _reason == None:
      await ctx.send(f"C'mon be reasonable and provide a reason {ctx.author.mention}.")
    else:
      mute_dm = f"Bonk! You have been muted in {ctx.guild.name} for: {_reason}"
      await member.add_roles(muted_role, reason = _reason)
      try:
        await member.send(mute_dm)
      except:
        return

#UNMUTE
@bot.command(name = 'unmute', help = 'Unmutes the member', invoke_without_command = True)
async def _unmute(ctx, member:discord.Member, *, _reason = None):
    muted_role = discord.utils.get(ctx.guild.roles, name = config.MUTED_ROLE_NAME)
    if _reason == None:
      await ctx.send(f"C'mon be reasonable and provide a reason {ctx.author.mention}.")
    else:
      unmute_dm = f"Bonk! You have been unmuted in {ctx.guild.name} for: {_reason}"
      await member.remove_roles(muted_role, reason = _reason)
      try:
        await member.send(unmute_dm)
      except:
        return

#BAN
@bot.command(name = 'ban', help = 'Bans the member')
@commands.has_permissions(ban_members = True)
async def _ban(ctx, user:discord.User, *, _reason = None):
    if user == None or user == ctx.message.author:
      await ctx.channel.send("You cannot ban yourself dummy")
      return
    if _reason == None:
      await ctx.send(f"C'mon be reasonable and provide a reason {ctx.author.mention}.")
    else:
      ban_dm = f"Bonk! You have been banned from {ctx.guild.name} for: {_reason}"
      await ctx.guild.ban(user, reason = _reason)
    try:
      await user.send(ban_dm)
    except:
      return

#UNBAN
@bot.command(name = 'unban', help = 'Unbans the member')
@commands.has_permissions(ban_members = True)
async def _unban(ctx, member:discord.User, *, _reason = None):
    banned_users = await ctx.guild.bans()
    for ban_entry in banned_users:
      user = ban_entry.user
      if (user.id) == (member.id):
        if _reason == None:
          await ctx.send(f"C'mon be reasonable and provide a reason {ctx.author.mention}.")
        else:
          await ctx.guild.unban(user, reason = _reason)

#KICK
@bot.command(name = 'kick', help = 'Kicks the member')
@commands.has_permissions(kick_members = True)
async def _kick(ctx, member:discord.Member, *, _reason = None):
    if member == None or member == ctx.message.author:
      await ctx.channel.send("You cannot kick yourself dummy")
      return
    if _reason == None:
      await ctx.send(f"C'mon be reasonable and provide a reason {ctx.author.mention}.")
    else:
      kick_dm = f"Bonk! You have been kicked from {ctx.guild.name} for: {_reason}"
      await member.kick(reason = _reason)
    try:
      await member.send(kick_dm)
    except:
      return

#REASON EDIT
@bot.command(name = 'reason', help = 'Update reason')
async def _reason(ctx, *, message):
    if ctx.channel.name == config.LOG_CHANNEL_NAME:
        await edit_reason(ctx)

#EVENTS LOGGING
#BANNED
@bot.event
async def on_member_ban(gld, usr):
    await asyncio.sleep(0.5)
    found_entry = None
    async for entry in gld.audit_logs(limit = 50, action = discord.AuditLogAction.ban, after = datetime.datetime.utcnow() - datetime.timedelta(seconds = 15), oldest_first = False):
        if entry.created_at < datetime.datetime.utcnow() - datetime.timedelta(seconds = 10):
            continue
        if entry.target.id == usr.id:
            found_entry = entry
            break
    if not found_entry:
        return
    await post_modlog(guild = gld, type = "BAN", user = found_entry.user, target = usr, reason = found_entry.reason)

#UNBANNED
@bot.event
async def on_member_unban(gld, usr):
    await asyncio.sleep(0.5)
    found_entry = None
    async for entry in gld.audit_logs(limit = 50, action = discord.AuditLogAction.unban, after = datetime.datetime.utcnow() - datetime.timedelta(seconds = 15), oldest_first = False):
        if entry.created_at < datetime.datetime.utcnow() - datetime.timedelta(seconds = 10):
            continue
        if entry.target.id == usr.id:
            found_entry = entry
            break
    if not found_entry:
        return
    await post_modlog(guild = gld, type = "UNBAN", user = found_entry.user, target = usr, reason = found_entry.reason)

#KICKED
@bot.event
async def on_member_remove(usr):
    await asyncio.sleep(0.5)
    found_entry = None
    async for entry in usr.guild.audit_logs(limit = 50, action = discord.AuditLogAction.kick, after = datetime.datetime.utcnow() - datetime.timedelta(seconds = 10), oldest_first = False):
        if entry.created_at < datetime.datetime.utcnow() - datetime.timedelta(seconds = 10):
            continue
        if entry.target.id == usr.id:
            found_entry = entry
            break
    if not found_entry:
        return
    await post_modlog(guild = usr.guild, type = "KICK", user = found_entry.user, target = usr, reason = found_entry.reason)

#MUTED / UNMUTED
@bot.event
async def on_member_update(before, after):
    if before.roles == after.roles:
        return
    muted_role = discord.utils.get(after.guild.roles, name = config.MUTED_ROLE_NAME)
    if not muted_role:
        return
    if muted_role in after.roles and not muted_role in before.roles:
        if after.joined_at > (datetime.datetime.utcnow() - datetime.timedelta(seconds = 10)):
            return
        await asyncio.sleep(0.5)
        found_entry = None
        async for entry in after.guild.audit_logs(limit = 50, action = discord.AuditLogAction.member_role_update, after = datetime.datetime.utcnow() - datetime.timedelta(seconds = 15), oldest_first = False):
            if entry.created_at < datetime.datetime.utcnow() - datetime.timedelta(seconds = 10):
                continue
            if entry.target.id == after.id and not muted_role in entry.before.roles and muted_role in entry.after.roles:
                found_entry = entry
                break
        if not found_entry:
            return
        await post_modlog(guild = after.guild, type = "MUTE", user = found_entry.user, target = after, reason = found_entry.reason)
    elif muted_role not in after.roles and muted_role in before.roles:
        if after.joined_at > (datetime.datetime.utcnow() - datetime.timedelta(seconds = 10)):
            return
        await asyncio.sleep(0.5)
        found_entry = None
        async for entry in after.guild.audit_logs(limit = 50, action = discord.AuditLogAction.member_role_update, after = datetime.datetime.utcnow() - datetime.timedelta(seconds = 15), oldest_first = False):
            if entry.created_at < datetime.datetime.utcnow() - datetime.timedelta(seconds = 10):
                continue
            if entry.target.id == after.id and muted_role in entry.before.roles and not muted_role in entry.after.roles:
                found_entry = entry
                break
        if not found_entry:
            return
        await post_modlog(guild = after.guild, type = "UNMUTE", user = found_entry.user, target = after, reason = found_entry.reason)

#MESSAGE EDITED (currently works only on messages in bot cache because its complicated if not impossible to implement otherwise)
@bot.event
async def on_message_edit(message_before, message_after):
    if message_before.content == message_after.content:
      return
    await post_message_log(guild = message_after.guild, type = "MESSAGE EDITED", arg1 = message_before, arg2 = message_after)

#MESSAGE DELETED (currently works only on messages in bot cache because it requires to separate current solution only for self deleted messages and implement the rest via Audit Log)
@bot.event
async def on_message_delete(message):
    await post_message_log(guild = message.guild, type = "MESSAGE DELETED", arg1 = message, arg2 = None)


#MESSAGE LOG EMBED BUILDER
async def post_message_log(guild, type, arg1, arg2):
    mod_log_channel = discord.utils.get(arg1.guild.text_channels, name = config.LOG_CHANNEL_NAME)
    
    if (arg1.author.bot):
      return
    if not mod_log_channel:
        return
    entryid = "1"
    async for s in mod_log_channel.history(limit = 100):
        if s.author.id != bot.user.id:
            continue
        if not s.embeds:
            continue
        entryid = str(int(s.embeds[0].author.name.split(" | Log Entry ")[1]) + 1)
        break

    e = discord.Embed(color = config.LOG_COLORS[type], timestamp = datetime.datetime.utcnow())
    e.set_author(name = f"{type.capitalize()} | Log Entry {entryid}")
    e.add_field(name = "Author", value = f"{arg1.author.mention} ({str(arg1.author)})", inline = True)
    e.add_field(name = "Channel", value = f"{arg1.channel.mention} ({str(arg1.channel)})", inline = True)

    if arg2 == None:
      e.add_field(name = "Message", value = arg1.content, inline=False)
    else:
      e.add_field(name = "Before", value = arg1.content, inline=False)
      e.add_field(name = "After", value = arg2.content, inline=False)
    await mod_log_channel.send(embed = e)

#MOD LOG EMBED BUILDER
async def post_modlog(guild, type, user, target, reason):
    mod_log_channel = discord.utils.get(guild.text_channels, name = config.LOG_CHANNEL_NAME)
    if not mod_log_channel:
        return
    entryid = "1"
    async for s in mod_log_channel.history(limit = 100):
        if s.author.id != bot.user.id:
            continue
        if not s.embeds:
            continue
        entryid = str(int(s.embeds[0].author.name.split(" | Log Entry ")[1]) + 1)
        break
    e = discord.Embed(color = config.LOG_COLORS[type], timestamp = datetime.datetime.utcnow())
    e.set_author(name = f"{type.capitalize()} | Log Entry {entryid}")
    e.add_field(name = "Member", value = f"{target.mention} ({str(target)})", inline = True)
    e.add_field(name = "Moderator", value = f"{user.mention} ({str(user)})", inline = True)
    e.add_field(name = "Reason", value = reason if reason else f"To update do `.reason {entryid} <reason>`", inline = False)
    await mod_log_channel.send(embed = e)

#LOG REASON EDIT HANDLER
async def edit_reason(msg):
    pmsg = msg.message.content.replace(".reason ", "")
    if not " " in pmsg:
        return
    entryid = pmsg.split(" ")[0]
    if not entryid.isdigit():
        return
    new_reason = " ".join(pmsg.split(" ")[1:])
    fnd_msg = None
    async for s in msg.channel.history(limit = 500):
        if s.author.id != bot.user.id:
            continue
        if not s.embeds:
            continue
        if s.embeds[0].author.name.endswith(f" | Log Entry {entryid}"):
            fnd_msg = s
            break
    if not fnd_msg:
        return
    fnd_em = fnd_msg.embeds[0]
    fnd_em.set_field_at(2, name = "Reason", value = new_reason, inline = False)
    await fnd_msg.edit(embed = fnd_em)

#still_alive()
bot.run(_token)