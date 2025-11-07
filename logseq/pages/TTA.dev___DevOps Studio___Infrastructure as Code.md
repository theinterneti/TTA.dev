# TTA.dev Infrastructure as Code Guide

component-type:: infrastructure
tech-stack:: terraform, ansible, kubernetes, docker
stage:: production
complexity:: advanced
related:: [[TTA.dev/DevOps Studio Architecture]], [[TTA.dev/CI-CD Pipeline]]

Complete Infrastructure as Code implementation for TTA.dev production environments

---

## 🏗️ IaC Overview

Infrastructure as Code (IaC) enables **versioned, repeatable, and automated** infrastructure management for TTA.dev applications. This guide covers complete production-ready infrastructure patterns.

### Core Principles

- **Everything as Code** - All infrastructure defined in version-controlled files
- **Immutable Infrastructure** - Replace rather than modify infrastructure
- **Automated Deployment** - Fully automated provisioning and updates
- **Environment Parity** - Consistent infrastructure across all environments
- **Disaster Recovery** - Built-in backup and recovery capabilities

### Technology Stack

- **Terraform** - Infrastructure provisioning and state management
- **Ansible** - Configuration management and application deployment
- **Kubernetes** - Container orchestration and workload management
- **Helm** - Kubernetes package management and templating
- **GitOps** - Git-driven infrastructure and application deployment

---

## 🧱 Infrastructure Architecture

### Multi-Tier Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    Production Environment                    │
├─────────────────────────────────────────────────────────────┤
│  Load Balancer Layer                                        │
│  ├─ Application Load Balancer (ALB)                         │
│  ├─ SSL/TLS Termination                                     │
│  └─ Web Application Firewall (WAF)                         │
├─────────────────────────────────────────────────────────────┤
│  Kubernetes Cluster Layer                                   │
│  ├─ Control Plane (Managed)                                │
│  ├─ Worker Nodes (Auto-scaling)                            │
│  ├─ Pod Security Policies                                  │
│  └─ Network Policies                                       │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                 │
│  ├─ Managed Databases (RDS, ElastiCache)                   │
│  ├─ Object Storage (S3, MinIO)                            │
│  ├─ Message Queues (SQS, Redis)                           │
│  └─ Search Engines (OpenSearch, Elasticsearch)             │
├─────────────────────────────────────────────────────────────┤
│  Observability Layer                                        │
│  ├─ Prometheus + Grafana                                   │
│  ├─ Jaeger Tracing                                         │
│  ├─ Loki Logging                                           │
│  └─ AlertManager                                           │
├─────────────────────────────────────────────────────────────┤
│  Security Layer                                             │
│  ├─ VPC with Private Subnets                              │
│  ├─ Security Groups and NACLs                             │
│  ├─ Secrets Management (Vault, AWS Secrets)               │
│  └─ Identity and Access Management                        │
└─────────────────────────────────────────────────────────────┘
```

### Environment Strategy

**Multi-Environment Deployment:**

- **Development** - Single-node cluster for feature development
- **Testing** - Multi-node cluster for integration testing
- **Staging** - Production-like environment for final validation
- **Production** - High-availability multi-region deployment

---

## 🛠️ Terraform Infrastructure

### Project Structure

```text
infrastructure/
├── environments/
│   ├── dev/
│   │   ├── main.tf                 # Development environment
│   │   ├── variables.tf            # Environment-specific variables
│   │   └── terraform.tfvars        # Variable values
│   ├── staging/
│   │   ├── main.tf                 # Staging environment
│   │   ├── variables.tf            # Environment-specific variables
│   │   └── terraform.tfvars        # Variable values
│   └── prod/
│       ├── main.tf                 # Production environment
│       ├── variables.tf            # Environment-specific variables
│       └── terraform.tfvars        # Variable values
├── modules/
│   ├── kubernetes-cluster/         # EKS/GKE cluster module
│   ├── database/                   # Database module
│   ├── networking/                 # VPC and networking
│   ├── observability/              # Monitoring infrastructure
│   └── security/                   # Security components
├── shared/
│   ├── backend.tf                  # Terraform backend configuration
│   ├── providers.tf                # Provider configurations
│   └── variables.tf                # Shared variables
└── scripts/
    ├── deploy.sh                   # Deployment automation
    ├── destroy.sh                  # Infrastructure cleanup
    └── validate.sh                 # Configuration validation
