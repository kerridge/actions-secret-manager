#!/bin/bash

# Environment variables are set from input passed to Github Actions
python ./main.py \
    --secret-name "GH_SSH_PRIVATE_KEY" \
    --secret-value "YOOO" \
    --action "create" \
    --token "" \
    --repository "django-s3-stack"
    # --secret-file "test.txt" \