"""
FashionCLIP Isolated Pipeline — ml-engine/fashionclip/

This package is completely isolated from the ResNet50 pipeline.
ResNet50 remains live in the backend. FashionCLIP runs in parallel
for evaluation. Swap trigger: one import change in search.py.
"""
