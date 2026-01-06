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


# Base colors for vague color parsing (HSL-friendly values)
BASE_COLORS = {
    "red": (0, 100, 50),
    "orange": (30, 100, 50),
    "yellow": (60, 100, 50),
    "lime": (90, 100, 50),
    "green": (120, 100, 40),
    "teal": (180, 100, 35),
    "cyan": (180, 100, 50),
    "blue": (210, 100, 50),
    "indigo": (240, 100, 40),
    "purple": (270, 100, 50),
    "violet": (270, 100, 60),
    "magenta": (300, 100, 50),
    "pink": (330, 100, 70),
    "brown": (30, 60, 30),
    "gray": (0, 0, 50),
    "grey": (0, 0, 50),
    "white": (0, 0, 100),
    "black": (0, 0, 0),
}

# Modifiers that adjust HSL values
MODIFIERS = {
    # Lightness modifiers
    "light": {"l_add": 20},
    "pale": {"l_add": 25, "s_mult": 0.6},
    "pastel": {"l_add": 30, "s_mult": 0.5},
    "dark": {"l_add": -25},
    "deep": {"l_add": -20, "s_mult": 1.1},
    # Saturation modifiers
    "bright": {"s_mult": 1.2, "l_add": 5},
    "vivid": {"s_mult": 1.3},
    "muted": {"s_mult": 0.5},
    "dull": {"s_mult": 0.4},
    "soft": {"s_mult": 0.6, "l_add": 10},
    # Combined effects
    "neon": {"s_mult": 1.4, "l_add": 10},
    "electric": {"s_mult": 1.3, "l_add": 5},
    "dusty": {"s_mult": 0.4, "l_add": -5},
    "warm": {"h_add": 15},
    "cool": {"h_add": -15},
}


def hsl_to_rgb(h: float, s: float, l: float) -> tuple[int, int, int]:
    """Convert HSL values to RGB. H is 0-360, S and L are 0-100."""
    h = h % 360
    s = max(0, min(100, s)) / 100
    l = max(0, min(100, l)) / 100

    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2

    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x

    return (
        int((r + m) * 255),
        int((g + m) * 255),
        int((b + m) * 255),
    )


def parse_vague_color(color_input: str) -> int | None:
    """
    Parse vague color descriptions like 'dark red', 'pastel pink', 'light blue'.
    Returns the color as an integer or None if not recognized.
    """
    words = color_input.lower().strip().split()
    if not words:
        return None

    # Find the base color (usually the last word)
    base_color = None
    base_hsl = None
    modifier_words = []

    for i, word in enumerate(words):
        if word in BASE_COLORS:
            base_color = word
            base_hsl = list(BASE_COLORS[word])
            modifier_words = words[:i] + words[i + 1 :]
            break

    if base_hsl is None:
        return None

    # Apply all modifiers
    h, s, l = base_hsl
    for modifier in modifier_words:
        if modifier in MODIFIERS:
            adj = MODIFIERS[modifier]
            h += adj.get("h_add", 0)
            s *= adj.get("s_mult", 1.0)
            l += adj.get("l_add", 0)

    # Clamp values
    h = h % 360
    s = max(0, min(100, s))
    l = max(0, min(100, l))

    # Convert to RGB then to integer
    r, g, b = hsl_to_rgb(h, s, l)
    return (r << 16) | (g << 8) | b


def get_color_from_input(color_input: str) -> tuple[int | None, str]:
    """
    Parse color input and return (color_int, hex_string).
    Tries hex code first, then exact color name, then vague descriptions.
    """
    hex_color = parse_hex_color(color_input)
    if hex_color is not None:
        return hex_color, f"#{hex_color:06X}"

    hex_color = color_name_to_hex(color_input)
    if hex_color is not None:
        return hex_color, f"#{hex_color:06X}"

    hex_color = parse_vague_color(color_input)
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
        description="A hex code, color name, or description (e.g., #FF5733, coral, dark red, pastel pink)",
        required=True,
    ),
):
    """Assign a color role to the user based on their input."""
    await interaction.response.defer(ephemeral=True)

    color_int, hex_string = get_color_from_input(color)

    if color_int is None:
        await interaction.followup.send(
            f"Could not recognize '{color}' as a valid color. "
            "Try a hex code like `#FF5733`, a color name like `coral`, "
            "or a description like `dark red`, `pastel pink`, `light blue`.",
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


@bot.slash_command(name="help", description="Learn how to use the color picker bot")
async def help_command(interaction: nextcord.Interaction):
    """Display help information about the color picker bot."""
    embed = nextcord.Embed(
        title="🎨 Color Wizard Help",
        description="Change your name color with `/pick <color>`!\n\n"
                    "You can specify colors in several ways:",
        color=nextcord.Color.blurple(),
    )

    # Hex codes section
    embed.add_field(
        name="Hex Codes",
        value="Use any 6-digit or 3-digit hex code:\n"
              "`#FF5733` · `#F00` · `A1B2C3`",
        inline=False,
    )

    # Base colors section
    base_color_list = ", ".join(f"`{c}`" for c in sorted(BASE_COLORS.keys()) if c != "grey")
    embed.add_field(
        name="Base Colors",
        value=base_color_list,
        inline=False,
    )

    # Color descriptions
    embed.add_field(
        name="Color Descriptions",
        value="Combine modifiers with base colors for custom shades:",
        inline=False,
    )

    # Lightness modifiers
    embed.add_field(
        name="💡 Lightness",
        value="`light` — brighter\n"
              "`pale` — lighter & softer\n"
              "`pastel` — very light & soft\n"
              "`dark` — darker\n"
              "`deep` — darker & richer",
        inline=True,
    )

    # Saturation modifiers
    embed.add_field(
        name="✨ Saturation",
        value="`bright` — more vibrant\n"
              "`vivid` — very saturated\n"
              "`muted` — less saturated\n"
              "`dull` — very desaturated\n"
              "`soft` — gentle & light",
        inline=True,
    )

    # Special effects
    embed.add_field(
        name="⚡ Special",
        value="`neon` — glowing effect\n"
              "`electric` — intense & bright\n"
              "`dusty` — muted & dark\n"
              "`warm` — shifted warmer\n"
              "`cool` — shifted cooler",
        inline=True,
    )

    # Examples
    embed.add_field(
        name="Examples",
        value="`/pick #FF5733` — hex code\n"
              "`/pick coral` — named color\n"
              "`/pick dark red` — base + modifier\n"
              "`/pick pastel pink` — soft pink\n"
              "`/pick neon green` — bright green",
        inline=False,
    )

    # Footer with tip
    embed.set_footer(text="Tip: The bot also recognizes CSS color names like 'coral', 'salmon', 'teal', etc.")

    await interaction.response.send_message(embed=embed, ephemeral=True)


def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN environment variable is not set!")
        print("Please set it in your .env file or environment.")
        exit(1)

    bot.run(token)


if __name__ == "__main__":
    main()
