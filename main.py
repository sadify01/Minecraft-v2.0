from ursina import *
from noise import *
import random
import math

app = Ursina()
window.color = color.rgb(0, 0, 0)
window.exit_button.visible = False

# Load player and hand models
class Player(Entity):
    def __init__(self):
        super().__init__(
            model="blocky_character.glb",
            texture="blocky_texture.png",
            scale=0.1,
            position=(0, 0, 0),
            collider="box",
            double_sided=True,
        )

        self.enabled = False
        self.grounded = False
        self.jump_height = 0.5
        self.jump_up_duration = 0.2
        self.jump_down_duration = 0.4
        self.gravity = 1.0 / self.jump_down_duration ** 2

        self.gun = handModel

    def update(self):
        if self.enabled:
            camera.rotation_y += held_keys['d'] * 1 - held_keys['a'] * 1
            self.rotation_y = camera.rotation_y
            direction = self.rotation_y
            dx = math.sin(direction)
            dz = math.cos(direction)

            # Handle player movement here
            speed = 2.5
            self.x += (held_keys['w'] - held_keys['s']) * dx * speed * time.dt
            self.z += (held_keys['w'] - held_keys['s']) * dz * speed * time.dt

            # Handle player jumping and gravity here
            if self.y > 0:
                self.y -= self.gravity * time.dt

                if self.y <= 0:
                    self.y = 0
                    self.grounded = True
            else:
                self.grounded = True

class Voxel(Button):
    def __init__(self, position=(0, 0, 0), texture='white_cube', color=color.color(0, 0, random.uniform(0.9, 1.0)), double_sided=False, collider=None):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            texture=texture,
            color=color,
            double_sided=double_sided,
            collider=collider,
        )

        self.position = position
        self.texture = texture
        self.collider = collider

        # Store terrain blocks
        if not hasattr(Cube, 'terrain_blocks'):
            Cube.terrain_blocks = {}
        Cube.terrain_blocks[self.position] = self

    def input(self, key):
        if self.hovered:
            if key == 'right mouse down':
                playRandomSound(breakSoundOptions, volume=0.5)
                destroy(self)

    @classmethod
    def get_terrain_block(cls, position):
        return cls.terrain_blocks.get(position, None)

class Cube(Entity):
    def __init__(self, position=(0, 0, 0), texture='white_cube', double_sided=False, collider=None):
        super().__init__(
            parent=scene,
            model='cube',
            position=position,
            texture=texture,
            double_sided=double_sided,
            collider=collider,
        )

def createTerrain(width, height):
    for i in range(width):
        for j in range(height):
            y = int(floor(noise([i / FREQ, j / FREQ]))) * AMP
            if y < -1:
                for _ in range(abs(y)):
                    voxel = Voxel(position=(i, _ - y / 2, j), texture='water.png', double_sided=True, collider='box')
            elif y == -1:
                for _ in range(1):
                    voxel = Voxel(position=(i, 0, j), texture='sand.png', double_sided=True, collider='box')
            else:
                for _ in range(y):
                    voxel = Voxel(position=(i, _ - y / 2, j), texture='grass.png', double_sided=True, collider='box')
                for _ in range(y, 0):
                    voxel = Voxel(position=(i, _ - y / 2, j), texture='dirt.png', double_sided=True, collider='box')

def destroyCube(remove=False):
    hit = raycast(distance=8)
    if hit:
        pos = hit.position
        pos = (floor(pos.x), floor(pos.y), floor(pos.z))

        if remove:
            destroy(Cube.get_terrain_block(pos))

def placeCube():
    hit = raycast(distance=8)
    if hit:
        pos = hit.position + hit.normal
        pos = (floor(pos.x), floor(pos.y), floor(pos.z))

        if placeable:
            if not Cube.get_terrain_block(pos):
                placeable = False
                Cube(position=pos, texture=stoneTexture, double_sided=True, collider='box')
                playRandomSound(placeSoundOptions, volume=0.5)
                invoke(resetPlaceable, delay=0.25)

