#!/usr/bin/python
# -*- coding: utf8 -*-

import pygame, jsonpickle, uuid
from os import path
from random import random, choice
from vector import Vector

class MotiveType:
  Unknown = 0
  Pedestrian = 1
  Car = 2

class Motive:
  def __init__(self, pos, direction, t):
    self.pos = Vector(pos)
    self.direction = direction
    self.type = t
    self.speed = random()
    self.age = pygame.time.get_ticks()
    self.ttl = 15000 + 5000 * random()

    self.color = (255, 255, 255)

    size = 1
    if self.type == MotiveType.Pedestrian:
      self.size = int(size)
    if self.type == MotiveType.Car:
      self.size = [int(size*2 + random()), int(size*2 + random() * 2)]

  def update(self, dt, checkForCollision):
    newPos = self.pos + self.direction * self.speed

    if checkForCollision(newPos):
      self.direction = choice([self.direction.getLeftPerpendicular(), self.direction.getRightPerpendicular()])
    else:
      self.pos = newPos


  def draw(self, screen):
    if self.type == MotiveType.Pedestrian:
      pygame.draw.circle(screen, self.color, self.pos.toIntArr(), self.size)
    if self.type == MotiveType.Car:
      pygame.draw.rect(screen, self.color, self.pos.toIntArr() + self.size)
      # forward = self.direction * self.size[1]/2
      # backward = self.direction * self.size[1]/2 * -1
      # left = self.direction.getLeftPerpendicular() * self.size[0]/2
      # right = self.direction.getRightPerpendicular() * self.size[0]/2

      # p1 = self.pos + forward + left
      # p2 = self.pos + forward + right
      # p3 = self.pos + backward + left
      # p4 = self.pos + backward + right
      # pygame.draw.polygon(screen, (0,255,255), [p1.toIntArr(), p2.toIntArr(), p3.toIntArr(), p4.toIntArr()])

class Main:

  def __init__(self):
    pygame.init()

    self.screenDim = (1440, 900)
    self.screen = pygame.display.set_mode(self.screenDim)
    self.background = (255, 255, 255)
    self.running = False

    self.mapData = None
    #self.mapDataPath = "data/test_"
    self.mapDataPath = "map.png"

    self.mapReloadInterval = 1000
    self.lastMapReload = 0

    self.drawBackground = True
    self.drawRoad = True
    self.threshold = 600

    self.motives = []
    self.populationLimit = 1000

  def reloadMap(self):
    list = range(1, 11)
    list.reverse()
    for i in list:
      #filename = self.mapDataPath
      filename = self.mapDataPath# + str(i) + ".png"
      if path.isfile(filename):
        #print filename
        img = pygame.image.load(filename)
        self.mapData = pygame.transform.scale(img, self.screenDim)
        break
    #print "done " + str(self.mapData)

  def isSet(self, pos):
    if not self.mapData:
      print "no mapData yet"
      return True

    if not isinstance(pos, Vector):
      pos = Vector(pos)

    if pos.x < 0 or pos.y < 0:
      return True
    if pos.x >= self.screenDim[0] or pos.y >= self.screenDim[1]:
      return True

    px = self.mapData.get_at(pos.toIntArr())
    return (px.r + px.g + px.b) < self.threshold

  def poll(self):
    events = pygame.event.get()
    for e in events:
      if e.type == pygame.QUIT:
        self.running = False
      elif e.type == pygame.KEYUP:
        if e.key == pygame.K_ESCAPE:
          self.running = False
        elif e.key == pygame.K_f:
          pygame.display.toggle_fullscreen()
        elif e.key == pygame.K_b:
          self.drawBackground = not self.drawBackground
        elif e.key == pygame.K_r:
          self.drawRoad = not self.drawRoad

  def spawn(self):
    x = choice(range(self.screenDim[0]))
    y = choice(range(self.screenDim[1]))
    pos = Vector(x,y)
    if not self.isSet(pos):
      self.motives.append(Motive(pos, Vector.randomUnitCircle(), choice([MotiveType.Car, MotiveType.Pedestrian])))

  def update(self, dt):

    time = pygame.time.get_ticks()

    if self.lastMapReload == 0 or self.lastMapReload + self.mapReloadInterval < time:
      self.lastMapReload = time
      #print "reloading map..."
      self.reloadMap()

    for motive in self.motives:
      motive.update(dt, self.isSet)

    if len(self.motives) < self.populationLimit:
      if len(self.motives) == 0:
        for i in range(100):
          self.spawn()
      else:
        self.spawn()

  def draw(self):
    if self.mapData and self.drawBackground:
      self.screen.blit(self.mapData, [0,0, self.screenDim[0], self.screenDim[1]])
    else:
      self.screen.fill((0,0,0))

    for motive in self.motives:
      motive.draw(self.screen)

  def run(self):

    self.running = True
    clock = pygame.time.Clock()
    while self.running:
      dt = clock.tick(40) / 1000.0

      self.screen.fill(self.background)

      self.poll()
      self.update(dt)
      self.draw()

      pygame.display.flip()

if __name__ == '__main__':
  main = Main()
  print "starting..."
  main.run()
  print "shuting down..."
