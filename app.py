
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import random, os, io, time
from dataclasses import dataclass
from typing import List, Optional

st.set_page_config(layout="wide", page_title="4-player Card Game (Streamlit)")

CARDS_DIR = os.path.join(os.path.dirname(__file__), "cards")

@dataclass(order=True)
class Card:
    value: int
    suit: int

    suits = ("Spades", "Hearts", "Diamonds", "Clubs")
    values = (None, None, "2", "3", "4", "5", "6", "7", "8", "9", "10",
              "Jack", "Queen", "King", "Ace")

    def filename(self):
        return f"{self.value}_{self.suit}.png"

    def __str__(self):
        return f\"{Card.values[self.value]} of {Card.suits[self.suit]}\"

class Deck:
    def __init__(self):
        self.cards = [Card(v,s) for v in range(2,15) for s in range(4)]
        random.shuffle(self.cards)

    def rm_card(self):
        return self.cards.pop() if self.cards else None

class Player:
    def __init__(self, name, is_human=False):
        self.name = name
        self.wins = 0
        self.card = None
        self.is_human = is_human

def card_greater(c1: Card, c2: Card):
    if c1.value > c2.value: return 1
    if c1.value < c2.value: return -1
    suit_strength = {0:4,1:3,2:2,3:1}
    if suit_strength[c1.suit] > suit_strength[c2.suit]: return 1
    if suit_strength[c1.suit] < suit_strength[c2.suit]: return -1
    return 0

# helper to load card image
def load_card_image(card: Card):
    path = os.path.join(CARDS_DIR, card.filename())
    return Image.open(path).convert("RGBA")

# create animation frames for dealing cards from deck center to player positions
def animate_deal(cards_images, positions, frame_count=12, background_size=(900,400)):
    frames = []
    bg = Image.new("RGBA", background_size, (34,139,34,255))  # table green
    # start positions (deck center)
    start = (background_size[0]//2 - 100, background_size[1]//2 - 150)
    for f in range(frame_count):
        im = bg.copy()
        for idx, img in enumerate(cards_images):
            sx, sy = start
            tx, ty = positions[idx]
            # linear interpolation
            t = (f+1)/frame_count
            cx = int(sx + (tx - sx) * t)
            cy = int(sy + (ty - sy) * t)
            im.paste(img, (cx, cy), img)
        frames.append(im)
    return frames

# layout
st.title("4-player Card Game — Streamlit (Animated dealing)")
st.write("One human player + 3 computer players. Click **Deal Round** to animate dealing 4 cards and pick the round winner. Tie broken by suit order: Spades > Hearts > Diamonds > Clubs.")

col1, col2 = st.columns([3,1])

with col2:
    if "game_state" not in st.session_state:
        st.session_state.game_state = None
    if st.button("New Game"):
        st.session_state.deck = None
        st.session_state.p1 = None
        st.session_state.p2 = None
        st.session_state.p3 = None
        st.session_state.p4 = None
        st.session_state.round = 0
        st.session_state.history = []
    if "deck" not in st.session_state or st.session_state.deck is None:
        deck = Deck()
        st.session_state.deck = deck
        st.session_state.p1 = Player("You", is_human=True)
        st.session_state.p2 = Player("AI-1")
        st.session_state.p3 = Player("AI-2")
        st.session_state.p4 = Player("AI-3")
        st.session_state.round = 0
        st.session_state.history = []
    st.write(f"Rounds played: {st.session_state.round}")
    st.write("Scores:")
    st.write(f"You: {st.session_state.p1.wins} | AI-1: {st.session_state.p2.wins} | AI-2: {st.session_state.p3.wins} | AI-3: {st.session_state.p4.wins}")
    if st.button("Deal Round"):
        # Draw four cards
        cards = []
        for _ in range(4):
            c = st.session_state.deck.rm_card()
            if c is None:
                st.warning("Deck exhausted. Start a new game.")
                cards = []
                break
            cards.append(c)
        if cards:
            st.session_state.round += 1
            # assign cards to players in order p1..p4
            players = [st.session_state.p1, st.session_state.p2, st.session_state.p3, st.session_state.p4]
            for p,c in zip(players, cards):
                p.card = c
            # prepare images
            imgs = [load_card_image(c).resize((140,210)) for c in cards]
            # target positions on canvas
            # positions correspond to player order: top (AI-1), right(AI-2), bottom(you), left(AI-3)
            W, H = 900, 400
            positions = [
                (W//2 - 70, 20),               # top center
                (W - 170, H//2 - 105),         # right
                (W//2 - 70, H - 230),          # bottom center (you)
                (20, H//2 - 105)               # left
            ]
            frames = animate_deal(imgs, positions, frame_count=14, background_size=(W,H))
            # display animation by streaming frames
            anim_slot = st.empty()
            for fr in frames:
                bio = io.BytesIO()
                fr.convert("RGB").save(bio, format="JPEG")
                anim_slot.image(bio.getvalue(), use_column_width=True)
                time.sleep(0.04)
            # show final dealt state and announce winner
            cols = st.columns(4)
            for i, p in enumerate(players):
                with cols[i]:
                    st.image(load_card_image(p.card).resize((160,240)))
                    st.write(f"**{p.name}**")
                    st.write(str(p.card))
            # determine winner
            winner = players[0]
            tie = False
            for p in players[1:]:
                cmp = card_greater(p.card, winner.card)
                if cmp == 1:
                    winner = p
                    tie = False
                elif cmp == 0:
                    # exact tie (rare unless same card) treat as tie
                    tie = True
            if tie:
                st.info("Round is a tie.")
            else:
                winner.wins += 1
                st.success(f"Round winner: {winner.name}! ({winner.card})")
            # save history
            st.session_state.history.append({
                "round": st.session_state.round,
                "cards": [str(c) for c in cards],
                "winner": winner.name if not tie else "Tie"
            })
    if st.button("Show History"):
        st.json(st.session_state.history)

with col1:
    st.image(os.path.join(CARDS_DIR, "14_0.png") if os.path.exists(os.path.join(CARDS_DIR, "14_0.png")) else None, width=180)
    st.write("Table view:")
    # draw a static table showing last dealt cards if exist
    if "p1" in st.session_state and st.session_state.p1 and st.session_state.p1.card:
        last = [st.session_state.p1, st.session_state.p2, st.session_state.p3, st.session_state.p4]
        board = Image.new("RGBA", (900,400), (34,139,34,255))
        positions = [(W//2 - 70, 20),(W - 170, H//2 - 105),(W//2 - 70, H - 230),(20, H//2 - 105)]
        for idx, p in enumerate(last):
            if p.card:
                img = load_card_image(p.card).resize((140,210))
                board.paste(img, positions[idx], img)
        buf = io.BytesIO()
        board.convert("RGB").save(buf, format="JPEG")
        st.image(buf.getvalue(), use_column_width=True)
    else:
        st.write("No cards dealt yet. Click **Deal Round**.")
