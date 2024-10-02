#!/bin/bash
set -e

if [[ -d "infra" ]]; then
    cd infra

    echo "Install AWS CDK version ${CDK_VERSION}.."

    npm i -g aws-cdk@${CDK_VERSION}
    npm ci --include=dev

    cdk bootstrap aws://${AWS_ACCOUNT_ID}/${AWS_REGION} --force


    echo "Synthesize infra.."

    npm run cdk synth -- \
        --quiet \
        --context name= "booker" \
        --context accountId=${AWS_ACCOUNT_ID} \
        --context region=${AWS_REGION} \
        --context apiKey= "no" \
        --context applicationTag= "double no"
fi