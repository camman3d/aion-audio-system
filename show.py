import csv
import threading
import dmx
import time
import paho.mqtt.client as mqtt
import pygame

class Show:
    name = ''
    audio_file = None
    client = None
    dmx_playing = False
    dmx_data = []
    loop_show = False
    dmx_loop_enabled = True

    def __init__(self, name, files) -> None:
        self.name = name
        self.files = files
        for file in files:
            print(f'[Show {name}] Loading file {file}')
            if file.endswith('.mp3') or file.endswith('.wav'):
                self.audio_file = file
            elif file.endswith('.dmx') or file.endswith('.show'):
                self.dmx_data = parse_dmx_data(file)
            elif file.endswith('.loop'):
                self.dmx_data = parse_dmx_data(file)
                self.loop_show = True

    def play(self):
        print(f'Playing show {self.name}')
        if self.audio_file:
            pygame.mixer.music.load(self.audio_file)
            pygame.mixer.music.play()
        if len(self.dmx_data) > 0:
            threading.Thread(target=self.play_dmx).start()

    def play_dmx(self):
        self.dmx_playing = True
        self.dmx_loop_enabled = self.loop_show
        start_time = time.time()
        for dmx_event in self.dmx_data:
            while time.time() - start_time < dmx_event['timestamp']:
                if not self.dmx_playing:
                    return
                time.sleep(0.001)
            dmx.output_device.output(dmx_event['universe'], dmx_event['channel'], dmx_event['value'])
        self.dmx_playing = False

        if self.loop_show and self.dmx_loop_enabled:
            self.play()

    def stop(self):
        self.dmx_playing = False
        self.dmx_loop_enabled = False
        if self.audio_file:
            pygame.mixer.music.stop()

    def listen(self, host):
        print(f'Starting MQTT client for topic /show/{self.name}')
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.client.connect(host)
        self.client.subscribe('/show/' + self.name)
        self.client.loop_start()

    def on_message(self, client, userdata, message):
        payload = message.payload.decode()
        if payload == "play":
            self.play()
        elif payload == "stop":
            self.stop()

def parse_dmx_data(file):
    dmx_data = []
    with open(file, 'r') as file:
        reader = csv.reader(file, delimiter=' ')
        for row in reader:
            timestamp, universe, channel, value = row
            dmx_data.append({
                'timestamp': float(timestamp),
                'universe': int(universe),
                'channel': int(channel),
                'value': int(value)
            })
    return dmx_data