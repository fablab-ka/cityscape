#!/usr/bin/python
# -*- coding: utf8 -*-

import pygame, random, jsonpickle, uuid
from os import path

from blobmanager import BlobManager
from roadmanager import RoadManager
from simulator import Simulator

class Main:

  def __init__(self):
    pygame.init()

    self.screenDim = (1024, 786)
    self.screen = pygame.display.set_mode(self.screenDim)
    self.background = (255, 255, 255)
    self.running = False

    self.scoreCheckInterval = 10000
    self.lastScoreCheck = 0
    self.currentBlobManagerScore = 0

    self.mapData = None
    #self.mapDataPath = "data/test_"
    self.mapDataPath = "map.png"

    self.updateBlobs = True

    self.blobManager = BlobManager(self.screenDim, self.mapData)
    self.roadManager = RoadManager(self.screenDim, self.blobManager)
    self.simulator = Simulator(self.blobManager, self.roadManager)

    self.mapReloadInterval = 1000
    self.lastMapReload = 0

    self.wasRight = False
    self.drawBackground = True

  def reloadMap(self):
    list = range(1, 11)
    list.reverse()
    for i in list:
      filename = self.mapDataPath# + str(i) + ".png"
      if path.isfile(filename):
        #print filename
        img = pygame.image.load(filename)
        self.mapData = pygame.transform.scale(img, self.screenDim)
        self.blobManager.mapData = self.mapData
        break
    #print "done " + str(self.mapData)

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
          self.roadManager.drawRoad = not self.roadManager.drawRoad
        elif e.key == pygame.K_l:
          self.roadManager.drawLine = not self.roadManager.drawLine
        elif e.key == pygame.K_c:
          self.blobManager.drawBlobs = not self.blobManager.drawBlobs
        elif e.key == pygame.K_u:
          self.updateBlobs = not self.updateBlobs
      elif e.type == pygame.MOUSEBUTTONDOWN:
          btns = pygame.mouse.get_pressed()
          self.wasRight = btns[2]
      elif e.type == pygame.MOUSEBUTTONUP:
        if self.wasRight:
          self.blobManager.removeAt(e.pos)
        else:
          self.blobManager.spawnAt(e.pos)

  def update(self, dt):

    time = pygame.time.get_ticks()

    if self.lastMapReload == 0 or self.lastMapReload + self.mapReloadInterval < time:
      self.lastMapReload = time
      #print "reloading map..."
      self.reloadMap()

    if self.updateBlobs:
      self.blobManager.update(dt)

      self.roadManager.update(dt)

    self.simulator.update(dt)


    if self.lastScoreCheck == 0 or self.lastScoreCheck + self.scoreCheckInterval < time:
      self.lastScoreCheck = time
      print "calculating scores..."
      newScore = self.blobManager.calculateScore()
      if newScore > self.currentBlobManagerScore:
        self.currentBlobManagerScore = newScore
        print "updating roads (score:" + str(self.currentBlobManagerScore) + ")"
        self.roadManager.regenerate()
      else:
        print "no score change"

  def draw(self):
    if self.mapData and self.drawBackground:
      self.screen.blit(self.mapData, [0,0, self.screenDim[0], self.screenDim[1]])
    else:
      self.screen.fill((0,0,0))

    self.blobManager.draw(self.screen)
    self.roadManager.draw(self.screen)
    self.simulator.draw(self.screen)

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
