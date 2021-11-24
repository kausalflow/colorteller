---
title: "{{ replace .Name "-" " " | title }}"
summary: ""
colors:
  - name: "" # optional
    hex: "" # hex code of the color, this is required.
images: # Create a folder in /static/images/colors that has the same name as this current markdown file and place the images there. We only need the file name here. If this is not clear, please refer to existing colors as references.
  # - path:
tags:
  - ""
hex: # a list of all the hex colors in this palette
  - ""
links:
  - name: ""
    link: ""
author:    # the person who submitted this tool to KausalFlow
date: {{ .Date }}
draft: false
---