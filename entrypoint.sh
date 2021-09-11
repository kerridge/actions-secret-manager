#!/bin/bash

# Environment variables are set from input passed to Github Actions
python ./main.py \
    --secret-name "${NAME}" \
    --secret-value "${VALUE}" \
    --action "${ACTION}" \
    --token "${TOKEN}" \
    --repository "${REPOSITORY}" \
    --file $FILE

# python ./main.py \
#     --secret-name "GH_SSH_PRIVATE_KEY" \
#     --secret-value "YOOO" \
#     --action "create" \
#     --token "" \
#     --repository "django-s3-stack"
    # --secret-file "test.txt" \


    # -e INPUT_ACTION -e INPUT_TOKEN -e INPUT_NAME -e INPUT_VALUE -e INPUT_REPOSITORY -e INPUT_FILE -e ACTION -e TOKEN -e NAME -e VALUE -e FILE -e REPOSITORY -e HOME -e GITHUB_JOB -e GITHUB_REF -e GITHUB_SHA -e GITHUB_REPOSITORY -e GITHUB_REPOSITORY_OWNER -e GITHUB_RUN_ID -e GITHUB_RUN_NUMBER -e GITHUB_RETENTION_DAYS -e GITHUB_ACTOR -e GITHUB_WORKFLOW -e GITHUB_HEAD_REF -e GITHUB_BASE_REF -e GITHUB_EVENT_NAME -e GITHUB_SERVER_URL -e GITHUB_API_URL -e GITHUB_GRAPHQL_URL -e GITHUB_WORKSPACE -e GITHUB_ACTION -e GITHUB_EVENT_PATH -e GITHUB_ACTION_REPOSITORY -e GITHUB_ACTION_REF -e GITHUB_PATH -e GITHUB_ENV -e RUNNER_OS -e RUNNER_TOOL_CACHE -e RUNNER_TEMP -e RUNNER_WORKSPACE -e ACTIONS_RUNTIME_URL -e ACTIONS_RUNTIME_TOKEN -e ACTIONS_CACHE_URL -e GITHUB_ACTIONS=true