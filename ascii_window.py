import pygame
import cv2
import numpy as np
from queue import Queue, Empty
import time

def ascii_art(image, cols=120, scale=0.43):
    char_list = ['@', '#', 'S', '%', '?', '*', '+', ';', ':', ',', '.']
    
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = image.shape
    cell_width = width / cols
    cell_height = scale * cell_width
    rows = int(height / cell_height)
    
    ascii_image = []
    for i in range(rows):
        y1, y2 = int(i * cell_height), int((i + 1) * cell_height)
        ascii_image.append("")
        for j in range(cols):
            x1, x2 = int(j * cell_width), int((j + 1) * cell_width)
            cell = image[y1:y2, x1:x2]
            avg = int(np.mean(cell))
            char_index = int((avg * (len(char_list) - 1)) / 255)
            ascii_image[i] += char_list[char_index]
    
    return ascii_image

def run_ascii_window(frame_queue, person_detected_queue):
    pygame.init()
    width, height = 640, 800
    screen = None
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Courier', 10)

    ascii_duration = 10  # Initial duration in seconds to keep the ASCII window open
    ascii_start_time = None
    last_person_detection_time = None

    running = True
    while running:
        person_detected = False
        while not person_detected_queue.empty():
            person_detected = person_detected_queue.get()

        current_time = time.time()

        if person_detected:
            if screen is None:
                screen = pygame.display.set_mode((width, height))
                pygame.display.set_caption("ASCII Webcam Filter")
                ascii_start_time = current_time
            last_person_detection_time = current_time
            ascii_duration = max(ascii_duration, (current_time - ascii_start_time) + 3)  # Add 3 seconds to the duration

        if screen is not None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            if current_time - ascii_start_time > ascii_duration:
                pygame.display.quit()
                screen = None
                ascii_duration = 10  # Reset duration for the next detection
            else:
                try:
                    frame = frame_queue.get_nowait()
                    ascii_frame = ascii_art(frame)
                    screen.fill((0, 0, 0))
                    for i, line in enumerate(ascii_frame):
                        text_surface = font.render(line, True, (255, 255, 255))
                        screen.blit(text_surface, (0, i * 10))
                    pygame.display.flip()
                except Empty:
                    pass

        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    print("This script should be run as part of the main.py script.")
    print("Please run main.py instead.")