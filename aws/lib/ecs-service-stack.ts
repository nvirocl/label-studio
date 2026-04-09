import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as efs from 'aws-cdk-lib/aws-efs';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { Construct } from 'constructs';

import { EcsService } from '@nvirocl/infra-cdk';

interface LabelStudioEcsServiceStackProps extends cdk.StackProps {
  appEnv: string;
  imageTag: string;
  domainName: string;
  albArn: string;
  albDns: string;
  albSgId: string;
  albCanonicalHostedZoneId: string;
  listenerArn: string;
  clusterName: string;
  repositoryName: string;
  efsSgId: string;
  efsFileSystemId: string;
}

export class LabelStudioEcsServiceStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: LabelStudioEcsServiceStackProps) {
    super(scope, id, props);

    const {
      appEnv,
      imageTag,
      domainName,
      albArn, albDns, albSgId, albCanonicalHostedZoneId,
      listenerArn,
      clusterName,
      repositoryName,
      efsSgId,
      efsFileSystemId,
    } = props;

    const ssmPath = `/label-studio/${appEnv}`;

    const vpc = ec2.Vpc.fromLookup(this, 'nviro-vpc', { isDefault: true });

    const cluster = ecs.Cluster.fromClusterAttributes(this, 'Cluster', { clusterName, vpc });

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

    const efsSg = ec2.SecurityGroup.fromSecurityGroupId(this, 'EfsSg', efsSgId);
    const fileSystem = efs.FileSystem.fromFileSystemAttributes(this, 'EfsFileSystem', {
      fileSystemId: efsFileSystemId,
      securityGroup: efsSg,
    });
    const accessPoint = new efs.AccessPoint(this, 'LabelStudioDataAccessPoint', {
      fileSystem,
      path: `/label-studio/${appEnv}/data`,
      createAcl: {
        ownerUid: '1001',
        ownerGid: '0',
        permissions: '775',
      },
      posixUser: {
        uid: '1001',
        gid: '0',
      },
    });

    // SSM String (non-secure)
    const dbHostParam = ssm.StringParameter.fromStringParameterName(this, 'DbHost', `${ssmPath}/DB_HOST`);
    const dbUserParam = ssm.StringParameter.fromStringParameterName(this, 'DbUser', `${ssmPath}/DB_USER`);
    const dbNameParam = ssm.StringParameter.fromStringParameterName(this, 'DbName', `${ssmPath}/DB_NAME`);
    const dbPortParam = ssm.StringParameter.fromStringParameterName(this, 'DbPort', `${ssmPath}/DB_PORT`);
    const lsUsernameParam = ssm.StringParameter.fromStringParameterName(this, 'LsUsername', `${ssmPath}/LABEL_STUDIO_USERNAME`);

    // SSM SecureString
    const dbPasswordParam = ssm.StringParameter.fromSecureStringParameterAttributes(this, 'DbPassword', { parameterName: `${ssmPath}/DB_PASSWORD` });
    const lsPasswordParam = ssm.StringParameter.fromSecureStringParameterAttributes(this, 'LsPassword', { parameterName: `${ssmPath}/LABEL_STUDIO_PASSWORD` });

    new EcsService(this, 'LabelStudioService', {
      name: 'label-studio',
      containerPort: 8080,
      cpu: 256,
      memory: 512,
      launchType: ecs.LaunchType.EC2,
      ecrRepositoryName: repositoryName,
      ecrImageTag: imageTag,
      cluster,
      httpsListener,
      alb,
      domainNames: [domainName],
      listenerRulePriority: 100,
      healthCheckPath: '/health',
      healthyHttpCodes: '200',
      checkHealthWithCurl: true,
      environment: {
        NODE_ENV: 'production',
        APP_ENV: appEnv,
        DJANGO_DB: 'default',
        LABEL_STUDIO_DATA_DIR: '/label-studio/data',
        LABEL_STUDIO_DISABLE_SIGNUP_WITHOUT_LINK: 'true',
        DEBUG: 'false',
        LABEL_STUDIO_HOST: `https://${domainName}`,
        DJANGO_ALLOWED_HOSTS: domainName,
        CSRF_TRUSTED_ORIGINS: `https://${domainName}`,
      },
      secrets: {
        POSTGRE_HOST: ecs.Secret.fromSsmParameter(dbHostParam),
        POSTGRE_USER: ecs.Secret.fromSsmParameter(dbUserParam),
        POSTGRE_NAME: ecs.Secret.fromSsmParameter(dbNameParam),
        POSTGRE_PORT: ecs.Secret.fromSsmParameter(dbPortParam),
        POSTGRE_PASSWORD: ecs.Secret.fromSsmParameter(dbPasswordParam),
        LABEL_STUDIO_USERNAME: ecs.Secret.fromSsmParameter(lsUsernameParam),
        LABEL_STUDIO_PASSWORD: ecs.Secret.fromSsmParameter(lsPasswordParam),
      },
      efsVolumes: [
        {
          volumeName: 'label-studio-data',
          fileSystemId: efsFileSystemId,
          containerPath: '/label-studio/data',
          accessPointId: accessPoint.accessPointId,
        },
      ],
    });
  }
}
