#!/usr/bin/python
# -*- coding: utf8 -*-

import pygame, random, jsonpickle, uuid
from os import path

from blobmanager import BlobManager
from roadmanager import RoadManager

class Main:

  def __init__(self):
    pygame.init()

    self.screenDim = (1024, 786)
    self.screen = pygame.display.set_mode(self.screenDim)
    self.background = (255,255,255)
    self.running = False

    self.scoreCheckInterval = 10000
    self.lastScoreCheck = 0
    self.currentBlobManagerScore = 0

    img = pygame.image.load('map.png')
    self.mapData = pygame.transform.scale(img, self.screenDim)
    self.blobManager = BlobManager(self.screenDim, self.mapData)
    self.roadManager = RoadManager(self.screenDim, self.mapData, self.blobManager)

  def poll(self):
    events = pygame.event.get()
    for e in events:
      if e.type == pygame.QUIT:
        self.running = False
      elif e.type == pygame.KEYUP:
        if e.key == pygame.K_ESCAPE:
          self.running = False

  def update(self, dt):
    self.blobManager.update(dt)
    self.roadManager.update(dt)

    time = pygame.time.get_ticks()
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
    self.screen.blit(self.mapData, [0,0, self.screenDim[0], self.screenDim[1]])

    self.blobManager.draw(self.screen)
    self.roadManager.draw(self.screen)

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