```

### Core Infrastructure Modules

#### Kubernetes Cluster Module

```hcl
# modules/kubernetes-cluster/main.tf
module "eks_cluster" {
  source = "terraform-aws-modules/eks/aws"

  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version

  vpc_id     = var.vpc_id
  subnet_ids = var.private_subnet_ids

  # Node groups configuration
  eks_managed_node_groups = {
    main = {
      min_size       = var.min_nodes
      max_size       = var.max_nodes
      desired_size   = var.desired_nodes
      instance_types = var.instance_types

      k8s_labels = {
        Environment = var.environment
        Application = "tta-dev"
      }

      tags = var.common_tags
    }
  }

  # Cluster security configuration
  cluster_endpoint_private_access = true
  cluster_endpoint_public_access  = true

  # Enable logging
  cluster_enabled_log_types = [
    "api", "audit", "authenticator", "controllerManager", "scheduler"
  ]

  tags = var.common_tags
}

# Configure OIDC provider for service accounts
data "tls_certificate" "cluster" {
  url = module.eks_cluster.cluster_oidc_issuer_url
}

resource "aws_iam_openid_connect_provider" "cluster" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.cluster.certificates[0].sha1_fingerprint]
  url             = module.eks_cluster.cluster_oidc_issuer_url

  tags = var.common_tags
}
```

#### Database Module

```hcl
# modules/database/main.tf
resource "aws_db_instance" "main" {
  identifier = "${var.environment}-tta-dev-db"

  # Engine configuration
  engine         = "postgres"
  engine_version = var.postgres_version
  instance_class = var.db_instance_class

  # Storage configuration
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type         = "gp3"
  storage_encrypted    = true

  # Database configuration
  db_name  = var.database_name
  username = var.database_username
  password = var.database_password

  # Network configuration
  db_subnet_group_name = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]

  # Backup configuration
  backup_retention_period = var.backup_retention_days
  backup_window          = var.backup_window
  maintenance_window     = var.maintenance_window

  # Monitoring
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn

  # Security
  deletion_protection = var.environment == "prod"
  skip_final_snapshot = var.environment != "prod"

  tags = merge(var.common_tags, {
    Name = "${var.environment}-tta-dev-database"
  })
}

# Redis cluster for caching
resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "${var.environment}-tta-dev-cache"
  description                = "TTA.dev Redis cluster"

  node_type                 = var.redis_node_type
  num_cache_clusters        = var.redis_num_nodes
  port                      = 6379
  parameter_group_name      = "default.redis7"

  subnet_group_name         = aws_elasticache_subnet_group.main.name
  security_group_ids        = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  tags = var.common_tags
}
```

#### Networking Module

```hcl
# modules/networking/main.tf
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.common_tags, {
    Name = "${var.environment}-tta-dev-vpc"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(var.common_tags, {
    Name = "${var.environment}-tta-dev-igw"
  })
}

# Public subnets for load balancers
resource "aws_subnet" "public" {
  count = length(var.availability_zones)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(var.common_tags, {
    Name = "${var.environment}-tta-dev-public-${count.index + 1}"
    Type = "public"
  })
}

# Private subnets for applications and databases
resource "aws_subnet" "private" {
  count = length(var.availability_zones)

  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(var.common_tags, {
    Name = "${var.environment}-tta-dev-private-${count.index + 1}"
    Type = "private"
  })
}

# NAT Gateways for outbound internet access
resource "aws_eip" "nat" {
  count  = length(var.availability_zones)
  domain = "vpc"

  tags = merge(var.common_tags, {
    Name = "${var.environment}-tta-dev-nat-eip-${count.index + 1}"
  })
}

resource "aws_nat_gateway" "main" {
  count = length(var.availability_zones)

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(var.common_tags, {
    Name = "${var.environment}-tta-dev-nat-${count.index + 1}"
  })

  depends_on = [aws_internet_gateway.main]
}
```

### Environment Configuration

#### Production Environment

```hcl
# environments/prod/main.tf
terraform {
  required_version = ">= 1.0"

  backend "s3" {
    bucket = "tta-dev-terraform-state-prod"
    key    = "infrastructure/prod/terraform.tfstate"
    region = "us-west-2"

    dynamodb_table = "tta-dev-terraform-locks"
    encrypt        = true
  }
}

# Providers
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "TTA.dev"
      Environment = "production"
      ManagedBy   = "terraform"
      Team        = "platform"
    }
  }
}

