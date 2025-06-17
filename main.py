import tkinter as tk
import pygame
import os
import io
import random

from tkinter import filedialog, ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
from mutagen.mp3 import MP3



class MP3Player:
    def __init__(self, root):
        self.root = root
        self.root.title("Elite MP3 Player")
        self.root.geometry("600x800")
        self.root.configure(bg="#121212")
        pygame.mixer.init()
        self.current_file = None
        self.paused = False
        self.photo = None
        self.volume = 1.0
        self.is_looping = False
        self.is_shuffling = False
        self.playlist = []
        self.current_index = -1
        self.current_lyrics = []

        # Style configuration
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", padding=10, font=("Arial", 12, "bold"), background="#1db954", foreground="white")
        style.map("TButton", background=[("active", "#17a34a")])
        style.configure("TLabel", background="#121212", foreground="#ffffff", font=("Arial", 14))
        style.configure("TScale", background="#121212", troughcolor="#282828", sliderlength=20)
        style.configure("Vertical.TScale", background="#121212", troughcolor="#282828")
        style.configure("TListbox", background="#282828", foreground="white", font=("Arial", 10))

        # Main frame
        main_frame = tk.Frame(root, bg="#121212")
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Album art
        self.canvas = tk.Canvas(main_frame, width=450, height=450, bg="#121212", highlightthickness=0)
        self.canvas.pack(pady=10)
        self.default_art = self.create_default_art()
        self.art_id = self.canvas.create_image(225, 225, image=self.default_art)

        # Song info
        self.title_label = ttk.Label(main_frame, text="No file selected", wraplength=500, anchor="center", font=("Arial", 16, "bold"))
        self.title_label.pack(pady=5)
        self.artist_label = ttk.Label(main_frame, text="", wraplength=500, anchor="center", font=("Arial", 12))
        self.artist_label.pack(pady=5)
        self.album_label = ttk.Label(main_frame, text="", wraplength=500, anchor="center", font=("Arial", 10, "italic"))
        self.album_label.pack(pady=5)

        # Progress bar
        progress_frame = tk.Frame(main_frame, bg="#121212")
        progress_frame.pack(pady=10)
        self.progress = ttk.Scale(progress_frame, from_=0, to=100, orient="horizontal", length=450)
        self.progress.pack()
        self.progress.bind("<ButtonRelease-1>", self.seek)

        # Time labels
        time_frame = tk.Frame(main_frame, bg="#121212")
        time_frame.pack()
        self.current_time = ttk.Label(time_frame, text="0:00", font=("Arial", 10))
        self.current_time.pack(side="left", padx=15)
        self.total_time = ttk.Label(time_frame, text="0:00", font=("Arial", 10))
        self.total_time.pack(side="right", padx=15)

        # Volume control
        volume_frame = tk.Frame(main_frame, bg="#121212")
        volume_frame.pack(pady=5)
        ttk.Label(volume_frame, text="Volume", font=("Arial", 10)).pack(side="left", padx=5)
        self.volume_scale = ttk.Scale(volume_frame, from_=0, to=1, orient="horizontal", length=120, value=1.0)
        self.volume_scale.pack(side="left")
        self.volume_scale.bind("<ButtonRelease-1>", self.set_volume)

        # Playback controls
        button_frame = tk.Frame(main_frame, bg="#121212")
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Add", command=self.add_to_playlist).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Prev", command=self.play_previous).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Play", command=self.play).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Pause", command=self.pause).grid(row=0, column=3, padx=5)
        ttk.Button(button_frame, text="Next", command=self.play_next).grid(row=0, column=4, padx=5)
        ttk.Button(button_frame, text="Loop", command=self.toggle_loop).grid(row=0, column=5, padx=5)
        ttk.Button(button_frame, text="Shuffle", command=self.toggle_shuffle).grid(row=0, column=6, padx=5)

        # Playlist display
        playlist_frame = tk.Frame(main_frame, bg="#121212")
        playlist_frame.pack(pady=10, fill="x")
        self.playlist_box = tk.Listbox(playlist_frame, height=5, bg="#282828", fg="white", font=("Arial", 10), selectbackground="#1db954")
        self.playlist_box.pack(fill="x", padx=5)
        self.playlist_box.bind("<Double-1>", self.play_selected)

        # Lyrics display
        self.lyrics_label = ttk.Label(main_frame, text="Lyrics not available", wraplength=500, anchor="center", font=("Arial", 10))
        self.lyrics_label.pack(pady=10)

        self.update_progress()
        pygame.mixer.music.set_endevent(pygame.USEREVENT)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_default_art(self):
        img = Image.new("RGB", (450, 450), "#282828")
        draw = ImageDraw.Draw(img)
        draw.rectangle((10, 10, 440, 440), fill="#1c1c1c")
        draw.ellipse((150, 150, 300, 300), fill="#1db954")
        draw.text((180, 210), "♪", fill="white", font=ImageFont.truetype("arial.ttf", 80))
        return ImageTk.PhotoImage(img)

    def load_album_art(self, file):
        try:
            audio = MP3(file, ID3=mutagen.id3.ID3)
            for tag in audio.tags.values():
                if isinstance(tag, mutagen.id3.APIC):
                    img = Image.open(io.BytesIO(tag.data))
                    img = img.resize((450, 450), Image.LANCZOS)
                    self.photo = ImageTk.PhotoImage(img)
                    self.canvas.itemconfig(self.art_id, image=self.photo)
                    return
        except:
            self.canvas.itemconfig(self.art_id, image=self.default_art)

    def load_file(self, file):
        self.current_file = file
        audio = MP3(file)
        title = audio.get("TIT2", os.path.basename(file))
        artist = audio.get("TPE1", "Unknown Artist")
        album = audio.get("TALB", "Unknown Album")
        self.title_label.config(text=title)
        self.artist_label.config(text=artist)
        self.album_label.config(text=album)
        pygame.mixer.music.load(file)
        self.total_time.config(text=self.format_time(audio.info.length))
        self.load_album_art(file)
        self.progress.set(0)
        self.load_lyrics(file)
        self.update_playlist_display()

    def add_to_playlist(self):
        files = filedialog.askopenfilenames(filetypes=[("MP3 files", "*.mp3")])
        if files:
            self.playlist.extend(files)
            self.update_playlist_display()
            if self.current_index == -1 and self.playlist:
                self.current_index = 0
                self.load_file(self.playlist[self.current_index])
                self.play()

    def update_playlist_display(self):
        self.playlist_box.delete(0, tk.END)
        for i, file in enumerate(self.playlist):
            name = os.path.basename(file)
            self.playlist_box.insert(tk.END, name)
            if i == self.current_index:
                self.playlist_box.selection_clear(0, tk.END)
                self.playlist_box.selection_set(i)

    def play_selected(self, event):
        selection = self.playlist_box.curselection()
        if selection:
            self.current_index = selection[0]
            self.load_file(self.playlist[self.current_index])
            self.play()

    def play(self):
        if self.current_file:
            if self.paused:
                pygame.mixer.music.unpause()
                self.paused = False
            else:
                pygame.mixer.music.play()
            self.update_progress()

    def pause(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.paused = True

    def stop(self):
        pygame.mixer.music.stop()
        self.paused = False
        self.progress.set(0)
        self.current_time.config(text="0:00")

    def play_next(self):
        if self.playlist and self.current_index < len(self.playlist) - 1:
            self.current_index += 1
            self.load_file(self.playlist[self.current_index])
            self.play()
        elif self.is_looping and self.playlist:
            self.current_index = 0
            self.load_file(self.playlist[self.current_index])
            self.play()

    def play_previous(self):
        if self.playlist and self.current_index > 0:
            self.current_index -= 1
            self.load_file(self.playlist[self.current_index])
            self.play()
        elif self.is_looping and self.playlist:
            self.current_index = len(self.playlist) - 1
            self.load_file(self.playlist[self.present_index])
            self.play()

    def toggle_loop(self):
        self.is_looping = not self.is_looping
        pygame.mixer.music.set_endevent(pygame.USEREVENT if self.is_looping else 0)

    def toggle_shuffle(self):
        self.is_shuffling = not self.is_shuffling
        if self.is_shuffling:
            random.shuffle(self.playlist)
            if self.current_file in self.playlist:
                self.current_index = self.playlist.index(self.current_file)
            self.update_playlist_display()

    def seek(self, event):
        if self.current_file:
            position = self.progress.get() / 100 * MP3(self.current_file).info.length
            pygame.mixer.music.play(start=position)

    def set_volume(self, event):
        self.volume = self.volume_scale.get()
        pygame.mixer.music.set_volume(self.volume)

    def load_lyrics(self, file):
        try:
            audio = MP3(file, ID3=mutagen.id3.ID3)
            lyrics = audio.get("USLT::eng", None)
            if lyrics:
                self.lyrics_label.config(text=lyrics.text[:200] + "..." if len(lyrics.text) > 200 else lyrics.text)
            else:
                self.lyrics_label.config(text="Lyrics not available")
        except:
            self.lyrics_label.config(text="Lyrics not available")

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def update_progress(self):
        if pygame.mixer.music.get_busy():
            pos = pygame.mixer.music.get_pos() / 1000
            self.current_time.config(text=self.format_time(pos))
            if self.current_file:
                total = MP3(self.current_file).info.length
                self.progress.set(pos / total * 100)
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT and self.is_looping:
                self.play()
            elif event.type == pygame.USEREVENT and not self.is_looping and self.current_index < len(self.playlist) - 1:
                self.play_next()
        self.root.after(1000, self.update_progress)

    def on_closing(self):
        pygame.mixer.music.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MP3Player(root)
    root.mainloop()
