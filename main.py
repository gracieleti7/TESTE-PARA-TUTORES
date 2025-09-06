# main.py
# Jogo Roguelike simples em PgZero
# Bibliotecas usadas: pgzero, math, random, Rect (pygame)

from random import randint, random
import math
from pygame import Rect

# --- Configurações da tela ---
WIDTH = 800
HEIGHT = 600
TILE_SIZE = 48
MAP_COLS = WIDTH // TILE_SIZE
MAP_ROWS = HEIGHT // TILE_SIZE

# --- Estados do jogo ---
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_GAME_OVER = "game_over"

MOVE_SPEED = 240.0  # pixels por segundo

# --- Função auxiliar ---
def clamp(valor, minimo, maximo):
    return max(minimo, min(maximo, valor))

# --- Classe para animação de sprites ---
class AnimadorSprite:
    def __init__(self, frames_idle, frames_walk, duracao=0.18):
        self.frames_idle = frames_idle[:]
        self.frames_walk = frames_walk[:]
        self.duracao = duracao
        self.tempo = 0.0
        self.indice = 0
        self.andando = False

    def atualizar(self, dt):
        self.tempo += dt
        frames = self.frames_walk if self.andando else self.frames_idle
        if not frames:
            return None
        if self.tempo >= self.duracao:
            self.tempo -= self.duracao
            self.indice = (self.indice + 1) % len(frames)
        return frames[self.indice]

# --- Classe para movimento em grade ---
class MovimentoGrade:
    def __init__(self, celula_inicial):
        self.cel_x, self.cel_y = celula_inicial
        self.x = (self.cel_x + 0.5) * TILE_SIZE
        self.y = (self.cel_y + 0.5) * TILE_SIZE
        self.alvo = (self.cel_x, self.cel_y)
        self.movendo = False

    def definir_alvo(self, celula):
        if celula != (self.cel_x, self.cel_y):
            self.alvo = celula
            self.movendo = True

    def atualizar(self, dt):
        tx = (self.alvo[0] + 0.5) * TILE_SIZE
        ty = (self.alvo[1] + 0.5) * TILE_SIZE
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)

        if dist < 1e-3:
            self.x, self.y = tx, ty
            self.cel_x, self.cel_y = self.alvo
            self.movendo = False
            return False

        passo = MOVE_SPEED * dt
        if passo >= dist:
            self.x, self.y = tx, ty
            self.cel_x, self.cel_y = self.alvo
            self.movendo = False
            return False

        nx, ny = dx / dist, dy / dist
        self.x += nx * passo
        self.y += ny * passo
        return True

    def posicao(self):
        return self.x, self.y

# --- Classe Herói ---
class Heroi:
    def __init__(self, celula_inicial):
        self.movimento = MovimentoGrade(celula_inicial)
        self.animador = AnimadorSprite(
            ["hero_idle_0", "hero_idle_1"],
            ["hero_walk_0", "hero_walk_1", "hero_walk_2", "hero_walk_3"],
            duracao=0.14,
        )
        self.vida = 3
        self.vivo = True
        self.timer_passos = 0.0

    def atualizar(self, dt):
        movendo = self.movimento.atualizar(dt)
        self.animador.andando = movendo
        imagem = self.animador.atualizar(dt)

        if movendo:
            self.timer_passos += dt
            if self.timer_passos > 0.28:
                self.timer_passos = 0.0
                if estado_jogo.som_ativo:
                    try:
                        sounds.step.play()
                    except:
                        pass
        else:
            self.timer_passos = 0.0

        return imagem

    def mover(self, dx, dy):
        if self.movimento.movendo:
            return
        novo_x = clamp(self.movimento.cel_x + dx, 0, MAP_COLS - 1)
        novo_y = clamp(self.movimento.cel_y + dy, 0, MAP_ROWS - 1)
        self.movimento.definir_alvo((novo_x, novo_y))

# --- Classe Inimigo ---
class Inimigo:
    def __init__(self, celula_inicial, raio=2):
        self.movimento = MovimentoGrade(celula_inicial)
        self.inicial = celula_inicial
        self.raio = raio
        self.animador = AnimadorSprite(
            ["enemy_idle_0", "enemy_idle_1"],
            ["enemy_walk_0", "enemy_walk_1", "enemy_walk_2"],
            duracao=0.18,
        )
        self.cooldown = 0.0
        self.escolher_alvo()

    def escolher_alvo(self):
        sx, sy = self.inicial
        alvo = (
            randint(max(0, sx - self.raio), min(MAP_COLS - 1, sx + self.raio)),
            randint(max(0, sy - self.raio), min(MAP_ROWS - 1, sy + self.raio)),
        )
        self.movimento.definir_alvo(alvo)

    def atualizar(self, dt):
        movendo = self.movimento.atualizar(dt)
        if not movendo and random() < 0.01:
            self.escolher_alvo()
        self.animador.andando = movendo
        if self.cooldown > 0:
            self.cooldown -= dt
        return self.animador.atualizar(dt)

    def tentar_dano(self, heroi):
        if self.cooldown > 0:
            return False
        if (self.movimento.cel_x == heroi.movimento.cel_x and
            self.movimento.cel_y == heroi.movimento.cel_y):
            self.cooldown = 1.0
            return True
        return False

