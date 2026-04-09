# Label Studio — AWS CDK Deploy

Infraestructura AWS para Label Studio usando CDK (TypeScript).

## Estructura del proyecto

```
aws/
├── bin/
│   └── app.ts                  # Entry point CDK — instancia los stacks
├── lib/
│   ├── foundation-stack.ts     # Stack ECR (repositorio de imágenes)
│   └── ecs-service-stack.ts    # Stack ECS (servicio, EFS, SSM)
├── scripts/
│   └── setup-ssm.ts            # Sube parámetros a SSM Parameter Store
├── .env                        # Variables locales (no commitear)
├── .env.example                # Plantilla de variables
├── buildAndPushImage.sh        # Build y push de imagen Docker a ECR
├── cdk.json
└── package.json
```

## Stacks

- **`label-studio-ecr-stack`** — Repositorio ECR para las imágenes Docker.
- **`label-studio-{env}`** — Servicio ECS con ALB, EFS y variables desde SSM.

## Requisitos previos

- [Node.js](https://nodejs.org/) >= 22
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) configurado (`aws configure`)
- [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html): `npm install -g aws-cdk`
- Docker (para construir y subir imágenes)

## Configuración

Copia el archivo de ejemplo y completa los valores:

```bash
cp .env.example .env
```

Variables requeridas en `.env`:

| Variable                       | Descripción                                           |
|--------------------------------|-------------------------------------------------------|
| `APP_ENV`                      | Ambiente: `development`, `staging` o `production`     |
| `ALB_ARN`                      | ARN del Application Load Balancer existente           |
| `ALB_DNS`                      | DNS del ALB                                           |
| `ALB_SG_ID`                    | ID del Security Group del ALB                         |
| `ALB_CANONICAL_HOSTED_ZONE_ID` | Hosted Zone ID canónico del ALB                       |
| `LISTENER_ARN`                 | ARN del listener HTTPS del ALB                        |
| `CLUSTER_NAME`                 | Nombre del cluster ECS                                |
| `REPOSITORY_NAME`              | Nombre del repositorio ECR (ej. `org/app`)            |
| `DOMAIN_NAME`                  | Dominio del servicio (ej. `app.example.com`)          |
| `EFS_FILE_SYSTEM_ID`           | ID del sistema de archivos EFS                        |
| `EFS_SG_ID`                    | ID del Security Group del EFS                         |
| `DB_HOST`                      | Host del servidor PostgreSQL (solo para `prod:setup-ssm`)  |
| `DB_USER`                      | Usuario de la base de datos (solo para `prod:setup-ssm`)   |
| `DB_NAME`                      | Nombre de la base de datos (solo para `prod:setup-ssm`)    |
| `DB_PORT`                      | Puerto PostgreSQL, default `5432` (solo para `prod:setup-ssm`) |
| `DB_PASSWORD`                  | Contraseña DB — se sube como SecureString (solo para `prod:setup-ssm`) |
| `LABEL_STUDIO_USERNAME`        | Email del admin (solo para `prod:setup-ssm`)               |
| `LABEL_STUDIO_PASSWORD`        | Contraseña del admin — se sube como SecureString (solo para `prod:setup-ssm`) |

## Instalación de dependencias

```bash
npm ci
```

## Subir parámetros a SSM

Antes del primer deploy, sube los parámetros a SSM:

```bash
npm run prod:setup-ssm
```

Esto sube todos los parámetros de DB y Label Studio a SSM bajo `/label-studio/{APP_ENV}/`:

| Parámetro SSM            | Tipo           |
|--------------------------|----------------|
| `DB_HOST`                | String         |
| `DB_USER`                | String         |
| `DB_NAME`                | String         |
| `DB_PORT`                | String         |
| `DB_PASSWORD`            | SecureString   |
| `LABEL_STUDIO_USERNAME`  | String         |
| `LABEL_STUDIO_PASSWORD`  | SecureString   |

El contenedor recibe estos valores como secrets en runtime — no aparecen en CloudFormation.

## Versión de la imagen

El tag de la imagen ECR se construye automáticamente como `v{version}` desde el campo `version` en `package.json`. Para deployar una nueva versión, actualiza ese campo antes de deployar:

```json
{ "version": "1.2.0" }
```

El stack usará `v1.2.0` como tag al hacer deploy.

## Construir y subir imagen Docker

El script `buildAndPushImage.sh` construye la imagen y la sube a ECR.
La versión se toma del campo `version` en `package.json`, a menos que se pase como argumento.

```bash
./buildAndPushImage.sh          # usa versión de package.json
./buildAndPushImage.sh 2.1.0    # versión manual
```

## Despliegue

```bash
npm run prod:deploy
```

Para deployar un stack específico:

```bash
npx cdk deploy label-studio-ecr-stack          # solo ECR
npx cdk deploy label-studio-production         # solo ECS
```

## Destruir los stacks

> **Importante:** el certificado ACM no se elimina en el primer intento debido a que
> CloudFormation no puede eliminarlo mientras el listener del ALB aún lo referencia.
> Es necesario ejecutar el destroy **dos veces**:

```bash
npx cdk destroy --all   # primer intento — puede fallar en el certificado
npx cdk destroy --all   # segundo intento — elimina el certificado y el resto
```
