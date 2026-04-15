import pygame
import sys
import random
from collections import deque

# --- CONFIG ---
GRID_SIZE = 4
CELL_SIZE = 100
MARGIN = 3
SIDE_PANEL = 280
BOTTOM_PANEL = 150
WIDTH = GRID_SIZE * (CELL_SIZE + MARGIN) + SIDE_PANEL
HEIGHT = GRID_SIZE * (CELL_SIZE + MARGIN) + BOTTOM_PANEL
FPS = 30

# --- COLORS ---
BG = (230, 250, 230)
GREEN1 = (180, 230, 180)
GREEN2 = (120, 190, 120)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (250, 240, 150)
RED = (240, 100, 100)
GRAY = (210, 210, 210)
BLUE = (100, 150, 255)
ORANGE = (255, 180, 100)
PURPLE = (200, 150, 255)
FOG = (100, 100, 100, 180)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wumpus World - Knowledge-Based Agent")
font = pygame.font.SysFont("arial", 18)
small_font = pygame.font.SysFont("arial", 14)
icon_font = pygame.font.SysFont("arial", 22, bold=True)
clock = pygame.time.Clock()

# --- BUTTON CLASS ---
class Button:
    def __init__(self, text, rect, color, icon):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.color = color
        self.icon = icon

    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=10)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=10)
        icon_txt = icon_font.render(self.icon, True, BLACK)
        text_txt = font.render(self.text, True, BLACK)
        screen.blit(icon_txt, (self.rect.x + 10, self.rect.y + 6))
        screen.blit(text_txt, (self.rect.x + 40, self.rect.y + 7))

    def clicked(self, pos):
        return self.rect.collidepoint(pos)


# --- KNOWLEDGE BASE CLASS ---
class KnowledgeBase:
    def __init__(self):
        self.facts = set()  # All known facts
        self.visited = set()  # Visited cells
        self.safe = {(0, 3)}  # Proven safe cells (start position)
        self.breeze_cells = set()  # Cells with breeze
        self.stench_cells = set()  # Cells with stench
        self.possible_pits = set()  # Possible pit locations
        self.possible_wumpus = set()  # Possible wumpus locations
        self.wumpus_location = None  # Confirmed wumpus location
        self.wumpus_alive = True
        
    def add_percept(self, pos, percepts):
        """Add percepts from current position to KB"""
        self.visited.add(pos)
        x, y = pos
        neighbors = self.get_neighbors(x, y)
        
        # No Breeze → all neighbors are safe from pits
        if "Breeze" not in percepts:
            self.facts.add(f"NoBreeze_{x}_{y}")
            for nx, ny in neighbors:
                self.safe.add((nx, ny))
                self.facts.add(f"Safe_{nx}_{ny}")
                # Remove from possible pits
                if (nx, ny) in self.possible_pits:
                    self.possible_pits.remove((nx, ny))
        else:
            # Breeze detected → at least one neighbor has pit
            self.breeze_cells.add(pos)
            self.facts.add(f"Breeze_{x}_{y}")
            for nx, ny in neighbors:
                if (nx, ny) not in self.visited and (nx, ny) not in self.safe:
                    self.possible_pits.add((nx, ny))
        
        # No Stench → all neighbors are safe from wumpus
        if "Stench" not in percepts:
            self.facts.add(f"NoStench_{x}_{y}")
            for nx, ny in neighbors:
                self.safe.add((nx, ny))
                self.facts.add(f"Safe_{nx}_{ny}")
                # Remove from possible wumpus
                if (nx, ny) in self.possible_wumpus:
                    self.possible_wumpus.remove((nx, ny))
        else:
            # Stench detected → wumpus is in one of neighbors
            self.stench_cells.add(pos)
            self.facts.add(f"Stench_{x}_{y}")
            if self.wumpus_alive:
                for nx, ny in neighbors:
                    if (nx, ny) not in self.visited and (nx, ny) not in self.safe:
                        self.possible_wumpus.add((nx, ny))
        
        # Glitter → gold is here
        if "Glitter" in percepts:
            self.facts.add(f"Gold_{x}_{y}")
    
    def get_neighbors(self, x, y):
        """Get valid neighboring cells"""
        neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                neighbors.append((nx, ny))
        return neighbors
    
    def infer_wumpus_location(self):
        """Try to deduce exact wumpus location"""
        if not self.wumpus_alive or len(self.stench_cells) < 2:
            return None
        
        # Find intersection of possible wumpus from multiple stench cells
        if len(self.possible_wumpus) == 1:
            self.wumpus_location = list(self.possible_wumpus)[0]
            return self.wumpus_location
        return None
    
    def get_safe_unvisited(self):
        """Get safe cells that haven't been visited"""
        return [(x, y) for x, y in self.safe if (x, y) not in self.visited]