def resetPlaceable():
    global placeable
    placeable = True

def playRandomSound(sounds, volume=1.0):
    random.choice(sounds).play(volume=volume)

class Mob(Entity):
    def __init__(self, mob_name):
        mob_properties = mobs.get(mob_name)
        if mob_properties:
            super().__init__(
                model=mob_properties["model"],
                texture=mob_properties["texture"],
                rotation=mob_properties["rotation"],
                scale=mob_properties["scale"],
                position=(mob_properties["x"], mob_properties["origin_y"], mob_properties["z"]),
                collider=mob_properties["collider"],
                double_sided=mob_properties["double_sided"],
            )

            self.mob_name = mob_name
            self.is_dead = mob_properties["is_dead"]
            self.hp = mob_properties["hp"]
            self.hurt_sounds = mob_properties["hurt_sounds"]
            self.death_sounds = mob_properties["death_sounds"]
            mobs[mob_name]["entity"] = self

    def take_damage(self, damage):
        if not self.is_dead:
            self.hp -= damage
            playRandomSound(self.hurt_sounds, volume=0.5)
            if self.hp <= 0:
                self.die()

    def die(self):
        if not self.is_dead:
            self.is_dead = True
            playRandomSound(self.death_sounds, volume=0.5)
            mobs[self.mob_name]["entity"] = None
            destroy(self)

    def update(self):
        pass

def loadModel(model_name, texture_name, position=(0, 0, 0), scale=1):
    return Entity(model=model_name, texture=texture_name, position=position, scale=scale, collider='box')

def loadTexture(texture_name):
    return load_texture(texture_name)

def loadSounds():
    # Define sound options
    global hitSoundOptions, breakSoundOptions, placeSoundOptions, mineSoundOptions, itemSwapSoundOptions
    global cowHurtOptions, cowDeathOptions, zombieHurtOptions, zombieDeathOptions, creeperHurtOptions, creeperDeathOptions
    global endermanHurtOptions, endermanDeathOptions, ghastHurtOptions, ghastDeathOptions, pigHurtOptions, pigDeathOptions
    global sheepHurtOptions, sheepDeathOptions, skeletonHurtOptions, skeletonDeathOptions, spiderHurtOptions, spiderDeathOptions

    # Block hit and break sounds
    hitSoundOptions = [Audio(f'sounds/{i}') for i in ['block_hit_1.wav', 'block_hit_2.wav', 'block_hit_3.wav']]
    breakSoundOptions = [Audio(f'sounds/{i}') for i in ['block_break_1.wav', 'block_break_2.wav', 'block_break_3.wav']]

    # Block place and mine sounds
    placeSoundOptions = [Audio(f'sounds/{i}') for i in ['block_place_1.wav', 'block_place_2.wav', 'block_place_3.wav']]
    mineSoundOptions = [Audio(f'sounds/{i}') for i in ['block_mine_1.wav', 'block_mine_2.wav', 'block_mine_3.wav']]

    # Item swap sound
    itemSwapSoundOptions = [Audio(f'sounds/{i}') for i in ['item_swap_1.wav', 'item_swap_2.wav']]

    # Mob hurt and death sounds
    cowHurtOptions = [Audio(f'sounds/{i}') for i in ['cow_hurt_1.wav', 'cow_hurt_2.wav']]
    cowDeathOptions = [Audio(f'sounds/{i}') for i in ['cow_death_1.wav', 'cow_death_2.wav']]

    zombieHurtOptions = [Audio(f'sounds/{i}') for i in ['zombie_hurt_1.wav', 'zombie_hurt_2.wav']]
    zombieDeathOptions = [Audio(f'sounds/{i}') for i in ['zombie_death_1.wav', 'zombie_death_2.wav']]

    creeperHurtOptions = [Audio(f'sounds/{i}') for i in ['creeper_hurt_1.wav', 'creeper_hurt_2.wav']]
    creeperDeathOptions = [Audio(f'sounds/{i}') for i in ['creeper_death_1.wav', 'creeper_death_2.wav']]

    endermanHurtOptions = [Audio(f'sounds/{i}') for i in ['enderman_hurt_1.wav', 'enderman_hurt_2.wav']]
    endermanDeathOptions = [Audio(f'sounds/{i}') for i in ['enderman_death_1.wav', 'enderman_death_2.wav']]

    ghastHurtOptions = [Audio(f'sounds/{i}') for i in ['ghast_hurt_1.wav', 'ghast_hurt_2.wav']]
    ghastDeathOptions = [Audio(f'sounds/{i}') for i in ['ghast_death_1.wav', 'ghast_death_2.wav']]

    pigHurtOptions = [Audio(f'sounds/{i}') for i in ['pig_hurt_1.wav', 'pig_hurt_2.wav']]
    pigDeathOptions = [Audio(f'sounds/{i}') for i in ['pig_death_1.wav', 'pig_death_2.wav']]

    sheepHurtOptions = [Audio(f'sounds/{i}') for i in ['sheep_hurt_1.wav', 'sheep_hurt_2.wav']]
    sheepDeathOptions = [Audio(f'sounds/{i}') for i in ['sheep_death_1.wav', 'sheep_death_2.wav']]

    skeletonHurtOptions = [Audio(f'sounds/{i}') for i in ['skeleton_hurt_1.wav', 'skeleton_hurt_2.wav']]
    skeletonDeathOptions = [Audio(f'sounds/{i}') for i in ['skeleton_death_1.wav', 'skeleton_death_2.wav']]

    spiderHurtOptions = [Audio(f'sounds/{i}') for i in ['spider_hurt_1.wav', 'spider_hurt_2.wav']]
    spiderDeathOptions = [Audio(f'sounds/{i}') for i in ['spider_death_1.wav', 'spider_death_2.wav']]

