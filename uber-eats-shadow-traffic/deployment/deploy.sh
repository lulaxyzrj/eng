#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'


SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"


NAMESPACE="shadowtraffic"

MESSAGE_COUNT=""
MESSAGE_RATE=""
RATE_UNIT="second"
BATCH_SIZE=""
PARALLELISM=""
MAX_EVENTS=""

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
ShadowTraffic Deployment Script with Generation Control

Usage: $0 [CONFIG_NAME] [CONNECTION_NAME] [OPTIONS]

Arguments:
    CONFIG_NAME      Configuration file name (default: uber-eats)
    CONNECTION_NAME  Connection file name (default: kafka-k8s)

Basic Options:
    -h, --help       Show this help message
    -n, --namespace  Kubernetes namespace (default: shadowtraffic)
    -d, --debug      Enable debug mode (show transformed config)
    -f, --follow     Follow logs after deployment
    -c, --clean      Clean up existing deployment before deploying
    -l, --list       List available configurations and connections
    -v, --validate   Validate configuration without deploying

Generation Control Options:
    --count NUM      Total number of messages to generate per generator (uses 'events')
    --max-events NUM Use 'maxEvents' instead of 'events' (allows generators to stop at different times)
    --rate NUM       Messages per time unit (adds delay between messages)
    --rate-unit UNIT Time unit for rate: second|minute|hour (default: second)
    --batch SIZE     Kafka batch size (default: from connection config)
    --parallel NUM   Number of parallel generator threads

Examples:
    $0

    $0 uber-eats kafka-k8s --count 1000 --rate 100

    $0 uber-eats kafka-k8s --rate 6000 --rate-unit minute

    $0 uber-eats kafka-k8s --count 10000

    $0 uber-eats kafka-k8s --max-events 10000

    $0 uber-eats kafka-k8s --parallel 5 --rate 1000

EOF
}

POSITIONAL_ARGS=()
FOLLOW_LOGS=false
CLEAN_FIRST=false
DEBUG_MODE=false
LIST_ONLY=false
VALIDATE_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -d|--debug)
            DEBUG_MODE=true
            shift
            ;;
        -f|--follow)
            FOLLOW_LOGS=true
            shift
            ;;
        -c|--clean)
            CLEAN_FIRST=true
            shift
            ;;
        -l|--list)
            LIST_ONLY=true
            shift
            ;;
        -v|--validate)
            VALIDATE_ONLY=true
            shift
            ;;
        --count)
            MESSAGE_COUNT="$2"
            shift 2
            ;;
        --max-events)
            MAX_EVENTS="$2"
            shift 2
            ;;
        --rate)
            MESSAGE_RATE="$2"
            shift 2
            ;;
        --rate-unit)
            RATE_UNIT="$2"
            if [[ ! "$RATE_UNIT" =~ ^(second|minute|hour)$ ]]; then
                print_error "Invalid rate unit: $RATE_UNIT (use: second, minute, hour)"
                exit 1
            fi
            shift 2
            ;;
        --batch)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --parallel|--parallelism)
            PARALLELISM="$2"
            shift 2
            ;;
        -*)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
        *)
            POSITIONAL_ARGS+=("$1")
            shift
            ;;
    esac
done

CONFIG_NAME="${POSITIONAL_ARGS[0]:-uber-eats}"
CONNECTION_NAME="${POSITIONAL_ARGS[1]:-kafka-k8s}"

if [ "$LIST_ONLY" = true ]; then
    echo -e "${BLUE}📋 Available Configurations:${NC}"
    echo "=========================="
    if [ -d "$PROJECT_ROOT/gen/template" ]; then
        for config in "$PROJECT_ROOT"/gen/template/*.json; do
            if [ -f "$config" ]; then
                basename "$config" .json
            fi
        done
    fi

    echo ""
    echo -e "${BLUE}🔗 Available Connections:${NC}"
    echo "======================="
    if [ -d "$PROJECT_ROOT/connections" ]; then
        for conn in "$PROJECT_ROOT"/connections/*.json; do
            if [ -f "$conn" ]; then
                name=$(basename "$conn" .json)
                kind=$(jq -r '.kind' "$conn" 2>/dev/null || echo "unknown")
                printf "  %-20s (%s)\n" "$name" "$kind"
            fi
        done
    fi
    exit 0
fi

echo -e "${BLUE}🚀 ShadowTraffic Deployment${NC}"
echo "=========================="
echo "📋 Config: $CONFIG_NAME"
echo "🔗 Connection: $CONNECTION_NAME"
echo "📦 Namespace: $NAMESPACE"

echo ""
echo -e "${BLUE}⚙️  Generation Settings:${NC}"
if [ -n "$MESSAGE_COUNT" ]; then
    echo "  Message limit: $MESSAGE_COUNT per generator (using 'events')"
elif [ -n "$MAX_EVENTS" ]; then
    echo "  Message limit: $MAX_EVENTS per generator (using 'maxEvents')"
else
    echo "  Messages: Continuous (unlimited)"
fi

if [ -n "$MESSAGE_RATE" ]; then
    echo "  Rate: $MESSAGE_RATE messages per $RATE_UNIT"
    DELAY=$((1000 / MESSAGE_RATE))
    if [ "$RATE_UNIT" = "minute" ]; then
        DELAY=$((60000 / MESSAGE_RATE))
    elif [ "$RATE_UNIT" = "hour" ]; then
        DELAY=$((3600000 / MESSAGE_RATE))
    fi
    echo "  Delay: ${DELAY}ms between messages"
else
    echo "  Rate: Unlimited (no delay)"
fi

if [ -n "$BATCH_SIZE" ]; then
    echo "  Batch Size: $BATCH_SIZE"
fi

if [ -n "$PARALLELISM" ]; then
    echo "  Parallelism: $PARALLELISM"
fi

echo ""

print_status "Checking prerequisites..."
for tool in kubectl jq; do
    if ! command -v $tool &> /dev/null; then
        print_error "$tool is required but not installed"
        exit 1
    fi
done
print_success "Prerequisites checked"

CONFIG_FILE="$PROJECT_ROOT/gen/template/$CONFIG_NAME.json"
if [ ! -f "$CONFIG_FILE" ]; then
    print_error "Configuration not found: $CONFIG_FILE"
    echo ""
    echo "Available configurations:"
    ls -1 "$PROJECT_ROOT/gen/template/" 2>/dev/null | grep '\.json$' | sed 's/\.json$//' | sed 's/^/  - /'
    exit 1
fi

CONNECTION_FILE="$PROJECT_ROOT/connections/$CONNECTION_NAME.json"
if [ ! -f "$CONNECTION_FILE" ]; then
    print_error "Connection not found: $CONNECTION_FILE"
    echo ""
    echo "Available connections:"
    ls -1 "$PROJECT_ROOT/connections/" 2>/dev/null | grep '\.json$' | sed 's/\.json$//' | sed 's/^/  - /'
    exit 1
fi

LICENSE_FILE="$PROJECT_ROOT/st-key.env"
if [ ! -f "$LICENSE_FILE" ]; then
    print_error "License file not found: $LICENSE_FILE"
    exit 1
fi

TEMP_LICENSE="/tmp/st-license-$$.env"
grep "^LICENSE_" "$LICENSE_FILE" > "$TEMP_LICENSE"

if [ ! -s "$TEMP_LICENSE" ]; then
    print_error "No LICENSE_* variables found in $LICENSE_FILE"
    rm -f "$TEMP_LICENSE"
    exit 1
fi

for var in LICENSE_ID LICENSE_EMAIL LICENSE_ORGANIZATION LICENSE_EDITION LICENSE_EXPIRATION LICENSE_SIGNATURE; do
    if ! grep -q "^$var=" "$TEMP_LICENSE"; then
        print_error "Missing required license variable: $var"
        rm -f "$TEMP_LICENSE"
        exit 1
    fi
done

print_success "License validation passed"

CONNECTION_KIND=$(jq -r '.kind' "$CONNECTION_FILE")
print_status "Connection type: $CONNECTION_KIND"

TEMP_CONFIG="/tmp/shadowtraffic-config-$$.json"

print_status "Transforming configuration..."

CONNECTION_CONFIG=$(jq '.config // .' "$CONNECTION_FILE")

GENERATION_CONTROL="{}"

if [ "$CONNECTION_KIND" = "kafka" ]; then
    GENERATION_CONTROL=$(jq -n \
        --arg count "$MESSAGE_COUNT" \
        --arg max_events "$MAX_EVENTS" \
        --arg rate "$MESSAGE_RATE" \
        --arg rate_unit "$RATE_UNIT" \
        --arg batch "$BATCH_SIZE" \
        --arg parallel "$PARALLELISM" \
        '{
            count: (if $count != "" then ($count | tonumber) else null end),
            maxEvents: (if $max_events != "" then ($max_events | tonumber) else null end),
            rate: (if $rate != "" then ($rate | tonumber) else null end),
            rateUnit: (if $rate != "" then $rate_unit else null end),
            batchSize: (if $batch != "" then ($batch | tonumber) else null end),
            parallelism: (if $parallel != "" then ($parallel | tonumber) else null end)
        }')
fi

jq --argjson conn_config "$CONNECTION_CONFIG" \
   --argjson gen_control "$GENERATION_CONTROL" \
'
del(.connections) |

def calculateDelay($rate; $unit):
    if $rate == null then
        null
    else
        if $unit == "second" then
            (1000 / $rate | floor)
        elif $unit == "minute" then
            (60000 / $rate | floor)
        elif $unit == "hour" then
            (3600000 / $rate | floor)
        else
            null
        end
    end;

.generators = (.generators | map(
    if has("bucket") then
        .topic = (.bucketConfigs.keyPrefix | rtrimstr("/") | gsub("/"; "-")) |
        .value = .data |

        if has("fork") then
            .key = { "_gen": "uuid" }
        else
            if .value.order_id then
                .key = .value.order_id
            elif .value.user_id then
                .key = .value.user_id
            elif .value.driver_id then
                .key = .value.driver_id
            elif .value.product_id then
                .key = .value.product_id
            elif .value.restaurant_id then
                .key = .value.restaurant_id
            elif .value.payment_id then
                .key = .value.payment_id
            elif .value.shift_id then
                .key = .value.shift_id
            elif .value.uuid then
                .key = .value.uuid
            else
                .key = { "_gen": "uuid" }
            end
        end |

        if $gen_control.count != null then
            .events = $gen_control.count
        elif $gen_control.maxEvents != null then
            .maxEvents = $gen_control.maxEvents
        else . end |

        if $gen_control.rate != null then
            .delay = calculateDelay($gen_control.rate; $gen_control.rateUnit)
        else . end |

        del(.bucket, .bucketConfigs, .data, .fork)
    else
        .
    end
)) |

.generators = (.generators | map(
    walk(
        if type == "object" and has("_gen") and ._gen == "var" and .var == "forkKey" then
            { "_gen": "uuid" }
        elif type == "object" and has("_gen") and ._gen == "lookup" then
            { "_gen": "sequentialInteger", "startingFrom": 1 }
        elif type == "object" and has("_gen") and ._gen == "previousEvent" and has("path") then
            .path = (.path | map(if . == "data" then "value" else . end))
        else
            .
        end
    )
)) |

.connections = {
    "kafka": (
        $conn_config |
        if $gen_control.batchSize != null then
            .batchSize = $gen_control.batchSize
        else . end
    )
} |

if $gen_control.parallelism != null then
    .parallelism = $gen_control.parallelism
else . end
' "$CONFIG_FILE" > "$TEMP_CONFIG"

print_success "Configuration transformed"

if [ "$DEBUG_MODE" = true ]; then
    echo ""
    echo -e "${BLUE}Transformed configuration:${NC}"
    jq '.' "$TEMP_CONFIG" | head -50
    echo "... (truncated)"
    echo ""

    echo -e "${BLUE}Generation settings applied:${NC}"
    jq '.generators[0] | {topic, events, maxEvents, delay}' "$TEMP_CONFIG" 2>/dev/null || echo "Could not extract generator settings"
    echo ""
fi

echo ""
echo -e "${BLUE}📊 Kafka Topics and Generation Info:${NC}"
TOPICS=$(jq -r '.generators[] | select(has("topic")) | .topic' "$TEMP_CONFIG" | sort -u)
if [ -z "$TOPICS" ]; then
    print_warning "No topics found in configuration"
else
    echo "$TOPICS" | while read -r topic; do
        echo "  📋 $topic"

        GEN_INFO=$(jq -r --arg topic "$topic" '
            .generators[] |
            select(.topic == $topic) |
            {
                events: (if .events then "\(.events) messages" else null end),
                maxEvents: (if .maxEvents then "max \(.maxEvents) messages" else null end),
                delay: (if .delay then "\(.delay)ms delay" else null end)
            } |
            to_entries |
            map(select(.value != null) | .value) |
            join(", ")
        ' "$TEMP_CONFIG" | head -1)

        if [ -n "$GEN_INFO" ]; then
            echo "     └─ Settings: $GEN_INFO"
        else
            echo "     └─ Settings: continuous, no delay"
        fi
    done
fi

if [ -n "$MESSAGE_COUNT" ]; then
    TOPIC_COUNT=$(echo "$TOPICS" | wc -l)
    TOTAL_MESSAGES=$((MESSAGE_COUNT * TOPIC_COUNT))
    echo ""
    echo -e "${BLUE}Total messages to generate: $TOTAL_MESSAGES ($MESSAGE_COUNT per topic × $TOPIC_COUNT topics)${NC}"
fi

if [ "$VALIDATE_ONLY" = true ]; then
    print_success "Configuration validation completed"
    rm -f "$TEMP_CONFIG" "$TEMP_LICENSE"
    exit 0
fi

if [ "$CLEAN_FIRST" = true ]; then
    print_status "Cleaning existing deployment..."
    kubectl delete deployment shadowtraffic -n "$NAMESPACE" --ignore-not-found=true
    kubectl delete configmap shadowtraffic-config -n "$NAMESPACE" --ignore-not-found=true
    kubectl delete secret shadowtraffic-license -n "$NAMESPACE" --ignore-not-found=true
    sleep 2
    print_success "Cleanup completed"
fi

echo ""
print_status "Deploying to Kubernetes..."

kubectl apply -f "$SCRIPT_DIR/deployment.yaml"

sleep 2

print_status "Creating license secret..."
kubectl create secret generic shadowtraffic-license \
    --from-env-file="$TEMP_LICENSE" \
    --namespace="$NAMESPACE" \
    --dry-run=client -o yaml | kubectl apply -f -

print_status "Creating configuration..."
kubectl create configmap shadowtraffic-config \
    --from-file=config.json="$TEMP_CONFIG" \
    --namespace="$NAMESPACE" \
    --dry-run=client -o yaml | kubectl apply -f -

echo ""
print_status "Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s \
    deployment/shadowtraffic -n "$NAMESPACE" 2>/dev/null || true

echo ""
print_success "Deployment complete!"
echo ""
kubectl get pods -n "$NAMESPACE"

rm -f "$TEMP_CONFIG" "$TEMP_LICENSE"

echo ""
echo -e "${BLUE}📝 Useful commands:${NC}"
echo "  View logs:        kubectl logs -f -n $NAMESPACE deployment/shadowtraffic"
echo "  Monitor progress: ./shadowtraffic-ctl.sh logs -f | grep -E 'generated|sent|complete'"
echo "  Check status:     ./shadowtraffic-ctl.sh status"
echo "  View topics:      ./shadowtraffic-ctl.sh topics"

if [ -n "$MESSAGE_COUNT" ]; then
    echo ""
    echo -e "${YELLOW}Note: Generation will stop after $MESSAGE_COUNT messages per topic${NC}"
    echo "  Check completion: kubectl logs -n $NAMESPACE deployment/shadowtraffic | grep -i complete"
fi

if [ "$FOLLOW_LOGS" = true ]; then
    echo ""
    print_status "Following logs (Ctrl+C to exit)..."
    sleep 2
    kubectl logs -f -n "$NAMESPACE" deployment/shadowtraffic
fi