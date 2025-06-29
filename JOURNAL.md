---
title: "Note Block Maestro"
author: "Luke Collingridge"
description: "A physical note block that plays MIDI files as note block audio, and can also convert them to schematic or data pack form for use in-game."
created_at: "2025-06-28"
---

# June 28th: Planning

Today was spent planning out the project just to make sure it's technically feasible, as well as doing some basic setup and preparation. As for hardware, this is what I've come up with so far:
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
