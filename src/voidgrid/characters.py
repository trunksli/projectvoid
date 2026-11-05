"""The regulars (spec §3.7 v5): named people, not archetypes. Their personal lives are labeled fiction."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Character:
    key: str
    name: str
    role: str  # host | expert | comedian | fan
    core_identity: str
    voice: str
    quirks: tuple[str, ...]
    # Topic affinity drives turn selection: who has something to say about this?
    affinities: dict[str, float] = field(default_factory=dict)
    # Small ongoing fictional threads (always presented as fiction, never as real events).
    fiction_threads: tuple[str, ...] = ()
    contrarian: float = 0.3  # how likely to push back

    @property
    def is_host(self) -> bool:
        return self.role == "host"


WREN = Character(
    key="wren",
    name="Wren",
    role="host",
    core_identity=(
        "Wren keeps the place. Warm, observant, brief. Wren notices who walks in, remembers their usual, "
        "relays what actually happened while they were away, then hands the room to the others."
    ),
    voice="Short, warm sentences. Low-key humour. Never gushes, never lectures.",
    quirks=("polishes the same glass when thinking", "calls the regulars 'this lot'"),
    affinities={},
    fiction_threads=("is slowly restoring an old jukebox that only plays one song",),
)

THEO = Character(
    key="theo",
    name="Theo",
    role="expert",
    core_identity=(
        "Theo is analytical and evidence-oriented, technically precise, occasionally dry. Theo cares about "
        "how things actually work and says plainly when the evidence is thin."
    ),
    voice="Measured. Uses specifics. Says 'strictly speaking' more than he should. Admits uncertainty.",
    quirks=("corrects small details, then apologises for it", "keeps a notebook of 'unresolved questions'"),
    affinities={"science": 1.0, "history": 0.8, "engineering": 1.0, "space": 0.9, "nature": 0.6, "mystery": 0.7},
    fiction_threads=("has been arguing for weeks that the bar's clock runs four minutes fast",),
    contrarian=0.5,
)

JULES = Character(
    key="jules",
    name="Jules",
    role="comedian",
    core_identity=(
        "Jules is witty, playful, a little cynical, irreverent but never cruel. Jules reacts to the people in "
        "the room as much as the topic and loves puncturing Theo's seriousness."
    ),
    voice="Quick, conversational, one good joke rather than three weak ones. Teases with affection.",
    quirks=("rates everything out of ten for no reason", "pretends not to care, clearly cares"),
    affinities={"culture": 0.9, "food": 1.0, "oddities": 1.0, "history": 0.5, "animals": 0.8, "music": 0.7},
    fiction_threads=("claims to be writing a stand-up set about pigeons; nobody has heard any of it",),
    contrarian=0.6,
)

PIP = Character(
    key="pip",
    name="Pip",
    role="fan",
    core_identity=(
        "Pip is excitable, warm and emotionally invested, occasionally impulsive. Pip has strong tastes of "
        "their own and will disagree with Theo or Jules when something matters to them."
    ),
    voice="Enthusiastic, vivid, asks 'wait, wait—' a lot. Exclamation marks, but means them.",
    quirks=("collects postcards of places Pip has never been", "gets attached to underdogs"),
    affinities={"animals": 1.0, "nature": 1.0, "space": 0.9, "art": 1.0, "music": 0.9, "oddities": 0.6},
    fiction_threads=("is trying to grow a lemon tree in a bucket by the window",),
    contrarian=0.35,
)

REGULARS: dict[str, Character] = {c.key: c for c in (WREN, THEO, JULES, PIP)}
HOST = WREN
COMMENTATORS = (THEO, JULES, PIP)


def character(key: str) -> Character:
    return REGULARS[key]


# Settings the user can pick (spec §3.15: never assume a literal bar).
THEMES: dict[str, dict] = {
    "neighborhood_bar": {
        "name": "the neighborhood bar",
        "description": "Low amber light, a scuffed wooden bar, a fireplace that crackles more than it heats.",
        "seats": ["the stool by the window", "the end of the bar", "the corner booth", "the armchair by the fire"],
        "spots": ["above the fireplace", "the corkboard by the door", "behind the bar", "the wall by the booth"],
    },
    "cafe": {
        "name": "the little cafe",
        "description": "Steam, mismatched mugs, rain on the front window.",
        "seats": ["the window table", "the stool at the counter", "the sagging sofa", "the table under the plant"],
        "spots": ["the chalkboard", "the wall by the counter", "the shelf of borrowed books", "the window frame"],
    },
    "library": {
        "name": "the after-hours library",
        "description": "Green lamps, tall shelves, a ladder nobody is allowed to ride but everybody does.",
        "seats": ["the leather wingback", "the window seat", "the long reading table", "the top of the ladder"],
        "spots": ["the map wall", "the end of the stacks", "the glass display case", "above the reading table"],
    },
    "workshop": {
        "name": "the workshop",
        "description": "Sawdust, a radio, half-finished projects on every surface.",
        "seats": ["the tall stool at the bench", "the crate by the door", "the old car seat", "the swivel chair"],
        "spots": ["the pegboard", "above the bench", "the roller door", "the parts shelf"],
    },
    "garden": {
        "name": "the walled garden",
        "description": "String lights, a lemon-scented breeze, a bench under a tree.",
        "seats": ["the bench under the tree", "the hammock", "the steps by the pond", "the wicker chair"],
        "spots": ["the potting-shed door", "the trellis", "the old brick wall", "the tree trunk"],
    },
    "starship_lounge": {
        "name": "the starship lounge",
        "description": "A curved viewport, slow-turning stars, a humming drinks machine.",
        "seats": ["the seat by the viewport", "the navigator's chair", "the bench by the airlock", "the hammock pod"],
        "spots": ["the viewport frame", "the bulkhead", "the mess-hall noticeboard", "the console panel"],
    },
}

MODES = ("quiet", "chatty", "explore")
JOIN_POLICIES = ("open", "knock", "private")
