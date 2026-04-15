import pygame
import sys
import random
from collections import deque

# --- CONFIG ---
GRID_SIZE = 4
CELL_SIZE = 100
MARGIN = 3
SIDE_PANEL = 300
BOTTOM_PANEL = 150
WIDTH = GRID_SIZE * (CELL_SIZE + MARGIN) + SIDE_PANEL
HEIGHT = GRID_SIZE * (CELL_SIZE + MARGIN) + BOTTOM_PANEL
FPS = 5  # Lebih lambat untuk AI mode

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
DARK_GREEN = (50, 150, 50)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wumpus World - KB Agent with Forward Chaining")
font = pygame.font.SysFont("arial", 16)
font_small = pygame.font.SysFont("arial", 14)
icon_font = pygame.font.SysFont("arial", 22, bold=True)
title_font = pygame.font.SysFont("arial", 18, bold=True)
clock = pygame.time.Clock()

# --- Load images atau buat placeholder ---
def create_placeholder_image(color, size=CELL_SIZE):
    surf = pygame.Surface((size, size))
    surf.fill(color)
    return surf

try:
    images = {
        "agent": pygame.image.load("image/agent.png"),
        "wumpus": pygame.image.load("image/wumpus.jpeg"),
        "pit": pygame.image.load("image/pit.png"),
        "gold": pygame.image.load("image/gold.png"),
    }
    for key in images:
        images[key] = pygame.transform.scale(images[key], (CELL_SIZE - 10, CELL_SIZE - 10))
except:
    # Fallback jika gambar tidak ada
    images = {
        "agent": create_placeholder_image(BLUE, CELL_SIZE - 10),
        "wumpus": create_placeholder_image(RED, CELL_SIZE - 10),
        "pit": create_placeholder_image(BLACK, CELL_SIZE - 10),
        "gold": create_placeholder_image(YELLOW, CELL_SIZE - 10),
    }

# --- BUTTON CLASS ---
class Button:
    def __init__(self, text, rect, color, icon=""):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.color = color
        self.icon = icon
        self.enabled = True

    def draw(self):
        color = self.color if self.enabled else GRAY
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=8)

        if self.icon != "" and self.text == "":
            icon_txt = icon_font.render(self.icon, True, BLACK)
            icon_rect = icon_txt.get_rect(center=self.rect.center)
            screen.blit(icon_txt, icon_rect)
        elif self.icon == "" and self.text != "":
            text_txt = font.render(self.text, True, BLACK)
            text_rect = text_txt.get_rect(center=self.rect.center)
            screen.blit(text_txt, text_rect)
        else:
            icon_txt = icon_font.render(self.icon, True, BLACK)
            text_txt = font.render(self.text, True, BLACK)
            total_width = icon_txt.get_width() + 6 + text_txt.get_width()
            start_x = self.rect.centerx - total_width // 2
            icon_rect = icon_txt.get_rect(midleft=(start_x, self.rect.centery))
            text_rect = text_txt.get_rect(midleft=(icon_rect.right + 6, self.rect.centery))
            screen.blit(icon_txt, icon_rect)
            screen.blit(text_txt, text_rect)

    def clicked(self, pos):
        return self.enabled and self.rect.collidepoint(pos)


