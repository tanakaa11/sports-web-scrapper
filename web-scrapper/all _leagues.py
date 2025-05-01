import customtkinter as ctk
from bs4 import BeautifulSoup
import requests
import webbrowser
from PIL import Image, ImageDraw
from customtkinter import CTkImage
import platform
import threading
from urllib.parse import urljoin
from queue import Queue

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Constants
TEXT_COLOR = "#FFFFFF"
BUTTON_COLOR = "#3B3B3B"
HOVER_COLOR = "#4A4A4A"
ACCENT_COLOR = "#1F6AA5"
FONT = ("Arial", 14)
TITLE_FONT = ("Arial", 16, "bold")

sports = {
    'Soccer': {
        'EPL': 'https://socceronline.me/epl-streams',
        'Serie A': 'https://socceronline.me/serie-a-streams',
        'Bundesliga': 'https://socceronline.me/bundesliga-streams',
        'La Liga': 'https://socceronline.me/la-liga-streams',
        'French Ligue 1': 'https://socceronline.me/ligue-1-streams',
        'UEFA Champions League': 'https://socceronline.me/uefa-champions-league-streams'
    },
    'Basketball': {
        'NBA': 'https://nbabox.me/watch-nba-streams',
        'EuroLeague': 'https://nbabox.me/watch-euroleague-streams'
    },
    'Tennis': {
        'Wimbledon': 'https://tennisonline.me/wimbledon-online-stream',
        'US Open': 'https://tennisonline.me/us-open-online-stream'
    }
}


class Loader:
    def __init__(self, parent):
        self.frame = ctk.CTkFrame(parent)
        self.label = ctk.CTkLabel(self.frame, text="Loading", font=TITLE_FONT)
        self.label.pack(pady=10)
        self.dots = 0
        self.animation_active = False

    def start(self):
        self.frame.pack(pady=20)
        self.animation_active = True
        self.animate()

    def stop(self):
        self.animation_active = False
        self.frame.pack_forget()

    def animate(self):
        if self.animation_active:
            self.dots = (self.dots + 1) % 4
            self.label.configure(text=f"Loading{'.' * self.dots}")
            self.frame.after(500, self.animate)


