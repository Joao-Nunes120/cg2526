"""
Projeto de Computação Gráfica 2025/2026 
"""

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from PIL import Image
import sys, math, time

# ---------- Config ----------
WINDOW_W, WINDOW_H = 1200, 800

# ---------- State ----------
last_time = time.time()
state = {
    'car_pos': [0.0, 0.0, 0.0],
    'car_heading': 0.0,
    'car_speed': 0.0,
    'steer_angle': 0.0,
    'left_door_open': False,
    'right_door_open': False,
    'garage_open': False,
    'camera_mode': 0,
    'cam_azim': 30.0,
    'cam_elev': 20.0,
    'cam_dist': 5,
    'show_help': True,
    'wheel_spin': 0.0,
    'wheel_rotation': 0.0
}

keys = { 'w': False, 'a': False, 's': False, 'd': False }

door_base_top = (0,0,0)
door_base_bottom = (0,0,0)
door_base_rear = (0,0,0)
door_rear_bottom = (0,0,0)

# ---- movimento suave ----
MOVE_STEP = 0.03
TURN_FACTOR = 0.03
STEER_STEP = 0.5
WHEEL_SPIN_STEP = 4


# ---------- Materials ----------
MATERIALS = {
    'blue': ([0.02,0.02,0.1,1.0],[0.05,0.05,0.7,1.0],[0.5,0.5,0.6,1.0],40),
    'metal': ([0.15,0.15,0.15,1.0],[0.6,0.6,0.6,1.0],[0.9,0.9,0.9,1.0],80),
    'rubber': ([0.02,0.02,0.02,1.0],[0.05,0.05,0.05,1.0],[0.1,0.1,0.1,1.0],5),
    'glass': ([0.3,0.25,0.05,0.3],[1.0,0.9,0.3,0.3],[1.0,0.95,0.5,0.3],10),
    'wood': ([0.12,0.06,0.02,1.0],[0.6,0.3,0.12,1.0],[0.2,0.18,0.15,1.0],10),
    'grass': ([0.0,0.1,0.0,1.0],[0.1,0.6,0.1,1.0],[0.2,0.3,0.2,1.0],20),
    'car_red': ([0.2,0.0,0.0,1.0],[0.8,0.1,0.1,1.0],[0.9,0.3,0.3,1.0],50),
    'hood_blue': ([0.0,0.0,0.3,1.0],[0.2,0.3,1.0,1.0],[0.1,0.1,0.2,1.0],10),
    'fender_metal': ([0.08,0.08,0.09,1.0],[0.12,0.12,0.13,1.0],[0.10,0.10,0.10,1.0],5.0),
    'rim': ([0.08,0.08,0.08,1.0],[0.35,0.35,0.35,1.0],[0.20,0.20,0.20,1.0],40.0),
    "glass": ([0.2,0.4,0.45,0.25],[0.2,0.4,0.45,0.25],[0.8,0.9,1.0,0.25],20.0),
    "carbon_dark": ([0.02,0.02,0.02,1.0],[0.08,0.08,0.08,1.0],[0.15,0.15,0.15,1.0],40.0)
}

textures = {}
quadric = None

# ---------- Helpers ----------
def set_material(name):
    amb,dif,spec,shin = MATERIALS[name]
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, amb)
    glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, dif)
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, spec)
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, shin)

def init_quadric():
    global quadric
    if quadric is None:
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)
        gluQuadricTexture(quadric, GL_TRUE)

def make_checker_texture(tile_count=16, tile_size=8):
    size = tile_count * tile_size
    img = Image.new('RGB', (size,size))
    pixels = img.load()
    for y in range(size):
        for x in range(size):
            tx = (x // tile_size) % 2
            ty = (y // tile_size) % 2
            if (tx ^ ty) == 0:
                pixels[x,y] = (200,200,200)
            else:
                pixels[x,y] = (70,70,70)
    return img

def load_texture_from_image(img, name):
    data = img.tobytes('raw','RGB',0,-1)
    texid = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texid)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGB, img.width, img.height, GL_RGB, GL_UNSIGNED_BYTE, data)
    textures[name] = texid
    return texid

# ---------- Scene ----------
def draw_ground():
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, textures.get('ground', 0))
    set_material('wood')
    glPushMatrix()
    glTranslatef(0, -0.01, 0)
    size = 60.0
    repeat = 30.0
    glBegin(GL_QUADS)
    glNormal3f(0,1,0)
    glTexCoord2f(0,0); glVertex3f(-size,0,-size)
    glTexCoord2f(repeat,0); glVertex3f(size,0,-size)
    glTexCoord2f(repeat,repeat); glVertex3f(size,0,size)
    glTexCoord2f(0,repeat); glVertex3f(-size,0,size)
    glEnd()
    glPopMatrix()
    glDisable(GL_TEXTURE_2D)


# ---------- Garage ----------
def draw_garage():

    cx = -1.7
    cz = 15.0

    width  = 8.0
    depth  = 8.0
    height = 4.0

    left   = cx - width/2
    right  = cx + width/2
    front  = cz - depth/2   
    back   = cz + depth/2  

    y0 = 0.0
    y1 = height

    # Porta
    door_w = 6.0
    door_h = 3.0

    dl = cx - door_w/2
    dr = cx + door_w/2
    dt = door_h

    set_material("blue")

    
    glNormal3f(0, 0, 1)
    glBegin(GL_QUADS)
    glVertex3f(left,  y0, back)
    glVertex3f(right, y0, back)
    glVertex3f(right, y1, back)
    glVertex3f(left,  y1, back)
    glEnd()

    glNormal3f(-1, 0, 0)
    glBegin(GL_QUADS)
    glVertex3f(left, y0, front)
    glVertex3f(left, y1, front)
    glVertex3f(left, y1, back)
    glVertex3f(left, y0, back)
    glEnd()

    glNormal3f(1, 0, 0)
    glBegin(GL_QUADS)
    glVertex3f(right, y0, back)
    glVertex3f(right, y1, back)
    glVertex3f(right, y1, front)
    glVertex3f(right, y0, front)
    glEnd()

    glNormal3f(0, -1, 0)
    glBegin(GL_QUADS)
    glVertex3f(left,  y1, front)
    glVertex3f(left,  y1, back)
    glVertex3f(right, y1, back)
    glVertex3f(right, y1, front)
    glEnd()

    #parede frontal com buraco para porta
    glNormal3f(0, 0, -1)

    glBegin(GL_QUADS)
    glVertex3f(left, y0, front)
    glVertex3f(left, y1, front)
    glVertex3f(dl, y1, front)
    glVertex3f(dl, y0, front)
    glEnd()

    glBegin(GL_QUADS)
    glVertex3f(dr, y0, front)
    glVertex3f(dr,y1, front)
    glVertex3f(right,y1, front)
    glVertex3f(right,y0, front)
    glEnd()

    glBegin(GL_QUADS)
    glVertex3f(dl, y1, front)
    glVertex3f(dl, dt, front)
    glVertex3f(dr, dt, front)
    glVertex3f(dr, y1, front)
    glEnd()

    draw_garage_door()


def draw_garage_door():

    cx = -1.7
    cz = 15.0
    depth = 8.0

    door_w = 6.0
    door_h = 3.0
    door_t = 0.15

    front = cz - depth/2  

    #angulo porta
    angle = 100 if state['garage_open'] else 0

    glPushMatrix()

    glTranslatef(cx, 0, front)

    
    #angulo e direção abertura
    glTranslatef(0, door_h, 0)
    glRotatef(angle, 1, 0, 0)

    glTranslatef(0, -door_h, 0)

    set_material("metal")

    glPushMatrix()
    glTranslatef(0, door_h/2, 0)
    glScalef(door_w, door_h, door_t)
    glutSolidCube(1.0)
    glPopMatrix()

    glPopMatrix()

def draw_tree(x, z):
    set_material('wood')
    glPushMatrix()
    glTranslatef(x, 0, z)
    glTranslatef(0, 1.0, 0)
    glScalef(0.25, 4.0, 0.25)
    glutSolidCube(1.0)
    glPopMatrix()

    set_material('grass')
    glPushMatrix()
    glTranslatef(x, 2.3, z)
    glScalef(1.5, 1.7, 1.5)
    glutSolidSphere(0.7, 18, 14)
    glPopMatrix()

def draw_lamp_post(x,z):
    set_material('metal')
    glPushMatrix()
    glTranslatef(x,0,z)
    glTranslatef(0,1.5,0)
    glScalef(0.12,3.0,0.12)
    glutSolidCube(1.0)
    glPopMatrix()

    set_material('glass')
    glPushMatrix()
    glTranslatef(x,3.0,z)
    glutSolidSphere(0.18,16,12)
    glPopMatrix()

