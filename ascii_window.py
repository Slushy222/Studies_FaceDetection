import pygame
import cv2
import numpy as np
from queue import Queue, Empty

def ascii_art(image, cols, rows):
    char_list = '@%#*+=-:. '
    
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    processed_image = cv2.resize(image, (cols, rows), interpolation=cv2.INTER_AREA)
    
    ascii_image = []
    char_list_len = len(char_list) - 1
    
    for i in range(rows):
        current_row = ""
        for j in range(cols):
            pixel_value = processed_image[i, j]
            char_index = int(pixel_value * char_list_len / 255)
            current_row += char_list[char_index]
                
        ascii_image.append(current_row)
    
    return ascii_image

def run_ascii_window(frame_queue, person_detected_queue):
    pygame.init()
    width, height = 800, 600
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    pygame.display.set_caption("to have")
    icon = pygame.image.load('red-icon-01.png')
    pygame.display.set_icon(icon)
    
    fps_clock = pygame.time.Clock()
    
    # Fixed font size
    font_size = 10
    try:
        font = pygame.font.SysFont('consolas', font_size)
    except:
        font = pygame.font.SysFont('courier', font_size)
    
    # Pre-render characters
    char_surfaces = {char: font.render(char, True, (255, 255, 255)) for char in '@%#*+=-:. '}
    
    # Fixed character dimensions
    char_width = font_size * 0.6
    char_height = font_size + 1
    
    fullscreen = False
    original_size = (width, height)
    last_resize_time = pygame.time.get_ticks()
    resize_cooldown = 100
    
    last_valid_frame = None
    
    running = True
    while running:
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode(original_size, pygame.RESIZABLE)
            elif event.type == pygame.VIDEORESIZE and not fullscreen:
                if current_time - last_resize_time > resize_cooldown:
                    screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    original_size = (event.w, event.h)
                    last_resize_time = current_time

        screen.fill((0, 0, 0))

        try:
            frame = frame_queue.get_nowait()
            if frame is not None and frame.size > 0:
                last_valid_frame = frame
        except Empty:
            pass
        except Exception as e:
            print(f"Error getting frame: {e}")

        if last_valid_frame is not None:
            current_w, current_h = screen.get_size()
            frame_h, frame_w = last_valid_frame.shape[:2]
            
            # Calculate how many characters can fit in the window
            cols = int(current_w / char_width)
            rows = int(current_h / char_height)
            
            try:
                # Generate ASCII frame
                ascii_frame = ascii_art(last_valid_frame, cols, rows)
                
                # Display ASCII frame
                for i, line in enumerate(ascii_frame):
                    y_pos = i * char_height
                    
                    for j, char in enumerate(line):
                        if char in char_surfaces:
                            x_pos = j * char_width
                            screen.blit(char_surfaces[char], (x_pos, y_pos))
                            
            except Exception as e:
                print(f"Error processing frame: {e}")

        pygame.display.flip()
        fps_clock.tick(30)

    pygame.quit()