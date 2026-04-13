import * as cdk from 'aws-cdk-lib';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import { Construct } from 'constructs';

interface LabelStudioFoundationStackProps extends cdk.StackProps {
  repositoryName: string;
}

export class LabelStudioFoundationStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: LabelStudioFoundationStackProps) {
    super(scope, id, props);

    new ecr.Repository(this, 'ECRRepository', {
      repositoryName: props.repositoryName,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      imageTagMutability: ecr.TagMutability.MUTABLE,
      imageScanOnPush: true,
      lifecycleRules: [
        {
          description: 'Keep last 5 images',
          tagStatus: ecr.TagStatus.ANY,
          maxImageCount: 5,
        },
        {
          description: 'Remove untagged images after 7 days',
          tagStatus: ecr.TagStatus.UNTAGGED,
          maxImageAge: cdk.Duration.days(7),
        },
      ],
    });
  }
}