def draw_chassis():
    glPushMatrix()
    set_material('car_red')

    z_front = 1.75
    z_mid = 0.70
    z_rear = -1.75

    front_width = 1.4
    mid_width   = 1.55
    rear_width  = 1.70

    fw = front_width / 2.0
    mw = mid_width   / 2.0
    rw = rear_width  / 2.0

    h_top = 0.55
    h_front_lower = 0.25
    h_mid_lower = 0.25
    h_rear_lower = 0.25

    # =============================
    #            TOP
    # =============================
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0) # para cima
    glVertex3f(-fw, h_top, z_front)
    glVertex3f( fw, h_top, z_front)
    glVertex3f( mw, h_top, z_mid)
    glVertex3f(-mw, h_top, z_mid)
    glEnd()

    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0) # para cima
    glVertex3f(-mw, h_top, z_mid)
    glVertex3f( mw, h_top, z_mid)
    glVertex3f( rw, h_top, z_rear)
    glVertex3f(-rw, h_top, z_rear)
    glEnd()

    # =============================
    #            BASE
    # =============================
    glBegin(GL_QUADS)
    glNormal3f(0, -1, 0) # para baixo
    glVertex3f(-fw, h_front_lower,z_front)
    glVertex3f(-mw, h_mid_lower,z_mid)
    glVertex3f( mw, h_mid_lower,z_mid)
    glVertex3f( fw, h_front_lower,z_front)
    glEnd()

    glBegin(GL_QUADS)
    glNormal3f(0, -1, 0)  # para baixo
    glVertex3f(-mw, h_mid_lower,z_mid)
    glVertex3f(-rw, h_rear_lower,z_rear)
    glVertex3f( rw, h_rear_lower,z_rear)
    glVertex3f( mw, h_mid_lower,z_mid)
    glEnd()

    # =============================
    #      LATERAL ESQUERDA
    # =============================
    glBegin(GL_QUADS)
    glNormal3f(-1, 0, 0)  
    glVertex3f(-fw, h_top,  z_front)
    glVertex3f(-fw, h_front_lower, z_front)
    glVertex3f(-mw, h_mid_lower, z_mid)
    glVertex3f(-mw, h_top, z_mid)
    glEnd()

    glBegin(GL_QUADS)
    glNormal3f(-1, 0, 0)  
    glVertex3f(-mw, h_top, z_mid)
    glVertex3f(-mw, h_mid_lower, z_mid)
    glVertex3f(-rw, h_rear_lower, z_rear)
    glVertex3f(-rw, h_top, z_rear)
    glEnd()

    # =============================
    #      LATERAL DIREITA
    # =============================
    glBegin(GL_QUADS)
    glNormal3f(1, 0, 0)
    glVertex3f(fw, h_top, z_front)
    glVertex3f(fw, h_front_lower, z_front)
    glVertex3f(mw, h_mid_lower,z_mid)
    glVertex3f(mw, h_top,z_mid)
    glEnd()

    glBegin(GL_QUADS)
    glNormal3f(1, 0, 0)  
    glVertex3f(mw, h_top,z_mid)
    glVertex3f(mw, h_mid_lower,z_mid)
    glVertex3f(rw, h_rear_lower,z_rear)
    glVertex3f(rw, h_top,z_rear)
    glEnd()

    # =============================
    #            TRASEIRA
    # =============================
    glBegin(GL_QUADS)
    glNormal3f(0, 0, -1)  
    glVertex3f(-rw, h_top,z_rear)
    glVertex3f(-rw, h_rear_lower,z_rear)
    glVertex3f( rw, h_rear_lower,z_rear)
    glVertex3f( rw, h_top,z_rear)
    glEnd()

    glPopMatrix()

def draw_hood():
   
    glPushMatrix()
 
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, textures["carbon"])

    hood_length = 1.1

    width = 1.20
    fw = width / 2.0
    rw = width / 2.0

    chassis_top = 0.55

    h_front = chassis_top + 0.07
    h_rear = chassis_top + 0.27

    z_front = 3.5 / 2.0
    z_rear = z_front - hood_length

    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)

    glTexCoord2f(0.0, 0.0)
    glVertex3f(-fw, h_front,z_front)

    glTexCoord2f(1.0, 0.0)
    glVertex3f( fw, h_front,z_front)

    glTexCoord2f(1.0, 1.0)
    glVertex3f( rw, h_rear,z_rear)

    glTexCoord2f(0.0, 1.0)
    glVertex3f(-rw, h_rear,z_rear)

    glEnd()

    glDisable(GL_TEXTURE_2D)

    glBegin(GL_QUADS)
    glNormal3f(-0.7, 0.4, 0)
    glVertex3f(-rw, h_rear, z_rear)
    glVertex3f(-rw, chassis_top, z_rear)
    glVertex3f(-fw, chassis_top, z_front)
    glVertex3f(-fw, h_front, z_front)
    glEnd()

    glBegin(GL_QUADS)
    glNormal3f(0.7, 0.4, 0)
    glVertex3f( rw, h_rear, z_rear)
    glVertex3f( fw, h_front, z_front)
    glVertex3f( fw, chassis_top,z_front)
    glVertex3f( rw, chassis_top, z_rear)
    glEnd()

    glPopMatrix()


def draw_front_bumper():
    glPushMatrix()
    set_material('car_red')

    z_chassis_front = 1.75
    z_front = 1.95

    h_top = 0.55
    h_bottom = 0.25

    bumper_width = 1.20
    bw = bumper_width / 2.0          

    capo_front_width = 1.20 / 2.0   

    # -------------------------
    # entrada ar
    # -------------------------
    grill_width  = 0.60
    gw = grill_width / 2.0           

    grill_top    = 0.50
    grill_bottom = 0.33

    grill_depth  = 0.05
    z_back = z_front - grill_depth   

    #painel inclinado
    glBegin(GL_QUADS)

    glNormal3f(0, 0.6, 0.8)  

    glVertex3f(-capo_front_width, 0.62, z_chassis_front)
    glVertex3f( capo_front_width, 0.62, z_chassis_front)
    glVertex3f( bw,h_top, z_front)
    glVertex3f(-bw,h_top, z_front)
    glEnd()

    # Faixa de cima
    glBegin(GL_QUADS)
    glNormal3f(0, 0, 1)
    glVertex3f(-bw, h_top,z_front)
    glVertex3f( bw, h_top,z_front)
    glVertex3f( bw, grill_top,z_front)
    glVertex3f(-bw, grill_top,z_front)
    glEnd()

    # Faixa de baixo
    glBegin(GL_QUADS)
    glNormal3f(0, 0, 1)
    glVertex3f(-bw, grill_bottom, z_front)
    glVertex3f( bw, grill_bottom, z_front)
    glVertex3f( bw, h_bottom, z_front)
    glVertex3f(-bw, h_bottom,z_front)
    glEnd()

    # Faixa esquerda
    glBegin(GL_QUADS)
    glNormal3f(0, 0, 1)
    glVertex3f(-bw, grill_top, z_front)
    glVertex3f(-gw, grill_top,z_front)
    glVertex3f(-gw, grill_bottom,z_front)
    glVertex3f(-bw, grill_bottom,z_front)
    glEnd()

    # Faixa direita
    glBegin(GL_QUADS)
    glNormal3f(0, 0, 1)
    glVertex3f( gw, grill_top,z_front)
    glVertex3f( bw, grill_top,z_front)
    glVertex3f( bw, grill_bottom,z_front)
    glVertex3f( gw, grill_bottom,z_front)
    glEnd()

    #paredes da entrada de ar (dar profunidade)
    # Esquerda
    glBegin(GL_QUADS)
    glNormal3f(-1, 0, 0)
    glVertex3f(-capo_front_width, 0.62, z_chassis_front)
    glVertex3f(-capo_front_width, h_bottom,z_chassis_front)
    glVertex3f(-bw, h_bottom,z_front)
    glVertex3f(-bw,h_top, z_front)
    glEnd()

    # Direita
    glBegin(GL_QUADS)
    glNormal3f(1, 0, 0)
    glVertex3f(capo_front_width, 0.62,z_chassis_front)
    glVertex3f(capo_front_width, h_bottom,z_chassis_front)
    glVertex3f(bw,h_bottom,z_front)
    glVertex3f(bw,h_top,z_front)
    glEnd()


    set_material('car_red')

    # Teto interno
    glBegin(GL_QUADS)
    glNormal3f(0, -1, 0)
    glVertex3f(-gw, grill_top, z_front)
    glVertex3f( gw, grill_top, z_front)
    glVertex3f( gw, grill_top, z_back)
    glVertex3f(-gw, grill_top, z_back)
    glEnd()

    # Piso interno
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glVertex3f(-gw, grill_bottom, z_front)
    glVertex3f( gw, grill_bottom, z_front)
    glVertex3f( gw, grill_bottom, z_back)
    glVertex3f(-gw, grill_bottom, z_back)
    glEnd()

    # Parede esquerda interna
    glBegin(GL_QUADS)
    glNormal3f(-1, 0, 0)
    glVertex3f(-gw, grill_top,z_front)
    glVertex3f(-gw, grill_bottom, z_front)
    glVertex3f(-gw, grill_bottom, z_back)
    glVertex3f(-gw, grill_top,z_back)
    glEnd()

    # Parede direita interna
    glBegin(GL_QUADS)
    glNormal3f(1, 0, 0)
    glVertex3f( gw, grill_top,z_front)
    glVertex3f( gw, grill_bottom,z_front)
    glVertex3f( gw, grill_bottom, z_back)
    glVertex3f( gw, grill_top,z_back)
    glEnd()

    # Fundo do túnel
    set_material('rubber')
    glBegin(GL_QUADS)
    glNormal3f(0, 0, -1)
    glVertex3f(-gw, grill_top,z_back)
    glVertex3f( gw, grill_top,z_back)
    glVertex3f( gw, grill_bottom, z_back)
    glVertex3f(-gw, grill_bottom, z_back)
    glEnd()

    glPopMatrix()



