#!/bin/bash
for filename in *.jpg; do
    convert "$filename" -resize "400x>" "$filename"
done
