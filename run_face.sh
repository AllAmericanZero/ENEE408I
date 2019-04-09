#!/bin/bash

python3 extract_embeddings.py --dataset dataset \
    --embeddings output/embeddings.pickle \
    --detector face_detection_model \
    --embedding-model openface_nn4.small2.v1.t7

python3 train_model.py --embeddings output/embeddings.pickle \
    --recognizer output/recognizer.pickle \
    --le output/le.pickle

python3 follow_face.py --detector face_detection_model \
    --embedding-model openface_nn4.small2.v1.t7 \
    --recognizer output/recognizer.pickle \
    --le output/le.pickle
