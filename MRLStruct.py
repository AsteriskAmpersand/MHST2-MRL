# -*- coding: utf-8 -*-
"""
Created on Sun Aug 22 08:28:09 2021

@author: Asterisk
"""

import io
import sys
sys.path.insert(1, './common')
from Cstruct import PyCStruct,readBinary

hashMap = {}
with open("MRLHashes.csv","r") as inf:
    for entry in inf.read().split('\n'):
        name,_,_,_,jamcrc = entry.split(",")
        hashMap[int(jamcrc,16)] = name
inverseHashMap = {val:key for key,val in hashMap.items()}

NULL = 0xCDCDCDCD

def print(*args,**kwargs):
    pass

class MRLHeader(PyCStruct):
    fields = {"id":"long",
              "unkn":"uint",
              "materialCount":'uint',
              'textureCount':'uint',
              'unkn2':'uint64',
              'textureOffset':'uint64',
              'materialOffset':'uint64'}
    
def arraypad(size,default,arr):
    if len(arr) > size: raise
    return arr + [default]*(size - len*arr)
    
class MRLTexture(PyCStruct):
    fields = {"fileTypeCode":"uint",
              "unkn2":"byte[20]",
              "_path":'ubyte[128]'}
    def marshall(self,stream):
        super().marshall(stream)
        self.path = bytes(self._path[:self._path.index(0)]).decode('utf-8')
        return self
    def construct(self,data):
        data["_path"] = arraypad(128,0xCD,list(data['path'].encode('utf-8'))+[0])

class MRLMaterial(PyCStruct):
    fields = {"headID":"uint",
              "nullCD":"uint",
              "materialNameHash":'uint',
              'matSize':'uint',
              'shaderHash':'uint',
              'skinID':'uint',
              'unkn4':'short',
              'floatArrayOffset':'ubyte',
              'unkn5':'ubyte[9]',
              'unkn6':'ubyte',
              'unkn7':'ubyte[19]',
              'startAddr':'uint64',
              'unkn8':'uint64'
              }

class MRLProperty(PyCStruct):
    fields = {"hash":'uint32',
              'value':'uint32'}#Probably should use int
    def marshall(self,stream):
        super().marshall(stream)        
        if self.hash in hashMap:
            self.name = hashMap[self.hash]
            #print(self.name)
        else:
            #print("Unknown hash %X"%self.hash)
            self.name = None
        self.active = NULL != self.value
        self.next = self.hash == 0 or self.name == '$Globals'#260 for premade buffers?
        return self
    def construct(self,data):
        if data['name'] in inverseHashMap:
            data['hash'] = inverseHashMap[data['name']]
        else:
            raise KeyError
        super().construct(data)
    def getName(self):
        if self.name: return self.name
        else: return "Unknown Hash %X"%self.hash
    def getValueStr(self):
        if self.active:
            return str(self.value)
        else:
            return "INVALID"
    def __str__(self):
        return self.getName()+": "+self.getValueStr()

spacer = '_________________________________\n'
class MaterialBuffer():
    def marshall(self,buffer):
        sentinel = len(buffer)
        stream = io.BytesIO(buffer)
        self.properties = []
        self.values = []
        self.textures = []
        storage = [self.properties,self.textures,self.values,]
        operator = [lambda s: MRLProperty().marshall(s),
                    lambda s: MRLProperty().marshall(s),
                    lambda s: readBinary("float",s),]
        active = 0
        while stream.tell() < sentinel:
            prop = operator[active](stream)
            storage[active].append(prop)
            if active < 2 and prop.next:
                active+=1                
        return self
    def __getitem__(self,ix):
        return self.properties[ix]
    def __setitem__(self,ix,value):
        self.properties[ix] = value
    def __str__(self):
        string = ''
        string+='\t'+spacer
        plen,vlen = len(self.properties),len(self.values)
        string+='\tProperties (%d/%d) [%d]: \n'%(plen,vlen,4*(plen))
        string+='\t'+spacer
        for ix,prop in enumerate(self.properties):
            string += '\t'+str(ix)+": "+str(prop)+'\n'
        string+='\t'+spacer
        string+='\tTextures: \n'
        string+='\t'+spacer
        for ix,tex in enumerate(self.textures):
            string += '\t'+str(ix)+": "+str(tex)+'\n'
        return string
    
class _MaterialBuffer():
    def marshall(self,buffer):
        sentinel = len(buffer)
        stream = io.BytesIO(buffer)
        self.properties = []
        print("====================")
        print(sentinel//4)
        while stream.tell() < sentinel:
            val = readBinary("uint",stream)
            if val in hashMap:
                print((stream.tell()-4)//4,hashMap[val])
        print("====================")
        return None

def align(alignment,stream):
    stream.read((-stream.tell())%alignment)

class MRL():
    def __init__(self):
        self.header = MRLHeader()
        self.textures = []
        self.materials = []
    def marshall(self,stream):
        self.header.marshall(stream) 
        self.textures = [MRLTexture().marshall(stream) for tex in range(self.header.textureCount)]
        self.materials = [MRLMaterial().marshall(stream) for mat in range(self.header.materialCount)]
        align(16,stream)
        for ix,material in enumerate(self.materials):
            stream.seek(material.startAddr)
            materialBuffer = stream.read(material.matSize)
            buffer = MaterialBuffer().marshall(materialBuffer)
            material.buffer = buffer
            print(ix)
            print(buffer)
            print("=========================")
        return self

def MRLFile(filepath):
    with open(filepath,"rb") as inf:
        mrl = MRL().marshall(inf)
    return mrl

if __name__ in '__main__':
    import csv
    
    i = 0
    from pathlib import Path
    filelist = Path(r"C:\Users\Asterisk\Documents\MHST2").rglob('*mrl')
    keys = []
    data = []
    #filelist = [r"C:\Users\Asterisk\Documents\MHST2\archive\stage\v05_01\v05_01_field\stage\_common_sky\common01_noon.mrl"]
    for file in filelist:
        mrl = MRLFile(file)
        for material in mrl.materials:
            md = material.dict()
            keys = md.keys()
            data.append({**md,"file":str(file)})
        #raise
        #if i > 10: raise
        #i += 1
    
    f = open('mrlDB.csv','w')
    w = csv.DictWriter(f,["file"]+list(keys))
    w.writeheader()
    w.writerows(data)
    f.close()
    
#import pandas as pd
#mrlDB = pd.read_csv("mrlDB.csv")
