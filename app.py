import streamlit as st
import json
from datetime import datetime
from collections import defaultdict
import os
import base64
from openai import OpenAI
client = OpenAI()

# -----------------------------
# MUST BE FIRST — ONLY ONCE
# -----------------------------


st.set_page_config(
    page_title="Bird Hunt",
    page_icon="🐦",
    layout="wide"
)

# -----------------------------
# Global CSS (background + frame)
# -----------------------------


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKGROUND_PATH = os.path.join(BASE_DIR, "assets", "background3.png")

def set_background(image_path: str):
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    st.markdown(f"""
    <style>
    /* FULL PAGE background — grows with content */
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/png;base64,{encoded}");
        background-size: cover;
        background-position: top center;
        background-repeat: no-repeat;
        min-height: 100vh;
    }}
    </style>
    """, unsafe_allow_html=True)

set_background(BACKGROUND_PATH)

# -----------------------------
# OPEN inner cream card
# -----------------------------

st.markdown("""
<style>
/* Main layout container (full-width, background already handled above) */
[data-testid="stMainBlockContainer"] {
    width: 100vw;
    max-width: none;
    min-height: 100vh;
    padding: 4rem 0 4rem 0;
}

/* ONLY FIRST VERT BLOCK Cream content card — stable, centered, grows with content */
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] { 
    background-color: rgba(255, 255, 240, 0.96);
    border-radius: 28px;

    max-width: 700px;
    margin: 0 auto;

    padding: 3rem 3rem 4.5rem 3rem;

    box-shadow: 0 12px 40px rgba(0,0,0,0.08);
}

/* REMOVE background from ALL nested blocks */
[data-testid="stVerticalBlock"] [data-testid="stVerticalBlock"] {
    background: transparent !important;
    box-shadow: none !important;
    padding: 0 !important;
}


[data-testid="stCaption"] {
    font-size: 1.5rem !important;
    line-height: 1.5;
    background: yellow !important;
    color: #333333;
}

</style>
""", unsafe_allow_html=True)

# This is the container your app lives in
content = st.container()



# -----------------------------
# APP CONTENT (this is what you wrap)
# -----------------------------

st.title("🐦 Bird Hunt")

DEV_MODE = st.sidebar.checkbox(
    "🛠 Dev mode (disable cache)",
    value=True,
    help="Turn ON while developing. Turn OFF for speed."
)

st.markdown(
    """
**Objective:** Spot and log the most unique bird species in NYC each week.  
Rare birds earn more points. The weekly leaderboard resets every Monday.
"""
)

# get the bird picture

def show_bird_image(bird_name: str):

    filename = bird_name.replace(" ", "_") + ".jpg"
    path = os.path.join("images", "birds", filename)
    placeholder_path = os.path.join("images", "birds", "placeholder.jpg")

    if os.path.exists(path):
        st.image(path, width="stretch")
    elif os.path.exists(placeholder_path):
        st.image(placeholder_path, width="stretch")
    else:
        st.caption("🖼️ No image available")

DATA_FILE = "submissions.json"

# -----------------------------
# Bird rarity + points (MVP)
# -----------------------------
# -----------------------------
# Bird rarity + points (MVP)
# -----------------------------

BIRD_POINTS = {

    # -----------------------------
    # DECEMBER BIRD LIST
    # -----------------------------

    # abundant tier
    "House Sparrow": 5,
    "Rock Pigeon": 5,
    "American Robin": 5,
    "European Starling": 5,
    "Mourning Dove": 5,
    "White-throated Sparrow": 5,
    "Canada Goose": 5,
    "Mallard": 5,
    "Ring-billed Gull": 5,
    "Herring Gull": 5,

    # common tier
    "Northern Cardinal": 10,
    "Blue Jay": 10,
    "Tufted Titmouse": 10,
    "Red-tailed Hawk": 10,
    "American Crow": 10,
    "Song Sparrow": 10,
    "House Finch": 10,
    "Dark-eyed Junco": 10,
    "Hermit Thrush": 10,
    "Great Black-backed Gull": 10,
    "Hooded Merganser": 10,

    # uncommon tier
    "Carolina Wren": 15,
    "Red-bellied Woodpecker": 15,
    "Downy Woodpecker": 15,
    "Cooper's Hawk": 15,
    "White-breasted Nuthatch": 15,
    "Yellow-bellied Sapsucker": 15,
    "Gray Catbird": 15,
    "Black-capped Chickadee": 15,
    "Fox Sparrow": 15,
    "Yellow-rumped Warbler": 15,
  

    # occasional tier
    "American Goldfinch": 20,
    "Ruby-crowned Kinglet": 20,
    "Golden-crowned Kinglet": 20,
    "Peregrine Falcon": 20,

    # rare tier
    "Great Horned Owl": 25,
    "Nashville Warbler": 20,

}



