#!/bin/bash

NAMESPACE="shadowtraffic"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

show_help() {
    echo "🚀 Enhanced ShadowTraffic Dynamic Management (Bash 3.x)"
    echo "======================================================"
    echo ""
    echo "Usage: ./utils.sh [COMMAND]"
    echo ""
    echo "📊 Status & Analysis:"
    echo "  status          - Show deployment status and metadata"
    echo "  config          - Deep configuration analysis"
    echo "  templates       - Analyze available templates"
    echo "  connections     - Analyze available connections"
    echo ""
    echo "🔍 Discovery & Intelligence:"
    echo "  discover        - Find configurations and deployments"
    echo "  matrix          - Show template×connection compatibility matrix"
    echo "  recommend       - Recommend optimal configurations"
    echo ""
    echo "🛠️  Operations:"
    echo "  logs            - Follow logs with intelligent filtering"
    echo "  shell           - Get shell access with context"
    echo "  restart         - Restart with configuration validation"
    echo "  switch          - Switch between template/connection combinations"
    echo ""
    echo "🧪 Development:"
    echo "  validate        - Validate template and connection files"
    echo "  preview         - Preview configuration composition"
    echo "  benchmark       - Analyze generation performance"
    echo ""
    echo "🔧 Management:"
    echo "  delete          - Delete deployment with backup option"
    echo "  context         - Set kubectl context with namespace"
    echo "  backup          - Backup current configuration"
    echo "  help            - Show this help"
}

get_deployment_info() {
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        local config=$(kubectl get namespace "$NAMESPACE" -o jsonpath='{.metadata.labels.config}' 2>/dev/null || echo "unknown")
        local connection=$(kubectl get namespace "$NAMESPACE" -o jsonpath='{.metadata.labels.connection}' 2>/dev/null || echo "unknown")
        local template=$(kubectl get namespace "$NAMESPACE" -o jsonpath='{.metadata.labels.template}' 2>/dev/null || echo "unknown")
        local generators=$(kubectl get namespace "$NAMESPACE" -o jsonpath='{.metadata.labels.generators}' 2>/dev/null || echo "unknown")
        echo "$config|$connection|$template|$generators"
    else
        echo "not-deployed|not-deployed|not-deployed|0"
    fi
}

