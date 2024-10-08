import json
import os
import time
import threading
import pygame
from show import Show
import dmx

config = {}

def read_config():
    global config
    with open('config.json', 'r') as file:
        config = json.load(file)

def build_shows():
    grouped_files = {}
    for filename in os.listdir('shows'):
        name, _ = os.path.splitext(filename)
        full_file = os.path.join('shows/', filename)

        if name in grouped_files:
            grouped_files[name].append(full_file)
        else:
            grouped_files[name] = [full_file]

    shows = []
    for name, files in grouped_files.items():
        show = Show(name, files)
        if config['mqtt']['enabled']:
            show.listen(config['mqtt']['host'])
        shows.append(show)

    return shows

def play_audio(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()

def stop_audio():
    pygame.mixer.music.stop()

def handle_input(shows):
    while True:
        command = input("Enter a command (1-9 to play a show, q to quit): ").lower()
        if command == 'q':
            return False
        elif command.isdigit() and 1 <= int(command) <= 9:
            show_index = int(command) - 1
            if show_index < len(shows):
                shows[show_index].play()
            else:
                print(f"No show at index {show_index + 1}")
        else:
            print("Invalid command")

def main():
    read_config()
    dmx.configure_dmx(config['dmx']['protocol'], config['dmx']['host'])
    shows = build_shows()

    pygame.init()
    pygame.mixer.init()

    print("Aion Show System")
    print("Enter 1-9 to play a show, or 'q' to quit")

    input_thread = threading.Thread(target=handle_input, args=(shows,), daemon=True)
    input_thread.start()

    running = True
    while running:
        if not input_thread.is_alive():
            running = False
        time.sleep(0.1)

    for show in shows:
        show.stop()
    dmx.output_device.stop()
    pygame.quit()

if __name__ == "__main__":
    main()