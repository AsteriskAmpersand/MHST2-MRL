# -*- coding: utf-8 -*-
"""
Created on Sun Aug 22 14:03:52 2021

@author: Asterisk
"""

import CRC

horrorshow = lambda x: ((x& 0x000fffff) << 12)

hashMap = {}
with open("MFXStringDump.txt","r") as inf:
    for string in map(lambda x: x.strip(), inf.read().split('\n')):
        hashMap[string] = CRC.numericJam(string)
with open("SAStringDump.txt","r") as inf:
    for string in map(lambda x: x.strip(), inf.read().split('\n')):
        hashMap[string] = CRC.numericJam(string)
with open("MRLHashesRaw.csv",'w') as outf:
    for string in hashMap:
        if "," not in string:
            outf.write(string+','+"%X\n"%horrorshow(hashMap[string]))
    outf.write(",0")