# --- AGENT CLASS ---
class Agent:
    def __init__(self):
        self.x, self.y = 0, 3
        self.direction = "RIGHT"  # RIGHT, UP, LEFT, DOWN
        self.directions = ["RIGHT", "UP", "LEFT", "DOWN"]
        self.has_arrow = True
        self.has_gold = False
        self.alive = True
        self.score = 0
        self.kb = KnowledgeBase()
        self.path = []  # Planned path
        
    def get_direction_vector(self):
        """Get movement vector for current direction"""
        vectors = {"RIGHT": (1, 0), "UP": (0, -1), "LEFT": (-1, 0), "DOWN": (0, 1)}
        return vectors[self.direction]
    
    def turn_left(self):
        idx = self.directions.index(self.direction)
        self.direction = self.directions[(idx + 1) % 4]
        self.score -= 1
        return "Turned left"
    
    def turn_right(self):
        idx = self.directions.index(self.direction)
        self.direction = self.directions[(idx - 1) % 4]
        self.score -= 1
        return "Turned right"
    
    def move_forward(self, world):
        dx, dy = self.get_direction_vector()
        nx, ny = self.x + dx, self.y + dy
        
        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
            self.x, self.y = nx, ny
            self.score -= 1
            
            # Check for dangers
            if (nx, ny) in world.pits:
                self.alive = False
                self.score -= 1000
                return "💀 Fell into a pit!"
            elif (nx, ny) == world.wumpus and world.wumpus_alive:
                self.alive = False
                self.score -= 1000
                return "😵 Wumpus got you!"
            
            # Get percepts and update KB
            percepts = world.get_percepts((nx, ny))
            self.kb.add_percept((nx, ny), percepts)
            
            # Forward chaining inference
            self.kb.infer_wumpus_location()
            
            return f"Moved to ({nx}, {ny})"
        else:
            return "Bump! Can't move there."
    
    def shoot(self, world):
        if not self.has_arrow:
            return "No arrow left!"
        
        self.has_arrow = False
        self.score -= 10
        dx, dy = self.get_direction_vector()
        
        # Check if arrow hits wumpus
        arrow_x, arrow_y = self.x, self.y
        hit = False
        
        for _ in range(GRID_SIZE):
            arrow_x += dx
            arrow_y += dy
            if not (0 <= arrow_x < GRID_SIZE and 0 <= arrow_y < GRID_SIZE):
                break
            if (arrow_x, arrow_y) == world.wumpus and world.wumpus_alive:
                world.wumpus_alive = False
                self.kb.wumpus_alive = False
                hit = True
                break
        
        if hit:
            return "🎯 Scream! Wumpus is dead!"
        else:
            return "Arrow missed..."
    
    def grab_gold(self, world):
        if (self.x, self.y) == world.gold and not self.has_gold:
            self.has_gold = True
            self.score += 1000
            return "🏆 Grabbed the gold!"
        return "No gold here."
    
    def find_path_to_safe_cell(self):
        """BFS to find path to nearest safe unvisited cell"""
        safe_unvisited = self.kb.get_safe_unvisited()
        if not safe_unvisited:
            return []
        
        # BFS
        queue = deque([((self.x, self.y), [])])
        visited = {(self.x, self.y)}
        
        while queue:
            (cx, cy), path = queue.popleft()
            
            if (cx, cy) in safe_unvisited:
                return path + [(cx, cy)]
            
            for nx, ny in self.kb.get_neighbors(cx, cy):
                if (nx, ny) not in visited and (nx, ny) in self.kb.safe:
                    visited.add((nx, ny))
                    queue.append(((nx, ny), path + [(nx, ny)]))
        
        return []


