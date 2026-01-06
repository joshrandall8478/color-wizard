import os
import re
import nextcord
from nextcord.ext import commands
from nextcord import SlashOption
import webcolors


def parse_hex_color(color_input: str) -> int | None:
    """Parse a hex color string and return it as an integer."""
    color_input = color_input.strip().lstrip("#")

    if re.match(r"^[0-9A-Fa-f]{6}$", color_input):
        return int(color_input, 16)

    if re.match(r"^[0-9A-Fa-f]{3}$", color_input):
        expanded = "".join(c * 2 for c in color_input)
        return int(expanded, 16)

    return None


def color_name_to_hex(color_name: str) -> int | None:
    """Convert a color name to hex integer using webcolors library."""
    try:
        hex_value = webcolors.name_to_hex(color_name.lower().strip())
        return int(hex_value.lstrip("#"), 16)
    except ValueError:
        return None


def get_color_from_input(color_input: str) -> tuple[int | None, str]:
    """
    Parse color input and return (color_int, hex_string).
    Tries hex code first, then color name.
    """
    hex_color = parse_hex_color(color_input)
    if hex_color is not None:
        return hex_color, f"#{hex_color:06X}"

    hex_color = color_name_to_hex(color_input)
    if hex_color is not None:
        return hex_color, f"#{hex_color:06X}"

    return None, ""


def get_role_name(hex_string: str) -> str:
    """Generate a role name from a hex color string."""
    return f"color-{hex_string.lstrip('#').upper()}"


class ColorBot(commands.Bot):
    def __init__(self):
        intents = nextcord.Intents.default()
        intents.members = True
        intents.guilds = True
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f"Bot is ready! Logged in as {self.user}")
        print(f"Connected to {len(self.guilds)} guild(s)")


bot = ColorBot()


@bot.slash_command(name="pick", description="Pick a color for your name!")
async def pick_color(
    interaction: nextcord.Interaction,
    color: str = SlashOption(
        name="color",
        description="A hex code (e.g., #FF5733) or color name (e.g., red, blue, coral)",
        required=True,
    ),
):
    """Assign a color role to the user based on their input."""
    await interaction.response.defer(ephemeral=True)

    color_int, hex_string = get_color_from_input(color)

    if color_int is None:
        await interaction.followup.send(
            f"Could not recognize '{color}' as a valid color. "
            "Try a hex code like `#FF5733` or a color name like `red`, `blue`, `coral`, etc.",
            ephemeral=True,
        )
        return

    guild = interaction.guild
    if guild is None:
        await interaction.followup.send(
            "This command can only be used in a server.",
            ephemeral=True,
        )
        return

    member = interaction.user
    if not isinstance(member, nextcord.Member):
        await interaction.followup.send(
            "Could not retrieve your member information.",
            ephemeral=True,
        )
        return

    role_name = get_role_name(hex_string)
    discord_color = nextcord.Color(color_int)

    existing_role = nextcord.utils.get(guild.roles, name=role_name)

    if existing_role is None:
        try:
            existing_role = await guild.create_role(
                name=role_name,
                color=discord_color,
                reason=f"Color role created by {member.display_name}",
            )
            print(f"Created new role: {role_name}")
        except nextcord.Forbidden:
            await interaction.followup.send(
                "I don't have permission to create roles. "
                "Please make sure I have the 'Manage Roles' permission.",
                ephemeral=True,
            )
            return
        except nextcord.HTTPException as e:
            await interaction.followup.send(
                f"Failed to create role: {e}",
                ephemeral=True,
            )
            return

    # Remove any existing color roles from the user
    color_roles_to_remove = [
        role for role in member.roles
        if role.name.startswith("color-") and role.name != role_name
    ]

    try:
        if color_roles_to_remove:
            await member.remove_roles(*color_roles_to_remove, reason="Switching color")

        if existing_role not in member.roles:
            await member.add_roles(existing_role, reason="Color picked by user")
    except nextcord.Forbidden:
        await interaction.followup.send(
            "I don't have permission to manage your roles. "
            "Please make sure my role is above the color roles.",
            ephemeral=True,
        )
        return
    except nextcord.HTTPException as e:
        await interaction.followup.send(
            f"Failed to assign role: {e}",
            ephemeral=True,
        )
        return

    # Create an embed to show the color
    embed = nextcord.Embed(
        title="Color Applied!",
        description=f"Your name color has been set to **{hex_string}**",
        color=discord_color,
    )
    embed.add_field(name="Input", value=color, inline=True)
    embed.add_field(name="Hex Code", value=hex_string, inline=True)
    embed.add_field(name="Role", value=role_name, inline=True)

    await interaction.followup.send(embed=embed, ephemeral=True)


def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN environment variable is not set!")
        print("Please set it in your .env file or environment.")
        exit(1)

    bot.run(token)


if __name__ == "__main__":
    main()