def draw_fender_upper():
    glPushMatrix()
    set_material('fender_metal')

    import numpy as np

    def N(a, b, c):
        v1 = b - a
        v2 = c - a
        n = np.cross(v1, v2)
        return n / np.linalg.norm(n)

    chassis_top = 0.55
    h_front = chassis_top + 0.07
    h_rear = chassis_top + 0.27

    z_front = 3.5 / 2.0
    hood_length = 1.1
    z_rear = z_front - hood_length

    hood_half = 0.60

    fender_front = hood_half + 0.10
    fender_rear = hood_half + 0.20

    L1 = np.array((-hood_half, h_front, z_front))
    L2 = np.array((-hood_half, h_rear, z_rear))
    L3 = np.array((-fender_rear, h_rear - 0.05, z_rear))
    L4 = np.array((-fender_front, h_front - 0.05, z_front))

    normal_left = N(L1, L2, L3)

    
    R1 = np.array((hood_half, h_front, z_front))
    R2 = np.array((hood_half, h_rear, z_rear))
    R3 = np.array((fender_rear, h_rear - 0.05, z_rear))
    R4 = np.array((fender_front, h_front - 0.05, z_front))

    normal_right = N(R1, R4, R3)

    glBegin(GL_QUADS)
    glNormal3f(*normal_left)
    glVertex3f(*L1)
    glVertex3f(*L2)
    glVertex3f(*L3)
    glVertex3f(*L4)

    glNormal3f(*normal_right)
    glVertex3f(*R1)
    glVertex3f(*R4)
    glVertex3f(*R3)
    glVertex3f(*R2)

    glEnd()
    glPopMatrix()

def draw_fender_middle_and_lower():
    glPushMatrix()
    set_material('fender_metal')

    import numpy as np

    def N(a, b, c):
        v1 = np.subtract(b, a)
        v2 = np.subtract(c, a)
        n = np.cross(v1, v2)
        return n / np.linalg.norm(n)

    chassis_top = 0.55
    chassis_base = 0.25

    z_front = 1.75
    hood_length = 1.1
    z_rear = z_front - hood_length 

    hood_half = 0.60

    fender_top_front = hood_half + 0.10
    fender_top_rear = hood_half + 0.20

    fender_mid_front = hood_half + 0.18
    fender_mid_rear = hood_half + 0.27

    fender_low_front = hood_half + 0.23
    fender_low_rear = hood_half + 0.33

    h_top_front = chassis_top + 0.07
    h_top_rear = chassis_top + 0.27

    h_mid_front = h_top_front - 0.15
    h_mid_rear = h_top_rear - 0.18

    h_low_front = chassis_base
    h_low_rear = chassis_base

    # =============================
    # CAMADA MÉDIA
    # =============================

    L1 = np.array((-fender_top_front, h_top_front - 0.05, z_front))
    L2 = np.array((-fender_top_rear, h_top_rear - 0.05, z_rear))
    L3 = np.array((-fender_mid_rear, h_mid_rear, z_rear))
    L4 = np.array((-fender_mid_front, h_mid_front, z_front))

    normal_mid_left = N(L1, L2, L3)

    glBegin(GL_QUADS)
    glNormal3f(*normal_mid_left)
    glVertex3f(*L1)
    glVertex3f(*L2)
    glVertex3f(*L3)
    glVertex3f(*L4)

    R1 = np.array((fender_top_front, h_top_front - 0.05, z_front))
    R2 = np.array((fender_mid_front, h_mid_front, z_front))
    R3 = np.array((fender_mid_rear, h_mid_rear, z_rear))
    R4 = np.array((fender_top_rear, h_top_rear - 0.05, z_rear))

    normal_mid_right = N(R1, R2, R3)

    glNormal3f(*normal_mid_right)
    glVertex3f(*R1)
    glVertex3f(*R2)
    glVertex3f(*R3)
    glVertex3f(*R4)
    glEnd()

    # =============================
    # CAMADA INFERIOR
    # =============================

    L5 = np.array((-fender_mid_front, h_mid_front, z_front))
    L6 = np.array((-fender_mid_rear, h_mid_rear, z_rear))
    L7 = np.array((-fender_low_rear, h_low_rear, z_rear))
    L8 = np.array((-fender_low_front, h_low_front, z_front))

    normal_low_left = N(L5, L6, L7)

    glBegin(GL_QUADS)
    glNormal3f(*normal_low_left)
    glVertex3f(*L5)
    glVertex3f(*L6)
    glVertex3f(*L7)
    glVertex3f(*L8)

    R5 = np.array((fender_mid_front, h_mid_front, z_front))
    R6 = np.array((fender_low_front, h_low_front, z_front))
    R7 = np.array((fender_low_rear, h_low_rear, z_rear))
    R8 = np.array((fender_mid_rear, h_mid_rear, z_rear))

    normal_low_right = N(R5, R6, R7)

    glNormal3f(*normal_low_right)
    glVertex3f(*R5)
    glVertex3f(*R6)
    glVertex3f(*R7)
    glVertex3f(*R8)
    glEnd()

    glPopMatrix()

def draw_fender_transition():
    glPushMatrix()
    set_material('car_red')

    import numpy as np

    def N(a, b, c):
        v1 = np.subtract(b, a)
        v2 = np.subtract(c, a)
        n = np.cross(v1, v2)
        n = n / np.linalg.norm(n)
        return n

    top_bump = np.array((0.60, 0.55, 1.95))
    mid_bump = np.array((0.60, 0.40, 1.95))
    low_bump = np.array((0.60, 0.25, 1.95))

    top_fend = np.array((0.70, 0.57, 1.75))
    mid_fend = np.array((0.78, 0.47, 1.75))
    low_fend = np.array((0.83, 0.25, 1.75))

    # direita
    n_right = N(mid_bump, low_bump, low_fend)

    # TOP right
    glBegin(GL_QUADS)
    glNormal3f(*n_right)
    glVertex3f(*top_bump)
    glVertex3f(*mid_bump)
    glVertex3f(*mid_fend)
    glVertex3f(*top_fend)
    glEnd()

    # mid right
    glBegin(GL_QUADS)
    glNormal3f(*n_right)
    glVertex3f(*mid_bump)
    glVertex3f(*low_bump)
    glVertex3f(*low_fend)
    glVertex3f(*mid_fend)
    glEnd()

    # esquerda
    def mirror(v):
        return np.array((-v[0], v[1], v[2]))

    tb = mirror(top_bump)
    mb = mirror(mid_bump)
    lb = mirror(low_bump)
    tf = mirror(top_fend)
    mf = mirror(mid_fend)
    lf = mirror(low_fend)

    n_left = -N(mb, lb, lf)

    # top left
    glBegin(GL_QUADS)
    glNormal3f(*n_left)
    glVertex3f(*tb)
    glVertex3f(*mb)
    glVertex3f(*mf)
    glVertex3f(*tf)
    glEnd()

    # lower left
    glBegin(GL_QUADS)
    glNormal3f(*n_left)
    glVertex3f(*mb)
    glVertex3f(*lb)
    glVertex3f(*lf)
    glVertex3f(*mf)
    glEnd()

    glPopMatrix()


def draw_fender_transition_small():
    glPushMatrix()
    set_material('car_red')

    A = (-0.70, 0.55, 1.75)
    B = (-0.60, 0.55, 1.95)
    C = (-0.60, 0.62, 1.75)

    Out = (
        (A[0] + B[0] + C[0]) / 3 - 0.05,
        (A[1] + B[1] + C[1]) / 3,
        (A[2] + B[2] + C[2]) / 3 - 0.05
    )

    glBegin(GL_QUADS)
    glNormal3f(-0.25, 0.6, 0.75)
    glVertex3f(*A)
    glVertex3f(*C)
    glVertex3f(*Out)
    glVertex3f(*B)
    glEnd()

    def M(p):
        return (-p[0], p[1], p[2])

    glBegin(GL_QUADS)
    glNormal3f(0.25, 0.6, 0.75)
    glVertex3f(*M(A))
    glVertex3f(*M(C))
    glVertex3f(*M(Out))
    glVertex3f(*M(B))
    glEnd()

    glPopMatrix()

