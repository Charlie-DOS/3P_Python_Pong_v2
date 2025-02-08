import os
import pygame
import math
import random
import json

# Initialize Pygame
pygame.init()

# Controls - Changed to use clearer names and added pause control
P1_UP = pygame.K_s
P1_DOWN = pygame.K_a
P2_UP = pygame.K_DOWN
P2_DOWN = pygame.K_UP
P3_UP = pygame.K_o
P3_DOWN = pygame.K_l
LANGUAGE_KEY = pygame.K_TAB
QUIT_KEY = pygame.K_ESCAPE
START_KEY = pygame.K_RETURN
PAUSE_KEY = pygame.K_p

MENU = "menu"
PLAYING = "playing"
PAUSED = "paused"
GAME_OVER = "game_over"


# Constants
WINDOW_SIZE = 800
PADDLE_LENGTH = 100
PADDLE_WIDTH = 10
BALL_RADIUS = 10
BALL_SPEED = 5
PADDLE_SPEED = 8
HEX_RADIUS = WINDOW_SIZE // 3
main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, "data")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

# Set up display
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Hexagonal Pong")

# utils
def load_sound(name):
    class NoneSound:
        def play(self):
            pass

    if not pygame.mixer or not pygame.mixer.get_init():
        return NoneSound()

    fullname = os.path.join(data_dir, name)
    sound = pygame.mixer.Sound(fullname)

    return sound

def get_font_for_language(language, size=36):
    """Returns a suitable font depending on the selected language."""
    if language == "ja":
        return pygame.font.SysFont(["hiraginosans", "osaka", "arialunicode", "notosanscjkjp", "msgothic", "meiryo"], size)
    return pygame.font.Font(None, size)  # Default Pygame font for other languages


# Load the language file
def load_translations(file_path="lang.json"):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Translation file '{file_path}' not found!")
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# Fallback function for missing translations
def get_text(language, key):
    """Retrieve translated text, falling back to English if not found."""
    return TRANSLATIONS.get(language, {}).get(key, TRANSLATIONS["en"].get(key, key))

# Load translations once at startup
TRANSLATIONS = load_translations()



def get_hex_walls():
    """Return list of wall segments as (start_point, end_point) tuples"""
    walls = []
    center_x = WINDOW_SIZE // 2
    center_y = WINDOW_SIZE // 2
    

    for i in range(6):
        angle1 = math.pi/3 * i
        angle2 = math.pi/3 * (i + 1)
        x1 = center_x + HEX_RADIUS * math.cos(angle1)
        y1 = center_y + HEX_RADIUS * math.sin(angle1)
        x2 = center_x + HEX_RADIUS * math.cos(angle2)
        y2 = center_y + HEX_RADIUS * math.sin(angle2)
        walls.append(((x1, y1), (x2, y2)))
    
    return walls

class Paddle:
    def __init__(self, angle, color, player):
        self.angle = math.radians(angle)  # Convert to radians
        self.color = color
        self.player = player
        self.position = 0  # Position along the hexagon side
        self.score = 0
        
    def get_endpoints(self):
        center_x = WINDOW_SIZE // 2
        center_y = WINDOW_SIZE // 2

        # Choose one or the other sign to orient correctly:
        wall_angle = self.angle + math.pi/2  

        # Move the center point *inward* by inset
        inset = PADDLE_WIDTH / 2 + 5  # enough margin to keep the paddle fully inside
        side_radius = (HEX_RADIUS * math.cos(math.pi / 6)) - inset

        base_x = center_x + side_radius * math.cos(self.angle)
        base_y = center_y + side_radius * math.sin(self.angle)


        # Vector for half the paddle length parallel to the wall
        paddle_vec_x = (PADDLE_LENGTH / 2) * math.cos(wall_angle)
        paddle_vec_y = (PADDLE_LENGTH / 2) * math.sin(wall_angle)

        # Offset along the wall for movement
        offset_x = self.position * (PADDLE_LENGTH / 2) * math.cos(wall_angle)
        offset_y = self.position * (PADDLE_LENGTH / 2) * math.sin(wall_angle)

        start_pos = (
            base_x + paddle_vec_x + offset_x,
            base_y + paddle_vec_y + offset_y
        )
        end_pos = (
            base_x - paddle_vec_x + offset_x,
            base_y - paddle_vec_y + offset_y
        )
        return start_pos, end_pos
    
    def draw(self):
        start_pos, end_pos = self.get_endpoints()
        pygame.draw.line(screen, self.color, start_pos, end_pos, PADDLE_WIDTH)