provider "kubernetes" {
  host                   = module.kubernetes_cluster.cluster_endpoint
  cluster_ca_certificate = base64decode(module.kubernetes_cluster.cluster_certificate_authority_data)
  token                  = data.aws_eks_cluster_auth.main.token
}

# Data sources
data "aws_eks_cluster_auth" "main" {
  name = module.kubernetes_cluster.cluster_name
}

# Core infrastructure modules
module "networking" {
  source = "../../modules/networking"

  environment        = "prod"
  vpc_cidr          = "10.0.0.0/16"
  availability_zones = ["us-west-2a", "us-west-2b", "us-west-2c"]

  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnet_cidrs = ["10.0.10.0/24", "10.0.20.0/24", "10.0.30.0/24"]

  common_tags = local.common_tags
}

module "kubernetes_cluster" {
  source = "../../modules/kubernetes-cluster"

  cluster_name       = "tta-dev-prod"
  kubernetes_version = "1.28"
  environment       = "prod"

  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids

  min_nodes      = 3
  max_nodes      = 10
  desired_nodes  = 5
  instance_types = ["m5.large", "m5.xlarge"]

  common_tags = local.common_tags
}

module "database" {
  source = "../../modules/database"

  environment = "prod"

  # PostgreSQL configuration
  postgres_version    = "15.4"
  db_instance_class   = "db.r6g.large"
  allocated_storage   = 100
  max_allocated_storage = 1000

  database_name     = "ttadev_prod"
  database_username = "ttadev"
  database_password = var.database_password

  backup_retention_days = 30
  backup_window        = "03:00-04:00"
  maintenance_window   = "sun:04:00-sun:05:00"

  # Redis configuration
  redis_node_type  = "cache.r6g.large"
  redis_num_nodes  = 3

  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids

  common_tags = local.common_tags
}

module "observability" {
  source = "../../modules/observability"

  environment    = "prod"
  cluster_name   = module.kubernetes_cluster.cluster_name

  prometheus_storage_size = "100Gi"
  grafana_storage_size   = "20Gi"
  loki_storage_size      = "200Gi"

  alert_webhook_url = var.slack_webhook_url

  common_tags = local.common_tags
}

# Local values
locals {
  common_tags = {
    Project     = "TTA.dev"
    Environment = "production"
    ManagedBy   = "terraform"
    Team        = "platform"
    CostCenter  = "engineering"
  }
}
```

---

## 🔧 Ansible Configuration Management

### Ansible Project Structure

```text
ansible/
├── inventories/
│   ├── dev/
│   │   ├── hosts.yml               # Development inventory
│   │   └── group_vars/
│   ├── staging/
│   │   ├── hosts.yml               # Staging inventory
│   │   └── group_vars/
│   └── prod/
│       ├── hosts.yml               # Production inventory
│       └── group_vars/
├── playbooks/
│   ├── site.yml                    # Main playbook
│   ├── kubernetes-setup.yml        # K8s cluster configuration
│   ├── observability-setup.yml     # Monitoring stack
│   └── application-deploy.yml      # Application deployment
├── roles/
│   ├── kubernetes/                 # Kubernetes configuration
│   ├── prometheus/                 # Prometheus setup
│   ├── grafana/                    # Grafana configuration
│   ├── loki/                       # Loki log aggregation
│   └── security/                   # Security hardening
├── group_vars/
│   ├── all.yml                     # Global variables
│   ├── kubernetes.yml              # K8s specific variables
│   └── observability.yml          # Monitoring variables
├── host_vars/                      # Host-specific variables
├── files/                          # Static files
├── templates/                      # Jinja2 templates
└── ansible.cfg                     # Ansible configuration
```

### Core Playbooks

#### Main Site Playbook

```yaml
# playbooks/site.yml
---
- name: Configure TTA.dev Infrastructure
  hosts: all
  become: yes
  gather_facts: yes

  pre_tasks:
    - name: Update system packages
      package:
        name: "*"
        state: latest
      when: ansible_os_family == "RedHat" or ansible_os_family == "Debian"

    - name: Install common tools
      package:
        name:
          - curl
          - wget
          - git
          - htop
          - vim
        state: present

- name: Configure Kubernetes Cluster
  import_playbook: kubernetes-setup.yml
  when: "'kubernetes' in group_names"

- name: Configure Observability Stack
  import_playbook: observability-setup.yml
  when: "'monitoring' in group_names"

