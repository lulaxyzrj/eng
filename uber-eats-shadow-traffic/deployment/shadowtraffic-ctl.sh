#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

NAMESPACE="${ST_NAMESPACE:-shadowtraffic}"
DEPLOYMENT_NAME="shadowtraffic"

print_status() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

show_help() {
    cat << EOF
ShadowTraffic Control Script

Usage: $0 COMMAND [OPTIONS]

Commands:
    status          Show deployment status and health
    logs            View deployment logs
    restart         Restart the deployment
    scale           Scale the deployment
    topics          List Kafka topics being generated
    config          View current configuration
    progress        Monitor generation progress (for limited runs)
    stats           Show generation statistics
    port-forward    Forward local port to ShadowTraffic

Options:
    -n, --namespace  Kubernetes namespace (default: $NAMESPACE)
    -f, --follow     Follow logs (for logs command)
    -t, --tail       Number of log lines (default: 50)
    -r, --replicas   Number of replicas (for scale command)

Examples:
    $0 status
    $0 logs --follow
    $0 scale --replicas 3

EOF
}

COMMAND=$1
shift || true

FOLLOW=false
TAIL_LINES=50
REPLICAS=1

while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -t|--tail)
            TAIL_LINES="$2"
            shift 2
            ;;
        -r|--replicas)
            REPLICAS="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

check_deployment() {
    if ! kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" &>/dev/null; then
        print_error "ShadowTraffic deployment not found in namespace '$NAMESPACE'"
        echo "Run './deploy.sh' to deploy ShadowTraffic first"
        return 1
    fi
    return 0
}

