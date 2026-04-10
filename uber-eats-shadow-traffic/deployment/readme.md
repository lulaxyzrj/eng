# Uber Eats Shadow Traffic Generator

A comprehensive data generation system using [ShadowTraffic](https://shadowtraffic.io) to simulate realistic Uber Eats-like traffic patterns for Kafka. This project includes enhanced deployment scripts with advanced generation control capabilities.

## 🚀 Features

### Core Capabilities
- **Multi-topic Kafka data generation** simulating an Uber Eats ecosystem
- **Realistic data relationships** between users, drivers, restaurants, orders, and more
- **Kubernetes deployment** with full lifecycle management
- **20+ interconnected data streams** covering all aspects of food delivery

### ✨ Enhanced Generation Control
- **Message Count Control**: Set exact number of messages to generate
- **Rate Limiting**: Control generation speed (messages per second/minute/hour)
- **Performance Tuning**: Configure parallelism and batch sizes
- **Real-time Monitoring**: Track generation progress and statistics
- **Environment Management**: Deploy different configurations per environment

## 📋 Prerequisites

- Kubernetes cluster with `kubectl` configured
- Kafka cluster (deployed via Terraform or manually)
- `jq` installed for JSON processing
- ShadowTraffic license file (`st-key.env`)
- Docker (if using Minikube locally)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd uber-eats-shadow-traffic
   ```

2. **Add your ShadowTraffic license**:
   ```bash
   cat > st-key.env << EOF
   LICENSE_ID=your-license-id
   LICENSE_EMAIL=your-email
   LICENSE_ORGANIZATION=your-org
   LICENSE_EDITION=your-edition
   LICENSE_EXPIRATION=your-expiration
   LICENSE_SIGNATURE=your-signature
   EOF
   ```

3. **Setup the deployment tools**:
   ```bash
   cd deployment/
   chmod +x *.sh
   ./setup.sh
   ```

## 🚀 Quick Start

### Basic Deployment

```bash
./deployment/deploy.sh

./deployment/deploy.sh uber-eats kafka-k8s

./deployment/deploy.sh uber-eats kafka-k8s-do
```

### Controlled Generation

```bash
./deployment/deploy.sh uber-eats kafka-k8s --count 1000
./deployment/deploy.sh uber-eats kafka-k8s --rate 100
./deployment/deploy.sh uber-eats kafka-k8s --count 10000 --rate 500 --parallel 5
```

### Management

```bash
./deployment/shadowtraffic-ctl.sh status
./deployment/shadowtraffic-ctl.sh logs -f
./deployment/shadowtraffic-ctl.sh topics
./deployment/shadowtraffic-ctl.sh progress
```

## 📊 Data Topics Generated

The system generates data for the following Kafka topics:

| Topic | Description | Data Generated |
|-------|-------------|----------------|
| `kafka-orders` | Customer orders | Order details, items, totals |
| `kafka-events` | System events | User actions, system events |
| `kafka-payments` | Payment transactions | Payment processing events |
| `kafka-status` | Order status updates | Status changes, timestamps |
| `kafka-gps` | GPS tracking | Driver locations, routes |
| `kafka-shift` | Driver shifts | Shift start/end, availability |
| `kafka-search` | Search queries | User searches, filters |
| `kafka-route` | Delivery routes | Optimized paths, distances |
| `kafka-receipts` | Order receipts | Final receipts, totals |
| `mongodb-users` | User profiles | Customer information |
| `postgres-drivers` | Driver profiles | Driver details, ratings |
| `mysql-restaurants` | Restaurant data | Restaurant info, hours |
| `mysql-menu` | Menu items | Food items, prices |
| `mysql-products` | Product catalog | Product details, categories |
| `mongodb-recommendations` | Recommendations | Personalized suggestions |
| `mongodb-support` | Support tickets | Customer support data |
| And more... | | |

## 🎮 Advanced Usage

### Interactive Menu
```bash
./deployment/st-menu.sh
```

### Calculate Optimal Settings
```bash
./deployment/calc-settings.sh
```

### Environment-Specific Deployments
```bash
./deployment/deploy-env.sh dev
./deployment/deploy-env.sh staging
./deployment/deploy-env.sh load
```

### Real-time Monitoring
```bash
./deployment/monitor.sh
./deployment/health-check.sh
```

## ⚙️ Configuration Options

### Generation Control Parameters

| Parameter | Description | Example | Default |
|-----------|-------------|---------|---------|
| `--count` | Total messages per generator | `--count 1000` | Unlimited |
| `--max-events` | Maximum messages (flexible stop) | `--max-events 10000` | Unlimited |
| `--rate` | Messages per time unit | `--rate 100` | Unlimited |
| `--rate-unit` | Time unit (second/minute/hour) | `--rate-unit minute` | second |
| `--parallel` | Parallel generator threads | `--parallel 5` | 1 |
| `--batch` | Kafka batch size | `--batch 1000` | Default |

### Deployment Options

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--namespace` | Kubernetes namespace | `-n production` |
| `--clean` | Clean before deploying | `--clean` |
| `--validate` | Validate without deploying | `--validate` |
| `--debug` | Show configuration transformation | `--debug` |
| `--follow` | Follow logs after deployment | `--follow` |
| `--list` | List available configurations | `--list` |

## 📈 Common Scenarios

### Development Testing
```bash
./deployment/deploy.sh uber-eats kafka-k8s --rate 1 --clean
```

### Integration Testing
```bash
./deployment/deploy.sh uber-eats kafka-k8s --count 1000 --rate 100
```

### Load Testing
```bash
./deployment/deploy.sh uber-eats kafka-k8s --parallel 10 --batch 10000
```

### Production Data Seeding
```bash
./deployment/deploy.sh uber-eats kafka-k8s --count 50000 --rate 1000 --parallel 5
```

## 📁 Project Structure

```
uber-eats-shadow-traffic/
├── deployment/
│   ├── deploy.sh                 
│   ├── shadowtraffic-ctl.sh      
│   ├── deployment.yaml           
│   ├── st-menu.sh               
│   ├── monitor.sh               
│   ├── calc-settings.sh         
│   └── ... (20+ utility scripts)
├── gen/
│   └── template/
│       └── uber-eats.json       
├── connections/
│   └── kafka-k8s.json           
├── st-key.env                   
└── README.md                    
```

## 🐛 Troubleshooting

### Quick Diagnostics
```bash
./deployment/troubleshoot.sh
./deployment/health-check.sh
./deployment/deploy.sh uber-eats kafka-k8s --validate --debug
```

### Common Issues

**Pods not starting:**
```bash
./deployment/shadowtraffic-ctl.sh events
./deployment/shadowtraffic-ctl.sh logs --tail 100
```

**Rate limiting not working:**
- Ensure you're using the latest deploy.sh
- Check that `delay` field is being set: `--debug` flag
- Rate = 1000 / delay (milliseconds)

**High memory usage:**
```bash
./deployment/deploy.sh uber-eats kafka-k8s --parallel 1 --clean
kubectl top pod -n shadowtraffic
```

## 📚 Documentation

- [Generation Control Guide](GENERATION_CONTROL.md) - Comprehensive guide to all features
- [Quick Reference](QUICK_REFERENCE.md) - Parameter quick reference
- [Command Cheat Sheet](COMMAND_CHEATSHEET.md) - All commands at a glance
- [Installation Guide](INSTALLATION.md) - Detailed setup instructions

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [ShadowTraffic](https://shadowtraffic.io) for the powerful data generation engine
- Inspired by real-world food delivery systems
- Built with Kubernetes and Kafka best practices

## 📞 Support

For issues and questions:
- Check the [troubleshooting guide](#-troubleshooting)
- Run `./deployment/troubleshoot.sh` for diagnostics
- Review logs with `./deployment/shadowtraffic-ctl.sh logs`
- Open an issue in the repository

---

**Note**: Remember to keep your `st-key.env` file secure and never commit it to version control.