analyze_templates() {
    echo "📋 Template Analysis"
    echo "==================="
    echo ""

    if [ ! -d "$PROJECT_ROOT/templates" ]; then
        echo "❌ Templates directory not found: $PROJECT_ROOT/templates"
        return 1
    fi

    local total_templates=0
    local total_generators=0

    for template in "$PROJECT_ROOT/templates"/*.json; do
        if [ -f "$template" ]; then
            local name=$(basename "$template" .json)
            local size=$(du -h "$template" | cut -f1)
            local generators=$(jq '.generators | length' "$template" 2>/dev/null || echo "?")
            local description=$(jq -r '.metadata.description // "No description"' "$template" 2>/dev/null)
            local features=$(jq -r '.metadata.features[]? // empty' "$template" 2>/dev/null | wc -l)
            local lookups=$(jq '[.generators[] | .. | objects | select(has("_gen") and ._gen == "lookup")] | length' "$template" 2>/dev/null || echo "0")
            local state_machines=$(jq '[.generators[] | .. | objects | select(has("_gen") and ._gen == "stateMachine")] | length' "$template" 2>/dev/null || echo "0")
            local forks=$(jq '[.generators[] | select(has("fork"))] | length' "$template" 2>/dev/null || echo "0")

            echo "  📋 $name ($size)"
            echo "     📝 $description"
            echo "     📊 $generators generators, $lookups lookups, $state_machines state machines, $forks forks"
            echo "     ✨ $features features"
            echo ""

            total_templates=$((total_templates + 1))
            if [ "$generators" != "?" ]; then
                total_generators=$((total_generators + generators))
            fi
        fi
    done

    echo "📈 Summary: $total_templates templates, $total_generators total generators"
}

analyze_connections() {
    echo "🔗 Connection Analysis"
    echo "====================="
    echo ""

    if [ ! -d "$PROJECT_ROOT/connections" ]; then
        echo "❌ Connections directory not found: $PROJECT_ROOT/connections"
        return 1
    fi

    local total_connections=0

    for conn in "$PROJECT_ROOT/connections"/*.json; do
        if [ -f "$conn" ]; then
            local name=$(basename "$conn" .json)
            local kind=$(jq -r '.kind // "unknown"' "$conn" 2>/dev/null)
            local description=$(jq -r '.description // "No description"' "$conn" 2>/dev/null)

            case "$kind" in
                "kafka")
                    local detail=$(jq -r '.config.producerConfigs."bootstrap.servers" // "localhost:9092"' "$conn" 2>/dev/null)
                    echo "  🔗 $name ($kind)"
                    echo "     📝 $description"
                    echo "     🌐 Brokers: $detail"
                    ;;
                "azureBlobStorage")
                    local account=$(jq -r '.config.connectionConfigs.connectionString' "$conn" 2>/dev/null | grep -o 'AccountName=[^;]*' | cut -d'=' -f2 || echo "unknown")
                    echo "  🔗 $name ($kind)"
                    echo "     📝 $description"
                    echo "     ☁️  Account: $account"
                    ;;
                "s3"|"minio")
                    local bucket=$(jq -r '.config.connectionConfigs.bucket // "unknown"' "$conn" 2>/dev/null)
                    local endpoint=$(jq -r '.config.connectionConfigs.endpoint // "aws"' "$conn" 2>/dev/null)
                    echo "  🔗 $name ($kind)"
                    echo "     📝 $description"
                    echo "     🪣 Bucket: $bucket, Endpoint: $endpoint"
                    ;;
                "postgres"|"mysql"|"jdbc")
                    local db=$(jq -r '.config.connectionConfigs.jdbcUrl' "$conn" 2>/dev/null | grep -o '/[^?]*' | cut -d'/' -f2 || echo "unknown")
                    echo "  🔗 $name ($kind)"
                    echo "     📝 $description"
                    echo "     🗄️  Database: $db"
                    ;;
                *)
                    echo "  🔗 $name ($kind)"
                    echo "     📝 $description"
                    ;;
            esac
            echo ""

            total_connections=$((total_connections + 1))
        fi
    done

    echo "📈 Summary: $total_connections connection configurations"
}

show_compatibility_matrix() {
    echo "🔄 Template × Connection Compatibility Matrix"
    echo "============================================="
    echo ""

    if [ ! -d "$PROJECT_ROOT/templates" ] || [ ! -d "$PROJECT_ROOT/connections" ]; then
        echo "❌ Templates or connections directory not found"
        return 1
    fi

    printf "%-20s" "Template \\ Connection"
    for conn in "$PROJECT_ROOT/connections"/*.json; do
        if [ -f "$conn" ]; then
            local name=$(basename "$conn" .json | cut -c1-10)
            printf "%-12s" "$name"
        fi
    done
    echo ""

    printf "%-20s" "===================="
    for conn in "$PROJECT_ROOT/connections"/*.json; do
        if [ -f "$conn" ]; then
            printf "%-12s" "==========="
        fi
    done
    echo ""

    for template in "$PROJECT_ROOT/templates"/*.json; do
        if [ -f "$template" ]; then
            local template_name=$(basename "$template" .json | cut -c1-18)
            printf "%-20s" "$template_name"

            for conn in "$PROJECT_ROOT/connections"/*.json; do
                if [ -f "$conn" ]; then
                    local conn_kind=$(jq -r '.kind' "$conn" 2>/dev/null)

                    case "$conn_kind" in
                        "kafka"|"azureBlobStorage"|"s3"|"minio"|"postgres"|"mysql")
                            printf "%-12s" "✅"
                            ;;
                        *)
                            printf "%-12s" "❓"
                            ;;
                    esac
                fi
            done
            echo ""
        fi
    done

    echo ""
    echo "Legend: ✅ Compatible  ❓ Unknown/Experimental"
}

show_recommendations() {
    echo "💡 Configuration Recommendations"
    echo "==============================="
    echo ""

    echo "🧪 Development & Testing:"
    echo "  📋 minimal-demo + kafka-local     → Quick testing"
    echo "  📋 ubereats-core + postgres-dev   → Core feature development"
    echo "  📋 payments-only + minio-local    → Payment system testing"
    echo ""

    echo "🏢 Production Scenarios:"
    echo "  📋 ubereats-full + azure-blob     → Complete data lake"
    echo "  📋 ubereats-full + kafka-prod     → Real-time streaming"
    echo "  📋 analytics-subset + s3-prod     → Analytics pipeline"
    echo ""

    echo "🔬 Specialized Use Cases:"
    echo "  📋 user-data + postgres-prod      → User management system"
    echo "  📋 payments-only + kafka-prod     → Financial event processing"
    echo "  📋 location-tracking + s3-prod    → GPS analytics"
    echo ""

    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        local info=$(get_deployment_info)
        local current_template=$(echo "$info" | cut -d'|' -f3)
        local current_connection=$(echo "$info" | cut -d'|' -f2)

        echo "🎯 Based on your current deployment ($current_template → $current_connection):"

        case "$current_connection" in
            *kafka*)
                echo "  💡 Try switching to postgres-dev for relational analysis"
                echo "  💡 Or try minio-local for object storage testing"
                ;;
            *postgres*|*mysql*)
                echo "  💡 Try switching to kafka-local for streaming"
                echo "  💡 Or try azure-blob for data lake scenarios"
                ;;
            *azure*|*s3*|*minio*)
                echo "  💡 Try switching to kafka-local for real-time processing"
                echo "  💡 Or try postgres-dev for SQL analytics"
                ;;
        esac
    fi
}

validate_configurations() {
    echo "✅ Configuration Validation"
    echo "=========================="
    echo ""

    local total_errors=0

    echo "📋 Validating templates..."
    if [ -d "$PROJECT_ROOT/templates" ]; then
        for template in "$PROJECT_ROOT/templates"/*.json; do
            if [ -f "$template" ]; then
                local name=$(basename "$template" .json)
                if jq empty "$template" 2>/dev/null; then
                    local generators=$(jq '.generators | length' "$template" 2>/dev/null || echo "0")
                    echo "  ✅ $name ($generators generators)"
                else
                    echo "  ❌ $name - Invalid JSON"
                    total_errors=$((total_errors + 1))
                fi
            fi
        done
    else
        echo "  ❌ Templates directory not found"
        total_errors=$((total_errors + 1))
    fi

    echo ""

    echo "🔗 Validating connections..."
    if [ -d "$PROJECT_ROOT/connections" ]; then
        for conn in "$PROJECT_ROOT/connections"/*.json; do
            if [ -f "$conn" ]; then
                local name=$(basename "$conn" .json)
                if jq empty "$conn" 2>/dev/null; then
                    local kind=$(jq -r '.kind // "unknown"' "$conn" 2>/dev/null)
                    echo "  ✅ $name ($kind)"
                else
                    echo "  ❌ $name - Invalid JSON"
                    total_errors=$((total_errors + 1))
                fi
            fi
        done
    else
        echo "  ❌ Connections directory not found"
        total_errors=$((total_errors + 1))
    fi

    echo ""

    if [ $total_errors -eq 0 ]; then
        echo "🎉 All configurations are valid!"
    else
        echo "⚠️  Found $total_errors validation errors"
    fi

    return $total_errors
}

preview_composition() {
    local template_name="$1"
    local connection_name="$2"

    if [ -z "$template_name" ] || [ -z "$connection_name" ]; then
        echo "Usage: ./utils.sh preview <template> <connection>"
        return 1
    fi

    local template_file="$PROJECT_ROOT/templates/$template_name.json"
    local connection_file="$PROJECT_ROOT/connections/$connection_name.json"

    if [ ! -f "$template_file" ]; then
        echo "❌ Template not found: $template_file"
        return 1
    fi

    if [ ! -f "$connection_file" ]; then
        echo "❌ Connection not found: $connection_file"
        return 1
    fi

    echo "🔍 Configuration Preview: $template_name → $connection_name"
    echo "======================================================="
    echo ""

    local generators=$(jq '.generators | length' "$template_file" 2>/dev/null || echo "?")
    local template_desc=$(jq -r '.metadata.description // "No description"' "$template_file" 2>/dev/null)
    echo "📋 Template: $template_name"
    echo "   📝 $template_desc"
    echo "   📊 $generators generators"
    echo ""

    local conn_kind=$(jq -r '.kind' "$connection_file" 2>/dev/null)
    local conn_desc=$(jq -r '.description // "No description"' "$connection_file" 2>/dev/null)
    echo "🔗 Connection: $connection_name"
    echo "   📝 $conn_desc"
    echo "   🔧 Type: $conn_kind"
    echo ""

    echo "🔄 Transformation Preview:"
    case "$conn_kind" in
        "kafka")
            echo "   📦 Containers → Topics (e.g., mssql/users/ → mssql-users)"
            echo "   🔗 Lookups → Topic references"
            ;;
        "s3"|"minio")
            echo "   📦 Containers → S3 bucket objects"
            echo "   🔗 Lookups → Object references"
            ;;
        "postgres"|"mysql")
            echo "   📦 Containers → Database tables (e.g., mssql/users/ → mssql_users)"
            echo "   🔗 Lookups → Table references"
            ;;
        "azureBlobStorage")
            echo "   📦 Containers → Blob containers (unchanged)"
            echo "   🔗 Lookups → Container references"
            ;;
    esac

    echo ""
    echo "💡 To compose and deploy: ./dynamic-deploy.sh compose $template_name $connection_name"
}

show_enhanced_status() {
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        echo "❌ ShadowTraffic namespace does not exist"
        echo ""
        echo "💡 Available templates:"
        analyze_templates | head -10
        echo ""
        echo "💡 Deploy with: ./dynamic-deploy.sh compose <template> <connection>"
        return 1
    fi

    local info=$(get_deployment_info)
    local config=$(echo "$info" | cut -d'|' -f1)
    local connection=$(echo "$info" | cut -d'|' -f2)
    local template=$(echo "$info" | cut -d'|' -f3)
    local generators=$(echo "$info" | cut -d'|' -f4)

    echo "📊 Enhanced ShadowTraffic Status"
    echo "==============================="
    echo ""
    echo "🎯 Configuration: $config"
    echo "📋 Template: $template"
    echo "🔗 Connection: $connection"
    echo "📊 Generators: $generators"
    echo "🏗️  Namespace: $NAMESPACE"
    echo ""

    local temp_config="/tmp/shadowtraffic-current-config.json"
    kubectl get configmap shadowtraffic-config -n "$NAMESPACE" -o jsonpath='{.data.config\.json}' > "$temp_config" 2>/dev/null

    if [ -f "$temp_config" ]; then
        local generated_at=$(jq -r '.metadata.generated_at // "unknown"' "$temp_config" 2>/dev/null)
        echo "⏰ Generated: $generated_at"
        echo ""
    fi

    echo "📦 Pods:"
    kubectl get pods -n "$NAMESPACE" -o wide 2>/dev/null || echo "  No pods found"
    echo ""

    echo "🚀 Deployment:"
    kubectl get deployment shadowtraffic -n "$NAMESPACE" 2>/dev/null || echo "  No deployment found"
    echo ""

    echo "📋 ConfigMap:"
    kubectl get configmap shadowtraffic-config -n "$NAMESPACE" 2>/dev/null || echo "  No configmap found"

    rm -f "$temp_config"
}

intelligent_logs() {
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        echo "❌ ShadowTraffic namespace does not exist"
        return 1
    fi

    local info=$(get_deployment_info)
    local config=$(echo "$info" | cut -d'|' -f1)
    local connection=$(echo "$info" | cut -d'|' -f2)
    local template=$(echo "$info" | cut -d'|' -f3)

    echo "📋 Following logs for ShadowTraffic"
    echo "Template: $template → Connection: $connection"
    echo "=================================="
    kubectl logs -l app=shadowtraffic -n "$NAMESPACE" -f --tail=50
}

case "$1" in
    "status")
        show_enhanced_status
        ;;
    "config")
        show_enhanced_status
        echo ""
        analyze_templates | head -15
        ;;
    "templates")
        analyze_templates
        ;;
    "connections")
        analyze_connections
        ;;
    "matrix")
        show_compatibility_matrix
        ;;
    "recommend")
        show_recommendations
        ;;
    "validate")
        validate_configurations
        ;;
    "preview")
        preview_composition "$2" "$3"
        ;;
    "logs")
        intelligent_logs
        ;;
    "discover")
        analyze_templates
        echo ""
        analyze_connections
        ;;
    "help"|*)
        show_help
        ;;
esac