- name: Deploy Applications
  import_playbook: application-deploy.yml
  when: "'applications' in group_names"
```

#### Kubernetes Setup Playbook

```yaml
# playbooks/kubernetes-setup.yml
---
- name: Configure Kubernetes Cluster
  hosts: kubernetes
  become: yes

  roles:
    - role: kubernetes
      vars:
        k8s_version: "{{ kubernetes_version }}"
        cluster_name: "{{ environment }}-tta-dev"

  tasks:
    - name: Install kubectl
      get_url:
        url: "https://dl.k8s.io/release/v{{ kubernetes_version }}/bin/linux/amd64/kubectl"
        dest: /usr/local/bin/kubectl
        mode: '0755'

    - name: Install Helm
      shell: |
        curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
      args:
        creates: /usr/local/bin/helm

    - name: Add Helm repositories
      kubernetes.core.helm_repository:
        name: "{{ item.name }}"
        repo_url: "{{ item.url }}"
      loop:
        - name: prometheus-community
          url: https://prometheus-community.github.io/helm-charts
        - name: grafana
          url: https://grafana.github.io/helm-charts
        - name: jaegertracing
          url: https://jaegertracing.github.io/helm-charts

    - name: Create namespaces
      kubernetes.core.k8s:
        name: "{{ item }}"
        api_version: v1
        kind: Namespace
        state: present
      loop:
        - tta-dev-apps
        - tta-dev-monitoring
        - tta-dev-system
```

### Application Deployment

#### Kubernetes Manifests

```yaml
# k8s/applications/tta-dev-api/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tta-dev-api
  namespace: tta-dev-apps
  labels:
    app: tta-dev-api
    version: "{{ app_version }}"
spec:
  replicas: {{ api_replicas | default(3) }}
  selector:
    matchLabels:
      app: tta-dev-api
  template:
    metadata:
      labels:
        app: tta-dev-api
        version: "{{ app_version }}"
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9464"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: api
        image: "{{ api_image }}:{{ app_version }}"
        ports:
        - containerPort: 8000
          name: http
        - containerPort: 9464
          name: metrics
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: url
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "http://jaeger-collector:14268/api/traces"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
      imagePullSecrets:
      - name: registry-credentials
```

---

## 📊 Observability Infrastructure

### Prometheus Configuration

```yaml
# k8s/monitoring/prometheus/values.yml
prometheus:
  prometheusSpec:
    retention: 30d
    storageSpec:
      volumeClaimTemplate:
        spec:
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 100Gi
          storageClassName: gp3

    additionalScrapeConfigs:
      - job_name: 'tta-dev-api'
        kubernetes_sd_configs:
          - role: pod
            namespaces:
              names:
                - tta-dev-apps
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
            action: keep
            regex: true
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
            action: replace
            target_label: __metrics_path__
            regex: (.+)

alertmanager:
  alertmanagerSpec:
    storage:
      volumeClaimTemplate:
        spec:
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 10Gi
          storageClassName: gp3

grafana:
  persistence:
    enabled: true
    size: 20Gi
    storageClassName: gp3

  adminPassword: "{{ grafana_admin_password }}"

  dashboardProviders:
    dashboardproviders.yaml:
      apiVersion: 1
      providers:
      - name: 'tta-dev-dashboards'
        orgId: 1
        folder: 'TTA.dev'
        type: file
        disableDeletion: false
        editable: true
        options:
          path: /var/lib/grafana/dashboards/tta-dev

  dashboards:
    tta-dev-dashboards:
      tta-dev-overview:
        gnetId: 15757
        revision: 1
        datasource: Prometheus
```

### Jaeger Tracing

```yaml
# k8s/monitoring/jaeger/values.yml
provisionDataStore:
  cassandra: false
  elasticsearch: true

elasticsearch:
  replicas: 3
  minimumMasterNodes: 2

  resources:
    requests:
      memory: "2Gi"
      cpu: "1000m"
    limits:
      memory: "4Gi"
      cpu: "2000m"

  volumeClaimTemplate:
    accessModes: ["ReadWriteOnce"]
    resources:
      requests:
        storage: 100Gi
    storageClassName: gp3

collector:
  replicaCount: 3
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"