cmd_status() {
    echo -e "${BLUE}🚀 ShadowTraffic Status${NC}"
    echo "======================"
    echo "Namespace: $NAMESPACE"
    echo ""

    if ! check_deployment; then
        return 1
    fi

    echo -e "${BLUE}Deployment:${NC}"
    kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE"

    echo -e "\n${BLUE}Pods:${NC}"
    kubectl get pods -n "$NAMESPACE" -l app=shadowtraffic -o wide

    PODS=$(kubectl get pods -n "$NAMESPACE" -l app=shadowtraffic -o jsonpath='{.items[*].metadata.name}')
    if [ -n "$PODS" ]; then
        echo -e "\n${BLUE}Pod Health:${NC}"
        for pod in $PODS; do
            STATUS=$(kubectl get pod "$pod" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
            READY=$(kubectl get pod "$pod" -n "$NAMESPACE" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')

            if [ "$STATUS" = "Running" ] && [ "$READY" = "True" ]; then
                print_success "$pod is healthy"
            else
                print_warning "$pod - Status: $STATUS, Ready: $READY"
            fi
        done
    fi
}

cmd_logs() {
    if ! check_deployment; then
        return 1
    fi

    print_status "Fetching logs from ShadowTraffic..."

    if [ "$FOLLOW" = true ]; then
        kubectl logs -f -n "$NAMESPACE" deployment/"$DEPLOYMENT_NAME" --tail=100
    else
        kubectl logs -n "$NAMESPACE" deployment/"$DEPLOYMENT_NAME" --tail="$TAIL_LINES"
    fi
}

cmd_restart() {
    if ! check_deployment; then
        return 1
    fi

    print_status "Restarting ShadowTraffic deployment..."
    kubectl rollout restart deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE"

    print_status "Waiting for rollout to complete..."
    kubectl rollout status deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE"

    print_success "Deployment restarted successfully"
}

cmd_scale() {
    if ! check_deployment; then
        return 1
    fi

    print_status "Scaling deployment to $REPLICAS replicas..."
    kubectl scale deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE" --replicas="$REPLICAS"

    print_status "Waiting for scaling to complete..."
    kubectl wait --for=condition=available --timeout=60s deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE"

    print_success "Scaled to $REPLICAS replicas"
    kubectl get pods -n "$NAMESPACE" -l app=shadowtraffic
}

cmd_topics() {
    if ! check_deployment; then
        return 1
    fi

    print_status "Extracting Kafka topics from configuration..."

    CONFIG=$(kubectl get configmap shadowtraffic-config -n "$NAMESPACE" -o jsonpath='{.data.config\.json}' 2>/dev/null)

    if [ -z "$CONFIG" ]; then
        print_error "Could not retrieve configuration"
        return 1
    fi

    echo -e "\n${BLUE}📊 Configured Kafka Topics:${NC}"

    TOPICS_INFO=$(echo "$CONFIG" | jq -r '
        .generators[] |
        select(has("topic")) |
        {
            topic: .topic,
            events: .events,
            maxEvents: .maxEvents,
            delay: .delay,
            messageCount: (if .events then "\(.events) (events)" elif .maxEvents then "\(.maxEvents) (maxEvents)" else "continuous" end),
            rate: (if .delay then "1 msg/\(.delay)ms" else "unlimited" end)
        } |
        @json
    ' | sort -u)

    echo "$TOPICS_INFO" | while read -r line; do
        TOPIC=$(echo "$line" | jq -r '.topic')
        EVENTS=$(echo "$line" | jq -r '.messageCount')
        RATE=$(echo "$line" | jq -r '.rate')

        echo "  📋 $TOPIC"
        echo "     ├─ Messages: $EVENTS"
        echo "     ├─ Rate: $RATE"

        COUNT=$(echo "$CONFIG" | jq -r --arg topic "$TOPIC" '.generators[] | select(.topic == $topic) | .topic' | wc -l)
        echo "     └─ Generators: $COUNT"
    done

    echo -e "\n${BLUE}Kafka Connection:${NC}"
    echo "$CONFIG" | jq '.connections.kafka' 2>/dev/null || echo "Not configured"

    PARALLELISM=$(echo "$CONFIG" | jq -r '.parallelism // "default"')
    echo -e "\n${BLUE}Global Settings:${NC}"
    echo "  Parallelism: $PARALLELISM"
}

cmd_progress() {
    if ! check_deployment; then
        return 1
    fi

    print_status "Monitoring generation progress..."

    CONFIG=$(kubectl get configmap shadowtraffic-config -n "$NAMESPACE" -o jsonpath='{.data.config\.json}' 2>/dev/null)

    if [ -z "$CONFIG" ]; then
        print_error "Could not retrieve configuration"
        return 1
    fi

    HAS_LIMIT=$(echo "$CONFIG" | jq 'any(.generators[]; has("events"))')

    if [ "$HAS_LIMIT" != "true" ]; then
        print_warning "No message limits configured - generation is continuous"
        echo "Use Ctrl+C to stop monitoring"
        echo ""
    fi

    echo -e "${BLUE}Monitoring progress (Ctrl+C to stop)...${NC}"
    echo ""

    kubectl logs -f -n "$NAMESPACE" deployment/"$DEPLOYMENT_NAME" --tail=0 | \
    while IFS= read -r line; do
        if echo "$line" | grep -iE "(generated|sent|produced|complete|finished|events remaining)" &>/dev/null; then
            echo "[$(date +'%H:%M:%S')] $line"
        fi
    done
}

cmd_stats() {
    if ! check_deployment; then
        return 1
    fi

    print_status "Gathering generation statistics..."

    LOGS=$(kubectl logs -n "$NAMESPACE" deployment/"$DEPLOYMENT_NAME" --tail=2000 2>/dev/null)

    if [ -z "$LOGS" ]; then
        print_error "No logs available"
        return 1
    fi

    echo -e "\n${BLUE}📊 Generation Statistics:${NC}"

    echo "  Message counts (estimated from logs):"

    TOPICS=$(kubectl get configmap shadowtraffic-config -n "$NAMESPACE" -o json | \
             jq -r '.data."config.json"' | \
             jq -r '.generators[] | select(has("topic")) | .topic' | sort -u)

    for topic in $TOPICS; do
        COUNT=$(echo "$LOGS" | grep -c "$topic" || echo "0")
        if [ "$COUNT" -gt 0 ]; then
            echo "    $topic: ~$COUNT mentions"
        fi
    done

    echo ""
    echo "  Generation timeline:"
    FIRST_LOG=$(echo "$LOGS" | head -1 | awk '{print $1, $2}')
    LAST_LOG=$(echo "$LOGS" | tail -1 | awk '{print $1, $2}')
    echo "    First log: $FIRST_LOG"
    echo "    Last log:  $LAST_LOG"

    ERROR_COUNT=$(echo "$LOGS" | grep -c "ERROR" || echo "0")
    WARN_COUNT=$(echo "$LOGS" | grep -c "WARN" || echo "0")

    echo ""
    echo "  Log summary:"
    echo "    Errors:   $ERROR_COUNT"
    echo "    Warnings: $WARN_COUNT"

    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo ""
        echo -e "${RED}  Recent errors:${NC}"
        echo "$LOGS" | grep "ERROR" | tail -3 | sed 's/^/    /'
    fi
}

cmd_config() {
    if ! check_deployment; then
        return 1
    fi

    print_status "Current ShadowTraffic configuration..."

    CONFIG=$(kubectl get configmap shadowtraffic-config -n "$NAMESPACE" -o jsonpath='{.data.config\.json}' 2>/dev/null)

    if [ -z "$CONFIG" ]; then
        print_error "Could not retrieve configuration"
        return 1
    fi

    echo "$CONFIG" | jq '.' | less
}

cmd_port_forward() {
    if ! check_deployment; then
        return 1
    fi

    print_status "Setting up port forwarding on localhost:8080..."
    echo "Press Ctrl+C to stop"

    kubectl port-forward -n "$NAMESPACE" deployment/"$DEPLOYMENT_NAME" 8080:8080
}

case "$COMMAND" in
    status)
        cmd_status
        ;;
    logs)
        cmd_logs
        ;;
    restart)
        cmd_restart
        ;;
    scale)
        cmd_scale
        ;;
    topics)
        cmd_topics
        ;;
    config)
        cmd_config
        ;;
    progress)
        cmd_progress
        ;;
    stats)
        cmd_stats
        ;;
    port-forward)
        cmd_port_forward
        ;;
    *)
        if [ -n "$COMMAND" ]; then
            echo "Unknown command: $COMMAND"
            echo ""
        fi
        show_help
        exit 1
        ;;
esac