# --- WORLD CLASS ---
class World:
    def __init__(self):
        self.pits = []
        self.wumpus = None
        self.gold = None
        self.wumpus_alive = True
        self.generate_world()
    
    def generate_world(self):
        """Generate random Wumpus World"""
        self.pits = []
        while len(self.pits) < 2:
            x, y = random.randint(0, 3), random.randint(0, 3)
            if (x, y) not in self.pits and (x, y) != (0, 3):
                self.pits.append((x, y))
        
        candidates = [(x, y) for x in range(GRID_SIZE) for y in range(GRID_SIZE)
                     if (x, y) not in self.pits and (x, y) != (0, 3)]
        self.wumpus = random.choice(candidates)
        
        candidates = [(x, y) for x, y in candidates if (x, y) != self.wumpus]
        self.gold = random.choice(candidates)
        self.wumpus_alive = True
    
    def get_percepts(self, pos):
        """Get percepts at given position"""
        percepts = []
        x, y = pos
        
        # Check for Breeze (adjacent to pit)
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (nx, ny) in self.pits:
                percepts.append("Breeze")
                break
        
        # Check for Stench (adjacent to Wumpus)
        if self.wumpus_alive:
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) == self.wumpus:
                    percepts.append("Stench")
                    break
        
        # Check for Glitter (on gold)
        if (x, y) == self.gold:
            percepts.append("Glitter")
        
        return percepts


# --- UI BUTTONS ---
buttons_right = [
    Button("RESET", (GRID_SIZE * (CELL_SIZE + MARGIN) + 20, 20, 240, 40), GRAY, "↻"),
    Button("AUTO PLAY", (GRID_SIZE * (CELL_SIZE + MARGIN) + 20, 70, 240, 40), GREEN1, "🤖"),
    Button("STOP", (GRID_SIZE * (CELL_SIZE + MARGIN) + 20, 120, 240, 40), RED, "■"),
]

