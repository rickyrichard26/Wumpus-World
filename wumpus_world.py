import tkinter as tk
from tkinter import messagebox
import random
from typing import List, Tuple, Set, Dict

class WumpusWorld:
    def __init__(self, master):
        self.master = master
        self.master.title("Wumpus World - Knowledge-Based Agent")
        self.master.geometry("1000x700")
        self.master.configure(bg='#1a1a2e')
        
        self.GRID_SIZE = 4
        self.CELL_SIZE = 100
        
        self.world = []
        self.agent = {}
        self.knowledge_base = {}
        self.visited_cells = set()
        self.percepts = []
        self.game_status = 'playing'
        self.log = []
        self.auto_play = False
        
        self.setup_ui()
        self.initialize_world()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.master, bg='#1a1a2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title = tk.Label(main_frame, text="WUMPUS WORLD", 
                        font=('Arial', 24, 'bold'), 
                        bg='#1a1a2e', fg='#00ff88')
        title.pack(pady=(0, 10))
        
        subtitle = tk.Label(main_frame, text="Knowledge-Based Agent", 
                           font=('Arial', 12), 
                           bg='#1a1a2e', fg='#88aaff')
        subtitle.pack(pady=(0, 20))
        
        content_frame = tk.Frame(main_frame, bg='#1a1a2e')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        left_frame = tk.Frame(content_frame, bg='#2a2a3e', relief=tk.RAISED, bd=2)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        canvas_frame = tk.Frame(left_frame, bg='#2a2a3e')
        canvas_frame.pack(pady=20, padx=20)
        
        self.canvas = tk.Canvas(canvas_frame, 
                               width=self.GRID_SIZE * self.CELL_SIZE,
                               height=self.GRID_SIZE * self.CELL_SIZE,
                               bg='#1a1a2e', highlightthickness=0)
        self.canvas.pack()
        

        control_frame = tk.Frame(left_frame, bg='#2a2a3e')
        control_frame.pack(pady=10)
        
        btn_new = tk.Button(control_frame, text="🔄 New Game", 
                           command=self.initialize_world,
                           bg='#7700ff', fg='white', font=('Arial', 12, 'bold'),
                           padx=20, pady=10, relief=tk.FLAT, cursor='hand2')
        btn_new.grid(row=0, column=0, padx=5, pady=5)
        
        self.btn_auto = tk.Button(control_frame, text="▶ Auto Play", 
                                 command=self.toggle_auto_play,
                                 bg='#00aa00', fg='white', font=('Arial', 12, 'bold'),
                                 padx=20, pady=10, relief=tk.FLAT, cursor='hand2')
        self.btn_auto.grid(row=0, column=1, padx=5, pady=5)
        
        arrow_frame = tk.Frame(left_frame, bg='#2a2a3e')
        arrow_frame.pack(pady=10)
        
        tk.Button(arrow_frame, text="↑", command=lambda: self.manual_move('UP'),
                 bg='#0066cc', fg='white', font=('Arial', 16, 'bold'),
                 width=3, height=1, relief=tk.FLAT, cursor='hand2').grid(row=0, column=1, padx=2, pady=2)
        
        tk.Button(arrow_frame, text="←", command=lambda: self.manual_move('LEFT'),
                 bg='#0066cc', fg='white', font=('Arial', 16, 'bold'),
                 width=3, height=1, relief=tk.FLAT, cursor='hand2').grid(row=1, column=0, padx=2, pady=2)
        
        self.btn_shoot = tk.Button(arrow_frame, text="🏹", command=self.shoot_arrow,
                                   bg='#cc0000', fg='white', font=('Arial', 16, 'bold'),
                                   width=3, height=1, relief=tk.FLAT, cursor='hand2')
        self.btn_shoot.grid(row=1, column=1, padx=2, pady=2)
        
        tk.Button(arrow_frame, text="→", command=lambda: self.manual_move('RIGHT'),
                 bg='#0066cc', fg='white', font=('Arial', 16, 'bold'),
                 width=3, height=1, relief=tk.FLAT, cursor='hand2').grid(row=1, column=2, padx=2, pady=2)
        
        tk.Button(arrow_frame, text="↓", command=lambda: self.manual_move('DOWN'),
                 bg='#0066cc', fg='white', font=('Arial', 16, 'bold'),
                 width=3, height=1, relief=tk.FLAT, cursor='hand2').grid(row=2, column=1, padx=2, pady=2)
        
        right_frame = tk.Frame(content_frame, bg='#1a1a2e')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        
        status_frame = tk.LabelFrame(right_frame, text="Agent Status", 
                                     bg='#2a2a3e', fg='#00ff88',
                                     font=('Arial', 12, 'bold'), relief=tk.RAISED, bd=2)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_text = tk.Text(status_frame, height=7, width=30, 
                                  bg='#1a1a2e', fg='#88aaff',
                                  font=('Arial', 10), relief=tk.FLAT)
        self.status_text.pack(padx=10, pady=10)
        
        percept_frame = tk.LabelFrame(right_frame, text="Current Percepts", 
                                      bg='#2a2a3e', fg='#00ff88',
                                      font=('Arial', 12, 'bold'), relief=tk.RAISED, bd=2)
        percept_frame.pack(fill=tk.X, pady=5)
        
        self.percept_text = tk.Text(percept_frame, height=4, width=30, 
                                   bg='#1a1a2e', fg='#ffaa00',
                                   font=('Arial', 10), relief=tk.FLAT)
        self.percept_text.pack(padx=10, pady=10)
        
        log_frame = tk.LabelFrame(right_frame, text="Activity Log", 
                                 bg='#2a2a3e', fg='#00ff88',
                                 font=('Arial', 12, 'bold'), relief=tk.RAISED, bd=2)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, height=15, width=30, 
                               bg='#1a1a2e', fg='#cccccc',
                               font=('Arial', 9), relief=tk.FLAT, wrap=tk.WORD)
        self.log_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        legend_frame = tk.LabelFrame(right_frame, text="Legend", 
                                    bg='#2a2a3e', fg='#00ff88',
                                    font=('Arial', 12, 'bold'), relief=tk.RAISED, bd=2)
        legend_frame.pack(fill=tk.X, pady=5)
        
        legend_text = "🤖 Agent\n💨 Breeze (Pit nearby)\n👃 Stench (Wumpus)\n✨ Gold\n🏹 Shoot Arrow"
        legend_label = tk.Label(legend_frame, text=legend_text, 
                               bg='#2a2a3e', fg='#cccccc',
                               font=('Arial', 9), justify=tk.LEFT)
        legend_label.pack(padx=10, pady=10)
        
    def initialize_world(self):
        """Initialize the Wumpus World with random positions"""
        self.world = [[{
            'pit': False, 'wumpus': False, 'gold': False,
            'breeze': False, 'stench': False, 'safe': True
        } for _ in range(self.GRID_SIZE)] for _ in range(self.GRID_SIZE)]
        
        while True:
            wx, wy = random.randint(0, 3), random.randint(0, 3)
            if not (wx == 0 and wy == 3):
                self.world[wy][wx]['wumpus'] = True
                self.world[wy][wx]['safe'] = False
                break
        
        pits_placed = 0
        while pits_placed < 3:
            px, py = random.randint(0, 3), random.randint(0, 3)
            if (not (px == 0 and py == 3) and 
                not self.world[py][px]['pit'] and 
                not self.world[py][px]['wumpus']):
                self.world[py][px]['pit'] = True
                self.world[py][px]['safe'] = False
                pits_placed += 1
        
        while True:
            gx, gy = random.randint(0, 3), random.randint(0, 3)
            if (not (gx == 0 and gy == 3) and 
                not self.world[gy][gx]['pit'] and 
                not self.world[gy][gx]['wumpus']):
                self.world[gy][gx]['gold'] = True
                break
        
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                neighbors = self.get_neighbors(x, y)
                for nx, ny in neighbors:
                    if self.world[ny][nx]['pit']:
                        self.world[y][x]['breeze'] = True
                    if self.world[ny][nx]['wumpus']:
                        self.world[y][x]['stench'] = True
        
        self.agent = {
            'x': 0, 'y': 3, 'direction': 'RIGHT',
            'has_gold': False, 'has_arrow': True, 'alive': True
        }
        
        self.knowledge_base = {'0,3': {'safe': True, 'visited': True}}
        self.visited_cells = {'0,3'}
        self.percepts = []
        self.game_status = 'playing'
        self.log = ['Game started! Agent spawned at (0, 3)']
        self.auto_play = False
        
        self.update_display()
        self.add_log('Game started! Agent at (0, 3)')
        
    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Get valid neighboring cells"""
        neighbors = []
        if x > 0: neighbors.append((x-1, y))
        if x < self.GRID_SIZE-1: neighbors.append((x+1, y))
        if y > 0: neighbors.append((x, y-1))
        if y < self.GRID_SIZE-1: neighbors.append((x, y+1))
        return neighbors
    
    def perceive(self, x: int, y: int) -> List[str]:
        """Get percepts at given position"""
        cell = self.world[y][x]
        percepts = []
        
        if cell['breeze']:
            percepts.append('Breeze')
        if cell['stench']:
            percepts.append('Stench')
        if cell['gold'] and not self.agent['has_gold']:
            percepts.append('Glitter')
        if cell['pit']:
            percepts.append('Scream (Fell into Pit!)')
        if cell['wumpus']:
            percepts.append('Scream (Eaten by Wumpus!)')
            
        return percepts
    
    def update_knowledge_base(self, x: int, y: int, percepts: List[str]):
        """Update KB using forward chaining"""
        key = f"{x},{y}"
        
        self.knowledge_base[key] = {
            'visited': True,
            'safe': True,
            'breeze': 'Breeze' in percepts,
            'stench': 'Stench' in percepts,
            'gold': 'Glitter' in percepts
        }
        
        neighbors = self.get_neighbors(x, y)
        
        if 'Breeze' not in percepts and 'Stench' not in percepts:
            for nx, ny in neighbors:
                nkey = f"{nx},{ny}"
                if nkey not in self.knowledge_base:
                    self.knowledge_base[nkey] = {'safe': True}
                elif not self.knowledge_base[nkey].get('visited', False):
                    self.knowledge_base[nkey]['safe'] = True
        else:
            for nx, ny in neighbors:
                nkey = f"{nx},{ny}"
                if nkey not in self.knowledge_base:
                    self.knowledge_base[nkey] = {
                        'safe': False,
                        'maybe_wumpus': 'Stench' in percepts,
                        'maybe_pit': 'Breeze' in percepts
                    }
                elif not self.knowledge_base[nkey].get('visited', False):
                    if not self.knowledge_base[nkey].get('safe', False):
                        if 'Stench' in percepts:
                            self.knowledge_base[nkey]['maybe_wumpus'] = True
                        if 'Breeze' in percepts:
                            self.knowledge_base[nkey]['maybe_pit'] = True
    
    def find_safe_move(self) -> Tuple[int, int]:
        """Find a safe cell to move to"""
        x, y = self.agent['x'], self.agent['y']
        neighbors = self.get_neighbors(x, y)
        
        for nx, ny in neighbors:
            key = f"{nx},{ny}"
            kb_info = self.knowledge_base.get(key, {})
            if kb_info.get('safe', False) and not kb_info.get('visited', False):
                return (nx, ny)

        for nx, ny in neighbors:
            key = f"{nx},{ny}"
            if self.knowledge_base.get(key, {}).get('visited', False):
                return (nx, ny)
        
        return None
    
    def move_agent(self, new_x: int, new_y: int):
        """Move agent to new position"""
        if not self.agent['alive'] or self.game_status != 'playing':
            return
        
        self.agent['x'] = new_x
        self.agent['y'] = new_y
        
        percepts = self.perceive(new_x, new_y)
        self.percepts = percepts
        self.visited_cells.add(f"{new_x},{new_y}")
        
        cell = self.world[new_y][new_x]
        if cell['pit']:
            self.agent['alive'] = False
            self.game_status = 'lost'
            self.add_log(f'Agent fell into pit at ({new_x}, {new_y})! GAME OVER')
            messagebox.showwarning("Game Over", "Agent fell into a pit!")
        elif cell['wumpus']:
            self.agent['alive'] = False
            self.game_status = 'lost'
            self.add_log(f'Agent eaten by Wumpus at ({new_x}, {new_y})! GAME OVER')
            messagebox.showwarning("Game Over", "Agent eaten by Wumpus!")
        else:
            self.add_log(f'Moved to ({new_x}, {new_y}). Percepts: {", ".join(percepts) if percepts else "None"}')
            self.update_knowledge_base(new_x, new_y, percepts)
            
            if 'Glitter' in percepts and not self.agent['has_gold']:
                self.agent['has_gold'] = True
                self.add_log('Gold grabbed!')
                
                if new_x == 0 and new_y == 3:
                    self.game_status = 'won'
                    self.add_log('Agent escaped with gold! YOU WIN!')
                    messagebox.showinfo("Victory!", "You won! Agent escaped with the gold!")
        
        self.update_display()
    
    def manual_move(self, direction: str):
        """Manual movement control"""
        if not self.agent['alive'] or self.game_status != 'playing':
            return
        
        x, y = self.agent['x'], self.agent['y']
        new_x, new_y = x, y
        
        if direction == 'UP' and y > 0:
            new_y -= 1
        elif direction == 'DOWN' and y < self.GRID_SIZE - 1:
            new_y += 1
        elif direction == 'LEFT' and x > 0:
            new_x -= 1
        elif direction == 'RIGHT' and x < self.GRID_SIZE - 1:
            new_x += 1
        else:
            return
        
        self.agent['direction'] = direction
        self.move_agent(new_x, new_y)
    
    def shoot_arrow(self):
        """Shoot arrow in current direction"""
        if not self.agent['has_arrow'] or not self.agent['alive']:
            return
        
        x, y = self.agent['x'], self.agent['y']
        direction = self.agent['direction']
        
        target_x, target_y = x, y
        if direction == 'RIGHT':
            target_x += 1
        elif direction == 'LEFT':
            target_x -= 1
        elif direction == 'UP':
            target_y -= 1
        elif direction == 'DOWN':
            target_y += 1
        
        self.agent['has_arrow'] = False
        
        if (0 <= target_x < self.GRID_SIZE and 
            0 <= target_y < self.GRID_SIZE and 
            self.world[target_y][target_x]['wumpus']):
            
            self.world[target_y][target_x]['wumpus'] = False
            self.world[target_y][target_x]['safe'] = True
            
            # Remove stench
            for dy in range(self.GRID_SIZE):
                for dx in range(self.GRID_SIZE):
                    neighbors = self.get_neighbors(dx, dy)
                    has_wumpus = any(self.world[ny][nx]['wumpus'] for nx, ny in neighbors)
                    self.world[dy][dx]['stench'] = has_wumpus
            
            self.add_log(f'Arrow shot {direction}! Wumpus killed at ({target_x}, {target_y})!')
            messagebox.showinfo("Success!", "Wumpus killed!")
        else:
            self.add_log(f'Arrow shot {direction}! Missed.')
        
        self.update_display()
    
    def toggle_auto_play(self):
        """Toggle automatic playing"""
        self.auto_play = not self.auto_play
        if self.auto_play:
            self.btn_auto.config(text="⏸ Stop Auto", bg='#cc0000')
            self.auto_move()
        else:
            self.btn_auto.config(text="▶ Auto Play", bg='#00aa00')
    
    def auto_move(self):
        """Automatic movement using KB reasoning"""
        if not self.auto_play or not self.agent['alive'] or self.game_status != 'playing':
            self.auto_play = False
            self.btn_auto.config(text="▶ Auto Play", bg='#00aa00')
            return
        
        safe_move = self.find_safe_move()
        if safe_move:
            self.move_agent(safe_move[0], safe_move[1])
            self.master.after(800, self.auto_move)
        else:
            self.add_log('No safe moves available!')
            self.auto_play = False
            self.btn_auto.config(text="▶ Auto Play", bg='#00aa00')
    
    def update_display(self):
        """Update all display elements"""
        self.draw_board()
        self.update_status()
        self.update_percepts()
        self.update_log()
    
    def draw_board(self):
        """Draw the game board"""
        self.canvas.delete('all')
        
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                x1 = x * self.CELL_SIZE
                y1 = y * self.CELL_SIZE
                x2 = x1 + self.CELL_SIZE
                y2 = y1 + self.CELL_SIZE
                
                is_agent = (self.agent['x'] == x and self.agent['y'] == y)
                is_visited = f"{x},{y}" in self.visited_cells
                kb_info = self.knowledge_base.get(f"{x},{y}", {})
                
                if is_agent:
                    color = '#ffdd00'
                elif is_visited:
                    color = '#00aa44'
                elif kb_info.get('safe', False):
                    color = '#0066cc'
                else:
                    color = '#333344'
                
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='#666666', width=2)
                
                if is_visited:
                    cell = self.world[y][x]
                    
                    if cell['pit']:
                        self.canvas.create_text(x1+15, y1+15, text='🕳️', font=('Arial', 16))
                    if cell['wumpus']:
                        self.canvas.create_text(x2-15, y1+15, text='👹', font=('Arial', 16))
                    if cell['gold'] and not self.agent['has_gold']:
                        self.canvas.create_text(x1+15, y2-15, text='✨', font=('Arial', 16))
                    
                    if cell['breeze']:
                        self.canvas.create_text(x1+self.CELL_SIZE//2-15, y1+self.CELL_SIZE//2, 
                                              text='💨', font=('Arial', 16))
                    if cell['stench']:
                        self.canvas.create_text(x1+self.CELL_SIZE//2+15, y1+self.CELL_SIZE//2, 
                                              text='👃', font=('Arial', 16))
                
                if is_agent:
                    agent_symbol = '🤖' if self.agent['alive'] else '💀'
                    self.canvas.create_text(x1+self.CELL_SIZE//2, y1+self.CELL_SIZE//2, 
                                          text=agent_symbol, font=('Arial', 32))
                
                self.canvas.create_text(x2-10, y2-10, text=f"{x},{y}", 
                                      fill='#888888', font=('Arial', 8))
    
    def update_status(self):
        """Update agent status display"""
        self.status_text.delete(1.0, tk.END)
        status = f"""Position: ({self.agent['x']}, {self.agent['y']})
Direction: {self.agent['direction']}
Has Gold: {'✓' if self.agent['has_gold'] else '✗'}
Has Arrow: {'✓' if self.agent['has_arrow'] else '✗'}
Status: {'✓ Alive' if self.agent['alive'] else '✗ Dead'}

Game: {self.game_status.upper()}"""
        self.status_text.insert(1.0, status)
    
    def update_percepts(self):
        """Update percepts display"""
        self.percept_text.delete(1.0, tk.END)
        if self.percepts:
            percept_str = '\n'.join(f'• {p}' for p in self.percepts)
        else:
            percept_str = 'No percepts'
        self.percept_text.insert(1.0, percept_str)
    
    def update_log(self):
        """Update activity log"""
        self.log_text.delete(1.0, tk.END)
        log_str = '\n'.join(self.log[-15:])  
        self.log_text.insert(1.0, log_str)
    
    def add_log(self, message: str):
        """Add entry to activity log"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log.append(f'[{timestamp}] {message}')
        self.update_log()


def main():
    """Main function to run the Wumpus World game"""
    root = tk.Tk()
    app = WumpusWorld(root)
    root.mainloop()


if __name__ == "__main__":
    main()