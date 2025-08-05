from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands

import config
import database_optimized as database
from config import is_leader_or_admin
# import bonus_weights  # Import the new weighted algorithm (DISABLED: file missing)
from logging_config import get_logger
from utils import has_any_role_id, is_admin, is_admin_leader_co_leader, is_admin_leader_co_elder_member, is_newbie, format_last_bonus, days_ago

GUILD_ID = discord.Object(id=config.GUILD_ID)
logger = get_logger("bonuses")

class BonusesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # ...existing code...
        # Move all command/event logic here

    class BonusSelect(discord.ui.View):
        def __init__(self, recommended_players, newbie_players, max_select, interaction_user_id):
            super().__init__(timeout=120)
            self.interaction_user_id = interaction_user_id
            self.selected = []
            self.confirmed = False
            self.cancelled = False
            self.undo_requested = False
            self.last_awarded = []
            
            # Build options like the old bot
            options = []
            
            # Add recommended players
            for p in recommended_players:
                label = f"{p['name']} (Next in Line)"
                
                # Build description with bonus and CWL performance data
                desc_parts = [f"Bonuses: {p.get('bonus_count', 0)}", f"Last: {format_last_bonus(p.get('last_bonus_date'))}"]
                
                # Add individual CWL performance data if available
                cwl_stars = int(p.get('cwl_stars', 0) or 0)
                missed_attacks = int(p.get('missed_attacks', 0) or 0)
                if cwl_stars > 0:
                    desc_parts.append(f"{cwl_stars} Stars")
                if missed_attacks > 0:
                    desc_parts.append(f"**{missed_attacks} Missed**")
                
                desc = " | ".join(desc_parts)
                options.append(discord.SelectOption(label=label, description=desc, value=p['name']))
            
            # Add separator and new members if any
            if newbie_players:
                options.append(discord.SelectOption(label="───────── Optional New Members ─────────", description="New members to consider", value="separator"))
                for p in newbie_players:
                    days = member_days(p.get('join_date', ''))
                    label = f"{p['name']} (New Member for {days} days)"
                    
                    # Build description with bonus and CWL performance data
                    desc_parts = [f"Bonuses: {p.get('bonus_count', 0)}", f"Last: {format_last_bonus(p.get('last_bonus_date'))}"]
                    
                    # Add individual CWL performance data if available
                    cwl_stars = int(p.get('cwl_stars', 0) or 0)
                    missed_attacks = int(p.get('missed_attacks', 0) or 0)
                    if cwl_stars > 0:
                        desc_parts.append(f"{cwl_stars} Stars")
                    if missed_attacks > 0:
                        desc_parts.append(f"**{missed_attacks} Missed**")
                    
                    desc = " | ".join(desc_parts)
                    options.append(discord.SelectOption(label=label, description=desc, value=p['name']))
            
            # Limit to Discord's 25 option max
            options = options[:25]
            
            self.select = discord.ui.Select(
                placeholder=f"Select up to {max_select} players for bonuses",
                min_values=1,
                max_values=min(max_select, len([opt for opt in options if opt.value != "separator"])),
                options=options
            )
            self.select.callback = self.select_callback
            self.add_item(self.select)
            
            # Add control buttons
            self.confirm_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.green)
            self.confirm_button.callback = self.confirm
            self.add_item(self.confirm_button)
            self.cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.red)
            self.cancel_button.callback = self.cancel
            self.add_item(self.cancel_button)
            self.undo_button = discord.ui.Button(label="Undo Last", style=discord.ButtonStyle.secondary, disabled=True)
            self.undo_button.callback = self.undo
            self.add_item(self.undo_button)
        async def select_callback(self, interaction: discord.Interaction):
            if interaction.user.id != self.interaction_user_id:
                await interaction.response.send_message("You can't select for this interaction.", ephemeral=True)
                return
            # Filter out separator values
            selected_values = [val for val in self.select.values if val != "separator"]
            self.selected = selected_values
            if selected_values:
                await interaction.response.send_message(f"Selected: {', '.join(selected_values)}", ephemeral=True)
            else:
                await interaction.response.send_message("Please select actual players (not separators).", ephemeral=True)
        async def confirm(self, interaction: discord.Interaction):
            if interaction.user.id != self.interaction_user_id:
                await interaction.response.send_message("You can't confirm this interaction.", ephemeral=True)
                return
            if not self.selected:
                await interaction.response.send_message("Please select at least one player before confirming.", ephemeral=True)
                return
            self.confirmed = True
            self.last_awarded = list(self.selected)
            self.undo_button.disabled = False
            await interaction.response.defer(ephemeral=True)
            self.stop()
        async def cancel(self, interaction: discord.Interaction):
            if interaction.user.id != self.interaction_user_id:
                await interaction.response.send_message("You can't cancel this interaction.", ephemeral=True)
                return
            self.cancelled = True
            await interaction.response.edit_message(content="Bonus awarding cancelled.", view=None)
            self.stop()
        async def undo(self, interaction: discord.Interaction):
            if interaction.user.id != self.interaction_user_id:
                await interaction.response.send_message("You can't undo this interaction.", ephemeral=True)
                return
            self.undo_requested = True
            await interaction.response.edit_message(content="Undo requested.", view=None)
            self.stop()

    @app_commands.command(
        name="give_cwl_bonuses",
        description="Give CWL Bonuses — Admin, Leader, Co-Leader"
    )
    @app_commands.check(is_admin_leader_co_leader)
    @app_commands.guilds(GUILD_ID)
    @app_commands.describe(bonus_count="Number of bonuses to give (5-9)")
    async def give_cwl_bonuses(self, interaction: discord.Interaction, bonus_count: int = 5):
        logger.info("[COMMAND] /give_cwl_bonuses invoked")
        try:
            await interaction.response.defer(ephemeral=True)
            
            if bonus_count < 5 or bonus_count > 9:
                await interaction.followup.send("Bonus count must be between 5 and 9.", ephemeral=True)
                return
                
            players = database.get_player_data()
            # Exclude 'New' for next-in-line
            next_in_line = [p for p in players if p.get("bonus_eligibility", 0) and not is_newbie(p.get("join_date", ""))]
            new_members = [p for p in players if p.get("bonus_eligibility", 0) and is_newbie(p.get("join_date", ""))]

            def sort_key(p):
                bonus_count_val = int(p.get("bonus_count", 0) or 0)
                last_bonus = p.get("last_bonus_date")
                if last_bonus:
                    try:
                        last_bonus = datetime.strptime(last_bonus, "%Y-%m-%d")
                    except Exception:
                        last_bonus = datetime.min
                else:
                    last_bonus = datetime.min
                return (bonus_count_val, last_bonus)

            # Sort next-in-line by bonus eligibility
            next_in_line.sort(key=sort_key)
            
            # Sort new members by join date (oldest first)
            def newbie_sort_key(p):
                join_date_str = p.get("join_date", "")
                if join_date_str and join_date_str != "None":
                    try:
                        return datetime.strptime(join_date_str, "%Y-%m-%d")
                    except Exception:
                        return datetime.min
                return datetime.min
            
            new_members.sort(key=newbie_sort_key)
            
            # Create bonus selection view
            recommended = next_in_line[:bonus_count]
            newbies = new_members[:3]  # Show up to 3 new members as options
            
            view = BonusesCog.BonusSelect(recommended, newbies, bonus_count, interaction.user.id)
            await interaction.followup.send("Select players to award bonuses:", view=view, ephemeral=True)
            await view.wait()
            
            if view.confirmed:
                # Award bonuses in DB
                awarded_players = []
                for name in view.selected:
                    success, message = database.award_player_bonus(name, str(interaction.user.id))
                    if success:
                        awarded_players.append(name)
                
                if awarded_players:
                    await interaction.followup.send(f"✅ Bonuses awarded to: {', '.join(awarded_players)}", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Failed to award bonuses. Please check the logs.", ephemeral=True)
            elif view.cancelled:
                await interaction.followup.send("❌ Bonus awarding cancelled.", ephemeral=True)
            elif view.undo_requested:
                # Implement undo logic if needed
                await interaction.followup.send("↩️ Undo requested - feature coming soon.", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in give_cwl_bonuses: {e}")
            await interaction.followup.send(f"❌ Error awarding bonuses: {e}", ephemeral=True)

    @app_commands.command(
        name="bonus_history_all",
        description="Show bonus history for all players — Admin, Leader, Co-Leader, Elder, Member"
    )
    @app_commands.check(is_admin_leader_co_elder_member)
    @app_commands.guilds(GUILD_ID)
    async def bonus_history_all(self, interaction: discord.Interaction):
        """Show bonus history for all players"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Get player data with bonus history
            players = database.get_player_data()
            
            # Filter players who have received bonuses
            bonus_players = [p for p in players if p.get("bonus_count", 0) > 0]
            
            if not bonus_players:
                await interaction.followup.send("❌ No players found with bonus history.", ephemeral=True)
                return
            
            # Sort by last bonus date (most recent first)
            def sort_key(p):
                last_bonus = p.get("last_bonus_date")
                if last_bonus:
                    try:
                        last_bonus = datetime.strptime(last_bonus, "%Y-%m-%d")
                    except Exception:
                        last_bonus = datetime.min
                else:
                    last_bonus = datetime.min
                return -last_bonus.timestamp() if last_bonus != datetime.min else float('-inf')
            bonus_players.sort(key=sort_key)
            
            # Create embed
            embed = discord.Embed(
                title="🏆 Bonus History - All Players",
                description=f"Players with bonus history (Total: {len(bonus_players)})",
                color=discord.Color.gold()
            )
            
            # Discord embed field limit is 25, so we may need to limit
            max_fields = 22  # Leave room for summary field
            if len(bonus_players) > max_fields:
                bonus_players = bonus_players[:max_fields]
                embed.set_footer(text=f"Showing first {max_fields} players with bonus history")
            
            def format_last_bonus(date_str):
                """Format the last bonus date for display"""
                if not date_str:
                    return "Never"
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    return date_obj.strftime("%b %d, %Y")
                except Exception:
                    return date_str
            
            for player in bonus_players:
                name = player.get("name", "Unknown")
                bonus_count = player.get("bonus_count", 0)
                last_bonus = format_last_bonus(player.get("last_bonus_date"))
                
                # Add field for each player
                embed.add_field(
                    name=f"{name}",
                    value=f"**Bonuses:** {bonus_count}\n**Last:** {last_bonus}",
                    inline=True
                )
            
            # Add summary information
            total_bonuses = sum(p.get("bonus_count", 0) for p in bonus_players)
            embed.add_field(
                name="📊 Summary",
                value=f"**Total Players:** {len(bonus_players)}\n**Total Bonuses Awarded:** {total_bonuses}",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in bonus_history_all: {e}", exc_info=True)
            await interaction.followup.send(f"Error retrieving bonus history: {e}", ephemeral=True)

    @app_commands.command(
        name="on_deck",
        description="Show players currently on deck for bonuses — Admin, Leader, Co-Leader, Elder, Member"
    )
    @app_commands.check(is_admin_leader_co_elder_member)
    @app_commands.guilds(GUILD_ID)
    async def on_deck(self, interaction: discord.Interaction):
        """Show players currently on deck for bonuses"""
        await interaction.response.defer(ephemeral=True)
        try:
            players = database.get_player_data()
            
            # Debug logging to check data
            logger.info(f"Total players retrieved: {len(players)}")
            
            # Log some sample data to debug
            for i, p in enumerate(players[:3]):
                logger.info(f"Player {i}: name={p.get('name')}, join_date={p.get('join_date')}, bonus_count={p.get('bonus_count')}, last_bonus_date={p.get('last_bonus_date')}, bonus_eligibility={p.get('bonus_eligibility')}")
                
                # Test newbie function
                join_date = p.get('join_date')
                if join_date:
                    is_new = is_newbie(str(join_date))
                    days = days_ago(str(join_date))
                    logger.info(f"  join_date={join_date}, is_newbie={is_new}, days_ago={days}")
            
            # Split players into eligible (60+ days) and new members (under 60 days)
            eligible_players = []
            new_members = []
            
            for p in players:
                if not p.get("bonus_eligibility", 0):
                    continue  # Skip ineligible players
                    
                join_date_str = str(p.get("join_date", "")) if p.get("join_date") else ""
                if is_newbie(join_date_str):
                    new_members.append(p)
                else:
                    eligible_players.append(p)

            logger.info(f"Eligible players (60+ days): {len(eligible_players)}")
            logger.info(f"New members (<60 days): {len(new_members)}")

            # Sort eligible players by bonus_count, then last_bonus_date
            def sort_key(p):
                bonus_count = int(p.get("bonus_count", 0) or 0)
                last_bonus = p.get("last_bonus_date")
                if last_bonus:
                    try:
                        # Handle different date formats
                        last_bonus_str = str(last_bonus)
                        if 'T' in last_bonus_str:  # ISO format with time
                            last_bonus = datetime.strptime(last_bonus_str.split('T')[0], "%Y-%m-%d")
                        elif ' ' in last_bonus_str:  # PostgreSQL timestamp format
                            last_bonus = datetime.strptime(last_bonus_str.split(' ')[0], "%Y-%m-%d")
                        else:
                            last_bonus = datetime.strptime(last_bonus_str, "%Y-%m-%d")
                    except Exception as e:
                        logger.warning(f"Date parsing error for {p.get('name')}: {last_bonus} -> {e}")
                        last_bonus = datetime.min
                else:
                    last_bonus = datetime.min
                return (bonus_count, last_bonus)

            eligible_players.sort(key=sort_key)
            
            # Sort new members by join date (oldest first, closest to 60 days)
            def newbie_sort_key(p):
                join_date_str = str(p.get("join_date", "")) if p.get("join_date") else ""
                if join_date_str and join_date_str != "None":
                    try:
                        if 'T' in join_date_str:  # ISO format with time
                            return datetime.strptime(join_date_str.split('T')[0], "%Y-%m-%d")
                        elif ' ' in join_date_str:  # PostgreSQL timestamp format
                            return datetime.strptime(join_date_str.split(' ')[0], "%Y-%m-%d")
                        else:
                            return datetime.strptime(join_date_str, "%Y-%m-%d")
                    except Exception as e:
                        logger.warning(f"Join date parsing error for {p.get('name')}: {join_date_str} -> {e}")
                        return datetime.min
                return datetime.min
            
            new_members.sort(key=newbie_sort_key)

            # Get the groups
            top_5_eligible = eligible_players[:5]
            next_eligible = eligible_players[5:10]  # Next 5 eligible players

            logger.info(f"Top 5 eligible: {[p.get('name') for p in top_5_eligible]}")
            logger.info(f"Next eligible: {[p.get('name') for p in next_eligible]}")
            logger.info(f"New members: {[p.get('name') for p in new_members]}")

            embed = discord.Embed(
                title="🎯 Players On Deck for Bonuses", 
                color=discord.Color.blue(),
                description="Bonus eligibility based on 60+ day membership rule"
            )

            # Section 1: Top 5 On Deck (60+ days)
            if top_5_eligible:
                top_5_text = []
                for p in top_5_eligible:
                    bonus_count = p.get("bonus_count", 0)
                    last_bonus = format_last_bonus(str(p.get("last_bonus_date", "")))
                    top_5_text.append(f"• **{p['name']}** - {bonus_count} bonuses, Last: {last_bonus}")
                
                embed.add_field(
                    name="🏆 Top 5 On Deck",
                    value="\n".join(top_5_text),
                    inline=False,
                )
            
            # Section 2: Next in Line (60+ days)
            if next_eligible:
                next_text = []
                for p in next_eligible:
                    bonus_count = p.get("bonus_count", 0)
                    last_bonus = format_last_bonus(str(p.get("last_bonus_date", "")))
                    next_text.append(f"• **{p['name']}** - {bonus_count} bonuses, Last: {last_bonus}")
                
                embed.add_field(
                    name="⏳ Next in Line (60+ Day Members)",
                    value="\n".join(next_text),
                    inline=False,
                )

            # Section 3: New Members (Under 60 days)
            if new_members:
                new_text = []
                for p in new_members:
                    days_member = days_ago(str(p.get("join_date", "")))
                    bonus_count = p.get("bonus_count", 0)
                    new_text.append(f"• **{p['name']}** - Member for {days_member} days ({bonus_count} bonuses)")
                
                embed.add_field(
                    name="🆕 New Members (Under 60 Days)",
                    value="\n".join(new_text) + "\n\n*New members can be included at leadership discretion*",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="🆕 New Members (Under 60 Days)",
                    value="No new members currently",
                    inline=False,
                )

            # Add footer with explanation
            embed.set_footer(text="60-day rule: Regular rotation includes members 60+ days. New members shown for consideration.")

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error in on_deck: {e}", exc_info=True)
            await interaction.followup.send(f"Error retrieving on deck players: {e}", ephemeral=True)

def member_days(join_date_str):
    """Calculate number of days since player joined"""
    try:
        join_date = datetime.strptime(join_date_str, "%Y-%m-%d")
        return (datetime.utcnow() - join_date).days
    except Exception:
        return "?"

async def setup(bot):
    await bot.add_cog(BonusesCog(bot))
