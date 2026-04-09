import * as cdk from 'aws-cdk-lib';
import { config } from '@dotenvx/dotenvx';

import { LabelStudioFoundationStack } from '#lib/foundation-stack';
import { LabelStudioEcsServiceStack } from '#lib/ecs-service-stack';
import { version } from '../package.json';

config();

const appEnv = process.env.APP_ENV!;
const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION ?? 'us-west-2',
};

const app = new cdk.App();

const foundationStack = new LabelStudioFoundationStack(app, 'label-studio-ecr-stack', {
  env,
  repositoryName: process.env.REPOSITORY_NAME!,
});

const appStack = new LabelStudioEcsServiceStack(app, `label-studio-${appEnv}`, {
  env,
  appEnv,
  albArn: process.env.ALB_ARN!,
  albDns: process.env.ALB_DNS!,
  albSgId: process.env.ALB_SG_ID!,
  albCanonicalHostedZoneId: process.env.ALB_CANONICAL_HOSTED_ZONE_ID!,
  listenerArn: process.env.LISTENER_ARN!,
  clusterName: process.env.CLUSTER_NAME!,
  repositoryName: process.env.REPOSITORY_NAME!,
  imageTag: `v${version}`,
  domainName: process.env.DOMAIN_NAME!,
  efsSgId: process.env.EFS_SG_ID!,
  efsFileSystemId: process.env.EFS_FILE_SYSTEM_ID!,
});

appStack.addDependency(foundationStack);
