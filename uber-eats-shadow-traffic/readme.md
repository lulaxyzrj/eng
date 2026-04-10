# Shadow Traffic

### get container
```bash
docker pull shadowtraffic/shadowtraffic:latest
```

### container or bucket
```bash
owshq-shadow-traffic-uber-eats
```

### uber eats: azure
```shell
docker run \
  --env-file st-key.env \
  -v $(pwd)/gen/azure/uber-eats.json:/home/config.json \
  shadowtraffic/shadowtraffic:latest \
  --config /home/config.json
```

## postgres [driver]
```shell
docker run \
  --env-file st-key.env \
  -v $(pwd)/gen/postgres/drivers.json:/home/config.json \
  shadowtraffic/shadowtraffic:latest \
  --config /home/config.json
```

### uber eats: minio
```shell
docker run \
  --env-file st-key.env \
  -e AWS_REGION=us-east-1 \
  -v $(pwd)/gen/minio/uber-eats.json:/home/config.json \
  shadowtraffic/shadowtraffic:latest \
  --config /home/config.json
```

### uber eats: kafka
```shell
docker run \
  --env-file st-key.env \
  -v $(pwd)/gen/kafka/uber-eats.json:/home/config.json \
  shadowtraffic/shadowtraffic:latest \
  --config /home/config.json
```
