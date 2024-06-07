import cv2
import sys
import numpy as np
from moviepy.editor import VideoFileClip
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk
import threading

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
        self.duration = None

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

        self.label = tk.Label(self.btn_frame, text="Duration (seconds):")
        self.label.pack(side=tk.LEFT, padx=5, pady=5)

        self.duration_entry = tk.Entry(self.btn_frame)
        self.duration_entry.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_save = tk.Button(self.btn_frame, text="Save", command=self.start_save_video)
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

    def apply_mosaic(self, frame, start_x, start_y, end_x, end_y, size=10):
        """
        Apply mosaic effect to the specified region of the frame.
        """
        sub_frame = frame[start_y:end_y, start_x:end_x]
        sub_frame = cv2.resize(sub_frame, (size, size), interpolation=cv2.INTER_LINEAR)
        sub_frame = cv2.resize(sub_frame, (end_x - start_x, end_y - start_y), interpolation=cv2.INTER_NEAREST)
        frame[start_y:end_y, start_x:end_x] = sub_frame
        return frame

    def save_video(self):
        if self.rect is None:
            print("Error: No rectangle drawn.")
            return

        try:
            self.duration = float(self.duration_entry.get())
        except ValueError:
            print("Error: Invalid duration.")
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

        # Get original video properties
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        output_path = "output.mov"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use mp4v codec for .mov format
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        frame_count = int(self.duration * fps)
        current_frame = 0

        while self.cap.isOpened() and current_frame < frame_count:
            ret, frame = self.cap.read()
            if not ret:
                break

            # Apply mosaic to the selected region
            frame = self.apply_mosaic(frame, start_x, start_y, end_x, end_y)
            out.write(frame)
            current_frame += 1

        self.cap.release()
        out.release()
        print("Output saved to", output_path)

    def start_save_video(self):
        save_thread = threading.Thread(target=self.save_video)
        save_thread.start()

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
