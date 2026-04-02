import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import { Construct } from 'constructs';
import { config } from '@dotenvx/dotenvx';

import { EcsService } from '@nvirocl/infra-cdk';

config();

const albArn = process.env.ALB_ARN!;
const albDns = process.env.ALB_DNS!;
const albSgId = process.env.ALB_SG_ID!;
const albCanonicalHostedZoneId = process.env.ALB_CANONICAL_HOSTED_ZONE_ID!;
const listenerArn = process.env.LISTENER_ARN!;
const clusterName = process.env.CLUSTER_NAME!;


const repositoryName = process.env.REPOSITORY_NAME!;
const domainNames = process.env.DOMAIN_NAMES?.split(',') ?? [];

class LabelStudioFoundationStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    new ecr.Repository(this, 'ECRRepository', {
      repositoryName: repositoryName,
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

class LabelStudioEcsServiceStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const vpc = ec2.Vpc.fromLookup(this, 'nviro-vpc', { isDefault: true });

    const cluster = ecs.Cluster.fromClusterAttributes(this, 'Cluster', {
      clusterName,
      vpc,
    });

    const albSg = ec2.SecurityGroup.fromSecurityGroupId(this, 'AlbSg', albSgId);

    const alb = elbv2.ApplicationLoadBalancer.fromApplicationLoadBalancerAttributes(
      this, 'Alb', {
        loadBalancerArn: albArn,
        securityGroupId: albSg.securityGroupId,
        loadBalancerDnsName: albDns,
        loadBalancerCanonicalHostedZoneId: albCanonicalHostedZoneId,
      },
    );

    const httpsListener = elbv2.ApplicationListener.fromApplicationListenerAttributes(
      this, 'HttpsListener', {
        listenerArn,
        securityGroup: albSg,
      },
    );

    // Image: nginx from AWS Public ECR — serves a simple welcome page on port 80
    const service = new EcsService(this, 'LabelStudioService', {
      name: 'label-studio',
      containerPort: 80,
      cpu: 256,
      memory: 512,
      launchType: ecs.LaunchType.EC2,
      ecrRepositoryName: repositoryName,
      ecrImageTag: 'latest',
      cluster,
      httpsListener,
      alb,
      domainNames,
      listenerRulePriority: 100,
      healthCheckPath: '/',
      healthyHttpCodes: '200',
    });
  }
}

const app = new cdk.App();

const foundationStack = new LabelStudioFoundationStack(app, 'label-studio-ecr-stack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION ?? 'us-west-2',
  },
});

const appStack = new LabelStudioEcsServiceStack(app, 'label-studio-ecs-stack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION ?? 'us-west-2',
  },
});

appStack.addDependency(foundationStack);
