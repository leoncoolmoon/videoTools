import cv2
import sys
import numpy as np
from moviepy.editor import VideoFileClip
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk

class VideoEditorApp:
    def __init__(self, root, video_path):
        self.root = root
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        self.rect = None
        self.start_point = None
        self.end_point = None
        self.drawing = False
        self.frame = None

        self.setup_ui()
        self.load_frame()

    def setup_ui(self):
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.vbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.hbar = tk.Scrollbar(self.root, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)

        self.canvas.bind("<Button-1>", self.on_button_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_up)

        self.btn_frame = tk.Frame(self.root)
        self.btn_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.btn_save = tk.Button(self.btn_frame, text="Save", command=self.save_video)
        self.btn_save.pack(side=tk.LEFT, padx=5, pady=5)

    def load_frame(self):
        input_time = float(input("Enter the start time (in seconds): "))
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        frame_number = int(input_time * fps)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        ret, self.frame = self.cap.read()
        if not ret:
            print("Error: Could not read frame at time", input_time)
            sys.exit(1)

        self.show_image(self.frame)

    def show_image(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        self.imgtk = ImageTk.PhotoImage(image=img)

        self.canvas.create_image(0, 0, anchor="nw", image=self.imgtk)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def on_button_down(self, event):
        self.drawing = True
        self.start_point = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        print(f"Mouse down at x={self.start_point[0]}, y={self.start_point[1]}")

    def on_mouse_move(self, event):
        if self.drawing:
            self.end_point = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
            print(f"Mouse move at x={self.end_point[0]}, y={self.end_point[1]}")
            self.show_image(self.frame)
            self.canvas.create_rectangle(self.start_point[0], self.start_point[1],
                                         self.end_point[0], self.end_point[1],
                                         outline="green", width=2)

    def on_button_up(self, event):
        self.drawing = False
        self.end_point = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        self.rect = (self.start_point, self.end_point)
        print(f"Mouse up at x={self.end_point[0]}, y={self.end_point[1]}")

    def save_video(self):
        if self.rect is None:
            print("Error: No rectangle drawn.")
            return

        start_x, start_y = map(int, self.rect[0])
        end_x, end_y = map(int, self.rect[1])

        # Ensure the coordinates are within the frame size
        start_x = max(0, min(start_x, self.frame.shape[1]))
        start_y = max(0, min(start_y, self.frame.shape[0]))
        end_x = max(0, min(end_x, self.frame.shape[1]))
        end_y = max(0, min(end_y, self.frame.shape[0]))

        # Adjust width and height to be even
        width = end_x - start_x
        height = end_y - start_y

        if width % 2 != 0:
            end_x -= 1
        if height % 2 != 0:
            end_y -= 1

        duration = float(input("Enter the duration (in seconds): "))
        clip = VideoFileClip(self.video_path).subclip(self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000, 
                                                     self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000 + duration)

        def crop_region(get_frame, t):
            frame = get_frame(t)
            return frame[start_y:end_y, start_x:end_x]

        cropped_clip = clip.fl(crop_region, apply_to=['mask', 'video'])

        output_path = "output.mov"
        cropped_clip.write_videofile(output_path, codec='libx264')#, bitrate="2000k")
        print("Output saved to", output_path)

        # Ensure to close the video clip properly
        clip.reader.close()
        if clip.audio:
            clip.audio.reader.close_proc()

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]
    root = tk.Tk()
    app = VideoEditorApp(root, video_path)
    root.mainloop()

if __name__ == "__main__":
    main()
