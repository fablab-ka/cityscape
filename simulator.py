import pygame
from random import random, choice
from vector import Vector

class MotiveType:
  Unknown = 0
  Pedestrian = 1
  Car = 2

class Motive:
  def __init__(self, start, target, targetId, t):
    self.pos = Vector(start)
    self.start = start
    self.target = target
    self.targetId = targetId
    self.type = t
    self.speed = random()
    self.age = pygame.time.get_ticks()
    self.ttl = 15000 + 5000 * random()

    self.arrivedAtTarget = False
    self.minTargetDistance = 10
    self.color = (255, 0, 0)

    size = 1
    if self.type == MotiveType.Pedestrian:
      self.size = int(size)
    if self.type == MotiveType.Car:
      self.size = [int(size + random() * 2), int(size + random() * 2)]

  def update(self, dt):
    direction = (self.target - self.start).getNormalized()
    variation = 0
    if random() > 0.5:
      variation = direction.getLeftPerpendicular()
    else:
      variation = direction.getRightPerpendicular()

    direction = (direction * (random() * 10) + variation * random()).getNormalized()

    self.pos += direction * self.speed

    self.arrivedAtTarget = (self.target - self.pos).getLengthSqr() < self.minTargetDistance

  def draw(self, screen):
    if self.type == MotiveType.Pedestrian:
      pygame.draw.circle(screen, self.color, self.pos.toIntArr(), self.size)
    if self.type == MotiveType.Car:
      pygame.draw.rect(screen, self.color, self.pos.toIntArr() + self.size)

class Simulator:
  def __init__(self, blobManager, roadManager):
    self.blobManager = blobManager
    self.roadManager = roadManager

    self.motives = []
    self.targetPopulation = 1000

  def fartherAway(self, start, endA, endB):
    distA = (endA-start).getLengthSqr()
    distB = (endB-start).getLengthSqr()

    return endA if distA < distB else endB

  def update(self, dt):
    time = pygame.time.get_ticks()

    dead = []
    for motive in self.motives:
      motive.update(dt)

      if (time - motive.age) > motive.ttl:
        dead.append(motive)
      else:
        if motive.arrivedAtTarget:
          motive.start = motive.target
          if self.blobManager.blobDict.has_key(motive.targetId):
            blob = self.blobManager.blobDict[motive.targetId]
            if len(blob.roads) > 0:
              road = choice(blob.roads)
              motive.target = self.fartherAway(motive.pos, road.start, road.end)
              motive.targetId = road.startId if motive.target == road.start else road.endId

    for deadMotive in dead:
      print "died"
      self.motives.remove(deadMotive)

    if len(self.roadManager.roads) > 0:
      if len(self.motives) < self.targetPopulation:
        if len(self.motives) == 0:
          for i in range(100):
            self.spawn()
        else:
          self.spawn()

  def spawn(self):
    road = choice(self.roadManager.roads)
    self.motives.append(Motive(road.start, road.end, road.endId, choice([MotiveType.Car, MotiveType.Pedestrian])))

  def draw(self, screen):
    for motive in self.motives:
      motive.draw(screen)