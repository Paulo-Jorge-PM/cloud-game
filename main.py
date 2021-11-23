#!/usr/bin/env python
# -*- coding: utf-8 -*

import sys, random
import pyglet
from pyglet.window import key, mouse
from pyglet.gl import *

'''
# This code is so you can run the samples without installing the package
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
'''

#Tell pyglet where to find the media resources
pyglet.resource.path = ['resources', 'resources/sprites', 'resources/animations', 'resources/sounds']
pyglet.resource.reindex()


"""
W_width=800
W_height=648
window = pyglet.window.Window(W_width, W_height,caption = 'Test', resizable=True, fullscreen=True)
#center window
#window.set_location(window.screen.width/2 - window.width/2, window.screen.height/2 - window.height/2)
"""

#FPS = pyglet.clock.ClockDisplay()

MAIN_BATCH = pyglet.graphics.Batch()

Z_INDEX1 = pyglet.graphics.OrderedGroup(0)
Z_INDEX2 = pyglet.graphics.OrderedGroup(1)
Z_INDEX3 = pyglet.graphics.OrderedGroup(2)
Z_INDEX4 = pyglet.graphics.OrderedGroup(3)
Z_INDEX5 = pyglet.graphics.OrderedGroup(4)
Z_INDEX6 = pyglet.graphics.OrderedGroup(5)
Z_INDEX7 = pyglet.graphics.OrderedGroup(6)
Z_INDEX8 = pyglet.graphics.OrderedGroup(7)
Z_INDEX9 = pyglet.graphics.OrderedGroup(8)
Z_INDEX10 = pyglet.graphics.OrderedGroup(9)

music_background = "forest.wav"
voice_intro = "voice_intro.wav"
sound_rain = "rain_loop.wav"
#voice_move_mouse = pyglet.resource.media("voice_move_mouse.mp3", streaming=False)
#voice_click_left_button = pyglet.resource.media("voice_click_left_button.mp3", streaming=False)

#FUNCTIONS
def make_sprite(file_name, x=0, y=0, batch=MAIN_BATCH, group = Z_INDEX5, dx=None, dy=None, animation=False, scale=1):
    if animation:
        load = pyglet.resource.animation(file_name)
    else:
        load = pyglet.resource.image(file_name)
    sprite = pyglet.sprite.Sprite(load, x=x, y=y, batch=batch, group=group)
    sprite.scale = scale
    if dx:
        sprite.dx=dx
    if dy:
        sprite.dy=dy
    return sprite

def play_sound_with_delay(dt, filename):
    sound = pyglet.resource.media(filename , streaming=False)
    voice_player = pyglet.media.Player()
    voice_player.queue(sound)
    voice_player.play()

def play_sound(filename, loop=False, volume=1):
    player = pyglet.media.Player()
    player.volume = volume
    sound = pyglet.resource.media(filename , streaming=False)
    if loop == True:
        looper = pyglet.media.SourceGroup(sound.audio_format, None)
        #looper = pyglet.media.SourceGroup()
        looper.loop = True
        looper.queue(sound)
        player.queue(looper)
    else:
        player.queue(sound)
    player.play()
    return player
    
def get_lines_from_file(filename):
        #strip is used to delete new line characters and white space at start and end of line
        lines = [line.strip() for line in open(filename)]
        return lines