def draw_raw_wheel(radius, width):
    set_material("rubber")
    glPushMatrix()
    gluCylinder(quadric, radius, radius, width, 26, 1)
    gluDisk(quadric, 0, radius, 26, 1)

    glTranslatef(0, 0, width)
    gluDisk(quadric, 0, radius, 26, 1)
    glPopMatrix()

    # jante
    set_material("rim")
    glPushMatrix()
    glTranslatef(0, 0, width + 0.003)

    rim_outer = radius * 0.80
    rim_inner = radius * 0.55
    center_r  = radius * 0.30

    gluDisk(quadric, rim_inner, rim_outer, 32, 1)
    gluDisk(quadric, 0, center_r, 20, 1)

    # Raios
    glBegin(GL_QUADS)
    spoke_width = 0.045
    num_spokes = 5
    for i in range(num_spokes):
        a = math.radians(i * (360 / num_spokes))
        x0 = center_r * math.cos(a)
        y0 = center_r * math.sin(a)
        x1 = rim_inner * math.cos(a)
        y1 = rim_inner * math.sin(a)
        px = -spoke_width * math.sin(a)
        py =  spoke_width * math.cos(a)

        glVertex3f(x0 - px, y0 - py, 0.004)
        glVertex3f(x0 + px, y0 + py, 0.004)
        glVertex3f(x1 + px, y1 + py, 0.004)
        glVertex3f(x1 - px, y1 - py, 0.004)
    glEnd()
    glPopMatrix()

def place_wheel(x, y, z, radius, width, is_left, is_front):
    glPushMatrix()
    glTranslatef(x, y, z)

    # -------------------------
    # ACKERMANN STEERING
    # -------------------------
    if is_front:
        base_angle = state['steer_angle']

        if base_angle > 0:  # virar esquerda
            steer = base_angle * (1.20 if is_left else 0.80)
        elif base_angle < 0:  # virar direita
            steer = base_angle * (0.80 if is_left else 1.20)
        else:
            steer = 0

        glRotatef(-steer, 0, 1, 0)

    if is_left:
        glRotatef(-90, 0, 1, 0)
    else:
        glRotatef(90, 0, 1, 0)
   

    direction_correction = -1 if is_left else 1
    spin_factor = 0.24 / radius
   

    spin_angle = direction_correction * (-state['wheel_spin'] * spin_factor)

    glRotatef(spin_angle, 0, 0, 1)

    draw_raw_wheel(radius, width)
    glPopMatrix()


def place_wheel_rear(x, y, z, radius, width, is_left, is_front):
    glPushMatrix()
    glTranslatef(x, y, z)

    # -------------------------
    # ACKERMANN STEERING
    # -------------------------
    if is_front:
        base_angle = state['steer_angle']

        if base_angle > 0:  # virar esquerda
            steer = base_angle * (1.20 if is_left else 0.80)
        elif base_angle < 0:  # virar direita
            steer = base_angle * (0.80 if is_left else 1.20)
        else:
            steer = 0

        glRotatef(-steer, 0, 1, 0)

    if is_left:
        glRotatef(-90, 0, 1, 0)
    else:
        glRotatef(90, 0, 1, 0)
   

    direction_correction = -1 if is_left else 1
    
    spin_factor_rear = 0.24 / radius 

    spin_angle = direction_correction * (-state['wheel_spin'] * spin_factor_rear)

    glRotatef(spin_angle, 0, 0, 1)

    draw_raw_wheel(radius, width)
    glPopMatrix()


def draw_front_wheels():
    radius = 0.22
    width  = 0.18

    wheel_y = 0.35 - radius + 0.25  
    wheel_x = 0.78 
    wheel_z = 1.25

 
    place_wheel(-wheel_x, wheel_y, wheel_z, radius, width, True,  True) # frente esquerda
    place_wheel(+wheel_x, wheel_y, wheel_z, radius, width, False, True) # frente direita



   
def draw_front_fender_arch():
    set_material('car_red')

    arch_x_inner = 0.72
    thickness    = 0.13
    arch_x_outer = arch_x_inner + thickness

    cy = 0.34
    cz = 1.22
    radius = 0.33
    segments = 32  

    def draw_side(sign):
        x_inner =  arch_x_inner * sign
        x_outer =  arch_x_outer * sign
        normal_x = 1.0 * sign 

        glBegin(GL_QUADS)
        for i in range(segments):
            a1 = math.pi * (i / segments)
            a2 = math.pi * ((i+1) / segments)

            y1 = cy + radius * math.sin(a1)
            z1 = cz + radius * math.cos(a1)

            y2 = cy + radius * math.sin(a2)
            z2 = cz + radius * math.cos(a2)

            ny = math.sin((a1 + a2) * 0.5)
            nz = math.cos((a1 + a2) * 0.5)

            glNormal3f(normal_x, ny * 0.4, nz * 0.4)

            glVertex3f(x_inner, y1, z1)
            glVertex3f(x_inner, y2, z2)
            glVertex3f(x_outer, y2, z2)
            glVertex3f(x_outer, y1, z1)

        glEnd()

    # direito
    draw_side(+1)
    # esquerdo
    draw_side(-1)

def draw_windshield_frame():
    glPushMatrix()
    set_material("carbon_dark")

    hood_length = 1.1
    width = 1.20 / 2.0

    z_front = 3.5/2.0 - hood_length
    z_back  = z_front - 0.70

    h_front = 0.55 + 0.27
    h_back  = h_front + 0.37

    mold = 0.03

    glBegin(GL_QUADS)

    # esquerda
    glVertex3f(-width, h_front, z_front)
    glVertex3f(-width-mold, h_front, z_front)
    glVertex3f(-width-mold, h_back, z_back)
    glVertex3f(-width, h_back, z_back)

    # direita
    glVertex3f(width, h_front, z_front)
    glVertex3f(width+mold, h_front, z_front)
    glVertex3f(width+mold, h_back, z_back)
    glVertex3f(width, h_back, z_back)

    # baixo
    glVertex3f(-width, h_front, z_front)
    glVertex3f(width, h_front, z_front)
    glVertex3f(width, h_front+mold, z_front)
    glVertex3f(-width, h_front+mold, z_front)

    # topo
    glVertex3f(-width, h_back, z_back)
    glVertex3f(width, h_back, z_back)
    glVertex3f(width, h_back-mold, z_back)
    glVertex3f(-width, h_back-mold, z_back)

    glEnd()
    glPopMatrix()

def draw_windshield_glass():
    glPushMatrix()
    set_material("glass")

    hood_length = 1.1
    width = 1.20 / 2.0

    z_front = 3.5/2.0 - hood_length
    z_back = z_front - 0.70

    h_front = 0.55 + 0.27
    h_back = h_front + 0.37

    glBegin(GL_QUADS)
    glVertex3f(-width, h_front, z_front)
    glVertex3f(width, h_front, z_front)
    glVertex3f(width, h_back, z_back)
    glVertex3f(-width, h_back, z_back)
    glEnd()

    glPopMatrix()

def chassis_x_at_z(z):
    # Segmentos do chassi
    z_front =  1.75
    z_mid   =  0.70
    z_rear  = -1.75

    fw = 1.4  / 2.0   
    mw = 1.55 / 2.0   
    rw = 1.70 / 2.0   

    if z >= z_mid:
        t = (z - z_front) / (z_mid - z_front)
        return fw + t * (mw - fw)

    t = (z - z_mid) / (z_rear - z_mid)
    return mw + t * (rw - mw)

