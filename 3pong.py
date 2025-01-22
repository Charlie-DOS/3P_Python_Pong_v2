import os
import pygame
import math
import random

# Initialize Pygame
pygame.init()

# Controls
P1_1 = pygame.K_s
P1_2 = pygame.K_a
P2_1 = pygame.K_DOWN
P2_2 = pygame.K_UP
P3_1 = pygame.K_o
P3_2 = pygame.K_l
QUIT_GAME = pygame.K_ESCAPE

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

def main():
    # Create paddles at centers of walls: 30° (top-right), 150° (bottom-right), 270° (left)
    paddles = [
        Paddle(270, RED, "P1"),   # Actually defends ~90° side
        Paddle(30,  GREEN, "P2"), # Actually defends ~210° side
        Paddle(150, BLUE, "P3")   # Actually defends ~330° side
    ]

    last_paddle = None

    ball = Ball()
    clock = pygame.time.Clock()
    walls = get_hex_walls()
    game_over = False
    winner = None
    
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Load Sound Effects
        p1_s = load_sound("p1.wav")
        p2_s = load_sound("p2.wav")
        p3_s = load_sound("p3.wav")
        score_s = load_sound("score.wav")
        wall_s = load_sound("wall.wav")
        win_s = load_sound("win.wav")

        # Handle paddle movement
        keys = pygame.key.get_pressed()
        # Player 1 controls (A/S)
        if keys[P1_1]:
            paddles[0].position = min(1.6, paddles[0].position + PADDLE_SPEED/100)
        if keys[P1_2]:
            paddles[0].position = max(-1.6, paddles[0].position - PADDLE_SPEED/100)
            
        # Player 2 controls (Up/Down)
        if keys[P2_1]:
            paddles[1].position = min(1.65, paddles[1].position + PADDLE_SPEED/100)
        if keys[P2_2]:
            paddles[1].position = max(-1.5, paddles[1].position - PADDLE_SPEED/100)
            
        # Player 3 controls (O/L)
        if keys[P3_1]:
            paddles[2].position = min(1.5, paddles[2].position + PADDLE_SPEED/100)
        if keys[P3_2]:
            paddles[2].position = max(-1.65, paddles[2].position - PADDLE_SPEED/100)
        
        # esc to quit game
        if keys[QUIT_GAME]:
            running = False

        # If the game is over, skip the gameplay logic
        if game_over:
            # Display the winner
            win_s.play()
            font = pygame.font.Font(None, 72)
            winner_text = f"{winner.player} WINS!"
            text = font.render(winner_text, True, winner.color)
            text_rect = text.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2))
            screen.blit(text, text_rect)

            pygame.display.flip()
            continue  # Skip the rest of the loop when game is over

        # Move ball
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

        collision_type = ball.check_wall_collisions(walls, paddles)
        if collision_type == "scoring_wall":
            # If scoring wall hit, last active paddle gets the point
            # If the last paddle hits it's own scoring wall, decrease points
            score_s.play()
            min_dist = float('inf')
            losing_paddle = None
            for paddle in paddles:
                hex_radius = WINDOW_SIZE // 3
                paddle_x = WINDOW_SIZE//2 + hex_radius * math.cos(paddle.angle)
                paddle_y = WINDOW_SIZE//2 + hex_radius * math.sin(paddle.angle)
                dist = math.sqrt((ball.x - paddle_x)**2 + (ball.y - paddle_y)**2)
                if dist < min_dist:
                    min_dist = dist
                    losing_paddle = paddle
            if last_paddle == losing_paddle:
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
                game_over = True
                winner = paddle
                break

        # Draw everything
        screen.fill(BLACK)
        
        # Draw hexagon border (modified to draw only bounce walls)
        pygame.draw.line(screen, WHITE, walls[1][0], walls[1][1], 2)
        pygame.draw.line(screen, WHITE, walls[3][0], walls[3][1], 2)
        pygame.draw.line(screen, WHITE, walls[5][0], walls[5][1], 2)

        # Draw paddles and scores
        font = pygame.font.Font(None, 36)
        for i, paddle in enumerate(paddles):
            paddle.draw()
            score_text = font.render(str(paddle.score), True, paddle.color)
            text_x = WINDOW_SIZE // 2 + (HEX_RADIUS + 30) * math.cos(paddle.angle)
            text_y = WINDOW_SIZE // 2 + (HEX_RADIUS + 30) * math.sin(paddle.angle)
            screen.blit(score_text, (text_x - 10, text_y - 10))
        
        ball.draw()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()