# --- Estado geral do jogo ---
class EstadoJogo:
    def __init__(self):
        self.estado = STATE_MENU
        self.som_ativo = True
        self.heroi = Heroi((MAP_COLS // 2, MAP_ROWS // 2))
        self.inimigos = [Inimigo((2, 2)), Inimigo((MAP_COLS-3, 2)),
                         Inimigo((2, MAP_ROWS-3)), Inimigo((MAP_COLS-3, MAP_ROWS-3))]
        # Botões
        self.btn_start = Rect(WIDTH//2 - 120, 200, 240, 54)
        self.btn_som = Rect(WIDTH//2 - 120, 270, 240, 54)
        self.btn_sair = Rect(WIDTH//2 - 120, 340, 240, 54)

    def alternar_som(self):
        self.som_ativo = not self.som_ativo
        if not self.som_ativo:
            music.stop()
        else:
            try:
                music.play("bg_music")
            except:
                pass

    def novo_jogo(self):
        self.heroi = Heroi((MAP_COLS // 2, MAP_ROWS // 2))
        self.inimigos = [Inimigo((3, 3)), Inimigo((MAP_COLS-4, 3)),
                         Inimigo((3, MAP_ROWS-4)), Inimigo((MAP_COLS-4, MAP_ROWS-4))]
        self.estado = STATE_PLAYING
        if self.som_ativo:
            try:
                music.play("bg_music")
            except:
                pass

    def atualizar(self, dt):
        if self.estado != STATE_PLAYING:
            return
        self.heroi.atualizar(dt)
        for inimigo in self.inimigos:
            inimigo.atualizar(dt)
            if inimigo.tentar_dano(self.heroi):
                self.heroi.vida -= 1
                if self.som_ativo:
                    try:
                        sounds.hit.play()
                    except:
                        pass
                if self.heroi.vida <= 0:
                    self.heroi.vivo = False
                    self.estado = STATE_GAME_OVER

estado_jogo = EstadoJogo()

# --- Funções do PgZero ---
def draw():
    screen.clear()
    if estado_jogo.estado == STATE_MENU:
        desenhar_menu()
    elif estado_jogo.estado == STATE_PLAYING:
        desenhar_jogo()
    elif estado_jogo.estado == STATE_GAME_OVER:
        desenhar_game_over()

def desenhar_menu():
    screen.fill((20, 20, 40))
    screen.draw.text("Roguelike Simples", center=(WIDTH//2, 120), fontsize=48, color="white")
    desenhar_botao(estado_jogo.btn_start, "Começar")
    texto_som = "Som: LIGADO" if estado_jogo.som_ativo else "Som: DESLIGADO"
    desenhar_botao(estado_jogo.btn_som, texto_som)
    desenhar_botao(estado_jogo.btn_sair, "Sair")

def desenhar_botao(ret, texto):
    screen.draw.filled_rect(ret, (60, 60, 80))
    screen.draw.rect(ret, (200, 200, 220))
    screen.draw.textbox(texto, ret, align="center")

def desenhar_jogo():
    for c in range(MAP_COLS):
        for r in range(MAP_ROWS):
            cor = (40, 40, 40) if (c + r) % 2 == 0 else (50, 50, 50)
            screen.draw.filled_rect(Rect(c*TILE_SIZE, r*TILE_SIZE, TILE_SIZE, TILE_SIZE), cor)

    for inimigo in estado_jogo.inimigos:
        img = inimigo.animador.atualizar(0)
        x, y = inimigo.movimento.posicao()
        if img:
            screen.blit(img, (x - TILE_SIZE//2, y - TILE_SIZE//2))
        else:
            screen.draw.filled_circle((x, y), TILE_SIZE//3, (200, 50, 50))

    img_heroi = estado_jogo.heroi.animador.atualizar(0)
    hx, hy = estado_jogo.heroi.movimento.posicao()
    if img_heroi:
        screen.blit(img_heroi, (hx - TILE_SIZE//2, hy - TILE_SIZE//2))
    else:
        screen.draw.filled_circle((hx, hy), TILE_SIZE//2 - 4, (30, 120, 210))

    screen.draw.text(f"Vida: {estado_jogo.heroi.vida}", (10, 10), color="white")

def desenhar_game_over():
    screen.fill((0, 0, 0))
    screen.draw.text("GAME OVER", center=(WIDTH//2, HEIGHT//2 - 30), fontsize=72, color="red")
    screen.draw.text("Pressione Enter para voltar ao menu", center=(WIDTH//2, HEIGHT//2 + 40), fontsize=28, color="white")

def update(dt):
    if estado_jogo.estado == STATE_PLAYING:
        if not estado_jogo.heroi.movimento.movendo:
            if keyboard.left or keyboard.a:
                estado_jogo.heroi.mover(-1, 0)
            elif keyboard.right or keyboard.d:
                estado_jogo.heroi.mover(1, 0)
            elif keyboard.up or keyboard.w:
                estado_jogo.heroi.mover(0, -1)
            elif keyboard.down or keyboard.s:
                estado_jogo.heroi.mover(0, 1)
        estado_jogo.atualizar(dt)

def on_key_down(key):
    if key == keys.ESCAPE and estado_jogo.estado == STATE_PLAYING:
        estado_jogo.estado = STATE_MENU
    if key == keys.RETURN and estado_jogo.estado == STATE_GAME_OVER:
        estado_jogo.estado = STATE_MENU

def on_mouse_down(pos):
    if estado_jogo.estado == STATE_MENU:
        if estado_jogo.btn_start.collidepoint(pos):
            estado_jogo.novo_jogo()
        elif estado_jogo.btn_som.collidepoint(pos):
            estado_jogo.alternar_som()
        elif estado_jogo.btn_sair.collidepoint(pos):
            quit()


