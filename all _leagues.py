import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea, QTextEdit, QProgressBar
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from bs4 import BeautifulSoup
import requests

class DataFetcher(QThread):
    progress_update = pyqtSignal(int)
    finished = pyqtSignal(str)

    def __init__(self, league_url):
        super().__init__()
        self.league_url = league_url

    def run(self):
        try:
            response = requests.get(self.league_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                football_matches = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if 'vs' in href:
                        teams = href.split('vs')
                        team1 = teams[0].split('/')[-1].replace('-', ' ').replace('vs', '').title().strip()
                        team2 = teams[1].split('/')[0].replace('-', ' ').title().strip()
                        team1_clean = team1.replace(' Watch', '').replace(' Stream', '').replace(' Online', '').replace('Watch ', '').replace('Champions League', '')
                        team2_clean = team2.replace(' Watch', '').replace(' Stream', '').replace(' Online', '').replace('Watch', '').replace('Champions League', '')
                        football_matches.append(f"{team1_clean} vs {team2_clean}")
                self.finished.emit('\n'.join(football_matches) if football_matches else "No games today")
            else:
                raise ConnectionError("Failed to fetch data from the website.")
        except Exception as e:
            raise

class SportsStreamingApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sports Streams")
        self.setWindowIcon(QIcon('img/soccer-ball.ico'))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        self.create_navbar()
        self.create_scrollable_content()

        self.loader = QProgressBar()
        self.loader.setRange(0, 0)  # Infinite progress bar
        self.loader.hide()
        self.main_layout.addWidget(self.loader)

    def create_navbar(self):
        navbar_layout = QHBoxLayout()

        icons = {
            'Soccer': 'img/soccer-ball.ico',
            'Basketball': 'img/basketball-ball.ico',
            'Tennis': 'img/tennis.ico'
        }

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

        for sport, leagues in sports.items():
            icon_label = QLabel()
            pixmap = QPixmap(icons[sport])
            icon_label.setPixmap(pixmap.scaled(32, 32, Qt.KeepAspectRatio))
            icon_label.setAlignment(Qt.AlignCenter)

            button = QPushButton(sport)
            button.setIcon(QIcon(icons[sport]))
            button.setIconSize(pixmap.rect().size())
            button.setStyleSheet("QPushButton { border: none; background-color: transparent; color: white; } QPushButton:hover { background-color: #34495e; }")
            button.clicked.connect(lambda checked, l=leagues: self.open_sport_streams(l))

            navbar_layout.addWidget(button)

        navbar_widget = QWidget()
        navbar_widget.setLayout(navbar_layout)
        self.main_layout.addWidget(navbar_widget)

    def create_scrollable_content(self):
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.text_area)

        self.main_layout.addWidget(scroll_area)

    def open_sport_streams(self, sport_leagues):
        self.loader.show()  # Show loader before fetching data

        # Fetch data in a separate thread to avoid freezing the UI
        self.fetcher = DataFetcher(next(iter(sport_leagues.values())))
        self.fetcher.finished.connect(self.update_text_area)
        self.fetcher.finished.connect(self.loader.hide)
        self.fetcher.start()

    def update_text_area(self, data):
        self.text_area.setText(data)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SportsStreamingApp()
    window.setStyleSheet("QMainWindow { background-color: #ecf0f1; } QPushButton { border-radius: 5px; padding: 10px; background-color: #2c3e50; color: white; } QPushButton:hover { background-color: #34495e; }")
    window.show()
    sys.exit(app.exec_())