def loadMobProperties():
    # Define properties for mobs
    global mobs
    mobs = {
        "cow": {
            "model": "cow.gltf",
            "texture": "cow.png",
            "rotation": (0, 180, 0),
            "scale": (0.03, 0.03, 0.03),
            "x": 10,
            "origin_y": 0,
            "z": 10,
            "collider": "box",
            "double_sided": False,
            "is_dead": False,
            "hp": 10,
            "hurt_sounds": cowHurtOptions,
            "death_sounds": cowDeathOptions,
        },
        "zombie": {
            "model": "zombie.gltf",
            "texture": "zombie.png",
            "rotation": (0, 180, 0),
            "scale": (0.03, 0.03, 0.03),
            "x": -10,
            "origin_y": 0,
            "z": 10,
            "collider": "box",
            "double_sided": False,
            "is_dead": False,
            "hp": 20,
            "hurt_sounds": zombieHurtOptions,
            "death_sounds": zombieDeathOptions,
        },
        "creeper": {
            "model": "creeper.gltf",
            "texture": "creeper.png",
            "rotation": (0, 180, 0),
            "scale": (0.03, 0.03, 0.03),
            "x": 10,
            "origin_y": 0,
            "z": -10,
            "collider": "box",
            "double_sided": False,
            "is_dead": False,
            "hp": 15,
            "hurt_sounds": creeperHurtOptions,
            "death_sounds": creeperDeathOptions,
        },
        "enderman": {
            "model": "enderman.gltf",
            "texture": "enderman.png",
            "rotation": (0, 180, 0),
            "scale": (0.03, 0.03, 0.03),
            "x": -10,
            "origin_y": 0,
            "z": -10,
            "collider": "box",
            "double_sided": False,
            "is_dead": False,
            "hp": 30,
            "hurt_sounds": endermanHurtOptions,
            "death_sounds": endermanDeathOptions,
        },
        "ghast": {
            "model": "ghast.gltf",
            "texture": "ghast.png",
            "rotation": (0, 180, 0),
            "scale": (0.03, 0.03, 0.03),
            "x": 0,
            "origin_y": 0,
            "z": 0,
            "collider": "box",
            "double_sided": False,
            "is_dead": False,
            "hp": 25,
            "hurt_sounds": ghastHurtOptions,
            "death_sounds": ghastDeathOptions,
        },
        "pig": {
            "model": "pig.gltf",
            "texture": "pig.png",
            "rotation": (0, 180, 0),
            "scale": (0.03, 0.03, 0.03),
            "x": 0,
            "origin_y": 0,
            "z": 10,
            "collider": "box",
            "double_sided": False,
            "is_dead": False,
            "hp": 10,
            "hurt_sounds": pigHurtOptions,
            "death_sounds": pigDeathOptions,
        },
        "sheep": {
            "model": "sheep.gltf",
            "texture": "sheep.png",
            "rotation": (0, 180, 0),
            "scale": (0.03, 0.03, 0.03),
            "x": 0,
            "origin_y": 0,
            "z": -10,
            "collider": "box",
            "double_sided": False,
            "is_dead": False,
            "hp": 10,
            "hurt_sounds": sheepHurtOptions,
            "death_sounds": sheepDeathOptions,
        },
        "skeleton": {
            "model": "skeleton.gltf",
            "texture": "skeleton.png",
            "rotation": (0, 180, 0),
            "scale": (0.03, 0.03, 0.03),
            "x": -10,
            "origin_y": 0,
            "z": 0,
            "collider": "box",
            "double_sided": False,
            "is_dead": False,
            "hp": 20,
            "hurt_sounds": skeletonHurtOptions,
            "death_sounds": skeletonDeathOptions,
        },
        "spider": {
            "model": "spider.gltf",
            "texture": "spider.png",
            "rotation": (0, 180, 0),
            "scale": (0.03, 0.03, 0.03),
            "x": 10,
            "origin_y": 0,
            "z": 0,
            "collider": "box",
            "double_sided": False,
            "is_dead": False,
            "hp": 15,
            "hurt_sounds": spiderHurtOptions,
            "death_sounds": spiderDeathOptions,
        },
    }

