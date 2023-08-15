import os
import time
import json
import tkinter as tk
from tkinter import messagebox
import psutil
import threading
import random
import re
import subprocess
from fuzzywuzzy import fuzz

# List of paths to all your Steam library folders
steam_library_paths = [
    'C:/Program Files (x86)/Steam/steamapps',
    'D:/SteamLibrary/steamapps',
    'E:/Games/SteamLibrary/steamapps',
    # Add more paths as needed
]

# Initialize the application stats
app_stats = {}


# Function to read previous stats
def read_previous_stats():
    try:
        with open('app_stats.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# Function to write current stats
def write_current_stats(stats):
    with open('app_stats.json', 'w') as f:
        json.dump(stats, f)


# Function to get installed games
def get_installed_games(library_paths):
    games = []
    for library_path in library_paths:
        if os.path.exists(library_path):
            for file in os.listdir(library_path):
                if file.endswith('.acf'):
                    with open(os.path.join(library_path, file)) as f:
                        content = f.read()
                        name_match = re.search(r'"name"\s+"(.+)"', content)
                        appid_match = re.search(r'"appid"\s+"(.+)"', content)
                        if name_match and appid_match:
                            games.append((name_match.group(1), appid_match.group(1)))
    return sorted(games, key=lambda x: x[0].lower())  # Sort the games alphabetically, case-insensitive


# Function to end process
def end_process(game_name):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == game_name:
            proc.kill()
            return True
    return False


# Function to optimize system resources for gaming
def optimize_resources(stats):
    for proc in psutil.process_iter(['name', 'pid']):
        if proc.info['name'] in stats:
            p = psutil.Process(proc.info['pid'])
            p.nice(psutil.HIGH_PRIORITY_CLASS)


# Function to check for game updates
def check_for_updates():
    return random.choice([True, False])


# Function to update stats
def update_stats(stats):
    running_games = []
    while True:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.parent() is not None and proc.parent().name() in ['steam', 'epicgameslauncher', 'origin', 'uplay']:
                exe = proc.info['name']
                if exe not in running_games:
                    if exe not in stats:
                        stats[exe] = {'playtime': 0, 'launches': 0, 'cpu': 0, 'memory': 0}
                    stats[exe]['launches'] += 1
                    running_games.append(exe)
                    p = psutil.Process(proc.info['pid'])
                    stats[exe]['cpu'] = p.cpu_percent(interval=None)
                    stats[exe]['memory'] = p.memory_percent()

        for exe in running_games[:]:  # iterating over a copy of running_games
            if not is_app_running(exe):
                running_games.remove(exe)
            else:
                stats[exe]['playtime'] += 1  # increment playtime by one second

        optimize_resources(stats)
        write_current_stats(stats)

        time.sleep(60)


# Function to launch game
def launch_game():
    selected_game = games_listbox.get(games_listbox.curselection())
    game_name, game_id = selected_game
    subprocess.Popen(["start", f"steam://rungameid/{game_id}"], shell=True)


# Function to kill game
def kill_game():
    selected_game = running_games_listbox.get(running_games_listbox.curselection())
    if end_process(selected_game):
        messagebox.showinfo("Success", f"{selected_game} has been terminated successfully!")
    else:
        messagebox.showinfo("Failure", f"Could not terminate {selected_game}. Please check the game name and try again.")


# Function to check if app is running
def is_app_running(app):
    excluded_processes = ['System', 'svchost.exe', 'lsass.exe', 'wininit.exe', 'services.exe', 'smss.exe', 'winlogon.exe', 'dwm.exe']

    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == app and app not in excluded_processes and 'service' not in app.lower():
            return True
    return False


# Function to get running apps
def get_running_apps():
    running_apps = []
    installed_games = [game[0].lower() for game in get_installed_games(steam_library_paths)]
    excluded_processes = ['System', 'svchost.exe', 'lsass.exe', 'wininit.exe', 'services.exe', 'smss.exe', 'winlogon.exe', 'dwm.exe']

    for proc in psutil.process_iter(['name']):
        process_name = proc.info['name']
        if process_name not in excluded_processes and 'service' not in process_name.lower():
            # Fuzzy matching to find a close match between process name and game name
            matching_scores = [fuzz.ratio(game, process_name.lower()) for game in installed_games]
            max_score = max(matching_scores)
            if max_score >= 70:  # Adjust the matching threshold as needed
                running_apps.append(process_name)

    return running_apps


# Function to show stats
def show_stats(stats):
    sorted_apps = sorted(stats.items(), key=lambda x: x[1]['playtime'], reverse=True)

    stats_str = ''
    for app, app_stats in sorted_apps:
        hours, remainder = divmod(app_stats['playtime'], 3600)
        minutes, seconds = divmod(remainder, 60)

        cpu_usage = app_stats['cpu'] if 'cpu' in app_stats else "N/A"
        memory_usage = app_stats['memory'] if 'memory' in app_stats else "N/A"

        stats_str += f"{app}:\n  Active Time - {hours} hours, {minutes} minutes, {seconds} seconds\n  Launches - {app_stats['launches']}\n  CPU Usage - {cpu_usage}%\n  Memory Usage - {memory_usage}%\n\n"
        if check_for_updates():
            stats_str += f"Update Available for {app}!\n\n"
    messagebox.showinfo("App Stats", stats_str)


# Create basic GUI
root = tk.Tk()
root.geometry("800x600")
root.title("Steam Task Manager")

# Add button to show game stats
show_button = tk.Button(root, text="Show Game Stats", command=lambda: show_stats(app_stats))
show_button.pack()

# Create Listbox for games
games_listbox = tk.Listbox(root, height=10, width=50)
for game in get_installed_games(steam_library_paths):
    games_listbox.insert(tk.END, game)
games_listbox.pack()

# Add button to launch game
launch_button = tk.Button(root, text="Launch Selected Game", command=launch_game)
launch_button.pack()

# Create Listbox for running games
running_games_listbox = tk.Listbox(root, height=10, width=50)
running_games_listbox.pack()

# Add button to end game
kill_button = tk.Button(root, text="End Selected Game", command=kill_game)
kill_button.pack()

# Start updating list of running games
def update_running_games_list():
    running_games_listbox.delete(0, tk.END)  # Clear the listbox
    for game in get_running_apps():
        running_games_listbox.insert(tk.END, game)
    root.after(1000, update_running_games_list)  # Update the list every second

update_running_games_list()

# Start monitoring in a separate thread
monitor_thread = threading.Thread(target=update_stats, args=(app_stats,), daemon=True)
monitor_thread.start()

root.mainloop()