def draw_doors():
    global door_base_top, door_base_bottom, door_base_rear, door_rear_bottom

    for side in ("left", "right"):

        glPushMatrix()
        set_material('car_red')

        door_front_z = 0.55
        door_back_z = -0.80
        y_bottom = 0.25
        y_top = 0.82

        base_inner_front = chassis_x_at_z(door_front_z)
        base_inner_back = chassis_x_at_z(door_back_z)

        thickness = 0.06

        sign = -1 if side == "left" else 1

        x_inner_front = sign * base_inner_front
        x_inner_back = sign * base_inner_back
        x_outer_front = sign * (base_inner_front + thickness)
        x_outer_back = sign * (base_inner_back + thickness)

        pivot_x = x_outer_front
        pivot_y = y_bottom
        pivot_z = door_front_z

        if side == "left":
            angle = 70.0 if state['left_door_open'] else 0.0
        else:
            angle = -70.0 if state['right_door_open'] else 0.0

        glTranslatef(pivot_x, pivot_y, pivot_z)
        glRotatef(angle, 0, 1, 0)
        glTranslatef(-pivot_x, -pivot_y, -pivot_z)

        door_base_top = (x_outer_front, y_top, door_front_z)
        door_base_bottom = (x_outer_front, y_bottom, door_front_z)
        door_base_rear = (x_outer_back, y_top, door_back_z)
        door_rear_bottom = (x_outer_back, y_bottom, door_back_z)

        glBegin(GL_QUADS)
        normal_x = 1 if side == "right" else -1
        glNormal3f(normal_x, 0, 0)
        glVertex3f(x_outer_front, y_bottom, door_front_z)
        glVertex3f(x_outer_front, y_top, door_front_z)
        glVertex3f(x_outer_back, y_top, door_back_z)
        glVertex3f(x_outer_back, y_bottom, door_back_z)
        glEnd()

        glBegin(GL_QUADS)
        glNormal3f(-normal_x, 0, 0)
        glVertex3f(x_inner_front, y_bottom, door_front_z)
        glVertex3f(x_inner_front, y_top, door_front_z)
        glVertex3f(x_inner_back, y_top, door_back_z)
        glVertex3f(x_inner_back, y_bottom, door_back_z)
        glEnd()

        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        glVertex3f(x_inner_front, y_top, door_front_z)
        glVertex3f(x_outer_front, y_top, door_front_z)
        glVertex3f(x_outer_back, y_top, door_back_z)
        glVertex3f(x_inner_back, y_top, door_back_z)
        glEnd()

        glBegin(GL_QUADS)
        glNormal3f(0, -1, 0)
        glVertex3f(x_inner_front, y_bottom, door_front_z)
        glVertex3f(x_outer_front, y_bottom, door_front_z)
        glVertex3f(x_outer_back, y_bottom, door_back_z)
        glVertex3f(x_inner_back, y_bottom, door_back_z)
        glEnd()

        glBegin(GL_QUADS)
        glNormal3f(0, 0, 1)
        glVertex3f(x_inner_front, y_bottom, door_front_z)
        glVertex3f(x_outer_front, y_bottom, door_front_z)
        glVertex3f(x_outer_front, y_top, door_front_z)
        glVertex3f(x_inner_front, y_top, door_front_z)
        glEnd()

        glBegin(GL_QUADS)
        glNormal3f(0, 0, -1)
        glVertex3f(x_inner_back, y_bottom, door_back_z)
        glVertex3f(x_outer_back, y_bottom, door_back_z)
        glVertex3f(x_outer_back, y_top, door_back_z)
        glVertex3f(x_inner_back, y_top, door_back_z)
        glEnd()

        set_material("metal")

        handle_y = (y_bottom + y_top) / 2 + 0.05
        handle_z = door_front_z + 0.55 * (door_back_z - door_front_z)

        arm_x = x_outer_front + (0.002 if normal_x > 0 else -0.002)

        arm_w = 0.015
        arm_h = 0.02
        arm_d = 0.045
        spacing = 0.10
        peg_d = 0.045
        peg_h = arm_h
        peg_w = spacing + arm_w * 2

        glPushMatrix()
        glTranslatef(arm_x, handle_y, handle_z + spacing/2)
        glScalef(arm_d, arm_h, arm_w)
        glutSolidCube(1)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(arm_x, handle_y, handle_z - spacing/2)
        glScalef(arm_d, arm_h, arm_w)
        glutSolidCube(1)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(arm_x + (arm_d if normal_x > 0 else -arm_d), handle_y, handle_z)
        glScalef(peg_d, peg_h, peg_w)
        glutSolidCube(1)
        glPopMatrix()

        glPopMatrix()


def compute_door_glass_points():
    global door_base_top, door_base_bottom, door_base_rear
    global door_glass_top_front, door_glass_top_rear

    # Usa a mesma lógica original
    front_windshield_top = (0.63, 1.19, -0.05)

    # ponto frontal do vidro
    topA = front_windshield_top

    # recuo calculado pela porta
    recuo_x = door_base_top[0] - topA[0]

    # ponto traseiro
    topB = (door_base_rear[0] - recuo_x, 1.19, door_base_rear[2])

    door_glass_top_front = topA
    door_glass_top_rear  = topB

def draw_door_glass():
    # vidro da porta (direita e esquerda via mirroring)
    set_material("glass")

    baseA = door_base_top          
    baseB = door_base_rear        
    topA  = door_glass_top_front 
    topB  = door_glass_top_rear   

    for mirror in (1, -1):
        glPushMatrix()
        glScalef(mirror, 1, 1)

        glBegin(GL_QUADS)
        glVertex3f(*baseA)
        glVertex3f(*topA)
        glVertex3f(*topB)
        glVertex3f(*baseB)
        glEnd()

        glPopMatrix()

def draw_fender_to_windshield():
    set_material("car_red") 
    import numpy as np

    F = np.array((0.80, 0.77, 0.65))# fender exterior
    A = np.array((0.60, 0.82, 0.65))# fender interior
    B = np.array((0.63, 1.19, -0.05))# moldura do vidro 

    AB = A - F   
    AC = B - F  
    normal = np.cross(AB, AC)
    normal = normal / np.linalg.norm(normal)

    # -------------------------
    # LADO DIREITO
    # -------------------------
    glBegin(GL_TRIANGLES)
    glNormal3f(*normal)
    glVertex3f(*F)
    glVertex3f(*A)
    glVertex3f(*B)
    glEnd()

    # -------------------------
    # LADO ESQUERDO
    # -------------------------

    def M(p): 
        return np.array((-p[0], p[1], p[2]))

    Fm = M(F)
    Am = M(A)
    Bm = M(B)

    nm = np.array((-normal[0], normal[1], normal[2]))

    glBegin(GL_TRIANGLES)
    glNormal3f(*nm)
    glVertex3f(*Fm)
    glVertex3f(*Am)
    glVertex3f(*Bm)
    glEnd()

def draw_side_panel_connector():
    set_material("fender_metal")

    # Pontos do lado direito
    A = (0.63, 1.19, -0.05)  
    B = (0.80, 0.77, 0.65)    # fender superior
    C = door_base_top   

    import numpy as np
    AB = np.subtract(B, A)
    AC = np.subtract(C, A)
    normal = np.cross(AB, AC)
    normal = normal / np.linalg.norm(normal)   

    glBegin(GL_TRIANGLES)
    glNormal3f(*normal)
    glVertex3f(*A)
    glVertex3f(*C)  
    glVertex3f(*B)
    glEnd()

    def mirror(p): return (-p[0], p[1], p[2])

    A2 = mirror(A)
    B2 = mirror(B)
    C2 = mirror(C)

    normal2 = (-normal[0], normal[1], normal[2])

    glBegin(GL_TRIANGLES)
    glNormal3f(*normal2)
    glVertex3f(*A2)
    glVertex3f(*C2)
    glVertex3f(*B2)
    glEnd()


def draw_side_panel_fill():
    set_material("car_red")
    import numpy as np

    A = np.array((0.93, 0.25, 0.65))
    E = np.array((0.87, 0.64, 0.65))
    B = np.array((0.80, 0.77, 0.65))
    C = np.array(door_base_top)
    D = np.array(door_base_bottom)

    def N(p1, p2, p3):
        u = p2 - p1
        v = p3 - p1
        n = np.cross(u, v)
        return n / np.linalg.norm(n)

    n1 = N(A, E, B)

    glBegin(GL_QUADS)
    glNormal3f(*n1)
    glVertex3f(*A)
    glVertex3f(*E)
    glVertex3f(*B)
    glVertex3f(*C)
    glEnd()


    n2 = N(A, D, C)

    glBegin(GL_QUADS)
    glNormal3f(*n2)
    glVertex3f(*A)
    glVertex3f(*D)
    glVertex3f(*C)
    glVertex3f(*A)
    glEnd()

    A2 = np.array((-A[0], A[1], A[2]))
    E2 = np.array((-E[0], E[1], E[2]))
    B2 = np.array((-B[0], B[1], B[2]))
    C2 = np.array((-C[0], C[1], C[2]))
    D2 = np.array((-D[0], D[1], D[2]))
   
   #qaud1
    n1L = -N(A2, E2, B2)

    glBegin(GL_QUADS)
    glNormal3f(*n1L)
    glVertex3f(*A2)
    glVertex3f(*E2)
    glVertex3f(*B2)
    glVertex3f(*C2)
    glEnd()


    n2L = N(A2, C2, D2)

    glBegin(GL_QUADS)
    glNormal3f(*n2L)
    glVertex3f(*A2)
    glVertex3f(*C2)
    glVertex3f(*D2)
    glVertex3f(*A2)
    glEnd()


def build_quarter_window():
    import numpy as np
    global quarter_window_rear, quarter_A, quarter_B, quarter_C

    # Ponto A: topo traseiro da janela da porta
    quarter_A = np.array(door_glass_top_rear)

    # Ponto B: base traseira da janela da porta
    quarter_B = np.array(door_base_rear)

    quarter_C = np.array((
        door_base_rear[0] - 0.07,
        door_base_rear[1] + 0.07,
        -1.30
    ))

    quarter_window_rear = quarter_C

def draw_quarter_window_glass():
    import numpy as np
    set_material('glass')

    A = quarter_A
    B = quarter_B
    C = quarter_C

    AB = B - A
    AC = C - A
    n = np.cross(AB, AC)
    n = n / np.linalg.norm(n)

    for mirror in (1, -1):
        glPushMatrix()
        glScalef(mirror, 1, 1)

        glBegin(GL_TRIANGLES)
        glNormal3f(mirror * n[0], n[1], n[2])
        glVertex3f(*A)
        glVertex3f(*B)
        glVertex3f(*C)
        glEnd()

        glPopMatrix()


