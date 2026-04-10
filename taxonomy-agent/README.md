GCP Data Taxonomy Enforcement Agent
This repository contains the code for an AI agent designed to automatically check and enforce data taxonomy for artifacts created within a Google Cloud Platform (GCP) data platform. The agent is built using Google's Agent Development Kit (ADK) and leverages Vertex AI, powered by Gemini foundational models, for its core intelligence and operational capabilities.

Architecture Overview
The agent operates as follows:

Event Trigger: New artifact creation events (e.g., a new BigQuery table, a new Cloud Storage object) are published to a Pub/Sub topic.

Cloud Function Trigger: A Cloud Function subscribes to this Pub/Sub topic and triggers the Vertex AI Agent Engine.

AI Agent Execution: The ADK-based Python agent, deployed on Vertex AI Agent Engine, receives the artifact details.

Artifact Analysis: The agent uses custom tools to read metadata and content from the GCP artifact (e.g., BigQuery schema, Cloud Storage file content).

Taxonomy Classification: The agent leverages a fine-tuned Gemini model (via Vertex AI) to classify the artifact based on predefined taxonomy rules. This involves sophisticated reasoning and potentially multimodal understanding.

Action & Enforcement: Using function calling, the Gemini model instructs the agent to apply appropriate tags in Data Catalog, update Dataplex metadata, or trigger alerts for non-compliance.

MLOps: Vertex AI Pipelines, Model Monitoring, and ML Metadata are used to manage the agent's lifecycle, track lineage, and ensure continuous performance.