class SportsStreamsApp:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("Sports Streams")
        self.cache = {}
        self.queue = Queue()
        self.loader = None
        self.bg_image = None
        self.current_gradient_size = (0, 0)

        self.is_mobile = platform.system() in ["Android", "iOS"]
        self.width = 360 if self.is_mobile else 800
        self.height = 640 if self.is_mobile else 600
        self.app.geometry(f"{self.width}x{self.height}")

        self.create_navbar()
        self.create_content_frame()
        self.create_gradient_background()  # ← moved here
        self.check_queue()

    def create_gradient_background(self):
        width = self.app.winfo_width() or self.width
        height = self.app.winfo_height() or self.height

        width = min(width, 1920)
        height = min(height, 1080)

        if abs(self.current_gradient_size[0] - width) < 100 and \
           abs(self.current_gradient_size[1] - height) < 100:
            return

        try:
            gradient = Image.new('RGB', (256, 256), color=(0, 0, 0))
            draw = ImageDraw.Draw(gradient)

            for y in range(256):
                r = int((0x1F * (256 - y) + 0x2E * y) / 256)
                g = int((0x3B * (256 - y) + 0x2E * y) / 256)
                b = int((0x4D * (256 - y) + 0x2E * y) / 256)
                draw.line([(0, y), (256, y)], fill=(r, g, b))

            gradient = gradient.resize((width, height), Image.Resampling.LANCZOS)

            if self.bg_image:
                self.bg_label.configure(image=None)
                self.bg_image = None

            self.bg_image = ctk.CTkImage(light_image=gradient, size=(width, height))
            self.current_gradient_size = (width, height)

            if not hasattr(self, 'bg_label'):
                self.bg_label = ctk.CTkLabel(self.app, image=self.bg_image, text="")
                self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            else:
                self.bg_label.configure(image=self.bg_image)

            self.nav.lift()
            self.content_frame.lift()

        except Exception as e:
            print(f"Error creating gradient: {e}")
            self.app.configure(fg_color="#2E2E2E")

    def create_navbar(self):
        self.nav = ctk.CTkFrame(self.app, height=60, fg_color=BUTTON_COLOR)
        self.nav.pack(side="top", fill="x", pady=5, padx=5)
        self.nav.lift()

        icons = {
            'Soccer': 'img/soccer-ball.ico',
            'Basketball': 'img/basketball-ball.ico',
            'Tennis': 'img/tennis.ico'
        }

        for sport, leagues in sports.items():
            try:
                icon_img = CTkImage(Image.open(icons[sport]), size=(24, 24))
            except Exception:
                icon_img = None

            btn = ctk.CTkButton(
                self.nav,
                text=sport,
                image=icon_img,
                compound="left",
                command=lambda l=leagues: self.on_sport_click(l),
                width=120,
                height=40,
                fg_color=BUTTON_COLOR,
                hover_color=HOVER_COLOR,
                font=FONT
            )
            btn.image = icon_img
            btn.pack(side="left", padx=5, pady=5)

    def create_content_frame(self):
        self.content_frame = ctk.CTkScrollableFrame(
            self.app,
            width=self.width - 20,
            height=self.height - 80,
            fg_color="transparent"
        )
        self.content_frame.pack(padx=10, pady=(5, 10), fill="both", expand=True)
        self.content_frame.lift()

    def on_sport_click(self, leagues):
        self.clear_content()
        self.loader = Loader(self.content_frame)
        self.loader.start()

        threading.Thread(
            target=self.fetch_leagues_data,
            args=(leagues,),
            daemon=True
        ).start()

    def fetch_leagues_data(self, leagues):
        results = []
        for league_name, url in leagues.items():
            if url in self.cache:
                results.append((league_name, self.cache[url]))
            else:
                games = self.scrape_streams(url)
                self.cache[url] = games
                results.append((league_name, games))
        self.queue.put(results)

    def scrape_streams(self, url):
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            matches = []

            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'vs' in href.lower():
                    full_url = urljoin(url, href)
                    parts = href.split('/')[-1].replace('-', ' ').split('vs')
                    if len(parts) < 2:
                        continue
                    team1 = parts[0].strip().title()
                    team2 = parts[1].strip().title()
                    matches.append((f"{team1} vs {team2}", full_url))

            return matches if matches else [("No games available", None)]
        except Exception as e:
            return [(f"Error: {str(e)}", None)]

    def update_content(self, results):
        self.loader.stop()
        self.clear_content()

        for league_name, games in results:
            league_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            league_frame.pack(fill="x", pady=5, padx=5)

            ctk.CTkLabel(
                league_frame,
                text=f"{league_name}:",
                font=TITLE_FONT,
                text_color=ACCENT_COLOR
            ).pack(anchor="w", pady=(0, 5))

            for game_name, url in games:
                game_label = ctk.CTkLabel(
                    league_frame,
                    text=game_name,
                    font=FONT,
                    text_color=TEXT_COLOR,
                    cursor="hand2" if url else "arrow"
                )
                game_label.pack(anchor="w", padx=10, pady=2)

                if url:
                    game_label.configure(text_color="#1E90FF")
                    game_label.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def check_queue(self):
        while not self.queue.empty():
            results = self.queue.get()
            self.app.after(0, self.update_content, results)
        self.app.after(100, self.check_queue)

    def on_window_resize(self, event):
        self.create_gradient_background()

    def run(self):
        self.app.bind("<Configure>", self.on_window_resize)
        self.app.mainloop()


if __name__ == "__main__":
    app = SportsStreamsApp()
    app.run()