def draw_upper_side_panel():
    import numpy as np

    set_material('rubber')

    # Pontos do lado direito
    A = np.array(door_base_rear)    
    C = np.array(quarter_window_rear)    


    A_L = np.array((-A[0], A[1], A[2]))
    C_L = np.array((-C[0], C[1], C[2]))

    AB = C - A
    AC = A_L - A
    normal = np.cross(AB, AC)
    normal = normal / np.linalg.norm(normal)

    for mirror in (1, -1):
        glPushMatrix()
        glScalef(mirror, 1, 1)

        glBegin(GL_QUADS)
       
        glNormal3f(mirror * normal[0], normal[1], normal[2])

        glVertex3f(*A)
        glVertex3f(*C)
        glVertex3f(*C_L)
        glVertex3f(*A_L)

        glEnd()
        glPopMatrix()

def draw_upper_rear_transition_panel():
    import numpy as np
    
    set_material("hood_blue")

    
    C = np.array(quarter_window_rear)    
    C_L = np.array((-C[0], C[1], C[2]))  

    rear_z = -1.50  
    
    global rear_panel
    T  = np.array((C[0] ,C[1] -0.04, rear_z)) # direito traseiro
    T_L = np.array((-C[0] ,C[1] -0.04, rear_z)) # esquerdo traseiro

    rear_panel = T

    AB = T - C
    AC = C_L - C
    normal = np.cross(AB, AC)
    normal = normal / np.linalg.norm(normal)

    for mirror in (1, -1):
        glPushMatrix()
        glScalef(mirror, 1, 1)

        glBegin(GL_QUADS)
        glNormal3f(mirror * normal[0], normal[1], normal[2])

        glVertex3f(*C)    # frente direita
        glVertex3f(*T)    # trás direita
        glVertex3f(*T_L)  # trás esquerda
        glVertex3f(*C_L)  # frente esquerda

        glEnd()
        glPopMatrix()

def draw_rear_transition_panel():
    import numpy as np
    set_material("rubber")

    P = np.array(rear_panel)            # painel traseiro direito
    P_L = np.array((-P[0], P[1], P[2])) # painel traseiro esquerdo

    C = np.array((0.575, 0.55, -1.92))    # chassi traseiro direito
    C_L = np.array((-0.575, 0.55, -1.92)) # chassi traseiro esquerdo

 
    AB = C - P
    AC = P_L - P
    normal = np.cross(AB, AC)
    normal = normal / np.linalg.norm(normal)

    for mirror in (1, -1):
        glPushMatrix()
        glScalef(mirror, 1, 1)

        glBegin(GL_QUADS)
        glNormal3f(mirror * normal[0], normal[1], normal[2])

        glVertex3f(*P)     # painel traseiro direito
        glVertex3f(*C)     # chassi traseiro direito
        glVertex3f(*C_L)   # chassi traseiro esquerdo
        glVertex3f(*P_L)   # painel traseiro esquerdo

        glEnd()

        glPopMatrix()

def draw_rear_bumper():
    glPushMatrix()

    set_material('rubber')

    z_chassis_rear = -1.75
    z_bumper = -1.92

    h_top = 0.55
    h_bottom = 0.25

    cw = 0.85
    bw = 1.15 / 2.0

    glBegin(GL_QUADS)
    glNormal3f(0, 1, -1)
    glVertex3f(-cw, h_top, z_chassis_rear)
    glVertex3f(cw, h_top, z_chassis_rear)
    glVertex3f(bw, h_top, z_bumper)
    glVertex3f(-bw, h_top, z_bumper)
    glEnd()

    glBegin(GL_QUADS)
    glNormal3f(1, 0, 0)
    glVertex3f(cw, h_top, z_chassis_rear)
    glVertex3f(cw, h_bottom, z_chassis_rear)
    glVertex3f(bw, h_bottom, z_bumper)
    glVertex3f(bw, h_top, z_bumper)
    glEnd()

    glBegin(GL_QUADS)
    glNormal3f(-1, 0, 0)
    glVertex3f(-cw, h_top, z_chassis_rear)
    glVertex3f(-cw, h_bottom, z_chassis_rear)
    glVertex3f(-bw, h_bottom, z_bumper)
    glVertex3f(-bw, h_top, z_bumper)
    glEnd()

    glBegin(GL_QUADS)
    glNormal3f(0, 0, -1)
    glVertex3f(-bw, h_top, z_bumper)
    glVertex3f(bw, h_top, z_bumper)
    glVertex3f(bw, h_bottom, z_bumper)
    glVertex3f(-bw, h_bottom, z_bumper)
    glEnd()

    glPopMatrix()


def draw_fill_rear_gap():
    glPushMatrix()
    set_material("hood_blue")
    import numpy as np

    P1 = np.array((0.575, 0.55, -1.92))
    P2 = np.array(rear_panel)
    P3 = np.array((0.85, 0.55, -1.75))
    P4 = np.array(quarter_window_rear)

    v1 = P2 - P1
    v2 = P3 - P1
    normal1 = np.cross(v1, v2)
    normal1 = normal1 / np.linalg.norm(normal1)

    glBegin(GL_TRIANGLES)
    glNormal3f(*normal1)
    glVertex3f(*P1)
    glVertex3f(*P2)
    glVertex3f(*P3)
    glEnd()

    v3 = P3 - P4
    v4 = P2 - P4
    normal2 = np.cross(v3, v4)
    normal2 = normal2 / np.linalg.norm(normal2)

    glBegin(GL_TRIANGLES)
    glNormal3f(*normal2)
    glVertex3f(*P4)
    glVertex3f(*P3)
    glVertex3f(*P2)
    glEnd()

    P1L = np.array((-P1[0], P1[1], P1[2]))
    P2L = np.array((-P2[0], P2[1], P2[2]))
    P3L = np.array((-P3[0], P3[1], P3[2]))
    P4L = np.array((-P4[0], P4[1], P4[2]))

    glBegin(GL_TRIANGLES)
    glNormal3f(-normal1[0], normal1[1], normal1[2])
    glVertex3f(*P1L)
    glVertex3f(*P2L)
    glVertex3f(*P3L)
    glEnd()

    glBegin(GL_TRIANGLES)
    glNormal3f(-normal2[0], normal2[1], normal2[2])
    glVertex3f(*P4L)
    glVertex3f(*P3L)
    glVertex3f(*P2L)
    glEnd()

    glPopMatrix()

def draw_rear_side_panel():
    glPushMatrix()
    set_material("fender_metal")
    import numpy as np

    def N(p1, p2, p3):
        u = p2 - p1
        v = p3 - p1
        n = np.cross(u, v)
        return n / np.linalg.norm(n)

    A = np.array(door_rear_bottom)    
    D = np.array((door_base_rear[0], door_base_rear[1] - 0.15, door_base_rear[2]))
    E = np.array(door_base_rear)
    B = np.array(( 0.85, 0.55, -1.75))
    C = np.array(( 0.85, 0.25, -1.75))
 
    glBegin(GL_TRIANGLES)
    glNormal3f(*N(A, C, D))
    glVertex3f(*A)
    glVertex3f(*C)
    glVertex3f(*D)
    glEnd()

    glBegin(GL_TRIANGLES)
    glNormal3f(*N(D, C, B))
    glVertex3f(*D)
    glVertex3f(*C)
    glVertex3f(*B)
    glEnd()

    glBegin(GL_TRIANGLES)
    glNormal3f(*N(D, B, E))
    glVertex3f(*D)
    glVertex3f(*B)
    glVertex3f(*E)
    glEnd()


    A2 = np.array((-door_rear_bottom[0], door_rear_bottom[1], door_rear_bottom[2]))
    D2 = np.array((-door_base_rear[0], door_base_rear[1] - 0.15, door_base_rear[2]))
    E2 = np.array((-door_base_rear[0], door_base_rear[1], door_base_rear[2]))
    B2 = np.array((-0.85, 0.55, -1.75))
    C2 = np.array((-0.85, 0.25, -1.75))

    glBegin(GL_TRIANGLES)
    glNormal3f(*N(A2, D2, C2))
    glVertex3f(*A2)
    glVertex3f(*D2)
    glVertex3f(*C2)
    glEnd()

    glBegin(GL_TRIANGLES)
    glNormal3f(*N(D2, B2, C2))
    glVertex3f(*D2)
    glVertex3f(*B2)
    glVertex3f(*C2)
    glEnd()

    glBegin(GL_TRIANGLES)
    glNormal3f(*N(D2, E2, B2))
    glVertex3f(*D2)
    glVertex3f(*E2)
    glVertex3f(*B2)
    glEnd()

    glPopMatrix()