class Ball:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.x = WINDOW_SIZE // 2
        self.y = WINDOW_SIZE // 2
        angle = random.uniform(0, 2 * math.pi)
        self.dx = BALL_SPEED * math.cos(angle)
        self.dy = BALL_SPEED * math.sin(angle)
        self.flashing = True
        self.flash_start_time = pygame.time.get_ticks()

    def move(self):
        if not self.flashing:
            self.x += self.dx
            self.y += self.dy
    
    def draw(self):
        # If flashing, toggle visibility
        if self.flashing:
            elapsed_time = pygame.time.get_ticks() - self.flash_start_time
            if elapsed_time > 500:  # End flashing after 500ms
                self.flashing = False
            elif (elapsed_time // 100) % 2 == 0:  # Flash toggle every 100ms
                pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), BALL_RADIUS)
        else:
            # Draw the ball normally
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), BALL_RADIUS)

    def line_collision(self, p1, p2):
        """Check for collision with a line segment and return collision point if any"""
        x1, y1 = p1
        x2, y2 = p2
        
        # Vector from start of line to ball
        v1x = self.x - x1
        v1y = self.y - y1
        
        # Vector representing the line
        v2x = x2 - x1
        v2y = y2 - y1
        
        # Length of line squared
        l2 = v2x * v2x + v2y * v2y
        if l2 == 0:
            return None
        
        # Projection of v1 onto v2
        t = max(0, min(1, (v1x * v2x + v1y * v2y) / l2))
        
        # Closest point on line to ball
        px = x1 + t * v2x
        py = y1 + t * v2y
        
        # Distance from ball to line
        dx = self.x - px
        dy = self.y - py
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance <= BALL_RADIUS:
            # Normalize the normal vector
            if distance > 0:
                nx = dx / distance
                ny = dy / distance
            else:
                nx = 0
                ny = 1
                
            # Reflect velocity vector
            dot_product = self.dx * nx + self.dy * ny
            self.dx = self.dx - 2 * dot_product * nx
            self.dy = self.dy - 2 * dot_product * ny
            
            # Move ball out of collision
            self.x = px + nx * (BALL_RADIUS + 1)
            self.y = py + ny * (BALL_RADIUS + 1)
            
            return True
            
        return False

    def check_paddle_collision(self, paddle):
        """Check for collision with a paddle"""
        start_pos, end_pos = paddle.get_endpoints()
        return self.line_collision(start_pos, end_pos)

    def check_wall_collisions(self, walls, paddles):
        """Check for collisions with walls, returning if it's a scoring wall"""
        for i, wall in enumerate(walls):
            if self.line_collision(wall[0], wall[1]):
                # Check if this wall is a scoring wall (opposite to a paddle)
                for paddle in paddles:
                    # Get the wall number opposite to this paddle (add 3 positions in hexagon)
                    paddle_wall_num = int(math.degrees(paddle.angle) / 60) % 6
                    if i == paddle_wall_num:
                        return "scoring_wall"
                return "bounce_wall"      
        return None

def draw_menu(language="en"):
    """Draw the main menu screen"""
    overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE))
    overlay.set_alpha(120)
    screen.blit(overlay, (0, 0))
    
    # Draw title
    title_font = get_font_for_language(language, 72)
    title_text = title_font.render(get_text(language, "title"), True, WHITE)
    title_rect = title_text.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 4))
    screen.blit(title_text, title_rect)
    
    # Draw start instruction
    font = get_font_for_language(language)
    start_text = font.render(get_text(language, "start"), True, WHITE)
    start_rect = start_text.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2))
    screen.blit(start_text, start_rect)
    
    # Draw controls
    control_y = WINDOW_SIZE // 2 + 50
    for line in get_text(language, "controls"):
        control_text = font.render(line, True, WHITE)
        control_rect = control_text.get_rect(center=(WINDOW_SIZE // 2, control_y))
        screen.blit(control_text, control_rect)
        control_y += 30

def draw_pause_menu(language="en"):
    """Draw the pause menu overlay"""
    # Create semi-transparent overlay
    overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE))
    overlay.set_alpha(80)
    screen.blit(overlay, (0, 0))
    
    # Draw pause text
    font = get_font_for_language(language, 72)
    pause_text = font.render(get_text(language, "paused"), True, WHITE)
    pause_rect = pause_text.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2))
    screen.blit(pause_text, pause_rect)
    
    # Draw resume instruction
    font = get_font_for_language(language)
    resume_text = font.render(get_text(language, "resume"), True, WHITE)
    resume_rect = resume_text.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 + 50))
    screen.blit(resume_text, resume_rect)

