---
title: Decisions WaterSheep
emoji: 🐑
colorFrom: gray
colorTo: green
sdk: gradio
sdk_version: 6.31.0
python_version: "3.12.12"
app_file: app.py
pinned: false
license: apache-2.0
suggested_hardware: zero-a10g
short_description: Private Jev-style decisions, small backup model
---

Private backup decision service for the owner's APCCS and UCLRCDE projects. It
runs [WaterSheep](https://github.com/SamratDuttaOfficial/WaterSheep) by Samrat
Dutta (Apache-2.0; fine-tuned from ModernBERT-base by Answer.AI and LightOn)
behind one call, `systemone`, that takes and returns Jev System One JSON. By
default it runs on the processor, so it uses none of the daily graphics-card time.

Made-up or project text only. Never real case files.

Deployed from the APCCS repository (`deploy/hf_spaces/`). Edit it there, not here.
