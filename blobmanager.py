# -*- coding: utf8 -*-

import pygame,  jsonpickle, uuid, math
from os import path
from random import choice, random, randint
from vector import Vector

class Blob:
  def __init__(self, pos, radius):
    self.id = str(uuid.uuid1())
    self.pos = Vector(pos)
    self.radius = radius
    self.state = 0

  def clone(self):
    result = Blob(self.pos, self.radius)
    result.id = self.id
    result.state = self.state
    return result

  def __getstate__(self):
    return [self.id, self.pos, self.radius, self.state]

  def __setstate__(self, stateData):
    self.id = stateData[0]
    self.pos = stateData[1]
    self.radius = stateData[2]
    self.state = stateData[3]

class BlobManager:
  def __init__(self, screenDim, mapData):
    self.mapData = mapData
    self.screenDim = screenDim

    self.blobs = []
    self.blobColor = (255, 0, 0)

    self.blobPersistenceInterval = 10000
    self.lastPersistence = 0

    self.blobMergeLimit = 10
    self.blobMergeRadiusFactor = 2.5
    self.spawnRate = 10000
    self.lastSpawn = 0

    self.blobFile = "blobs.json"
    if path.isfile(self.blobFile):
      print "loading existing blobs..."
      with open(self.blobFile, 'r') as f:
        content = f.read()
        self.blobs = jsonpickle.decode(content)
      print "done."
    else:
      self.massiveSpawn(10, 10)

  def persistBlobs(self):
    print "persisting blobs..."
    blobData = jsonpickle.encode(self.blobs)
    with open(self.blobFile, 'w') as f:
      f.write(blobData)
    print "done."

  def isSet(self, pos):
    if isinstance(pos, Vector):
      pos = pos.toIntArr()

    if pos[0] < 0 or pos[1] < 0:
      return True
    if pos[0] >= self.screenDim[0] or pos[1] >= self.screenDim[1]:
      return True

    px = self.mapData.get_at(pos)
    return (px.r + px.g + px.b) > 600

  def mutate(self, blob):
    newBlob = blob.clone()

    if random() > 0.25:
      newBlob.pos.x = newBlob.pos.x + choice([1,-1])
    elif random() > 0.25:
      newBlob.pos.y = newBlob.pos.y + choice([1,-1])
    else:
      newBlob.radius = newBlob.radius + 1

    return newBlob

  def validate(self, blob):
    result = True
    pos = blob.pos
    if self.isSet(pos):
      result = False
    else:
      radius = blob.radius
      sqrRadius = radius**2
      for x in range(-radius, radius):
        for y in range(-radius, radius):
          if x*x + y*y <= sqrRadius:
            cPos = [pos.x + x, pos.y + y]
            if self.isSet(cPos):
              result = False
              break

        if not result:
          break

      for otherBlob in self.blobs:
        if otherBlob.id == blob.id:
          continue

        distance = Vector.distanceSqr(otherBlob.pos, blob.pos)
        if distance < (otherBlob.radius + blob.radius) ** 2:
          result = False
          break


    return result

  def getCenter(self, posA, posB):
    return [
      int((posA[0] + posB[0]) / 2.0),
      int((posA[1] + posB[1]) / 2.0)
    ]

  def findCloseBlobs(self, blob, radius):
    result = []

    radiusSqr = radius * radius
    for otherBlob in self.blobs:
      if otherBlob.id == blob.id:
        continue

      if Vector.distanceSqr(blob.pos, otherBlob.pos) < radiusSqr:
        result.append(otherBlob)

    return result

  def tryMergeBlob(self, blob):
    otherBlobs = self.findCloseBlobs(blob, blob.radius * self.blobMergeRadiusFactor)

    for otherBlob in otherBlobs:
      center = ((otherBlob.pos + blob.pos) / 2.0).toIntArr()
      newBlob = Blob(center, blob.radius + otherBlob.radius)

      if self.validate(newBlob):
        print "mergedBlob at", blob.pos
        self.blobs.remove(blob)
        self.blobs.remove(otherBlob)
        self.blobs.append(newBlob)
        break

  def getLocationNextToRandomBlob(self):
    x = -1
    y = -1
    blob = self.blobs[randint(0, len(self.blobs)-1)]
    d = random() * math.pi
    dir = [
      math.cos(d) * choice([1, -1]),
      math.sin(d) * choice([1, -1])
    ]

    distance = blob.radius * (1 + random())

    x = int(math.floor(blob.pos.x + dir[0] + distance))
    y = int(math.floor(blob.pos.y + dir[1] + distance))

    return [x, y]

  def spawn(self):
    print "spawning blobs"
    x = -1
    y = -1
    if len(self.blobs) > 0:
      x, y = self.getLocationNextToRandomBlob()
    else:
      x = randint(0, self.screenDim[0]-1)
      y = randint(0, self.screenDim[1]-1)

    if not self.isSet([x, y]):
      blob = Blob([x, y], 1)
      if self.validate(blob):
        print "blob spawned at", blob.pos
        self.blobs.append(blob)
      else:
        print "failed"

  def massiveSpawn(self, massiveSteps, massiveRadius):
    print "initially spawning blobs"

    total = float(self.screenDim[0] * self.screenDim[1])
    for mx in range(self.screenDim[0]/massiveSteps):
      for my in range(self.screenDim[1]/massiveSteps):
        x = mx*massiveSteps
        y = my*massiveSteps

        if not self.isSet([x, y]):
          blob = Blob([x, y], massiveRadius)
          if self.validate(blob):
            print len(self.blobs)," blobs spawned (", blob.pos,")"
            self.blobs.append(blob)

  def calculateScore(self):
    result = 0

    radiuses = 0.0
    for blob in self.blobs:
      radiuses = radiuses + blob.radius

    return radiuses/(float(len(self.blobs))+0.0001)

  def update(self, dt):
    blobsToTryMerge = []
    for i in range(len(self.blobs)):
      blob = self.blobs[i]
      mutatedBlob = self.mutate(blob) # mutating blobs
      if self.validate(mutatedBlob):
        self.blobs[i] = mutatedBlob
      else:
        blob.state = blob.state + 1

        if blob.radius < self.blobMergeLimit: # merging blobs
          blobsToTryMerge.append(blob)

    for blob in blobsToTryMerge:
      if blob in self.blobs:
        self.tryMergeBlob(blob)

    deadBlobs = []
    for blob in self.blobs:
      if not self.validate(blob): # removing dead blobs
        deadBlobs.append(blob)
    for blob in deadBlobs:
      print "removing dead blob at", blob.pos
      self.blobs.remove(blob)

    time = pygame.time.get_ticks()
    if self.lastSpawn + self.spawnRate > time:
      self.lastSpawn = time
      self.spawn()

    time = pygame.time.get_ticks()
    if self.lastPersistence + self.blobPersistenceInterval < time:
      self.lastPersistence = time
      self.persistBlobs()

  def draw(self, screen):
    for blob in self.blobs:
      pygame.draw.circle(screen, self.blobColor, blob.pos, blob.radius)
