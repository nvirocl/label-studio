import { config } from '@dotenvx/dotenvx';
import ssm from '@nvirocl/js-utils/aws/ssm';

config();

const appEnv = process.env.APP_ENV!;
const region = process.env.CDK_DEFAULT_REGION ?? 'us-west-2';

if (!appEnv) throw new Error('APP_ENV is required');

const ssmPath = `/label-studio/${appEnv}`;

const required = {
  DB_HOST: process.env.DB_HOST,
  DB_USER: process.env.DB_USER,
  DB_NAME: process.env.DB_NAME,
  DB_PORT: process.env.DB_PORT,
  DB_PASSWORD: process.env.DB_PASSWORD,
  LABEL_STUDIO_USERNAME: process.env.LABEL_STUDIO_USERNAME,
  LABEL_STUDIO_PASSWORD: process.env.LABEL_STUDIO_PASSWORD,
};

for (const [key, value] of Object.entries(required)) {
  if (!value) throw new Error(`${key} is required`);
}

ssm.setConfig({ region });

(async () => {
  try {
    // String parameters (non-secure)
    await ssm.putParameter(`${ssmPath}/DB_HOST`, required.DB_HOST!, { overwrite: true });
    await ssm.putParameter(`${ssmPath}/DB_USER`, required.DB_USER!, { overwrite: true });
    await ssm.putParameter(`${ssmPath}/DB_NAME`, required.DB_NAME!, { overwrite: true });
    await ssm.putParameter(`${ssmPath}/DB_PORT`, required.DB_PORT!, { overwrite: true });
    await ssm.putParameter(`${ssmPath}/LABEL_STUDIO_USERNAME`, required.LABEL_STUDIO_USERNAME!, { overwrite: true });

    // SecureString parameters
    await ssm.putParameter(`${ssmPath}/DB_PASSWORD`, required.DB_PASSWORD!, { type: 'SecureString', overwrite: true });
    await ssm.putParameter(`${ssmPath}/LABEL_STUDIO_PASSWORD`, required.LABEL_STUDIO_PASSWORD!, { type: 'SecureString', overwrite: true });

    console.log(`✓ All parameters stored in SSM under ${ssmPath}`);
  } catch (err) {
    console.error('Error setting up SSM parameters:', err);
    process.exit(1);
  }
})();