class MainWindow(pyglet.window.Window):
    def __init__(self):
        super(MainWindow, self).__init__(caption="Teste", fullscreen=True)
        
        #Constants, speed configurations
        self.CLOUDS2_DX = 30
        self.CLOUDS3_DX = 80
        self.FAIRY_DX = 600
        self.FAIRY_DY = 600
        self.FAIRY_SCALE_SPEED = 0.9#0.8
        self.FAIRY_MAX_SCALE = 7#5
        self.SEED_DY = 180#400
        self.RAIN_DY = 350
        self.TREE_GROWTH_SPEED = 0.025#0.02
        self.RESTART_OPACITY_DOWN_SPEED = 200#250
        self.SEED_BLINK_SPEED = 200
        
        #Track game current phase. I made the sates with the same name as their respective functions. List of all possible:
        #phase1_start
        #"restart_animate_fairy_stars" -> restart for new seeds phase 1: clean screen animation with fairy and stars animation
        #"animate_fairy_new_seeds" -> restart for new seeds phase 2: resets fairy position after the clean, get and creat the new seeds
        #"new_seeds_plant_animation" -> restart for new seeds phase 3: animate the new seeds goign to place
        #"watering" -> wait user to water soil with the cloud 
        #"phase1_end" -> when all seeds/sequences been showed and phase 1 ends, and we want to start phase 2 when children select sequences themselfs
        self.game_state = ""
        
        #SOUNDS/MUSCIC
        #List of sounds currently being played in a loop
        self.sounds_active = {}
        
        #Start music in background
        self.sounds_active["music_playing"] = play_sound(music_background, loop=True, volume=0.7)

        #Rain list made by the rain animation function when left click on the cloud, and used for calculations in the watering function for the tree grow
        self.rains = []
        #The rain is from a sprite grid, which is sliced in 10 rows and we iterate through (self.n_rains tracks this iteration) otherwise only 1 sprite would be a monotonous animation
        self.n_rains = 0
        
        #Fairy stars for animation
        self.stars = []
        
        #MOUSE
        #Change mouse to a grumpy cloud and load happy version for the change when left mouse is pressed
        self.cloud_normal = pyglet.resource.image("cloud_normal.png")
        self.cloud_happy = pyglet.resource.image("cloud_happy.png")
        cursor = pyglet.window.ImageMouseCursor(self.cloud_normal, self.cloud_normal.height/2, 0)
        self.set_mouse_cursor(cursor)
        #Track mouse position
        self.mouse_x = 0
        self.mouse_y = 0
        #And track left click
        self.left_mouse_state = False
        
        #Tree sprite
        self.new_tree = None
        
        #Seed opacity status for blink animation
        self.opacity_status = "down"
        
        #RUN WORLD BACKGROUND
        self.sky()
        self.ground()
        
        #CHARACTERS
        #Narrator
        #Call function/play sounds after x seconds. Template is schedule_once(function, time to wait, args/kargs of function)
        #pyglet.clock.schedule_once(play_sound_with_delay, 1.0, voice_intro)
        
        #Start fairy Oriana
        self.fairy()

        #Load seeds
        self.sequences = get_lines_from_file("data.txt")
        #Next seed sequence to show. PS: now the first, but will be updated while it goes on
        self.sequences_next = {0 : self.sequences[0]}
        
    def sky(self):
        clouds_index2_dx = self.CLOUDS2_DX
        clouds_index3_dx = self.CLOUDS3_DX
        sprite_width = 694
        sprite_height = 126
        self.clouds_index1 = []
        self.clouds_index2 = []
        self.clouds_index3 = []
        x=0
        #repeat images horizontally till they fill all the screen
        while x <= self.width:
            self.clouds_index1.append( make_sprite("clouds_index1.png", x=x, y=self.height-sprite_height, group=Z_INDEX1) )
            self.clouds_index2.append( make_sprite("clouds_index2.png", x=x, y=self.height-sprite_height-40, group=Z_INDEX2, dx=clouds_index2_dx) )
            self.clouds_index3.append( make_sprite("clouds_index3.png", x=x, y=self.height-sprite_height-87, group=Z_INDEX3, dx=clouds_index3_dx) )
            x += self.clouds_index3[0].width
        #Add one extra at the start, outside of the screen on the left, because of the loop animation of them moving (executed in the self.update function)
        self.clouds_index2.insert(0, make_sprite("clouds_index2.png", x=-self.clouds_index2[0].width, y=self.height-sprite_height-40, group=Z_INDEX2, dx=clouds_index2_dx) )
        self.clouds_index3.insert(0, make_sprite("clouds_index3.png", x=-self.clouds_index3[0].width, y=self.height-sprite_height-87, group=Z_INDEX3, dx=clouds_index3_dx) )

    def ground(self):
        #GROUND
        #I want the main scene to fit at least in the height 720px (because the monitor resolution 1280x720 is the one with less height of all the modern ones starting from the 1024x768), so I will try to center the main media and calculate it to fit 720px height 
        x=0
        self.ground_row1 = []
        row1_sprite_list = ["ground_row1_col1.png", "ground_row1_col2.png", "ground_row1_col3.png"]
        while x <= self.width:
            self.ground_row1.append( make_sprite(random.choice(row1_sprite_list), x=x, y=0, group=Z_INDEX6) )
            x += self.ground_row1[0].width
 
    def fairy(self):
        self.fairy = make_sprite("fairy.gif", y=256, group=Z_INDEX8, dx=self.FAIRY_DX, dy=self.FAIRY_DY, animation=True)
        self.fairy.y = self.height - self.fairy.height
 
    """ 
    def labels(self):
        self.text_label = text_label = pyglet.text.Label(
        'Welcome to this software!',
        x=100,
        #y=W_height-100,
        y=200,
        anchor_y='top',
        font_size=50,
        color=(255, 255, 255, 255),
        batch=MAIN_BATCH,
        group=Z_INDEX10)
    """

    def on_key_press(self, symbol, modifiers):
        if symbol == key.UP:
            if self.game_state == "animate_fairy_new_seeds":
                self.game_state = "phase1_start"
            else:
                self.game_state = "animate_fairy_new_seeds"
        if symbol == key.DOWN:
            if window.fullscreen == True:
                self.set_fullscreen(False)
                #pyglet.app.exit()
            else:
                self.set_fullscreen(True)
        if symbol == key.ESCAPE:
            pyglet.app.exit()
            #sys.exit()
            
    def on_key_release(self, symbol, modifiers):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            self.left_mouse_state = True
            #We start tracking mouse x and y here and not only in on_mouse_drag() because the user can click but not move the mouse, and we need x and y right away for the rain animation to position the rain
            self.mouse_x = x
            self.mouse_y = y
            
            #change mouse cloud to happy mode
            cursor = pyglet.window.ImageMouseCursor(self.cloud_happy, self.cloud_happy.height/2, 0)
            self.set_mouse_cursor(cursor)
            
            #Play Sounds
            if "rain" not in self.sounds_active and self.game_state not in ("new_seeds_plant_animation", "animate_fairy_new_seeds", "restart_animate_fairy_stars"):
                self.sounds_active["rain"] = play_sound(sound_rain, loop=True)
            
    def on_mouse_release(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            self.left_mouse_state = False
            
            #change mouse cloud to normal mode
            cursor = pyglet.window.ImageMouseCursor(self.cloud_normal, self.cloud_normal.height/2, 0)
            self.set_mouse_cursor(cursor)
            
            #Turn sounds off and deletes player
            if "rain" in self.sounds_active:
                self.sounds_active["rain"].pause()
                del self.sounds_active["rain"]
        
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        #keep track of mouse x and y for rain (f.e.) animations while left mouse is clicked
        if buttons == mouse.LEFT:
            self.mouse_x = x
            self.mouse_y = y
        
    def animate_clouds(self, dt):
        #ANIMATE CLOUDS
        #if last cloud is out of the screen, remove it out from the list and add a new one at the start: this creats the illusion of a loop inside the screen
        #PS: used the 1st "for loop" for not repeating the code
        for clouds in [self.clouds_index2, self.clouds_index3]:
            for sprite in clouds:
                if sprite.x >= self.width:
                    clouds.remove(sprite)
                    new_sprite = sprite
                    new_sprite.x = clouds[0].x - new_sprite.width
                    clouds.insert(0, new_sprite)
                #Here is the magic of movement
                sprite.x += sprite.dx * dt

    def animate_rain(self, dt):
        if self.left_mouse_state == True and self.game_state not in ("new_seeds_plant_animation", "animate_fairy_new_seeds", "restart_animate_fairy_stars"):
            rain_load = pyglet.resource.image("rain_day.png")
            rain_grid = pyglet.image.ImageGrid(rain_load, 10, 1)
            rain = pyglet.sprite.Sprite(rain_grid[self.n_rains], batch=MAIN_BATCH, group=Z_INDEX8)
            rain.dy = self.RAIN_DY
            rain.x = self.mouse_x - rain.width/2
            rain.y = self.mouse_y - rain.height
            self.rains.append( rain )
            #if grid ouf of index range, restart count
            if self.n_rains >= len(rain_grid)-1:
                self.n_rains = 0
            else:
                self.n_rains += 1
                
        for rain in self.rains:
            #Delete rain sprite in case it is out of screen, otherwise it will slow down the game
            if rain.y + rain.height < 0:
                self.rains.remove(rain)
            #Make Rain transparent when under ground
            elif rain.y <= self.ground_row1[0].height:
                rain.opacity = 0
            #Here is the magic of movement for the rain
            rain.y -= rain.dy * dt
            
            #If game state is waiting for watering the seeds    
            if self.game_state == "watering":
                seeds_left_x = self.seeds_current[0].x
                seeds_right_x = self.seeds_current[-1].x + self.seeds_current[-1].width
                seeds_top_y = self.seeds_current[0].y + self.seeds_current[0].height
                seeds_bottom_y = self.seeds_current[0].y
                
                #if rain.y <= seeds_top_y and rain.y >= seeds_bottom_y and rain.x + rain.width >= seeds_left_x and rain.x <= seeds_right_x:
                #The same but better code more cooler:
                #PS meaning: if rain is touching the seeds, creat tree or make it grow plus flowers, till it reaches scale 1
                if seeds_bottom_y <= rain.y <= seeds_top_y and seeds_left_x - rain.width <= rain.x <= seeds_right_x:
                    #Make seeds blink/opacity up and down when watering them
                    """for seed in self.seeds_current:
                        if seed.opacity == 0:
                            seed.opacity = min(255, seed.opacity + dt * self.SEED_BLINK_SPEED)
                        else:
                            seed.opacity = max(0, seed.opacity - dt * self.SEED_BLINK_SPEED)"""
                    self.seed_blink(dt)
                    self.tree_grow(dt)

    def seed_blink(self, dt):
        #set opacity status, going "up" or going "down"
        n = 0
        #while n < 255 * 2:
        for seed in self.seeds_current:
            if self.opacity_status == "down":
                seed.opacity = max(0, seed.opacity - dt * self.SEED_BLINK_SPEED)
            else:
                seed.opacity = min(255, seed.opacity + dt * self.SEED_BLINK_SPEED)
        self.seeds_current
        if seed.opacity == 0:
            self.opacity_status = "up"
        if seed.opacity == 255:
            self.opacity_status = "down"
        
                    
    def restart_animate_fairy_stars(self, dt):
        #Disable mouse while animation is running
        self.set_mouse_visible(False)
        
        #Animation of fairy movement
        self.fairy.x += self.fairy.dx * dt
        if self.fairy.y > self.ground_row1[0].height/6:
            self.fairy.y -= self.fairy.dy * dt
        if self.fairy.scale < self.FAIRY_MAX_SCALE:
            self.fairy.scale += self.FAIRY_SCALE_SPEED * dt
            
        #Slowly make them transparent, then delete tree, flowers and seeds from screen for a new seed sequence restart
        #Opacity down
        if self.new_tree:
            if self.new_tree.opacity != 0:
                self.new_tree.opacity = max(0, self.new_tree.opacity - (self.RESTART_OPACITY_DOWN_SPEED * dt) )
                for flower in self.flowers:
                    flower.opacity = max(0, flower.opacity - (self.RESTART_OPACITY_DOWN_SPEED * dt) )
                for seed in self.seeds_current:
                    seed.opacity = max(0, flower.opacity - (self.RESTART_OPACITY_DOWN_SPEED * dt) )
            #Delete when opacity is zero
            else:
                #I want to speed the game by deleting every sprite not needed anymore from memory, here I delete each individualy with pyglet delete() command. But maybe is not necessary, because next I delete the list that has all these sprites. But I do it anyway in hopes that it makes the game run faster, since it slows down a little with this many sprites animated on screen.
                for flower in self.flowers:
                    flower.delete()
                del self.flowers[:]
                print(self.flowers)
                for seed in self.seeds_current:
                    seed.delete()
                del self.seeds_current[:]
                self.new_tree.delete()
                #if self.new_tree is not defined this big if block will give error, so we redifine to None
                self.new_tree = None

        #While fairy moves, creat little stars behind
        #Load stars: each column of stars in vertical is a list, inside the list self.stars
        #Animation objective: move fairy and creat columns of stars till 50% of the screen width, then continue creating till fairy reaches out of screen but also deleting the ones behind till they all disapear
        #If starting animation and no stars in screen:
        if not self.stars:
            y = 0
            col_stars = []
            while y < self.height:
                star = make_sprite("stars.gif", x=0, group=Z_INDEX8, animation=True)
                star.y = y
                col_stars.append(star)
                y += star.height
            else:
                self.stars.append(col_stars)

        #If there are already stars, while stars summed width not reach more than half of the screen (1.6 for example; because stars start disapearing when fairy reaches half of the screen, so we need it to go the screen width plus half of it to be sure all the stars are out of the screen), create new stars when fairy is distant by the last column of stars by the width of the stars sprite
        elif self.fairy.x >= self.stars[-1][0].x + self.stars[-1][0].width + self.stars[-1][0].width and self.stars[0][0].width * len(self.stars) <= self.width * 1.6:
            y = 0
            col_stars = []
            while y < self.height:
                star = make_sprite("stars.gif", y=y, group=Z_INDEX8, animation=True)
                star.x = self.stars[-1][0].x + star.width
                col_stars.append(star)
                y += star.height
            else:
                self.stars.append(col_stars)
            #If stars occupy already half of the screen, make the first columns of stars invisible in the list of visible (we don't delete it yet, because we want it in the list of stars because of width calculations in the previous code logic
            if self.stars[0][0].width * len(self.stars) >= self.width/2:
                for stars in self.stars:
                    if stars[0].visible == True:
                        for star in stars:
                            star.visible = False
                            
                        #If last star is out of screen and animation ended, call next event animation in self.game_state
                        if stars[0].x > self.width:
                            #delete all sprites of stars from memory
                            for stars in self.stars:
                                for star in stars:
                                    star.delete()
                            #Empty list. Not: there is a difference between using 1) LIST = [] and 2) LIST[:] = [] or del LIST[:] but I think in this case it is not importante and makes no difference
                            #self.stars = []
                            #self.stars[:] = []
                            del self.stars[:]
                            #end this animation event and start the next one
                            self.game_state = "animate_fairy_new_seeds"
                        #break, because we have already found the firt visible star column of the list, don't need the others
                        break
        
    def animate_fairy_new_seeds(self, dt):
        if self.fairy.scale != 1:
            self.fairy.scale = 1
            self.fairy.x = -self.fairy.width
            self.fairy.y = self.height - self.fairy.height
        
        #If fairy out of position from previous animation, put it in place
        if self.fairy.x != 0:
            self.fairy.x = min(0, self.fairy.x + self.fairy.dx * dt)
        else:
            #And add new seeds
            self.new_seeds()
            
    def new_seeds(self):
        self.seeds_current = []

        for key in self.sequences_next:
            seeds = list(self.sequences_next[key])
            seed_key = key

        for seed_number in seeds:
            sprite_name = "gem" + str(seed_number) + ".png"
            seed = make_sprite(sprite_name, dy=self.SEED_DY, group=Z_INDEX7)
            seed.y = self.height
            #Center the seeds in the window. If not seeds make calculations for the 1st, if already one make calculations based on it
            if self.seeds_current:
                seed.x = self.seeds_current[0].x + seed.width * len(self.seeds_current)
            else:
                seed.x = self.width/2 - (len(seeds) * seed.width)/2
            self.seeds_current.append(seed)
        #Upadte self-sequences_next with next seed, if not out of seeds
        if len(self.sequences) >= seed_key+1:
            self.sequences_next = {seed_key+1 : self.sequences[seed_key+1]}
        #If the list of seeds reach the end, prepare to end phase 1
        else:
            self.game_state = "phase1_end"
        #When the new seeds are on screen, start their animation
        self.game_state = "new_seeds_plant_animation"
                
    def new_seeds_plant_animation(self, dt):
        #Move the seeds into the screen by sliding from the top of the screen
        for seed in self.seeds_current:
            if seed.y != self.ground_row1[0].height - seed.height:
                seed.y = max(self.ground_row1[0].height - seed.height, seed.y - seed.dy * dt)
            else:
                #Game waits for rain to drop in the seeds and grow tree
                self.game_state = "watering"
                #Enable mouse again
                self.set_mouse_visible(True)
        
    def tree_grow(self, dt):
        #If already tree, grow tree
        if self.new_tree:
            self.new_tree.scale = min(1, self.new_tree.scale + dt * self.TREE_GROWTH_SPEED)
            #Center the new scale sprite on screen
            self.new_tree.x = self.width/2 - self.new_tree.width/2
            
            #new flowers while grow
            if self.new_tree.scale >= self.new_flower_each_scale * len(self.flowers):
                flower = make_sprite("flowers.gif", y=self.ground_row1[0].height, animation=True, group=Z_INDEX8)
                flower.scale = 0.2
                flower.x = self.flowers[-1].x + flower.width
                self.flowers.append(flower)
                play_sound("completetask_0.wav", loop=False, volume=1)
            
            #if tree scales is 1, end and go to the next sequence/phase
            if self.new_tree.scale == 1:
                play_sound("sequence_end.wav", loop=False, volume=1)
                #jump to next phase: clearing all in screen with fairy+stars animation, for new seed if it exist
                self.game_state = "restart_animate_fairy_stars"
            
        #If no tree, creat sprite and plant new small tree baby :3
        else:
            #self.ground[0].height
            self.new_tree = make_sprite("tree1.png", y=self.ground_row1[0].height, group=Z_INDEX9)
            #Make the tree very small
            self.new_tree.scale = 0.01
            #Center the sprite on screen
            self.new_tree.x = self.width/2 - self.new_tree.width/2
            
            #first flower
            flower = make_sprite("flowers.gif", x=0, y=self.ground_row1[0].height, animation=True, group=Z_INDEX8)
            flower.scale = 0.2
            
            #list with all flowers
            self.flowers = []
            
            self.flowers.append(flower)
            play_sound("completetask_0.wav", loop=False, volume=0.7)
            
            #calculate when new flower
            self.total_flowers = self.width / float(flower.width)
            
            #The tree stops grow when reachs 1 scale. Creat a new flower each time the tree grows this:
            self.new_flower_each_scale = 1 / self.total_flowers

    def phase1_end(self, dt):
        #prepare phase 1 end where children only watch sequences, and go the phase 2, where the children can select sequences
        pass
        
    def on_draw(self):
        self.clear()
        MAIN_BATCH.draw()
        #FPS.draw()
        #Set window background color rgba (note: in gl is in scale 0 to 1, inestead of 0 to 255; that is why I devide the rgb values by 255, so we get a floated value in the 0 to 1 scale
        pyglet.gl.glClearColor(241.0/255, 246.0/255, 248.0/255, 1)
        
    def update(self, dt):
        self.animate_clouds(dt)
        self.animate_rain(dt)
        
        #If there is something in the self-game_state call it's function. I made the sates with the same name as their respective functions
        if self.game_state:
            #If it exists call function dynamically instead of using a long if elif f.e.: if self.game_state == "restart_animate_fairy_stars": self.restart_animate_fairy_stars(dt) etc
            try:
                getattr(self, self.game_state)(dt)
            except:
                pass
        """
        if self.game_state == "restart_animate_fairy_stars":
            self.restart_animate_fairy_stars(dt)
        elif self.game_state == "animate_fairy_new_seeds":
            self.animate_fairy_new_seeds(dt)
        elif self.game_state ==  "new_seeds_plant_animation":
            self.new_seeds_plant_animation(dt)
        elif self.game_state ==  "watering":
            self.watering(dt)
        """    

def update(dt):
    if window:
        window.update(dt)

"""
class Seeds():
    def __init__(self):
        self.filename = "resources.txt"
        self.sequences = self.get_lines_from_file(self.filename)
        
        for seq in self.sequences:
            for char in seq:
                print char

    def get_lines_from_file(self, filename):
        #strip is used to delete new line characters and white space at start and end of line
        lines = [line.strip() for line in open(filename)]
        return lines
"""

if __name__ == '__main__':
    #FPS delta time
    pyglet.clock.schedule_interval(update, 1/60.0)
    window = MainWindow()
    pyglet.app.run()


