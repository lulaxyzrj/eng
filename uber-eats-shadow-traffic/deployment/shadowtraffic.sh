#!/bin/bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

CONNECTION="kafka-k8s"
BATCH_SIZE=100
DELAY=60000
MODE="batch"

show_usage() {
    cat <<EOF
${BLUE}ShadowTraffic - Simple Data Generation${NC}

Usage: $0 <command> [options]

${GREEN}Commands:${NC}
  batch              Run batch mode (default: 100 messages, 1min delay)
  stream             Run streaming mode (continuous)
  quick              Quick test (10 messages, 1s delay)
  load               Heavy load test (1000 messages, 100ms delay)

  cronjob            Generate CronJob for automated runs
  status             Check deployment status
  logs               View logs
  stop               Stop current deployment

  setup              Initial setup (license, namespace, etc.)
  help               Show this help

${GREEN}Options:${NC}
  -c, --connection   Connection to use (default: kafka-k8s)
  -b, --batch        Batch size (default: 100)
  -d, --delay        Delay in ms (default: 60000)
  -s, --schedule     CronJob schedule (default: "0 * * * *")

${GREEN}Examples:${NC}
  $0 quick

  $0 batch

  $0 batch -b 500 -d 5000

  $0 stream -d 1000

  $0 batch -c postgres-prod

  $0 cronjob


  $0 cronjob -s "*/30 * * * *"

${GREEN}Connections:${NC}
  kafka-k8s          Kubernetes Kafka (default)
  postgres-prod      PostgreSQL
  s3-aws            AWS S3
  mongodb-atlas      MongoDB

  Add more in: connections/

EOF
}

COMMAND=${1:-help}
shift || true

while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--connection)
            CONNECTION="$2"
            shift 2
            ;;
        -b|--batch)
            BATCH_SIZE="$2"
            shift 2
            ;;
        -d|--delay)
            DELAY="$2"
            shift 2
            ;;
        -s|--schedule)
            SCHEDULE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

case $COMMAND in
    batch)
        echo -e "${GREEN}🚀 Starting batch mode${NC}"
        echo "   Connection: $CONNECTION"
        echo "   Batch size: $BATCH_SIZE messages"
        echo "   Delay: $(($DELAY/1000))s between messages"
        echo ""
        ./deploy.sh --mode batch --connection "$CONNECTION" --batch-size "$BATCH_SIZE" --delay "$DELAY"
        ;;

    stream|streaming)
        echo -e "${GREEN}🔄 Starting streaming mode${NC}"
        echo "   Connection: $CONNECTION"
        echo "   Throttle: $(($DELAY/1000))s between messages"
        echo ""
        ./deploy.sh --mode streaming --connection "$CONNECTION" --delay "$DELAY"
        ;;

    quick)
        echo -e "${GREEN}⚡ Quick test: 10 messages, 1s delay${NC}"
        ./deploy.sh --mode batch --connection "$CONNECTION" --batch-size 10 --delay 1000
        ;;

    load)
        echo -e "${GREEN}🔥 Load test: 1000 messages, 100ms delay${NC}"
        ./deploy.sh --mode batch --connection "$CONNECTION" --batch-size 1000 --delay 100
        ;;

    cronjob)
        SCHEDULE="${SCHEDULE:-0 * * * *}"
        echo -e "${GREEN}⏰ Generating CronJob${NC}"
        echo "   Schedule: $SCHEDULE"
        echo "   Connection: $CONNECTION"
        echo "   Batch size: $BATCH_SIZE"
        echo "   Delay: $(($DELAY/1000))s"
        echo ""
        ./deploy.sh --mode batch --connection "$CONNECTION" --batch-size "$BATCH_SIZE" --delay "$DELAY" --cronjob --schedule "$SCHEDULE"
        ;;

    status)
        echo -e "${GREEN}📊 Checking status${NC}"
        ./shadowtraffic-ctl.sh status
        ;;

    logs)
        echo -e "${GREEN}📜 Viewing logs${NC}"
        ./shadowtraffic-ctl.sh logs -f
        ;;

    stop)
        echo -e "${YELLOW}🛑 Stopping ShadowTraffic${NC}"
        kubectl delete deployment shadowtraffic -n shadowtraffic --ignore-not-found
        echo "Deployment stopped"
        ;;

    setup)
        echo -e "${GREEN}🔧 Running setup${NC}"
        ./setup.sh
        ;;

    help|--help|-h)
        show_usage
        ;;

    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac