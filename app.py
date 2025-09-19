
import streamlit as st
from PIL import Image
import random, os, io, time
from dataclasses import dataclass

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
        return f"{Card.values[self.value]} of {Card.suits[self.suit]}"

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
        self.hand = []
        self.is_human = is_human

def card_greater(c1: Card, c2: Card):
    if c1.value > c2.value: return 1
    if c1.value < c2.value: return -1
    suit_strength = {0:4,1:3,2:2,3:1}
    if suit_strength[c1.suit] > suit_strength[c2.suit]: return 1
    if suit_strength[c1.suit] < suit_strength[c2.suit]: return -1
    return 0

def load_card_image(card: Card):
    path = os.path.join(CARDS_DIR, card.filename())
    return Image.open(path).convert("RGBA")

def animate_deal(cards_images, positions, frame_count=12, background_size=(900,500)):
    frames = []
    bg = Image.new("RGBA", background_size, (34,139,34,255))
    start = (background_size[0]//2 - 100, background_size[1]//2 - 150)
    for f in range(frame_count):
        im = bg.copy()
        for idx, img in enumerate(cards_images):
            sx, sy = start
            tx, ty = positions[idx]
            t = (f+1)/frame_count
            cx = int(sx + (tx - sx) * t)
            cy = int(sy + (ty - sy) * t)
            im.paste(img, (cx, cy), img)
        frames.append(im)
    return frames

st.title("4-player Card Game — Streamlit (Animated dealing)")
st.write("One human + 3 computer players. Click **Deal Round** to animate dealing 4 cards and pick winner. Suit priority: Spades > Hearts > Diamonds > Clubs.")

col1, col2 = st.columns([3,1])

with col2:
    if st.button("New Game"):
        st.session_state.deck = Deck()
        st.session_state.p1 = Player("You", is_human=True)
        st.session_state.p2 = Player("AI-1")
        st.session_state.p3 = Player("AI-2")
        st.session_state.p4 = Player("AI-3")
        st.session_state.round = 0
        st.session_state.history = []

    if "deck" not in st.session_state:
        st.session_state.deck = Deck()
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
            players = [st.session_state.p1, st.session_state.p2, st.session_state.p3, st.session_state.p4]
            for p,c in zip(players, cards):
                p.hand.append(c)
            imgs = [load_card_image(c).resize((140,210)) for c in cards]
            W, H = 900, 500
            positions = [
                (W//2 - 70, 40),
                (W - 200, H//2 - 130),
                (W//2 - 70, H - 260),
                (40, H//2 - 130)
            ]
            frames = animate_deal(imgs, positions, frame_count=14, background_size=(W,H))
            anim_slot = st.empty()
            for fr in frames:
                bio = io.BytesIO()
                fr.convert("RGB").save(bio, format="JPEG")
                anim_slot.image(bio.getvalue(), use_container_width=True)
                time.sleep(0.04)
            cols = st.columns(4)
            for i, p in enumerate(players):
                with cols[i]:
                    st.write(f"**{p.name}**")
                    for card in p.hand:
                        st.image(load_card_image(card).resize((80,120)))
            winner = players[0]
            tie = False
            for p in players[1:]:
                cmp = card_greater(p.hand[-1], winner.hand[-1])
                if cmp == 1:
                    winner = p
                    tie = False
                elif cmp == 0:
                    tie = True
            if tie:
                st.info("Round is a tie.")
            else:
                winner.wins += 1
                st.success(f"Round winner: {winner.name}! ({winner.hand[-1]})")
            st.session_state.history.append({
                "round": st.session_state.round,
                "cards": [str(c) for c in cards],
                "winner": winner.name if not tie else "Tie"
            })

    if st.button("Show History"):
        st.json(st.session_state.history)

with col1:
    st.write("Table view:")
    if st.session_state.p1.hand:
        W,H = 900,500
        board = Image.new("RGBA", (W,H), (34,139,34,255))
        positions = [
            (W//2 - 70, 40),
            (W - 200, H//2 - 130),
            (W//2 - 70, H - 260),
            (40, H//2 - 130)
        ]
        last_cards = [p.hand[-1] for p in [st.session_state.p1, st.session_state.p2, st.session_state.p3, st.session_state.p4]]
        for idx, c in enumerate(last_cards):
            if c:
                img = load_card_image(c).resize((140,210))
                board.paste(img, positions[idx], img)
        buf = io.BytesIO()
        board.convert("RGB").save(buf, format="JPEG")
        st.image(buf.getvalue(), use_container_width=True)
    else:
        st.write("No cards dealt yet. Click **Deal Round**.")
