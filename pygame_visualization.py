import pygame
import numpy as np
from queue import Queue
import time
import random

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRID_COLOR = (225, 225, 225) #220, 220, 220 for light gray

def find_random_empty_position(grid, grid_width, grid_height):
    """
    Find a random empty position in the grid.
    Returns a tuple (x, y) of coordinates, or None if no empty positions exist.
    """
    empty_positions = []
    for y in range(grid_height):
        for x in range(grid_width):
            if grid[y][x] is None:
                empty_positions.append((x, y))
    
    if empty_positions:
        return random.choice(empty_positions)
    return None

class Cell:
    def __init__(self, grid_x, grid_y, class_id):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.class_id = class_id
        self.alive = True
        self.next_state = True
        self.cell_size = 8
        self.just_placed = True
        self.permanent = False  # Changed to allow movement
        
    def count_neighbors(self, grid, grid_width, grid_height):
        neighbors = 0
        self.neighbor_positions = []  # Store neighbor positions for movement
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                check_x = (self.grid_x + dx) % grid_width
                check_y = (self.grid_y + dy) % grid_height
                
                if grid[check_y][check_x] is not None and grid[check_y][check_x].alive:
                    neighbors += 1
                    self.neighbor_positions.append((check_x, check_y))
                
        return neighbors

    def find_empty_neighbor(self, grid, grid_width, grid_height):
        # Check all adjacent cells for an empty spot
        possible_moves = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                    
                new_x = (self.grid_x + dx) % grid_width
                new_y = (self.grid_y + dy) % grid_height
                
                if grid[new_y][new_x] is None:
                    possible_moves.append((new_x, new_y))
        
        return random.choice(possible_moves) if possible_moves else None

    def update(self, grid, grid_width, grid_height):
        if self.just_placed:
            self.just_placed = False
            return

        neighbors = self.count_neighbors(grid, grid_width, grid_height)
        
        # Movement rules based on neighbor count
        if neighbors < 2:
            # Lonely cells try to move towards others
            empty_spot = self.find_empty_neighbor(grid, grid_width, grid_height)
            if empty_spot:
                new_x, new_y = empty_spot
                grid[new_y][new_x] = self
                grid[self.grid_y][self.grid_x] = None
                self.grid_x = new_x
                self.grid_y = new_y
        
        elif neighbors > 3:
            # Overcrowded cells try to move away
            empty_spot = self.find_empty_neighbor(grid, grid_width, grid_height)
            if empty_spot:
                new_x, new_y = empty_spot
                grid[new_y][new_x] = self
                grid[self.grid_y][self.grid_x] = None
                self.grid_x = new_x
                self.grid_y = new_y
        
        # Cells with 2 or 3 neighbors stay in place
        self.alive = True
        self.next_state = True

    def draw(self, surface):
        if self.alive:
            pygame.draw.rect(surface, BLACK, 
                           (self.grid_x * self.cell_size, 
                            self.grid_y * self.cell_size, 
                            self.cell_size - 1, 
                            self.cell_size - 1))

def run_visualization(detection_queue, person_detected_queue):
    print("Visualization process starting...")
    
    try:
        pygame.init()
        print("Pygame initialized.")

        # Set up display
        width, height = 800, 600
        cell_size = 8
        grid_width = width // cell_size
        grid_height = height // cell_size
        
        screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("Cellular Automaton Grid")
        print("Pygame window created.")

        # Initialize empty grid
        grid = [[None for x in range(grid_width)] for y in range(grid_height)]
        
        clock = pygame.time.Clock()
        last_detection_time = {}
        detection_timeout = 1.0
        update_interval = 100  # 1 second between updates
        last_update_time = pygame.time.get_ticks()

        # Draw grid lines
        def draw_grid():
            for x in range(0, width, cell_size):
                pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, height))
            for y in range(0, height, cell_size):
                pygame.draw.line(screen, GRID_COLOR, (0, y), (width, y))

        running = True
        while running:
            dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    width, height = event.size
                    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
                    new_grid_width = width // cell_size
                    new_grid_height = height // cell_size
                    
                    new_grid = [[None for x in range(new_grid_width)] for y in range(new_grid_height)]
                    
                    for y in range(min(len(grid), new_grid_height)):
                        for x in range(min(len(grid[0]), new_grid_width)):
                            new_grid[y][x] = grid[y][x]
                            if new_grid[y][x] is not None:
                                new_grid[y][x].grid_x = x
                                new_grid[y][x].grid_y = y
                    
                    grid = new_grid
                    grid_width = new_grid_width
                    grid_height = new_grid_height

            # Process detection queue
            while not detection_queue.empty():
                detected_objects = detection_queue.get()
                
                for obj in detected_objects:
                    if obj.class_id == 0:  # Person detection
                        person_detected_queue.put(True)
                    
                    # Find random empty position
                    position = find_random_empty_position(grid, grid_width, grid_height)
                    if position:
                        x, y = position
                        new_cell = Cell(x, y, obj.class_id)
                        grid[y][x] = new_cell

            # Update cellular automaton based on interval
            current_tick = pygame.time.get_ticks()
            if current_tick - last_update_time >= update_interval:
                # Update all cells
                for y in range(grid_height):
                    for x in range(grid_width):
                        cell = grid[y][x]
                        if cell is not None:
                            cell.update(grid, grid_width, grid_height)
                
                last_update_time = current_tick

            # Draw
            screen.fill(WHITE)
            draw_grid()
            
            # Draw cells
            for y in range(grid_height):
                for x in range(grid_width):
                    if grid[y][x] is not None and grid[y][x].alive:
                        grid[y][x].draw(screen)

            pygame.display.flip()

    except Exception as e:
        print(f"Error in visualization process: {e}")
        raise e
    finally:
        pygame.quit()
        print("Visualization process ending.")

if __name__ == "__main__":
    print("This script should be run as part of the main.py script.")
    print("Please run main.py instead.")