def draw_rear_upper_link():
    glPushMatrix()
    set_material("fender_metal")
    import numpy as np

    def N(a, b, c):
        u = b - a
        v = c - a
        n = np.cross(u, v)
        n = n / np.linalg.norm(n)
        return n

    # -----------------------------
    # LADO DIREITO
    # -----------------------------
    P1 = np.array(door_base_rear)           
    P2 = np.array(rear_panel)                
    P3 = np.array((0.85, 0.55, -1.75))       

    nR = N(P1, P2, P3)

    if nR[0] < 0:
        nR = -nR

    glBegin(GL_TRIANGLES)
    glNormal3f(*nR)
    glVertex3f(*P1)
    glVertex3f(*P2)
    glVertex3f(*P3)
    glEnd()

    # -----------------------------
    # LADO ESQUERDO
    # -----------------------------
    P1L = np.array((-P1[0], P1[1], P1[2]))
    P2L = np.array((-P2[0], P2[1], P2[2]))
    P3L = np.array((-P3[0], P3[1], P3[2]))

    nL = N(P1L, P2L, P3L)

    if nL[0] > 0:
        nL = -nL

    glBegin(GL_TRIANGLES)
    glNormal3f(*nL)
    glVertex3f(*P1L)
    glVertex3f(*P2L)
    glVertex3f(*P3L)
    glEnd()

    glPopMatrix()
    


def draw_rear_fender_arch():
    set_material('car_red')

    # -------------------------
    # Dimensoes
    # -------------------------
    arch_x_inner = 0.84
    thickness    = 0.15
    arch_x_outer = arch_x_inner + thickness

    cy = 0.34
    cz = -1.25
    radius = 0.33
    segments = 32

    # Semicírculo 
    start_angle = 0.0          
    end_angle   = math.pi      

    inward_extra = 0.10          

    def draw_side(sign):
        glBegin(GL_QUADS)

        for i in range(segments):

            t1 = i / segments
            t2 = (i+1) / segments

        
            a1 = start_angle + (end_angle - start_angle) * t1
            a2 = start_angle + (end_angle - start_angle) * t2

            # arco YZ
            y1 = cy + radius * math.sin(a1)
            z1 = cz + radius * math.cos(a1)

            y2 = cy + radius * math.sin(a2)
            z2 = cz + radius * math.cos(a2)

            # -------------------------
            # X move-se para dentro ao longo do arco
            # -------------------------
            offset1 = t1 * inward_extra
            offset2 = t2 * inward_extra

            x_inner1 = (arch_x_inner - offset1) * sign
            x_outer1 = (arch_x_outer - offset1) * sign

            x_inner2 = (arch_x_inner - offset2) * sign
            x_outer2 = (arch_x_outer - offset2) * sign

            ny = math.sin((a1 + a2) * 0.5)
            nz = math.cos((a1 + a2) * 0.5)
            normal_x = sign

            glNormal3f(normal_x, ny * 0.4, nz * 0.4)

            glVertex3f(x_inner1, y1, z1)
            glVertex3f(x_inner2, y2, z2)
            glVertex3f(x_outer2, y2, z2)
            glVertex3f(x_outer1, y1, z1)

        glEnd()

    draw_side(+1)
    draw_side(-1)

def draw_rear_wheels():
    radius_front = 0.22
    wheel_y_front = 0.35 - radius_front + 0.25   

    radius_rear = 0.24
    width_rear  = 0.20

    wheel_y_rear = wheel_y_front + (radius_front - radius_rear)

    wheel_x = 0.77
    wheel_z = -1.25

    place_wheel_rear(-wheel_x, wheel_y_rear, wheel_z, radius_rear, width_rear, True,  False)  # trás esquerda
    place_wheel_rear(+wheel_x, wheel_y_rear, wheel_z, radius_rear, width_rear, False, False)  # trás direita


def draw_rear_triangle_piece():
    import numpy as np
    set_material("fender_metal")

    A = np.array(rear_panel)
    B = np.array(door_base_rear)
    C = np.array(quarter_window_rear)

    # função normal
    def N(a, b, c):
        u = b - a
        v = c - a
        n = np.cross(u, v)
        return n / np.linalg.norm(n)

    nR = N(A, B, C)

    if nR[0] < 0:
        nR = -nR

    glBegin(GL_TRIANGLES)
    glNormal3f(*nR)
    glVertex3f(*A)
    glVertex3f(*B)
    glVertex3f(*C)
    glEnd()


    A2 = np.array([-A[0], A[1], A[2]])
    B2 = np.array([-B[0], B[1], B[2]])
    C2 = np.array([-C[0], C[1], C[2]])

    nL = N(A2, B2, C2)

    if nL[0] > 0:
        nL = -nL

    glBegin(GL_TRIANGLES)
    glNormal3f(*nL)
    glVertex3f(*A2)
    glVertex3f(*B2)
    glVertex3f(*C2)
    glEnd()

def draw_rear_inner_panel():
    import numpy as np
    glPushMatrix()
    set_material("car_red")

    A = np.array(door_rear_bottom)   # inferior dianteiro
    B = np.array(door_base_rear)     # superior dianteiro

    A2 = np.array((-A[0], A[1], A[2]))   # inferior traseiro
    B2 = np.array((-B[0], B[1], B[2]))   # superior traseiro

 
    v1 = B - A
    v2 = B2 - A
    normal = np.cross(v1, v2)
    normal = normal / np.linalg.norm(normal)

    glBegin(GL_QUADS)
    glNormal3f(*normal)
    glVertex3f(*A)
    glVertex3f(*B)
    glVertex3f(*B2)
    glVertex3f(*A2)
    glEnd()

    glPopMatrix()


def draw_cabin_floor_fill():
    import numpy as np

    set_material("car_red")

    A = np.array((-0.93, 0.25, 0.65))
    B = np.array(( 0.93, 0.25, 0.65))
    C = np.array(( 0.80, 0.77, 0.65))
    D = np.array((-0.80, 0.77, 0.65))

    normal = (0.0, 1.0, 0.0)

    glBegin(GL_QUADS)
    glNormal3f(*normal)
    glVertex3f(*A)
    glVertex3f(*B)
    glVertex3f(*C)
    glVertex3f(*D)
    glEnd()

def draw_car_tablier():
    import numpy as np

    set_material("rubber")

    D1 = np.array(( 0.80, 0.77, 0.65))   # direita baixo
    D2 = np.array((-0.80, 0.77, 0.65))   # esquerda baixo
    T1 = np.array(( 0.60, 0.82, 0.65))   # direita cima
    T2 = np.array((-0.60, 0.82, 0.65))   # esquerda cima

    normal = (0.0, 1.0, 0.0)

    glBegin(GL_QUADS)
    glNormal3f(*normal)
    glVertex3f(*D2)   
    glVertex3f(*D1)
    glVertex3f(*T1)
    glVertex3f(*T2)
    glEnd()

def draw_steering_wheel():
    import numpy as np
    from math import acos, degrees

    # -----------------------------
    # COORDENADAS BRAÇO
    # -----------------------------
    P0 = np.array((0.45, 0.72, 0.65))  # origem da coluna
    P1 = np.array((0.45, 0.72, 0.45))  

    V = P1 - P0
    length = np.linalg.norm(V)
    Vn = V / length

    Z = np.array((0.0, 0.0, 1.0))
    dot = max(-1.0, min(1.0, float(np.dot(Z, Vn))))
    angle = degrees(acos(dot))
    axis = np.cross(Z, Vn)
    axis = axis / np.linalg.norm(axis) if np.linalg.norm(axis) > 1e-6 else np.array((1.0, 0.0, 0.0))

    radius = 0.05
    slices = 24

    # --------------------------------
    # COLUNA
    # --------------------------------
    set_material("metal")
    glPushMatrix()
    glTranslatef(*P0)
    glRotatef(angle, axis[0], axis[1], axis[2])

    quad = gluNewQuadric()
    gluCylinder(quad, radius, radius, length, slices, 1)

    #tamoa coluna
    glPushMatrix()
    glTranslatef(0, 0, length)  # mover até à ponta
    gluDisk(quad, 0.0, radius, slices, 1)
    glPopMatrix()

    glPopMatrix()

    #volante
    glPushMatrix()
    glTranslatef(*P1)

    set_material("rubber")
    glutSolidTorus(0.03, 0.13, 20, 40)

    glRotatef(state['wheel_rotation'], 0, 0, 1)

    #raios
    set_material("metal")
    spokes = [
        (90.0, 0.12),
        (330.0, 0.12),
        (210.0, 0.12),
    ]

    for angle_deg, seg_len in spokes:
        glPushMatrix()
        glRotatef(angle_deg, 0, 0, 1)
        glTranslatef(0.0, seg_len / 2.0, 0.0)
        glScalef(0.02, seg_len, 0.02)
        glutSolidCube(1.0)
        glPopMatrix()

    glPopMatrix()