query:
  replicaCount: 2
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"
```

---

## 🔐 Security Configuration

### Network Security

```hcl
# modules/security/network.tf
resource "aws_security_group" "kubernetes_nodes" {
  name_prefix = "${var.environment}-k8s-nodes-"
  vpc_id      = var.vpc_id

  # Allow all traffic within cluster
  ingress {
    from_port = 0
    to_port   = 65535
    protocol  = "tcp"
    self      = true
  }

  # Allow HTTPS from load balancer
  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.load_balancer.id]
  }

  # Allow SSH from bastion hosts
  ingress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.common_tags, {
    Name = "${var.environment}-k8s-nodes-sg"
  })
}

resource "aws_security_group" "database" {
  name_prefix = "${var.environment}-database-"
  vpc_id      = var.vpc_id

  # Allow PostgreSQL from Kubernetes nodes
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.kubernetes_nodes.id]
  }

  tags = merge(var.common_tags, {
    Name = "${var.environment}-database-sg"
  })
}
```

### Secrets Management

```yaml
# k8s/security/sealed-secrets.yml
apiVersion: v1
kind: Secret
metadata:
  name: database-credentials
  namespace: tta-dev-apps
type: Opaque
stringData:
  url: "postgresql://{{ database_username }}:{{ database_password }}@{{ database_host }}:5432/{{ database_name }}"
  host: "{{ database_host }}"
  port: "5432"
  name: "{{ database_name }}"
  username: "{{ database_username }}"
  password: "{{ database_password }}"
---
apiVersion: v1
kind: Secret
metadata:
  name: redis-credentials
  namespace: tta-dev-apps
type: Opaque
stringData:
  url: "redis://{{ redis_host }}:6379/0"
  host: "{{ redis_host }}"
  port: "6379"
```

### Pod Security Policies

```yaml
# k8s/security/pod-security-standards.yml
apiVersion: v1
kind: Namespace
metadata:
  name: tta-dev-apps
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: tta-dev-apps
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-tta-dev-api
  namespace: tta-dev-apps
spec:
  podSelector:
    matchLabels:
      app: tta-dev-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to: []  # Allow all outbound traffic
```

---

## 🚀 Deployment Automation

### CI/CD Pipeline Integration

```yaml
# .github/workflows/infrastructure-deploy.yml
name: Infrastructure Deployment

on:
  push:
    branches: [main]
    paths: ['infrastructure/**']
  pull_request:
    paths: ['infrastructure/**']

env:
  TF_VERSION: '1.6.0'
  ANSIBLE_VERSION: '8.0.0'

jobs:
  validate:
    name: Validate Infrastructure Code
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Format Check
        run: terraform fmt -check -recursive infrastructure/

      - name: Terraform Validate
        run: |
          cd infrastructure/environments/prod
          terraform init -backend=false
          terraform validate

      - name: Validate Ansible Playbooks
        run: |
          pip install ansible==${{ env.ANSIBLE_VERSION }}
          ansible-playbook --syntax-check ansible/playbooks/site.yml

  plan:
    name: Terraform Plan
    runs-on: ubuntu-latest
    needs: validate
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Plan
        run: |
          cd infrastructure/environments/prod
          terraform init
          terraform plan -out=tfplan

      - name: Upload Plan
        uses: actions/upload-artifact@v3
        with:
          name: terraform-plan
          path: infrastructure/environments/prod/tfplan

  deploy:
    name: Deploy Infrastructure
    runs-on: ubuntu-latest
    needs: validate
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Deploy Infrastructure
        run: |
          cd infrastructure/environments/prod
          terraform init
          terraform apply -auto-approve

      - name: Configure Applications
        run: |
          pip install ansible==${{ env.ANSIBLE_VERSION }}
          cd ansible
          ansible-playbook -i inventories/prod/hosts.yml playbooks/site.yml
```

### Deployment Scripts

```bash
#!/bin/bash
# scripts/deploy.sh - Infrastructure deployment automation

set -euo pipefail

ENVIRONMENT=${1:-""}
TERRAFORM_ACTION=${2:-"plan"}

if [[ -z "$ENVIRONMENT" ]]; then
    echo "Usage: $0 <environment> [plan|apply|destroy]"
    echo "Environments: dev, staging, prod"
    exit 1
fi

if [[ ! -d "infrastructure/environments/$ENVIRONMENT" ]]; then
    echo "Environment $ENVIRONMENT not found"
    exit 1
fi

echo "=== TTA.dev Infrastructure Deployment ==="
echo "Environment: $ENVIRONMENT"
echo "Action: $TERRAFORM_ACTION"
echo "========================================="

