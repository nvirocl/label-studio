# Label Studio — AWS CDK Deploy

Infraestructura AWS para Label Studio usando CDK (TypeScript). Incluye dos stacks:

- **`label-studio-ecr-stack`** — Repositorio ECR para las imágenes Docker.
- **`label-studio-ecs-stack`** — Servicio ECS en un ALB existente.

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

| Variable                     | Descripción                                      |
|------------------------------|--------------------------------------------------|
| `ALB_ARN`                    | ARN del Application Load Balancer existente      |
| `ALB_DNS`                    | DNS del ALB                                      |
| `ALB_SG_ID`                  | ID del Security Group del ALB                    |
| `ALB_CANONICAL_HOSTED_ZONE_ID` | Hosted Zone ID canónico del ALB               |
| `LISTENER_ARN`               | ARN del listener HTTPS del ALB                   |
| `CLUSTER_NAME`               | Nombre del cluster ECS                           |
| `REPOSITORY_NAME`            | Nombre del repositorio ECR (ej. `org/app`)       |
| `DOMAIN_NAMES`               | Dominios separados por coma (ej. `app.example.com`) |

## Instalación de dependencias

```bash
npm ci
```

## Despliegue

### Todos los stacks

```bash
npx cdk deploy --all
```

### Solo el repositorio ECR

```bash
npx cdk deploy label-studio-ecr-stack
```

### Solo el servicio ECS

> Requiere que el stack ECR ya esté desplegado.

```bash
npx cdk deploy label-studio-ecs-stack
```

## Construir y subir imagen Docker

El script `buildAndPushImage.sh` construye la imagen y la sube a ECR.
La versión de la imagen se toma del campo `version` en `package.json`, a menos que se pase como argumento.

### Usando la versión de `package.json`

```bash
./buildAndPushImage.sh
```

### Especificando una versión manualmente

```bash
./buildAndPushImage.sh 2.1.0
```

La imagen se taguea como `v<version>` y se sube al repositorio ECR configurado en `REPOSITORY_NAME`.

## Destruir los stacks

```bash
npx cdk destroy --all
```
