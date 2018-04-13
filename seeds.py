#!/usr/bin/env python
# -*- coding: utf-8 -*

import pyglet

class Seeds():
    def __init__(self):
        self.filename = "data.txt"
        self.sequences = self.get_lines_from_file(self.filename)
        
        load = pyglet.resource.image(gem1.png)
        self.seed = pyglet.sprite.Sprite(load, x=500, y=500, batch=MAIN_BATCH)
        
        for seq in self.sequences:
            for char in seq:
                print char
    
    def get_lines_from_file(self, filename):
        #strip is used to delete new line characters and white space at start and end of line
        lines = [line.strip() for line in open(filename)]
        return lines