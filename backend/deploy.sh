#!/bin/bash
set -e

case $1 in
    DEV)

        # Set REGION as a variable to be used later
        REGION=ap-southeast-2
        distributionId=E38KAJ75OO2YOS
        BUCKET=dbla-dev-region-compare-bucket-ih3w7k03cczz
        DATABUCKET=dbla-dev-region-compare-databucket-mfcj8vxqwejm
        ENV=dev
        ;;
    PROD)
        # Set REGION as a variable to be used later
        REGION=ap-southeast-2
        distributionId=E35MMVKBQJ74VK
        BUCKET=dbla-prod-region-compare-bucket-yaeuqbsgosze
        DATABUCKET=dbla-prod-region-compare-databucket-hszgancek39k
        ENV=default
        ;;
esac

case $2 in
    ALL)
        # Build and deploy the stack
        sam build && sam deploy --config-env $ENV

        # Copy frontend to S3 bucket
        aws s3 cp --recursive ../frontend/ s3://$BUCKET/ --exclude 'data/*'
        aws s3 cp --recursive ../frontend/data/ s3://$DATABUCKET/data/
        
        # Invalidate CloudFront cache
        aws cloudfront create-invalidation --distribution-id $distributionId --paths "/*.*" --region $REGION
        ;;
    FRONTEND)
        # Copy frontend to S3 bucket
        aws s3 cp --recursive ../frontend/ s3://$BUCKET/ --exclude 'data/*'
        aws s3 cp --recursive ../frontend/data/ s3://$DATABUCKET/data/

        # Invalidate CloudFront cache
        aws cloudfront create-invalidation --distribution-id $distributionId --paths "/*.*" --region $REGION
        ;;
    BACKEND)
        # Build and deploy the stack
        sam build && sam deploy --config-env elasticstream
        ;;
    *)
        echo "Invalid command"
        exit 1
esac