def main():
    # Initialize game state and language
    game_state = MENU
    language = "en"
    
    # Create game objects
    paddles = [
        Paddle(270, RED, "P1"),
        Paddle(30, GREEN, "P2"),
        Paddle(150, BLUE, "P3")
    ]
    ball = Ball()
    walls = get_hex_walls()
    last_paddle = None
    winner = None
    
    clock = pygame.time.Clock()
    running = True
    last_game_state = None
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == LANGUAGE_KEY:
                    available_languages = list(TRANSLATIONS.keys())
                    current_index = available_languages.index(language)
                    language = available_languages[(current_index + 1) % len(available_languages)]  # Cycle through languages
                elif event.key == START_KEY:
                    if game_state in [MENU, GAME_OVER]:
                        game_state = PLAYING
                        ball.reset()
                        for paddle in paddles:
                            paddle.score = 0
                elif event.key == PAUSE_KEY and game_state in [PLAYING, PAUSED]:
                    game_state = PAUSED if game_state == PLAYING else PLAYING
                elif event.key == QUIT_KEY:
                    running = False

                # Load Sound Effects
        p1_s = load_sound("p1.wav")
        p2_s = load_sound("p2.wav")
        p3_s = load_sound("p3.wav")
        score_s = load_sound("score.wav")
        wall_s = load_sound("wall.wav")
        win_s = load_sound("win.wav")

        # --- ALWAYS DRAW GAME SCREEN FIRST (before menus) ---
        screen.fill(BLACK)
        
        # Draw walls
        pygame.draw.line(screen, WHITE, walls[1][0], walls[1][1], 2)
        pygame.draw.line(screen, WHITE, walls[3][0], walls[3][1], 2)
        pygame.draw.line(screen, WHITE, walls[5][0], walls[5][1], 2)

        # Draw paddles and scores
        font = pygame.font.Font(None, 36)
        for paddle in paddles:
            paddle.draw()
            score_text = font.render(str(paddle.score), True, paddle.color)
            text_x = WINDOW_SIZE // 2 + (HEX_RADIUS + 30) * math.cos(paddle.angle)
            text_y = WINDOW_SIZE // 2 + (HEX_RADIUS + 30) * math.sin(paddle.angle)
            screen.blit(score_text, (text_x - 10, text_y - 10))
        
        # PLAYING state - Game logic
        if game_state == PLAYING:
            keys = pygame.key.get_pressed()
            
            # Handle paddle movement
            if keys[P1_UP]: paddles[0].position = min(1.6, paddles[0].position + PADDLE_SPEED/100)
            if keys[P1_DOWN]: paddles[0].position = max(-1.6, paddles[0].position - PADDLE_SPEED/100)
            
            if keys[P2_UP]: paddles[1].position = min(1.65, paddles[1].position + PADDLE_SPEED/100)
            if keys[P2_DOWN]: paddles[1].position = max(-1.5, paddles[1].position - PADDLE_SPEED/100)
            
            if keys[P3_UP]: paddles[2].position = min(1.5, paddles[2].position + PADDLE_SPEED/100)
            if keys[P3_DOWN]: paddles[2].position = max(-1.65, paddles[2].position - PADDLE_SPEED/100)

            # Move ball and handle collisions
            ball.move()
            
            # Check for collisions with paddles
            for paddle in paddles:
                if ball.check_paddle_collision(paddle):
                    last_paddle = paddle
                    if paddle.player == "P1":
                        p1_s.play()
                    elif paddle.player == "P2":
                        p2_s.play()
                    elif paddle.player == "P3":
                        p3_s.play()


            # Handle wall collisions
            collision_type = ball.check_wall_collisions(walls, paddles)
            if collision_type == "scoring_wall":
                # If scoring wall hit, last active paddle gets the point
                # If the last paddle hits it's own scoring wall, decrease points
                score_s.play()
                min_dist = float('inf')
                losing_paddle = None
                for paddle in paddles:
                    paddle_x = WINDOW_SIZE//2 + HEX_RADIUS * math.cos(paddle.angle)
                    paddle_y = WINDOW_SIZE//2 + HEX_RADIUS * math.sin(paddle.angle)
                    dist = math.sqrt((ball.x - paddle_x)**2 + (ball.y - paddle_y)**2)
                    if dist < min_dist:
                        min_dist = dist
                        losing_paddle = paddle
                
                if last_paddle == losing_paddle:
                    if losing_paddle.score > 0:
                        losing_paddle.score -= 1
                elif last_paddle:
                    last_paddle.score += 1
                last_paddle = None
                ball.reset()
            if collision_type == "bounce_wall":
                wall_s.play()

            # Check for winner
            for paddle in paddles:
                if paddle.score >= 10:
                    game_state = GAME_OVER
                    winner = paddle
                    break
            
            ball.draw()
            pygame.display.flip()

            

        # Handle different game states
        if game_state == MENU:
            draw_menu(language)
            pygame.display.flip()
            continue
            
        elif game_state == PAUSED:
            if last_game_state != PAUSED:
                draw_pause_menu(language)
                pygame.display.flip()
                last_game_state = game_state   

            continue

        elif game_state == GAME_OVER:
            screen.fill(BLACK)
            win_s.play()
            # Draw winner announcement
            font = get_font_for_language(language, 72)
            winner_text = f"{winner.player} {get_text(language, 'winner')}"
            text = font.render(winner_text, True, winner.color)
            text_rect = text.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2))
            screen.blit(text, text_rect)
            
            # Draw instructions
            font = get_font_for_language(language)
            play_again = font.render(get_text(language, "play_again"), True, WHITE)
            quit_text = font.render(get_text(language, "quit"), True, WHITE)
            
            play_again_rect = play_again.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 + 50))
            quit_rect = quit_text.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 + 90))
            
            screen.blit(play_again, play_again_rect)
            screen.blit(quit_text, quit_rect)
            pygame.display.flip()
            continue
        clock.tick(60)
        
        last_game_state = game_state

    pygame.quit()

if __name__ == "__main__":
    main()