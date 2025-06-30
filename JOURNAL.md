---
title: "Note Block Maestro"
author: "Luke Collingridge"
description: "A physical note block that plays MIDI files as note block audio, and can also convert them to schematic or data pack form for use in-game."
created_at: "2025-06-28"
---

# June 28th: Planning

Today was spent planning out the project just to make sure it's technically feasible, as well as doing some basic setup and preparation. As for hardware, this is what I've come up with so far (very tentative and incomplete list):
 - Raspberry Pi 4 B 2GB for main processing, playback, and converting of files 
 - 32 GB MicroSD card for OS files, programs, and audio files
 - HiFiBerry MiniAmp (3 W × 2) as the amplifier
 - Some kind of speakers for audio playback
 - Push buttons w/ LEDs for basic controls
 - USB-C PSU to power Pi and MiniAmp
 - Any wood I have lying around for the box

I also took a look into software to use for the project:
 - [Hyperchoron](https://github.com/thomas-xin/hyperchoron) as the tool to convert sequence files to Minecraft-compatible formats
 - [pynbs](https://github.com/OpenNBS/pynbs) and [pygame](https://github.com/pygame/pygame) to play audio from the speakers

Next I'll work on actually submitting the project, testing software from my PC, and figuring out specific hardware models to purchase as well as costs.

**Total time spent: 2 hours**

# June 29th: Planning, shopping, and finalizing

The past day has mostly been spent just planning and shopping for parts. I think I have figured out every part that I want to use:
 - Raspberry Pi 5 4GB for all processing
 - 64 GB MicroSD card for storage
 - USB MicroSD reader for my PC
 - MAX98357 I²S mono amp (3 W) for speaker output
 - Dayton PC105-4 4" speaker for good audio playback; should hit >90dB
 - 2.8″ SPI Arducam TFT with 5 MP camera and 320x240 display. It seems like an odd choice, but it has a really great deal right now, and the camera and touchscreen open up lots of future possibilities
 - 10x 12-mm push buttons
 - 2x KY‑040 encoders
 - Dupont jumper wire bundle
 - 600‑pc M3 nylon standoffs in case I don't have any lying around
 - Premium soldering kit in case I don't have one somewhere
 - Official	Pi 5 Active Cooler
 - Either 3d-printing filament or plywood for the container. 3d-printing would be much preferred but difficult for me to get access too, plus I'm low on budget
 - Screws and nuts, which I almost certainly have lying around
 - Possibly Pololu's power switch for smart shutdown, but only if I have the money to spare

Already filled my cart on Amazon and Vilros and am ready to submit my order anytime

The software stack remains similar, but I realized that instead of decoding `.nbs` files in real time, I can take in `.mid`, `.midi` or `.nbs` files as input, then export both a `.nbs` file and a `.flac` file. The `.flac` will be used for audio playback, as it will run very lightweight on the Pi 5, then the `.nbs` file can be decoded into `.json` and used for the visualizer. The visualizer is a new idea, and is essentially this: The parser reads how many instruments are in the song about to be played, and adds one note block sprite for each instrument, with their respective block sprite underneath it. Then, synced to the audio, every time a note plays from an instrument, that note block will output a music note. In the real game the notes are colored based on what frequency is playing, and I think the best way to do that for such a wide range is to see the highest and lowest notes in the song, then use that to change the hue of the notes. The bigger the range is, the smaller the difference in color between notes will be. I also plan to have a touchscreen and camera now, so touchscreen inputs are definitely going to happen, and I might incorporate some kind of camera controls with custom gestures. Still don't know exactly how I'll use all the features, but I will definitely try to use everything as much as possible. The next step will be submitting this project (still haven't done it) and beginning software testing on a VM.

**Total time spent: 9 hours**
