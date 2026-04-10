#!/bin/bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔧 ShadowTraffic Setup${NC}"
echo "===================="
echo ""

check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 found"
        return 0
    else
        echo -e "${RED}✗${NC} $1 not found"
        return 1
    fi
}

echo "Checking prerequisites..."
MISSING_DEPS=0

check_command kubectl || MISSING_DEPS=1
check_command jq || MISSING_DEPS=1

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    echo -e "${RED}Missing dependencies!${NC}"
    echo "Please install:"
    echo "  - kubectl: https://kubernetes.io/docs/tasks/tools/"
    echo "  - jq: https://stedolan.github.io/jq/download/"
    exit 1
fi

echo ""

echo "Checking Kubernetes cluster..."
if kubectl cluster-info &> /dev/null; then
    echo -e "${GREEN}✓${NC} Connected to Kubernetes cluster"
    CLUSTER_INFO=$(kubectl cluster-info | head -1)
    echo "  $CLUSTER_INFO"
else
    echo -e "${RED}✗${NC} Not connected to Kubernetes cluster"
    echo ""
    echo "Please start your Kubernetes cluster:"
    echo "  - Minikube: minikube start"
    echo "  - Docker Desktop: Enable Kubernetes in settings"
    echo "  - Kind: kind create cluster"
    exit 1
fi

echo ""

echo "Creating namespace..."
if kubectl get namespace shadowtraffic &> /dev/null; then
    echo -e "${YELLOW}!${NC} Namespace 'shadowtraffic' already exists"
else
    kubectl create namespace shadowtraffic
    echo -e "${GREEN}✓${NC} Created namespace 'shadowtraffic'"
fi

echo ""

echo "Setting up ShadowTraffic license..."
if kubectl get secret shadowtraffic-license -n shadowtraffic &> /dev/null; then
    echo -e "${YELLOW}!${NC} License secret already exists"
    read -p "Update license? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing license"
    else
        kubectl delete secret shadowtraffic-license -n shadowtraffic
        CREATE_LICENSE=1
    fi
else
    CREATE_LICENSE=1
fi

if [ "${CREATE_LICENSE:-0}" -eq 1 ]; then
    if [ -f "license.env" ]; then
        echo -e "${GREEN}✓${NC} Found license.env file"
        kubectl create secret generic shadowtraffic-license \
            --from-env-file=license.env \
            --namespace=shadowtraffic
        echo -e "${GREEN}✓${NC} Created license secret from license.env"
    elif [ -n "$SHADOWTRAFFIC_LICENSE" ]; then
        echo -e "${GREEN}✓${NC} Found SHADOWTRAFFIC_LICENSE environment variable"
        kubectl create secret generic shadowtraffic-license \
            --from-literal=license="$SHADOWTRAFFIC_LICENSE" \
            --namespace=shadowtraffic
        echo -e "${GREEN}✓${NC} Created license secret from environment variable"
    else
        echo -e "${YELLOW}!${NC} No license found"
        echo ""
        echo "Please enter your ShadowTraffic license key:"
        read -s LICENSE_KEY
        echo ""
        if [ -z "$LICENSE_KEY" ]; then
            echo -e "${RED}✗${NC} No license key provided"
            exit 1
        fi
        kubectl create secret generic shadowtraffic-license \
            --from-literal=license="$LICENSE_KEY" \
            --namespace=shadowtraffic
        echo -e "${GREEN}✓${NC} Created license secret"

        echo ""
        read -p "Save license to license.env file? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "SHADOWTRAFFIC_LICENSE=$LICENSE_KEY" > license.env
            echo -e "${GREEN}✓${NC} Saved license to license.env"
        fi
    fi
fi

echo ""

echo "Checking directory structure..."
DIRS=("gen/template" "connections" "deployment")
for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} Found $dir/"
    else
        echo -e "${YELLOW}!${NC} Creating $dir/"
        mkdir -p "$dir"
    fi
done

echo ""

if [ ! -f "connections/kafka-k8s.json" ]; then
    echo "Creating default Kafka connection..."
    cat > connections/kafka-k8s.json <<EOF
{
  "kafka": {
    "kind": "kafka",
    "producerConfigs": {
      "bootstrap.servers": "kafka-bootstrap.kafka:9092",
      "key.serializer": "org.apache.kafka.common.serialization.StringSerializer",
      "value.serializer": "org.apache.kafka.common.serialization.StringSerializer",
      "acks": "all",
      "retries": "3"
    }
  }
}
EOF
    echo -e "${GREEN}✓${NC} Created connections/kafka-k8s.json"
fi

echo ""
echo "Making scripts executable..."
chmod +x shadowtraffic.sh deploy.sh shadowtraffic-ctl.sh 2>/dev/null || true
echo -e "${GREEN}✓${NC} Scripts are executable"

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Make sure you have a template in gen/template/ (e.g., uber-eats.json)"
echo "2. Run a quick test:"
echo "   ${BLUE}./shadowtraffic.sh quick${NC}"
echo ""
echo "3. For help:"
echo "   ${BLUE}./shadowtraffic.sh help${NC}"
echo ""
echo "Happy data generation! 🚀"