# --- KNOWLEDGE BASE CLASS ---
class KnowledgeBase:
    def __init__(self, size=4):
        self.size = size
        self.visited = set()
        self.safe = set()
        self.breeze_at = set()
        self.stench_at = set()
        self.glitter_at = set()
        self.possible_pits = set()
        self.possible_wumpus = set()
        self.wumpus_location = None
        self.wumpus_alive = True
        
        # Start position is safe
        self.safe.add((0, 3))
        self.visited.add((0, 3))
    
    def get_neighbors(self, x, y):
        neighbors = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                neighbors.append((nx, ny))
        return neighbors
    
    def update(self, position, percept):
        """Update KB dengan Forward Chaining"""
        x, y = position
        self.visited.add((x, y))
        neighbors = self.get_neighbors(x, y)
        
        # RULE: Breeze logic
        if percept['breeze']:
            self.breeze_at.add((x, y))
            for nx, ny in neighbors:
                if (nx, ny) not in self.visited:
                    self.possible_pits.add((nx, ny))
        else:
            # No breeze = all neighbors safe from pits
            for nx, ny in neighbors:
                self.safe.add((nx, ny))
                if (nx, ny) in self.possible_pits:
                    self.possible_pits.remove((nx, ny))
        
        # RULE: Stench logic
        if percept['stench']:
            self.stench_at.add((x, y))
            if self.wumpus_alive:
                for nx, ny in neighbors:
                    if (nx, ny) not in self.visited:
                        self.possible_wumpus.add((nx, ny))
        else:
            # No stench = all neighbors safe from wumpus
            for nx, ny in neighbors:
                self.safe.add((nx, ny))
                if (nx, ny) in self.possible_wumpus:
                    self.possible_wumpus.remove((nx, ny))
        
        if percept['glitter']:
            self.glitter_at.add((x, y))
        
        # Deduce wumpus location
        if self.wumpus_alive and len(self.possible_wumpus) == 1:
            self.wumpus_location = list(self.possible_wumpus)[0]
    
    def is_safe(self, position):
        return (position in self.safe and 
                position not in self.possible_pits and 
                position not in self.possible_wumpus)
    
    def get_safe_unvisited_neighbors(self, position):
        x, y = position
        neighbors = self.get_neighbors(x, y)
        return [(nx, ny) for nx, ny in neighbors 
                if (nx, ny) not in self.visited and self.is_safe((nx, ny))]


# --- WUMPUS AGENT CLASS ---
class WumpusAgent:
    def __init__(self, world_size=4):
        self.kb = KnowledgeBase(world_size)
        self.world_size = world_size
        self.direction = 'right'  # right, up, left, down
        self.has_gold = False
        self.has_arrow = True
        self.alive = True
        self.score = 0
        self.plan = deque()
        self.returning_home = False
        
    def get_percept(self, pos, pits, wumpus, gold):
        """Generate percept based on position"""
        x, y = pos
        percept = {'breeze': False, 'stench': False, 'glitter': False}
        
        neighbors = self.kb.get_neighbors(x, y)
        
        # Check for breeze (pit nearby)
        for nx, ny in neighbors:
            if (nx, ny) in pits:
                percept['breeze'] = True
            if (nx, ny) == wumpus and self.kb.wumpus_alive:
                percept['stench'] = True
        
        # Check for glitter (gold at current position)
        if (x, y) == gold and not self.has_gold:
            percept['glitter'] = True
        
        return percept
    
    def find_path_bfs(self, start, goal):
        """BFS to find path through safe cells only"""
        if start == goal:
            return [start]
        
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            current, path = queue.popleft()
            x, y = current
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                next_pos = (nx, ny)
                
                if (0 <= nx < self.world_size and 0 <= ny < self.world_size and
                    next_pos not in visited and self.kb.is_safe(next_pos)):
                    
                    new_path = path + [next_pos]
                    
                    if next_pos == goal:
                        return new_path
                    
                    queue.append((next_pos, new_path))
                    visited.add(next_pos)
        
        return None
    
    def make_plan(self, current_pos):
        """Create action plan"""
        if self.returning_home:
            # Find path back to start
            path = self.find_path_bfs(current_pos, (0, 3))
            return path if path else []
        
        # Explore safe unvisited neighbors
        safe_neighbors = self.kb.get_safe_unvisited_neighbors(current_pos)
        if safe_neighbors:
            return [current_pos, safe_neighbors[0]]
        
        # Find path to any safe unvisited cell
        for x in range(self.world_size):
            for y in range(self.world_size):
                if (x, y) not in self.kb.visited and self.kb.is_safe((x, y)):
                    path = self.find_path_bfs(current_pos, (x, y))
                    if path:
                        return path
        
        # Return home if nothing to explore
        if current_pos != (0, 3):
            path = self.find_path_bfs(current_pos, (0, 3))
            return path if path else []
        
        return []


# --- WORLD CLASS ---
class WumpusWorld:
    def __init__(self):
        self.reset()
    
    def reset(self):
        # Generate random world
        self.pits = []
        while len(self.pits) < 3:
            x, y = random.randint(0, 3), random.randint(0, 3)
            if (x, y) not in self.pits and (x, y) != (0, 3):
                self.pits.append((x, y))
        
        valid_pos = [(x, y) for x in range(GRID_SIZE) for y in range(GRID_SIZE)
                     if (x, y) not in self.pits and (x, y) != (0, 3)]
        
        self.wumpus = random.choice(valid_pos)
        valid_pos.remove(self.wumpus)
        self.gold = random.choice(valid_pos)
        
        self.agent_pos = [0, 3]
        self.agent = WumpusAgent()
        self.game_over = False
        self.win = False
        self.status_msg = "Ready. Click START AI to begin."
        self.show_hidden = False  # Toggle untuk show/hide wumpus & pits