# Change to environment directory
cd "infrastructure/environments/$ENVIRONMENT"

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Validate configuration
echo "Validating Terraform configuration..."
terraform validate

# Plan or apply changes
case $TERRAFORM_ACTION in
    "plan")
        echo "Creating Terraform plan..."
        terraform plan -out=tfplan
        ;;
    "apply")
        echo "Applying Terraform changes..."
        terraform apply -auto-approve

        echo "Configuring applications with Ansible..."
        cd ../../../ansible
        ansible-playbook -i "inventories/$ENVIRONMENT/hosts.yml" playbooks/site.yml
        ;;
    "destroy")
        echo "Destroying infrastructure..."
        read -p "Are you sure you want to destroy $ENVIRONMENT environment? (yes/no): " confirm
        if [[ $confirm == "yes" ]]; then
            terraform destroy -auto-approve
        else
            echo "Deployment cancelled"
            exit 1
        fi
        ;;
    *)
        echo "Invalid action: $TERRAFORM_ACTION"
        echo "Valid actions: plan, apply, destroy"
        exit 1
        ;;
esac

echo "Deployment completed successfully!"
```

---

## 📊 Monitoring and Alerting

### Infrastructure Monitoring

```yaml
# monitoring/alerts/infrastructure.yml
groups:
- name: infrastructure
  rules:
  - alert: NodeDown
    expr: up{job="node-exporter"} == 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Node {{ $labels.instance }} is down"
      description: "Node {{ $labels.instance }} has been down for more than 5 minutes"

  - alert: HighCPUUsage
    expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 90
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage on {{ $labels.instance }}"
      description: "CPU usage is above 90% for more than 10 minutes"

  - alert: HighMemoryUsage
    expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 90
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage on {{ $labels.instance }}"
      description: "Memory usage is above 90% for more than 10 minutes"

  - alert: DiskSpaceLow
    expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 10
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Low disk space on {{ $labels.instance }}"
      description: "Disk space is below 10% on {{ $labels.device }}"
```

### Application Monitoring

```yaml
# monitoring/alerts/applications.yml
groups:
- name: applications
  rules:
  - alert: ApplicationDown
    expr: up{job="tta-dev-api"} == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "TTA.dev API is down"
      description: "TTA.dev API has been down for more than 2 minutes"

  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100 > 5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High error rate in TTA.dev API"
      description: "Error rate is above 5% for more than 5 minutes"

  - alert: HighLatency
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "High latency in TTA.dev API"
      description: "95th percentile latency is above 1 second for more than 10 minutes"
```

---

## 🎯 Best Practices

### Infrastructure Design

- **Immutable Infrastructure** - Replace rather than modify
- **Infrastructure as Code** - All changes through version control
- **Environment Parity** - Consistent configuration across environments
- **Automated Testing** - Validate infrastructure changes
- **Security by Default** - Secure configurations from the start

### Operational Excellence

- **Monitoring First** - Comprehensive observability from day one
- **Automated Recovery** - Self-healing infrastructure components
- **Change Management** - Controlled and validated deployments
- **Disaster Recovery** - Regular backup and recovery testing
- **Cost Optimization** - Continuous cost monitoring and optimization

### Security Hardening

- **Network Segmentation** - Micro-segmented network architecture
- **Least Privilege** - Minimal required permissions
- **Secrets Management** - Centralized secrets handling
- **Vulnerability Scanning** - Regular security assessments
- **Compliance Monitoring** - Continuous compliance validation

---

## 📚 Related Resources

### Core Documentation

- [[TTA.dev/DevOps Studio Architecture]] - Overall architecture
- [[TTA.dev/CI-CD Pipeline]] - Pipeline configuration
- [[TTA.dev/Security]] - Security best practices

### Implementation Guides

- [[TTA.dev/DevOps Studio/Container Orchestration]] - Kubernetes deployment
- [[TTA.dev/DevOps Studio/Monitoring Stack]] - Observability setup
- [[TTA.dev/DevOps Studio/Security Pipeline]] - Security implementation

### Learning Resources

- [[TTA.dev/Learning Paths]] - Structured learning progression
- [[TTA.dev/Best Practices]] - Operational best practices
- [[Infrastructure Learning Path]] - IaC mastery guide

---

**Last Updated:** November 7, 2025
**Next Review:** Monthly
**Maintained by:** TTA.dev Platform Team