# Load textures
stoneTexture = loadTexture("textures/stone.png")
handTexture = loadTexture("textures/hand.png")
handModel = loadModel("models/hand.obj", texture_name="textures/hand.png", position=(0, 0, 0), scale=0.2)

loadModel("models/cow.obj", texture_name="textures/cow.png", position=(0, 0, 0), scale=0.03)
loadModel("models/zombie.obj", texture_name="textures/zombie.png", position=(0, 0, 0), scale=0.03)
loadModel("models/creeper.obj", texture_name="textures/creeper.png", position=(0, 0, 0), scale=0.03)
loadModel("models/enderman.obj", texture_name="textures/enderman.png", position=(0, 0, 0), scale=0.03)
loadModel("models/ghast.obj", texture_name="textures/ghast.png", position=(0, 0, 0), scale=0.03)
loadModel("models/pig.obj", texture_name="textures/pig.png", position=(0, 0, 0), scale=0.03)
loadModel("models/sheep.obj", texture_name="textures/sheep.png", position=(0, 0, 0), scale=0.03)
loadModel("models/skeleton.obj", texture_name="textures/skeleton.png", position=(0, 0, 0), scale=0.03)
loadModel("models/spider.obj", texture_name="textures/spider.png", position=(0, 0, 0), scale=0.03)

# Load sounds
loadSounds()

# Load mob properties
loadMobProperties()

# Create the terrain
FREQ = 16
AMP = 6
WIDTH = 32
HEIGHT = 32

createTerrain(WIDTH, HEIGHT)

# Initialize player
player = Player()

def update():
    player.update()

app.run()