def draw_car():
    glPushMatrix()

    carx, cary, carz = state['car_pos']
    heading = state['car_heading']

    glTranslatef(carx, cary, carz)
    glRotatef(heading, 0, 1, 0)
    glTranslatef(0, -0.13, 0)

    # ----------GEOMETRIA OPACA ----------
    draw_chassis()
    draw_hood()
    draw_front_bumper()
    draw_fender_upper()
    draw_fender_middle_and_lower()
    draw_front_fender_arch()
    draw_fender_transition()
    draw_fender_transition_small()
    draw_front_wheels()
    draw_windshield_frame()

    draw_doors()

    # pontos do vidro da porta usados em outras funções
    compute_door_glass_points()
    build_quarter_window()

    draw_fender_to_windshield()
    draw_side_panel_connector()
    draw_side_panel_fill()
    draw_upper_side_panel()
    draw_upper_rear_transition_panel()
    draw_rear_transition_panel()
    draw_rear_bumper()
    draw_fill_rear_gap()
    draw_rear_side_panel()
    draw_rear_upper_link()
    draw_rear_fender_arch()
    draw_rear_wheels()
    draw_rear_triangle_piece()
    draw_rear_inner_panel()
    draw_cabin_floor_fill()
    draw_car_tablier()
    draw_steering_wheel()

    # ----------GEOMETRIA TRANSPARENTE ----------
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDepthMask(GL_FALSE)   

    # so vidros
    draw_windshield_glass()
    draw_door_glass()
    draw_quarter_window_glass()

    glDepthMask(GL_TRUE)
    glDisable(GL_BLEND)

    glPopMatrix()

    

def setup_lights():
    glEnable(GL_LIGHTING)
    glEnable(GL_NORMALIZE)

    # Luz ambiente
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT,[0.30, 0.30, 0.30, 1.0])

    # Luz principal 
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION,[0.0, 0.3, 1.0, 0.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE,[1.0, 1.0, 1.0, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR,[1.0, 1.0, 1.0, 1.0])

    # Luz secundária 
    glEnable(GL_LIGHT1)
    glLightfv(GL_LIGHT1, GL_POSITION,[-8.0, 3.2, 8.0, 1.0])
    glLightfv(GL_LIGHT1, GL_DIFFUSE, [1.0, 0.9, 0.7, 1.0])
    glLightfv(GL_LIGHT1, GL_SPECULAR,[1.0, 0.9, 0.7, 1.0])
    glLightf(GL_LIGHT1, GL_CONSTANT_ATTENUATION, 0.8)
    glLightf(GL_LIGHT1, GL_LINEAR_ATTENUATION,   0.02)




# ---------- Camera ----------
def apply_camera():
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    carx, cary, carz = state['car_pos']
    heading = math.radians(state['car_heading'])

    if state['camera_mode'] == 0:
        # ============================
        #   MODO 0: ORBIT FOLLOW
        # ============================
        az = math.radians(state['cam_azim'])
        el = math.radians(state['cam_elev'])
        d  = state['cam_dist']

        cx = carx + d * math.cos(el) * math.cos(az)
        cy = cary + 1.5 + d * math.sin(el)
        cz = carz + d * math.cos(el) * math.sin(az)

        gluLookAt(cx, cy, cz,
                  carx, cary + 0.7, carz,
                  0, 1, 0)

    elif state['camera_mode'] == 1:
        # ============================
        #   MODO 1: FOLLOW REAL
        # ============================
        x_dir = math.sin(heading)
        z_dir = math.cos(heading)

        back = 6.0
        cx = carx - back * x_dir
        cz = carz - back * z_dir
        cy = cary + 3.0

        gluLookAt(cx, cy, cz,
                  carx + x_dir, cary + 0.7, carz + z_dir,
                  0, 1, 0)

    elif state['camera_mode'] == 2:
    # ============================
    #   MODO 2: CÂMARA INTERIOR
    # ============================

    # deslocamento lateral para volante
        side_offset = -0.15

        backward_offset = 0.55 

        # altura 
        cy = cary + 0.90

        # calcular posição da câmara 
        cx = carx - math.sin(heading) * backward_offset - math.cos(heading) * side_offset
        cz = carz - math.cos(heading) * backward_offset + math.sin(heading) * side_offset

        #heading
        tx = carx + math.sin(heading) * 5.0
        ty = cy - 0.05  
        tz = carz + math.cos(heading) * 5.0

        gluLookAt(cx, cy, cz,
                tx, ty, tz,
                0, 1, 0)



    
# ---------- Display ----------
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0,0,WINDOW_W,WINDOW_H)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, float(WINDOW_W)/float(WINDOW_H), 0.1, 200.0)

    apply_camera()

    draw_ground()
    draw_garage()
    draw_car()  
    draw_tree(-8,8)
    draw_tree(6,-6)
    draw_tree(6,10)
    draw_tree(-8,-6)
    draw_lamp_post(-9,2)
    draw_lamp_post(8,3)

    if state['show_help']:
        draw_help_overlay()

    glutSwapBuffers()

# ---------- HUD ----------
def draw_text_2d(x,y,text):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix(); glLoadIdentity(); glOrtho(0,WINDOW_W,0,WINDOW_H,-1,1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix(); glLoadIdentity()
    glDisable(GL_LIGHTING)
    glColor3f(1,1,1)
    glRasterPos2f(x,y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
    glEnable(GL_LIGHTING)
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

def draw_help_overlay():
    lines = [
        'Controlos: WASD | G Garagem | V Camera | MoveCamera setas',
        f"Pos: x={state['car_pos'][0]:.2f} z={state['car_pos'][2]:.2f}"
    ]
    y = WINDOW_H - 20
    for l in lines:
        draw_text_2d(10,y,l)
        y -= 18

def keyboard(key, x, y):
    k = key.decode('utf-8') if isinstance(key, bytes) else key

    # sair
    if k in ('q','Q','\x1b'):
        sys.exit(0)

    # abrir/fechar garagem
    if k in ('g','G'):
        state['garage_open'] = not state['garage_open']

    # mudar camera
    if k in ('v','V'):
        if k in ('v','V'): state['camera_mode'] = (state['camera_mode'] + 1) % 3

    if k in ('l', 'L'):
        # esquerda = lado X negativo
        state['right_door_open'] = not state['right_door_open']

    if k in ('r', 'R'):
        # direita = lado X positivo
        state['left_door_open'] = not state['left_door_open']

    # marcar tecla como pressionada
    if k in keys:
        keys[k] = True



def keyboard_up(key, x, y):
    k = key.decode('utf-8') if isinstance(key, bytes) else key

    if k in keys:
        keys[k] = False

def special_input(key, x, y):
    if key == GLUT_KEY_LEFT:
        state['cam_azim'] -= 5.0
    elif key == GLUT_KEY_RIGHT:
        state['cam_azim'] += 5.0
    elif key == GLUT_KEY_UP:
        state['cam_elev'] = min(state['cam_elev'] + 5.0, 89.0)
    elif key == GLUT_KEY_DOWN:
        state['cam_elev'] = max(state['cam_elev'] - 5.0, -10.0)


def idle():

    # ---- virar para a esquerda ----
    if keys['a']:
        state['steer_angle'] = max(state['steer_angle'] - STEER_STEP, -30)
        state['wheel_rotation'] = max(state['wheel_rotation'] - 5, -250)

    # ---- virar para a direita (D) ----
    if keys['d']:
        state['steer_angle'] = min(state['steer_angle'] + STEER_STEP, 30)
        state['wheel_rotation'] = min(state['wheel_rotation'] + 5, 250)


        # ---- andar para a frente ----
    if keys['w']:
        steering_rad = math.radians(state['steer_angle'])

        state['car_heading'] -= math.degrees(math.sin(steering_rad) * TURN_FACTOR)

        heading = math.radians(state['car_heading'])
        state['car_pos'][0] += math.sin(heading) * MOVE_STEP
        state['car_pos'][2] += math.cos(heading) * MOVE_STEP

        state['wheel_spin'] -= WHEEL_SPIN_STEP


    # ---- andar para trás ----
    if keys['s']:
        steering_rad = math.radians(state['steer_angle'])
        state['car_heading'] -= math.degrees(math.sin(-steering_rad) * TURN_FACTOR)

        heading = math.radians(state['car_heading'])

        state['car_pos'][0] -= math.sin(heading) * MOVE_STEP
        state['car_pos'][2] -= math.cos(heading) * MOVE_STEP

        state['wheel_spin'] += WHEEL_SPIN_STEP

    glutPostRedisplay()

# ---------- Init ----------
def init():
    glClearColor(0.6,0.8,1.0,1.0)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_NORMALIZE)

    init_quadric()

    # ground texture
    img = make_checker_texture(tile_count=16, tile_size=8)
    load_texture_from_image(img, 'ground')

    img = Image.open("carbon_fiber.jpg").convert("RGB")
    load_texture_from_image(img, "carbon")

    setup_lights()


# ---------- Main ----------
def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutCreateWindow(b"SolucaoCG - Projeto CG 2025")

    init()
    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_input)
    glutKeyboardUpFunc(keyboard_up)


    glutMainLoop()

if __name__ == '__main__':
    main()



