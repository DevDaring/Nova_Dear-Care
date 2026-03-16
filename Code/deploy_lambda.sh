#!/bin/bash
# deploy_lambda.sh - Deploy Dear-Care Lambda function via CLI
# Usage: bash deploy_lambda.sh
set -e

FUNCTION_NAME="pocket-asha-clinical-notes"  # Already deployed with this name on AWS — do not change
REGION="us-east-1"
ACCOUNT_ID="${AWS_ACCOUNT_ID:-your_account_id}"
S3_BUCKET="${S3_BUCKET_NAME:-dear-care-data-${ACCOUNT_ID}}"
ROLE_NAME="pocket-asha-lambda-role"
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
RUNTIME="python3.10"
HANDLER="handler.handler"
TIMEOUT=60
MEMORY=256
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LAMBDA_DIR="${SCRIPT_DIR}/lambda"

echo "============================================"
echo "  Deploying Dear-Care Lambda Function"
echo "============================================"

# 1. Create IAM role if it doesn't exist
echo "[1/5] Checking IAM role..."
if ! aws iam get-role --role-name "$ROLE_NAME" --region "$REGION" 2>/dev/null; then
    echo "  Creating IAM role: $ROLE_NAME"
    cat > /tmp/trust-policy.json << 'TRUST'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}
TRUST
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file:///tmp/trust-policy.json \
        --region "$REGION"

    # Attach policies
    aws iam attach-role-policy --role-name "$ROLE_NAME" \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    aws iam attach-role-policy --role-name "$ROLE_NAME" \
        --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
    aws iam attach-role-policy --role-name "$ROLE_NAME" \
        --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

    echo "  Waiting for role propagation..."
    sleep 10
else
    echo "  Role exists: $ROLE_NAME"
fi

ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text --region "$REGION")
echo "  Role ARN: $ROLE_ARN"

# 2. Package Lambda code
echo "[2/5] Packaging Lambda function..."
cd "$LAMBDA_DIR"
zip -j /tmp/pocket-asha-lambda.zip handler.py
echo "  Package size: $(du -h /tmp/pocket-asha-lambda.zip | cut -f1)"

# 3. Create or update Lambda function
echo "[3/5] Deploying Lambda function..."
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" 2>/dev/null; then
    echo "  Updating existing function..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file fileb:///tmp/pocket-asha-lambda.zip \
        --region "$REGION"
    # Update config
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --timeout "$TIMEOUT" \
        --memory-size "$MEMORY" \
        --environment "Variables={S3_BUCKET_NAME=$S3_BUCKET,AWS_REGION_NAME=$REGION,BEDROCK_MODEL_ID=amazon.nova-lite-v1:0}" \
        --region "$REGION"
else
    echo "  Creating new function..."
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --role "$ROLE_ARN" \
        --handler "$HANDLER" \
        --zip-file fileb:///tmp/pocket-asha-lambda.zip \
        --timeout "$TIMEOUT" \
        --memory-size "$MEMORY" \
        --environment "Variables={S3_BUCKET_NAME=$S3_BUCKET,AWS_REGION_NAME=$REGION,BEDROCK_MODEL_ID=amazon.nova-lite-v1:0}" \
        --region "$REGION"
fi

# 4. Wait for function to be active
echo "[4/5] Waiting for function to be active..."
aws lambda wait function-active-v2 --function-name "$FUNCTION_NAME" --region "$REGION" 2>/dev/null || sleep 5
echo "  Function is active"

# 5. Test invocation
echo "[5/5] Testing Lambda function..."
aws lambda invoke \
    --function-name "$FUNCTION_NAME" \
    --payload '{"encounter_id": "test", "action": "generate_notes"}' \
    --region "$REGION" \
    /tmp/lambda-test-response.json

echo "  Test response:"
cat /tmp/lambda-test-response.json
echo ""

# Cleanup
rm -f /tmp/trust-policy.json /tmp/pocket-asha-lambda.zip /tmp/lambda-test-response.json

echo ""
echo "============================================"
echo "  Lambda deployment complete!"
echo "  Function: $FUNCTION_NAME"
echo "  Region:   $REGION"
echo "============================================"