TIER_COLORS = {
    "Abundant": "#FF8C00",    # orange
    "Common": "#FFD700",      # yellow
    "Uncommon": "#2E8B57",    # green
    "Occasional": "#1E90FF",  # blue
    "Rare": "#8A2BE2",        # purple
}


# -----------------------------
# Helpers
# -----------------------------


# -----------------------------
# Point tiers
# -----------------------------

TIER_BY_POINTS = {
    5: "Abundant",
    10: "Common",
    15: "Uncommon",
    20: "Occasional",
    25: "Rare",
}

# -----------------------------
# Lifetime medals
# -----------------------------

def compute_lifetime_medals(user):
    if DEV_MODE:
        return _compute_lifetime_medals_uncached(user)
    return _compute_lifetime_medals_cached(user)

def _compute_lifetime_medals_uncached(user):
    data = load_data()

    # group scores by week
    weekly = defaultdict(lambda: defaultdict(int))

    for e in data:
        weekly[e["week"]][e["user"]] += e["points"]

    medals = {"🥇": 0, "🥈": 0, "🥉": 0}

    current = current_week()

    for week, week_scores in weekly.items():
        if week == current:
            continue

        ranked = sorted(
            week_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        for i, (u, _) in enumerate(ranked[:3]):
            if u.lower() == user.lower():
                medals[["🥇", "🥈", "🥉"][i]] += 1

    return medals

@st.cache_data
def _compute_lifetime_medals_cached(user):
    return _compute_lifetime_medals_uncached(user)

# -----------------------------
# Lifetime Stats
# -----------------------------

def compute_lifetime_species(user):
    if DEV_MODE:
        return _compute_lifetime_species_uncached(user)
    return _compute_lifetime_species_cached(user)

def _compute_lifetime_species_uncached(user):
    data = load_data()

    species = {
        "Abundant": set(),
        "Common": set(),
        "Uncommon": set(),
        "Occasional": set(),
        "Rare": set(),
    }

    for e in data:
        if e["user"].lower() != user.lower():
            continue

        tier = TIER_BY_POINTS.get(e["points"])
        if tier:
            species[tier].add(e["bird"])

    return species

@st.cache_data
def _compute_lifetime_species_cached(user):
    return _compute_lifetime_species_uncached(user)


def species_collected_this_week(user):
    if DEV_MODE:
        return _species_collected_this_week_uncached(user)
    return _species_collected_this_week_cached(user)

def _species_collected_this_week_uncached(user):
    week = current_week()
    data = load_data()

    species = {
        entry["bird"]
        for entry in data
        if entry["user"].lower() == user.lower()
        and entry["week"] == week
    }

    return len(species)
@st.cache_data
def _species_collected_this_week_cached(user):
    return _species_collected_this_week_uncached(user)



# -----------------------------
# wikipedia pics
# -----------------------------
def bird_image_url(bird_name):
    name = bird_name.replace(" ", "_")
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{name}.jpg"

# -----------------------------
# This is for the rare bird message
# -----------------------------

def confirm_bird(bird):
    existing_count = count_user_bird_this_week(username, bird)

    if existing_count > 0:
        st.session_state["duplicate_message"] = (
            f"👏 Great job! You've already found **{bird}** this week."
        )
        return

    points = BIRD_POINTS.get(bird, 1)

    entry = {
        "user": username,
        "bird": bird,
        "points": points,
        "week": current_week(),
        "timestamp": datetime.now().isoformat()
    }
    save_entry(entry)

    st.session_state["confirmed"] = {
        "bird": bird,
        "points": points
    }

    st.session_state.pop("suggestions", None)

# -----------------------------
# Avoiding double-counts
# -----------------------------


def count_user_bird_this_week(user, bird):
    week = current_week()
    data = load_data()
    return sum(
        1 for entry in data
        if entry["user"].lower() == user.lower()
        and entry["bird"] == bird
        and entry["week"] == week
    )

BIRD_DESCRIPTIONS = {

    # Abundant Tier

    "House Sparrow": "Small brown-and-gray sparrow commonly found in flocks.",
    "Rock Pigeon": "It's a pigeon.",
    "American Robin": "Brick-red breast, gray-brown back. Medium sized thrush.",
    "European Starling": "Medium sized blackbird with a short tail. Usually seen in groups making a variety of calls.",
    "Mourning Dove": "Looks like a slimmer, more delicate pigeon with a long tail. Makes a soft, sad, \"oo-AH-oo-oo-oo\" call usually heard in the early morning.",
    "White-throated Sparrow": "Larger and cleaner-looking than a house sparrow, with bold black-and-white head stripes and a bright white throat.",
    "Mallard": "Familiar duck often found in city ponds, with males showing a glossy green head and yellow bill and females mottled brown for camouflage.",
    "Ring-billed Gull": "Medium-sized gray-and-white gull. Distinguished by a black ring around their bill.",
    "Herring Gull": "Larger and bulkier than a ring-billed gull. Yellow bills with a red spot on them (hard to see without binoculars), and pink feet.",
    "Canada Goose": "Large, heavy-bodied goose with a long black neck and a bold white chinstrap. Commonly seen grazing on lawns or honking loudly while flying in V-shaped flocks overhead.",

    # Common Tier

    "Northern Cardinal": "Males are bright red and females are warm brown with a little red; both have a thick, bright red-orange bill.",
    "Blue Jay": "Bright blue with bold white and black markings on the face and wings. Known for being noisy - you can easily ID them from their loud \"KEEEEEEER\" call.",
    "Tufted Titmouse": "Small gray bird with a crest and orange side. Very high pitched whistle that sounds like \"peter-peter-peter\" .",
    "Red-tailed Hawk": "A large soaring hawk with broad wings and a brick-red tail. Younger birds lack the red tail, but can be IDed by a band of brown markings on the belly. If you see a big brown and white bird circling, it's probably one of these.",
    "American Crow": "Large black bird, commonly seen in pairs or noisy groups. Gives a familiar \"caw-caw\" call.",
    "Song Sparrow": "Larger and chunkier than a house sparrow, with heavy streaking on the chest and a dark spot in the center. It can look like a messier, browner version of a white-throated sparrow.",
    "House Finch": "Slightly smaller than a sparrow. Males have red on the chest and head, and females are streaky brown.",
    "Dark-eyed Junco": "Looks like the shadow of a sparrow - a small gray bird with a pinkish bill. When flying look for white outer tail feathers.",
    "Hermit Thrush": "A shy brown thrush with a warm reddish tail, often seen hopping on the ground. Looks like a little brown robin.",
    "Great Black-backed Gull": "The largest and bulkiest gull. Dark black back, white head, and thick yellow bill.",
    "Hooded Merganser": "A medium-sized duck with a thin bill, often seen diving for fish in calm water. Males have a striking black-and-white fan-shaped crest, while females are brown with a shaggy reddish crest.",

    # uncommon tier
    "Carolina Wren": "A small, round brown bird with a bold white eyebrow. Known for singing a loud song sounding like \"tea-kettle, tea-kettle, tea-kettle\" .",
    "Red-bellied Woodpecker": "A medium-sized woodpecker with bold black-and-white striped wings and a red cap. Often seen high up in trees.",
    "Downy Woodpecker": "Small, black-and-white woodpecker about the size of a sparrow. It makes a soft \"pik\" call and a quick, light tapping noise on trees.",
    "Cooper's Hawk": "Sleek, medium-sized hawk with a slimmer body and longer tail than a red-tailed hawk. Adults show orange, scaly markings on the chest and bold black bands across the tail.",
    "White-breasted Nuthatch": "Small gray-and-white bird with a black cap. Often seen walking headfirst down tree trunks.",
    "Yellow-bellied Sapsucker": "Black-and-white woodpecker with some red on the head, often spotted by the neat rows of holes it drills in trees.",
    "Gray Catbird": "Looks like a gray robin. Has a call that sounds like a cat's meow.",
    "Black-capped Chickadee": "A tiny, round bird with a black cap and bib and pale cheeks. Curious and energetic, it moves quickly through branches and often comes close to people.",
    "Fox Sparrow": "A large, chunky sparrow with rich reddish-brown coloring and heavy dark spots on the chest. Often seen scratching loudly in leaf litter on the ground.",
    "Yellow-rumped Warbler": "A small gray-and-yellow songbird with a bright yellow patch on its lower back above the tail.",


   # occasional tier
    "American Goldfinch": "Males are bright yellow in summer, but by this time both males and females are pale brown with darker wings and subtle yellow hints along with a small, conical orange-pink bill.",
    "Ruby-crowned Kinglet": "Tiny, fast-moving olive-green bird that flicks its wings as it hops through trees. The red crown is usually hidden and rarely seen.",
    "Golden-crowned Kinglet": "Tiny, fast-moving olive-green bird with a bold yellow-and-black stripe on its head.",
    "Peregrine Falcon": "A sleek, powerful falcon with a blue-gray back, pale chest, and bold dark markings on the face. Famous for incredible speed, it is often seen perched high on buildings or diving sharply after birds in flight.",

   # rare tier
    "Great Horned Owl": "Large, powerful owl with prominent ear tufts and bright yellow eyes, often heard more than seen",
    "Nashville Warbler": "Small bird that looks gray on top and yellow underneath, with a faint eye ring. It’s often seen high up in trees and can be hard to spot without binoculars.",

}

# -----------------------------
# The AI ornithologist
# -----------------------------


def identify_bird(description):
    if DEV_MODE:
        return _identify_bird_uncached(description)
    return _identify_bird_cached(description)


def _identify_bird_uncached(description):
    bird_list = list(BIRD_POINTS.keys())

    prompt = f"""
You are an expert ornithologist specializing in birds found in Central Park, NYC.

A user described a bird as:
"{description}"

# -----------------------------
# Updated to draw from the list
# -----------------------------


You MUST choose ONLY from the following list of birds:
{bird_list}

Task:
- Select the TOP 3 most likely birds from the list above
- Assign a confidence score (0–1) to each
- Confidence values do NOT need to sum to 1
- Do NOT invent new bird names
- Respond with ONLY valid JSON
- No explanations, no markdown

JSON format:

[
  {{"bird": "Bird Name from list", "confidence": 0.6}},
  {{"bird": "Bird Name from list", "confidence": 0.3}},
  {{"bird": "Bird Name from list", "confidence": 0.1}}
]
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You strictly output JSON and only use provided bird names."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0
    )

    content = response.choices[0].message.content.strip()

    try:
        raw_suggestions = json.loads(content)
    except json.JSONDecodeError:
        return None

    allowed_birds = set(BIRD_POINTS.keys())

# Filter out any birds not in our official list
    suggestions = [
        s for s in raw_suggestions
        if s.get("bird") in allowed_birds
]

    if not suggestions:
        return None

    # -----------------------------
    # Heuristic filters (domain logic)
    # -----------------------------


    description_lower = description.lower()

    if "gull" in description_lower or "seagull" in description_lower:
        gulls = {
            "Ring-billed Gull",
            "Herring Gull",
            "Great Black-backed Gull"
        }
        filtered = [s for s in suggestions if s["bird"] in gulls]
        if filtered:
            suggestions = filtered


    # Normalize confidences
    total = sum(s["confidence"] for s in suggestions if s["confidence"] > 0)
    if total > 0:
        for s in suggestions:
            s["confidence"] /= total

    return suggestions

@st.cache_data(show_spinner=False)
def _identify_bird_cached(description):
    return _identify_bird_uncached(description)





def load_data():
    if DEV_MODE:
        return _load_data_uncached()
    return _load_data_cached()


def _load_data_uncached():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


@st.cache_data
def _load_data_cached():
    return _load_data_uncached()

def save_entry(entry):
    data = load_data()
    data.append(entry)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# 🔥 invalidate cached data
    st.cache_data.clear()



def current_week():
    return datetime.now().isocalendar().week

# -----------------------------
# Username
# -----------------------------
raw_username = st.text_input("Username")
username = raw_username.strip().lower()

if not username:
    st.stop()

if "selected_user" not in st.session_state:
    st.session_state["selected_user"] = None


# -----------------------------
# Main menu
# -----------------------------

if "_navigate_to" in st.session_state:
    st.session_state["choice"] = st.session_state.pop("_navigate_to")

choice = st.radio(
    "Choose an option", ["📝 Submit Bird", "🏆 Leaderboard", "📚 Lifetime Stats"],
    key="choice")

# =============================
# SUBMIT BIRD
# =============================
if choice == "📝 Submit Bird":
    st.subheader("Submit a Bird")
    count = species_collected_this_week(username)
    st.metric(
        label="Species collected this week",
        value=count
    )


    if "duplicate_message" in st.session_state:
        st.info(st.session_state["duplicate_message"])
        del st.session_state["duplicate_message"]

    if "confirmed" in st.session_state:
            c = st.session_state["confirmed"]
            st.success(f"Recorded! +{c['points']} points for {c['bird']}")


    # 🎉 Rarity reactions
            if c["points"] == 20:
                st.info("🎉 Congrats! This species is hard to find right now.")
                st.balloons()

            elif c["points"] == 25:
                st.info("🔥 Wow! This is a rare sighting.")
                st.balloons()

# ✅ CLEAR AFTER DISPLAY
            del st.session_state["confirmed"]


    description = st.text_area(
        "Describe the bird you saw",
        placeholder="Size, color, behavior, location in Central Park..."
    )

    if st.button("🔍 Identify bird"):
        if not description:
            st.warning("Please describe the bird first.")
        else:
            with st.spinner("Identifying bird..."):
                suggestions = identify_bird(description)
                st.session_state["suggestions"] = suggestions

if choice == "📝 Submit Bird" and "suggestions" in st.session_state:
    st.markdown("### Likely birds")
    st.caption(
        "Not seeing the right bird? Try adding size, behavior, or movement details. Click on the images to expand them for a better view."
    )

    for s in st.session_state["suggestions"]:
        bird = s["bird"]
        confidence = int(s["confidence"] * 100)

        with st.container():
            col1, col2 = st.columns([1, 2], vertical_alignment="top")

            with col1:
                show_bird_image(bird)

            with col2:

                st.markdown(f"### {bird}")

                st.markdown(
                    f"<div class='bird-desc'>{BIRD_DESCRIPTIONS.get(bird, 'No description available yet.')}</div>",
                    unsafe_allow_html=True
                )
   
                st.button(
                    "Yes — this is my bird",
                    key=f"confirm_{bird}",
                    on_click=confirm_bird,
                    args=(bird,)
                 )

        st.divider()

# =============================
# LEADERBOARD
# =============================
if choice == "🏆 Leaderboard":
    st.subheader("🏆 Leaderboard")



    data = load_data()

    weekly_scores = defaultdict(int)
    lifetime_scores = defaultdict(int)

    for entry in data:
        lifetime_scores[entry["user"]] += entry["points"]
        if entry["week"] == current_week():
            weekly_scores[entry["user"]] += entry["points"]

    st.markdown("### This Week")
    if weekly_scores:

        sorted_weekly = sorted(
            weekly_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        medals = ["🥇", "🥈", "🥉"]

        for i, (user, score) in enumerate(sorted_weekly, start=1):
            medal = medals[i - 1] if i <= 3 else ""
            if st.button(
                f"{i}. {medal} {user} — {score} pts",
                key=f"lb_{user}"
            ):
                st.session_state["selected_user"] = user
                st.session_state["_navigate_to"] = "📚 Lifetime Stats"
                st.rerun()
    else:
        st.write("No submissions yet this week.")

# =============================
# LIFETIME STATS
# =============================

view_user = st.session_state.get("selected_user") or username

if choice == "📚 Lifetime Stats":
    view_user = st.session_state.get("selected_user") or username

    st.subheader(f"📚 Lifetime Stats — {view_user}")

    # 🏅 Medals
    medals = compute_lifetime_medals(view_user)

    st.markdown("### 🏅 Lifetime Medals")
    st.write(
        f"🥇 {medals['🥇']}   "
        f"🥈 {medals['🥈']}   "
        f"🥉 {medals['🥉']}"
    )

    # 🐦 Species
    species = compute_lifetime_species(view_user)
    total = sum(len(v) for v in species.values())

    st.markdown(f"### 🐦 Species Collected ({total} total)")

    for tier, birds in species.items():
        if not birds:
            continue

        color = TIER_COLORS.get(tier, "#000000")

        st.markdown(
            f"<h4 style='color:{color}; margin-bottom:0.2em;'>"
            f"{tier} ({len(birds)})"
            f"</h4>",
            unsafe_allow_html=True
        )

        for b in sorted(birds):
            st.write(f"• {b}")

    # 🔙 Back button (only when viewing someone else)
    if st.session_state.get("selected_user"):
        if st.button("← Back to my stats"):
            st.session_state["selected_user"] = None