buttons_manual = [
    Button("", (WIDTH // 2 - 70, HEIGHT - 100, 40, 40), YELLOW, "↺"),
    Button("", (WIDTH // 2 - 20, HEIGHT - 100, 40, 40), YELLOW, "▲"),
    Button("", (WIDTH // 2 + 30, HEIGHT - 100, 40, 40), YELLOW, "↻"),
    Button("", (WIDTH // 2 - 70, HEIGHT - 55, 40, 40), YELLOW, "◀"),
    Button("", (WIDTH // 2 - 20, HEIGHT - 55, 40, 40), YELLOW, "🎯"),
    Button("", (WIDTH // 2 + 30, HEIGHT - 55, 40, 40), YELLOW, "▶"),
    Button("GRAB", (WIDTH // 2 + 85, HEIGHT - 100, 80, 40), ORANGE, "💎"),
]

# --- DRAWING FUNCTIONS ---
def draw_grid(world, agent, show_debug=False):
    """Draw the game grid"""
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            color = GREEN2 if (x + y) % 2 == 0 else GREEN1
            rect = pygame.Rect(x * (CELL_SIZE + MARGIN), y * (CELL_SIZE + MARGIN), 
                              CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, color, rect)
            
            # Show visited cells and their percepts
            if (x, y) in agent.kb.visited:
                # Draw percepts text
                percepts = world.get_percepts((x, y))
                y_offset = 10
                
                if "Breeze" in percepts:
                    txt = small_font.render("🌪️ Breeze", True, BLUE)
                    screen.blit(txt, (rect.x + 5, rect.y + y_offset))
                    y_offset += 20
                
                if "Stench" in percepts:
                    txt = small_font.render("💨 Stench", True, RED)
                    screen.blit(txt, (rect.x + 5, rect.y + y_offset))
                    y_offset += 20
                
                if "Glitter" in percepts:
                    txt = small_font.render("✨ Glitter", True, YELLOW)
                    screen.blit(txt, (rect.x + 5, rect.y + y_offset))
                
                # Draw visited indicator
                pygame.draw.circle(screen, WHITE, (rect.x + 15, rect.y + 85), 5)
            
            # Debug mode: show actual world
            if show_debug:
                if (x, y) in world.pits:
                    pygame.draw.circle(screen, BLACK, rect.center, 25)
                    txt = font.render("PIT", True, WHITE)
                    screen.blit(txt, (rect.x + 30, rect.y + 35))
                
                if (x, y) == world.wumpus:
                    pygame.draw.circle(screen, RED, rect.center, 30)
                    txt = font.render("W", True, WHITE)
                    screen.blit(txt, (rect.x + 40, rect.y + 35))
                    if not world.wumpus_alive:
                        pygame.draw.line(screen, BLACK, (rect.x + 20, rect.y + 20),
                                       (rect.x + 80, rect.y + 80), 3)
                
                if (x, y) == world.gold and not agent.has_gold:
                    pygame.draw.circle(screen, YELLOW, rect.center, 20)
                    txt = font.render("G", True, BLACK)
                    screen.blit(txt, (rect.x + 43, rect.y + 35))
            
            # Show safe cells (KB inference)
            if (x, y) in agent.kb.safe and (x, y) not in agent.kb.visited:
                s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                s.fill((100, 255, 100, 80))
                screen.blit(s, (rect.x, rect.y))
            
            # Show possible dangers
            if (x, y) in agent.kb.possible_pits:
                txt = small_font.render("P?", True, RED)
                screen.blit(txt, (rect.x + 5, rect.y + 70))
            
            if (x, y) in agent.kb.possible_wumpus:
                txt = small_font.render("W?", True, PURPLE)
                screen.blit(txt, (rect.x + 75, rect.y + 70))
    
    # Draw agent
    agent_rect = pygame.Rect(agent.x * (CELL_SIZE + MARGIN), 
                            agent.y * (CELL_SIZE + MARGIN), 
                            CELL_SIZE, CELL_SIZE)
    
    # Agent direction indicator
    direction_symbols = {"RIGHT": "→", "UP": "↑", "LEFT": "←", "DOWN": "↓"}
    agent_color = GREEN1 if agent.alive else RED
    pygame.draw.circle(screen, agent_color, agent_rect.center, 25, 5)
    txt = icon_font.render(direction_symbols[agent.direction], True, BLACK)
    screen.blit(txt, (agent_rect.centerx - 10, agent_rect.centery - 15))
    
    if agent.has_gold:
        txt = small_font.render("💎", True, YELLOW)
        screen.blit(txt, (agent_rect.x + 70, agent_rect.y + 10))


def draw_ui(agent, status_msg):
    """Draw UI elements"""
    for b in buttons_right:
        b.draw()
    for b in buttons_manual:
        b.draw()
    
    text_box = pygame.Rect(10, GRID_SIZE * (CELL_SIZE + MARGIN) + 10, 
                          WIDTH - SIDE_PANEL - 20, 30)
    pygame.draw.rect(screen, WHITE, text_box, border_radius=10)
    pygame.draw.rect(screen, BLACK, text_box, 2, border_radius=10)
    screen.blit(font.render(status_msg, True, BLACK), (text_box.x + 10, text_box.y + 7))
    
    info_x = GRID_SIZE * (CELL_SIZE + MARGIN) + 20
    info_y = 180
    
    info_texts = [
        f"Score: {agent.score}",
        f"Arrow: {'Yes' if agent.has_arrow else 'No'}",
        f"Gold: {'Yes' if agent.has_gold else 'No'}",
        f"Position: ({agent.x}, {agent.y})",
        f"Direction: {agent.direction}",
        "",
        f"Visited: {len(agent.kb.visited)}",
        f"Safe cells: {len(agent.kb.safe)}",
        f"Possible pits: {len(agent.kb.possible_pits)}",
        f"Wumpus: {'Dead' if not agent.kb.wumpus_alive else 'Alive'}",
    ]
    
    for i, text in enumerate(info_texts):
        txt = small_font.render(text, True, BLACK)
        screen.blit(txt, (info_x, info_y + i * 20))

def main():
    world = World()
    agent = Agent()
    status_msg = "Ready. Use buttons or AUTO PLAY."
    auto_mode = False
    step_delay = 0
    show_debug = False 
    
    percepts = world.get_percepts((agent.x, agent.y))
    agent.kb.add_percept((agent.x, agent.y), percepts)
    
    running = True
    while running:
        screen.fill(BG)
        draw_grid(world, agent, show_debug)
        draw_ui(agent, status_msg)
        pygame.display.flip()
        clock.tick(FPS)
        
        if auto_mode and agent.alive:
            if step_delay > 0:
                step_delay -= 1
            else:
                step_delay = 15  
                
                if agent.has_gold and (agent.x, agent.y) == (0, 3):
                    status_msg = "🎉 Mission Complete! Exited with gold!"
                    auto_mode = False
                elif "Glitter" in world.get_percepts((agent.x, agent.y)):
                    status_msg = agent.grab_gold(world)
                    agent.path = []
                elif agent.has_arrow and agent.kb.wumpus_location:
                    wx, wy = agent.kb.wumpus_location
                    dx, dy = agent.get_direction_vector()
                    if (agent.x == wx and dy != 0) or (agent.y == wy and dx != 0):
                        status_msg = agent.shoot(world)
                    else:
                        status_msg = "Repositioning to shoot..."
                        agent.path = []
                elif agent.path:
                    next_pos = agent.path.pop(0)
                    dx_needed = next_pos[0] - agent.x
                    dy_needed = next_pos[1] - agent.y
                    
                    current_vec = agent.get_direction_vector()
                    if (dx_needed, dy_needed) != current_vec:
                        agent.turn_right()
                        agent.path.insert(0, next_pos) 
                        status_msg = "Turning..."
                    else:
                        status_msg = agent.move_forward(world)
                else:
                    if agent.has_gold:
                        agent.path = agent.find_path_to_safe_cell()
                        if not agent.path:
                            status_msg = "Can't find path home!"
                            auto_mode = False
                    else:
                        agent.path = agent.find_path_to_safe_cell()
                        if not agent.path:
                            status_msg = "No more safe cells to explore!"
                            auto_mode = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_d:
                    show_debug = not show_debug
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                
                if buttons_right[0].clicked(pos): 
                    world = World()
                    agent = Agent()
                    percepts = world.get_percepts((agent.x, agent.y))
                    agent.kb.add_percept((agent.x, agent.y), percepts)
                    status_msg = "World reset."
                    auto_mode = False
                
                elif buttons_right[1].clicked(pos): 
                    auto_mode = True
                    status_msg = "🤖 AI is thinking..."
                
                elif buttons_right[2].clicked(pos):  
                    auto_mode = False
                    status_msg = "Stopped."
                
                if not auto_mode and agent.alive:
                    if buttons_manual[0].clicked(pos): 
                        status_msg = agent.turn_left()
                    elif buttons_manual[1].clicked(pos): 
                        status_msg = agent.move_forward(world)
                    elif buttons_manual[2].clicked(pos):  
                        status_msg = agent.turn_right()
                    elif buttons_manual[3].clicked(pos):  
                        status_msg = agent.turn_left()
                    elif buttons_manual[4].clicked(pos): 
                        status_msg = agent.shoot(world)
                    elif buttons_manual[5].clicked(pos):  
                        status_msg = agent.turn_right()
                    elif buttons_manual[6].clicked(pos):  
                        status_msg = agent.grab_gold(world)
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()