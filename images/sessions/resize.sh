#!/bin/bash
for filename in *.jpg; do
    convert "$filename" -resize 1200 "$filename"
    convert "$filename" -resize 400 "thumbnail/$filename"
done
