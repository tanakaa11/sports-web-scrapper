from bs4 import BeautifulSoup
import requests
import webbrowser
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk  # Import PIL for image handling

# Define global variables
active_button_index = None  # Variable to track the index of the active button
buttons = []  # List to store button references

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
}  # Specify the sports, leagues, and their URLs you want to scrape

all_labels = {}

# Function to scrape football game URLs from different leagues
def scrape_football_streams(league_url, frame):
    try:
        # Make a request to the website
        response = requests.get(league_url)

        # Check if the request was successful
        if response.status_code == 200:
            print("Request successful")
            print("Response content:", response.text)  # Debug statement

            # Create BeautifulSoup object
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find football game URLs and store them in a list
            football_urls = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'vs' in href:
                    teams = href.split('vs')
                    team1 = teams[0].split('/')[-1].replace('-', ' ').replace('vs', '').title().strip()
                    team2 = teams[1].split('/')[0].replace('-', ' ').title().strip()
                    # Remove specific words from the team names
                    team1_clean = team1.replace(' Watch', '').replace(' Stream', '').replace(' Online', '').replace('Watch ', '')
                    team2_clean = team2.replace(' Watch', '').replace(' Stream', '').replace(' Online', '').replace('Watch', '')
                    football_urls.append(f"{team1_clean} vs {team2_clean}")

            # Display the football game URLs or return None if no games found
            return football_urls if football_urls else None
        else:
            print("Error:", response.status_code)
            raise ConnectionError("Failed to fetch data from the website.")
    except Exception as e:
        print("An error occurred:", str(e))
        raise

# Function to open the sport streams page
def open_sport_streams(frame, sport_leagues):
    global active_button_index  # Access the global active_button_index variable

    # Clear previous content
    for widget in frame.winfo_children():
        widget.destroy()

    # Create navbar in the current frame
    create_navbar(frame)

    # Create a canvas with a scrollbar
    canvas = tk.Canvas(frame)
    scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    for league, league_url in sport_leagues.items():
        # Title label for each league
        title_label = ttk.Label(scrollable_frame, text=f"{league} Today's Matches:", style="Title.TLabel")
        title_label.pack(pady=5, anchor="w")

        # List to store labels for each league
        league_labels = []
        all_labels[league] = league_labels

        try:
            football_streams = scrape_football_streams(league_url, frame)
            if football_streams:
                for stream in football_streams:
                    # Create a clickable link label for each stream
                    link_label = ttk.Label(scrollable_frame, text=f"{stream}", style="Stream.TLabel", foreground="blue", cursor="hand2")
                    link_label.pack(anchor="w")
                    league_labels.append(link_label)

                    # Bind the label to open the link when clicked
                    link_label.bind("<Button-1>", lambda event, url=stream: webbrowser.open_new(url))
            else:
                # If no games found initially, display "No games today" under the league title
                no_games_label = ttk.Label(scrollable_frame, text="No games today", style="NoGames.TLabel")
                no_games_label.pack(anchor="w")
                league_labels.append(no_games_label)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    # Close the loading message after all frames have been loaded
    messagebox.showinfo("Loading", "All data loaded successfully.")

# Function to create the navbar with icons
def create_navbar(frame):
    global active_button_index  # Access the global active_button_index variable
    global buttons  # Access the global buttons list

    navbar_frame = ttk.Frame(frame)
    navbar_frame.pack(side=tk.TOP, fill=tk.X)

    # Define icons for each sport
    soccer_icon = Image.open('img/soccer-ball.ico').resize((32, 32))
    basketball_icon = Image.open('img/basketball-ball.ico').resize((32, 32))
    tennis_icon = Image.open('img/tennis.ico').resize((32, 32))

    # Convert icons to Tkinter-compatible format
    soccer_icon_tk = ImageTk.PhotoImage(soccer_icon)
    basketball_icon_tk = ImageTk.PhotoImage(basketball_icon)
    tennis_icon_tk = ImageTk.PhotoImage(tennis_icon)

    for sport, leagues in sports.items():
        # Button for each sport in the navbar with icon
        if sport == 'Soccer':
            sport_button = ttk.Button(navbar_frame, text=sport, image=soccer_icon_tk, compound=tk.LEFT, command=lambda l=leagues: open_sport_streams(frame, l), style="Button.TButton")
        elif sport == 'Basketball':
            sport_button = ttk.Button(navbar_frame, text=sport, image=basketball_icon_tk, compound=tk.LEFT, command=lambda l=leagues: open_sport_streams(frame, l), style="Button.TButton")
        elif sport == 'Tennis':
            sport_button = ttk.Button(navbar_frame, text=sport, image=tennis_icon_tk, compound=tk.LEFT, command=lambda l=leagues: open_sport_streams(frame, l), style="Button.TButton")

        sport_button.pack(side=tk.LEFT, padx=10, pady=5)
        buttons.append(sport_button)

        # Bind hover events to the buttons
        sport_button.bind("<Enter>", lambda event, button=sport_button: button.config(background="lightgrey"))
        sport_button.bind("<Leave>", lambda event, button=sport_button: button.config(background="SystemButtonFace"))

        # Bind the button click event
        sport_button.bind("<Button-1>", lambda event, button=sport_button: handle_button_click(button))

        # Keep a reference to the images to avoid garbage collection
        if sport == 'Soccer':
            sport_button.image = soccer_icon_tk
        elif sport == 'Basketball':
            sport_button.image = basketball_icon_tk
        elif sport == 'Tennis':
            sport_button.image = tennis_icon_tk


# Function to handle button click event
def handle_button_click(button):
    global active_button_index  # Access the global active_button_index variable
    global buttons  # Access the global buttons list

    for i, btn in enumerate(buttons):
        if btn == button:
            active_button_index = i  # Update the active_button_index
            btn.config(background="blue")  # Set the color of the clicked button to blue
        else:
            btn.config(background="SystemButtonFace")  # Reset the color of other buttons

# Main function
def main():
    root = tk.Tk()
    root.title("Sports Streams")
    root.iconbitmap('img/soccer-ball.ico')

    # Get the screen width and height
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calculate the x and y coordinates to center the window
    x_coordinate = (screen_width - 500) // 2  # Assuming the window width is 800
    y_coordinate = (screen_height - 600) // 2  # Assuming the window height is 600

    root.geometry(f"500x600+{x_coordinate}+{y_coordinate}")  # Set window size and position

    # Define custom fonts
    style = ttk.Style()
    style.configure("Title.TLabel", font=("Helvetica", 16, "bold"))
    style.configure("Stream.TLabel", font=("Helvetica", 12))
    style.configure("Button.TButton", font=("Arial", 12, "bold"))

    # Create navbar
    create_navbar(root)

    root.mainloop()


if __name__ == "__main__":
    main()

#if you're reading this sorry :(  this application is not finished but i'm working on it and i'm learning python and tkinter and i'm trying to make it better
#if you have any ideas or suggestions for me to improve this application, please let me know
#thank you

# oh yeah and it could be faster but damn it's 2 am and i'm tired of this shit
# if you need more help and wanna get close and personal with me ig: @tanks.jpeg