# --- GLOBAL STATE ---
world = WumpusWorld()
mode = "manual"
auto_running = False
step_delay = 0

# --- UI BUTTONS ---
buttons_right = [
    Button("START AI", (GRID_SIZE * (CELL_SIZE + MARGIN) + 20, 20, 260, 40), GREEN1),
    Button("STOP", (GRID_SIZE * (CELL_SIZE + MARGIN) + 20, 70, 125, 40), RED),
    Button("STEP", (GRID_SIZE * (CELL_SIZE + MARGIN) + 160, 70, 120, 40), ORANGE),
    Button("RESET", (GRID_SIZE * (CELL_SIZE + MARGIN) + 20, 120, 260, 40), GRAY),
    Button("SHOW WORLD", (GRID_SIZE * (CELL_SIZE + MARGIN) + 20, 170, 260, 40), PURPLE),
    Button("MANUAL MODE", (GRID_SIZE * (CELL_SIZE + MARGIN) + 20, 220, 260, 40), BLUE),
]

buttons_bottom = [
    Button("", (WIDTH // 2 - 90, HEIGHT - 100, 40, 40), YELLOW, "◄"),
    Button("", (WIDTH // 2 - 40, HEIGHT - 100, 40, 40), YELLOW, "▲"),
    Button("", (WIDTH // 2 + 10, HEIGHT - 100, 40, 40), YELLOW, "▼"),
    Button("", (WIDTH // 2 + 60, HEIGHT - 100, 40, 40), YELLOW, "►"),
    Button("GRAB", (WIDTH // 2 - 90, HEIGHT - 50, 70, 35), DARK_GREEN),
    Button("SHOOT", (WIDTH // 2 + 20, HEIGHT - 50, 70, 35), RED),
]

# --- HELPER FUNCTIONS ---
def draw_grid():
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            color = GREEN2 if (x + y) % 2 == 0 else GREEN1
            rect = pygame.Rect(x * (CELL_SIZE + MARGIN), y * (CELL_SIZE + MARGIN), 
                              CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, color, rect)
            
            # Draw KB info
            pos = (x, y)
            
            # Visited cells - lighter shade
            if pos in world.agent.kb.visited:
                s = pygame.Surface((CELL_SIZE, CELL_SIZE))
                s.set_alpha(50)
                s.fill(WHITE)
                screen.blit(s, (x * (CELL_SIZE + MARGIN), y * (CELL_SIZE + MARGIN)))
            
            # Safe cells - green border
            if pos in world.agent.kb.safe and pos not in world.agent.kb.visited:
                pygame.draw.rect(screen, DARK_GREEN, rect, 3)
            
            # Possible danger - warning indicators
            if pos in world.agent.kb.possible_pits:
                text = font_small.render("P?", True, RED)
                screen.blit(text, (x * (CELL_SIZE + MARGIN) + 5, 
                                  y * (CELL_SIZE + MARGIN) + 5))
            
            if pos in world.agent.kb.possible_wumpus:
                text = font_small.render("W?", True, RED)
                screen.blit(text, (x * (CELL_SIZE + MARGIN) + CELL_SIZE - 25, 
                                  y * (CELL_SIZE + MARGIN) + 5))
            
            # Show breeze/stench indicators
            if pos in world.agent.kb.breeze_at:
                pygame.draw.circle(screen, BLUE, 
                                 (x * (CELL_SIZE + MARGIN) + 15,
                                  y * (CELL_SIZE + MARGIN) + CELL_SIZE - 15), 5)
            
            if pos in world.agent.kb.stench_at:
                pygame.draw.circle(screen, RED,
                                 (x * (CELL_SIZE + MARGIN) + CELL_SIZE - 15,
                                  y * (CELL_SIZE + MARGIN) + CELL_SIZE - 15), 5)
            
            # Show world elements
            if world.show_hidden or mode == "manual":
                if pos in world.pits:
                    screen.blit(images["pit"], (x * (CELL_SIZE + MARGIN) + 5, 
                                                y * (CELL_SIZE + MARGIN) + 5))
                if pos == world.wumpus and world.agent.kb.wumpus_alive:
                    screen.blit(images["wumpus"], (x * (CELL_SIZE + MARGIN) + 5,
                                                   y * (CELL_SIZE + MARGIN) + 5))
            
            if pos == world.gold and not world.agent.has_gold:
                screen.blit(images["gold"], (x * (CELL_SIZE + MARGIN) + 5,
                                            y * (CELL_SIZE + MARGIN) + 5))
    
    # Draw agent
    ax, ay = world.agent_pos
    screen.blit(images["agent"], (ax * (CELL_SIZE + MARGIN) + 5,
                                  ay * (CELL_SIZE + MARGIN) + 5))

def draw_ui():
    # Draw buttons
    for b in buttons_right:
        b.draw()
    
    if mode == "manual":
        for b in buttons_bottom:
            b.draw()
    
    # Status box
    text_box = pygame.Rect(10, GRID_SIZE * (CELL_SIZE + MARGIN) + 10, 
                          WIDTH - SIDE_PANEL - 20, 120)
    pygame.draw.rect(screen, WHITE, text_box, border_radius=10)
    pygame.draw.rect(screen, BLACK, text_box, 2, border_radius=10)
    
    # Status message
    y_offset = text_box.y + 10
    lines = world.status_msg.split('\n')
    for line in lines:
        screen.blit(font.render(line, True, BLACK), (text_box.x + 10, y_offset))
        y_offset += 20
    
    # Info panel di kanan
    info_y = 280
    info_x = GRID_SIZE * (CELL_SIZE + MARGIN) + 20
    
    texts = [
        f"Mode: {mode.upper()}",
        f"Score: {world.agent.score}",
        f"Has Gold: {world.agent.has_gold}",
        f"Has Arrow: {world.agent.has_arrow}",
        f"Position: {tuple(world.agent_pos)}",
        "",
        "KB Status:",
        f"Visited: {len(world.agent.kb.visited)}",
        f"Safe: {len(world.agent.kb.safe)}",
        f"Possible Pits: {len(world.agent.kb.possible_pits)}",
        f"Possible Wumpus: {len(world.agent.kb.possible_wumpus)}",
    ]
    
    for text in texts:
        screen.blit(font_small.render(text, True, BLACK), (info_x, info_y))
        info_y += 18

def move_agent(dx, dy):
    """Manual move"""
    nx, ny = world.agent_pos[0] + dx, world.agent_pos[1] + dy
    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
        world.agent_pos = [nx, ny]
        world.agent.score -= 1
        
        # Check hazards
        if tuple(world.agent_pos) in world.pits:
            world.status_msg = "You fell into a pit! GAME OVER"
            world.game_over = True
            world.agent.alive = False
            world.agent.score -= 1000
        elif tuple(world.agent_pos) == world.wumpus and world.agent.kb.wumpus_alive:
            world.status_msg = "Wumpus got you! GAME OVER"
            world.game_over = True
            world.agent.alive = False
            world.agent.score -= 1000
        else:
            world.status_msg = f"Moved to {nx, ny}"
            # Update KB
            percept = world.agent.get_percept(tuple(world.agent_pos), 
                                             world.pits, world.wumpus, world.gold)
            world.agent.kb.update(tuple(world.agent_pos), percept)

def grab_gold():
    if tuple(world.agent_pos) == world.gold and not world.agent.has_gold:
        world.agent.has_gold = True
        world.agent.score += 1000
        world.status_msg = "Gold grabbed! Return to start (0,3)"
    else:
        world.status_msg = "No gold here!"

def shoot_arrow():
    if not world.agent.has_arrow:
        world.status_msg = "No arrow left!"
        return
    
    world.agent.has_arrow = False
    world.agent.score -= 10
    
    # Check if wumpus in line of sight (simplified - just check neighbors)
    ax, ay = world.agent_pos
    if world.wumpus in world.agent.kb.get_neighbors(ax, ay):
        world.agent.kb.wumpus_alive = False
        world.agent.kb.possible_wumpus.clear()
        world.agent.score += 500
        world.status_msg = "Wumpus killed!"
    else:
        world.status_msg = "Arrow missed!"

def ai_step():
    """Execute one AI step"""
    if world.game_over:
        return
    
    pos = tuple(world.agent_pos)
    
    # Get percept and update KB
    percept = world.agent.get_percept(pos, world.pits, world.wumpus, world.gold)
    world.agent.kb.update(pos, percept)
    
    status_parts = [f"At {pos}"]
    if percept['breeze']: status_parts.append("Feel breeze!")
    if percept['stench']: status_parts.append("Smell stench!")
    if percept['glitter']: status_parts.append("See glitter!")
    
    world.status_msg = " | ".join(status_parts)
    
    # Check for gold
    if percept['glitter'] and not world.agent.has_gold:
        world.agent.has_gold = True
        world.agent.score += 1000
        world.agent.returning_home = True
        world.status_msg += "\nGold grabbed! Returning home..."
        return
    
    # Check win condition
    if world.agent.has_gold and pos == (0, 3):
        world.game_over = True
        world.win = True
        world.status_msg = "SUCCESS! Agent returned with gold!"
        return
    
    # Shoot wumpus if known location
    if (world.agent.kb.wumpus_location and world.agent.has_arrow and
        world.agent.kb.wumpus_location in world.agent.kb.get_neighbors(*pos)):
        world.agent.has_arrow = False
        world.agent.score -= 10
        world.agent.kb.wumpus_alive = False
        world.agent.kb.possible_wumpus.clear()
        world.agent.kb.safe.add(world.agent.kb.wumpus_location)
        world.agent.score += 500
        world.status_msg += "\nWumpus killed!"
        return
    
    # Make plan and move
    if not world.agent.plan:
        plan = world.agent.make_plan(pos)
        if plan and len(plan) > 1:
            world.agent.plan = deque(plan[1:])  # Skip current position
    
    if world.agent.plan:
        next_pos = world.agent.plan.popleft()
        world.agent_pos = list(next_pos)
        world.agent.score -= 1
        
        # Check hazards
        if next_pos in world.pits:
            world.status_msg = "Agent fell into pit! GAME OVER"
            world.game_over = True
            world.agent.alive = False
            world.agent.score -= 1000
        elif next_pos == world.wumpus and world.agent.kb.wumpus_alive:
            world.status_msg = "Wumpus killed agent! GAME OVER"
            world.game_over = True
            world.agent.alive = False
            world.agent.score -= 1000
    else:
        world.status_msg += "\nNo safe path found. Stopping."
        world.game_over = True

# --- BUTTON HANDLERS ---
def handle_button(btn):
    global mode, auto_running, world
    
    if btn.text == "START AI":
        mode = "auto"
        auto_running = True
        world.status_msg = "AI Mode: Agent exploring..."
        buttons_right[0].enabled = False
        buttons_right[5].enabled = False
    
    elif btn.text == "STOP":
        auto_running = False
        world.status_msg = "AI Stopped."
    
    elif btn.text == "STEP":
        if mode == "auto":
            ai_step()
    
    elif btn.text == "RESET":
        world = WumpusWorld()
        mode = "manual"
        auto_running = False
        buttons_right[0].enabled = True
        buttons_right[5].enabled = True
    
    elif btn.text == "SHOW WORLD":
        world.show_hidden = not world.show_hidden
        btn.text = "HIDE WORLD" if world.show_hidden else "SHOW WORLD"
    
    elif btn.text == "MANUAL MODE":
        mode = "manual"
        auto_running = False
        world.status_msg = "Manual mode. Use arrow buttons."
        buttons_right[0].enabled = True
        buttons_right[5].enabled = True

# --- MAIN LOOP ---
running = True
frame_count = 0

while running:
    screen.fill(BG)
    draw_grid()
    draw_ui()
    pygame.display.flip()
    clock.tick(FPS)
    
    # AI auto step
    if auto_running and not world.game_over:
        frame_count += 1
        if frame_count >= 15:  # Execute every 15 frames (slower)
            ai_step()
            frame_count = 0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            
            # Check right panel buttons
            for b in buttons_right:
                if b.clicked(pos):
                    handle_button(b)
            
            # Check manual control buttons
            if mode == "manual" and not world.game_over:
                if buttons_bottom[0].clicked(pos): move_agent(-1, 0)
                if buttons_bottom[1].clicked(pos): move_agent(0, -1)
                if buttons_bottom[2].clicked(pos): move_agent(0, 1)
                if buttons_bottom[3].clicked(pos): move_agent(1, 0)
                if buttons_bottom[4].clicked(pos): grab_gold()
                if buttons_bottom[5].clicked(pos): shoot_arrow()

pygame.quit()
sys.exit()